# Prompt: Portfolio Efficient Frontier App — v2 (live market data)

I have a working single-file browser app (`portfolio-app/index.html`, attached) that solves a portfolio efficient-frontier QP using Pyodide. Expand it into a v2 that fetches **live historical prices from Yahoo Finance** and derives all inputs from the data. Keep the architecture identical: one self-contained `index.html`, Pyodide v0.29.3, no server, no build step.

## What to keep unchanged

- The `_payload` / `pyodide.globals.set` bridge pattern
- `cvxpy` as the solver with `cp.CLARABEL`
- Pyodide v0.29.3 and `loadPackage(["cvxpy-base", "clarabel"])` (no micropip needed — HTTP is handled entirely in JavaScript)
- Chart.js v4 for the efficient-frontier plot
- The same QP formulation: `min wᵀΣw` s.t. `1ᵀw = 1`, `rᵀw ≥ r*`, optional `w ≥ 0`
- The same chart (scatter + line), key-portfolio table, and clickable weights table

## What changes

In v1, the user typed in expected returns, standard deviations, and a correlation matrix by hand. In v2, the user picks stock tickers; the app downloads 1–5 years of adjusted closing prices from Yahoo Finance and computes all statistics automatically.

The Python solver code itself does **not** change — only the inputs it receives change (it still gets `r`, `Sigma`, `rf`, etc.; those values now come from historical data instead of manual inputs).

---

## Data fetching — JavaScript side

Fetch historical adjusted-close prices for each ticker in plain JavaScript using Yahoo Finance's v8 chart API, proxied through `corsproxy.io` to work around browser CORS restrictions.

**URL pattern:**
```
https://corsproxy.io/?url=https%3A%2F%2Fquery1.finance.yahoo.com%2Fv8%2Ffinance%2Fchart%2F{TICKER}%3Finterval%3D1d%26range%3D{PERIOD}
```

where `PERIOD` is one of `1y`, `2y`, `3y`, `5y`.

**Response parsing:** The JSON returned has the structure:
```json
{
  "chart": {
    "result": [{
      "timestamp": [1609459200, ...],
      "indicators": {
        "adjclose": [{ "adjclose": [132.69, ...] }]
      }
    }]
  }
}
```

Extract `timestamp[]` and `adjclose[]`, filter out `null` / `NaN` entries, and collect `[[timestamp, price], ...]` pairs per ticker.

**Error handling:**
- `chart.error` is non-null → throw with its `description` field
- `result` is missing or empty → throw "No data returned for {ticker}"
- HTTP non-OK → throw "HTTP {status} for {ticker}"
- Network / fetch failure → show a message that the CORS proxy may be unavailable and suggest using the companion notebook instead

Show a per-ticker loading status line while fetching (fetch tickers sequentially or in parallel, whichever is simpler).

---

## Data processing — Python side (in Pyodide)

Pass the raw price data and settings to Python as a JSON payload:

```json
{
  "prices": { "AAPL": [[ts1, p1], [ts2, p2], ...], "MSFT": [...], ... },
  "rf":       0.045,
  "no_short": true,
  "n_pts":    50
}
```

In Python, one entry-point function `process_and_optimize(raw)` does everything and returns JSON:

### Step 1 — Align prices

Group prices by **day bucket** (`day = timestamp // 86400`). Keep only dates where **all** tickers have a price. Require at least 60 common trading days; return an error JSON if not met.

### Step 2 — Log returns and annualisation

Build a price matrix `P` (shape `[days × n_assets]`), ordered by date. Compute daily log returns:

```
log_ret[t, i] = ln(P[t+1, i] / P[t, i])
```

Annualise (252 trading days per year):

```
ann_ret[i]    = mean(log_ret[:, i]) * 252
ann_cov[i, j] = cov(log_ret[:, i], log_ret[:, j]) * 252
```

### Step 3 — QP and frontier sweep

Use the **same `_qp` function** as in v1 (variables: `w` of length `n_assets`; no risk-free asset column is added — the risk-free rate `rf` only enters the Sharpe calculation and the sweep lower bound). Constraints:

- `sum(w) == 1`
- `ann_ret @ w >= r_target`
- `w >= 0` if `no_short` is true

Sweep `r_target` from `rf + 0.001` to `max(ann_ret) * 1.3` in `n_pts` steps.

### Step 4 — Return JSON

```json
{
  "frontier":    [{ "r": 12.3, "std": 18.1, "shp": 0.74, "w": [0.4, 0.3, 0.2, 0.1] }, ...],
  "names":       ["AAPL", "MSFT", "GOOGL", "AMZN"],
  "ann_ret":     [18.2, 14.1, 12.3, 11.0],
  "ann_std":     [28.1, 22.4, 25.0, 20.1],
  "i_mv":        7,
  "i_ms":        22,
  "n_obs":       503
}
```

All percentage values are stored as plain numbers (e.g. `18.2` means 18.2 %).

---

## UI — inputs

### Ticker tag input

A text field where the user types a ticker symbol and presses **Enter** (or **,**) to add it as a removable chip/tag. Each tag shows the symbol and a **×** button. Minimum 2 tickers; maximum 10.

Default tickers on load: `AAPL`, `MSFT`, `GOOGL`, `AMZN`.

Tickers are sent to Yahoo Finance exactly as typed (upper-cased). Show a note that non-US tickers need a suffix (e.g. `SAP.DE`, `7203.T`).

### Other inputs

| Control | Default | Notes |
|---|---|---|
| Period dropdown | `2y` | Options: `1y`, `2y`, `3y`, `5y` |
| Risk-free rate | `4.5 %` | Number input, step 0.1 |
| No short selling | checked | Checkbox |
| Frontier points | `50` | Number input, 10–100 |

### Button

One prominent **"Fetch Data & Compute"** button. While running: disable the button and show a text progress line that updates as each ticker is fetched and then as Python runs.

---

## UI — outputs

### Data preview table

After successful data fetching and before (or alongside) the chart, show a compact table:

| Ticker | Ann. Return | Ann. Std Dev | Obs. |
|---|---|---|---|
| AAPL | 18.2 % | 28.1 % | 503 |
| … | … | … | … |

(`Obs.` is the number of common trading days used.)

### Chart

Same as v1: efficient frontier line + individual asset scatter points (triangle markers) + Min-Variance diamond + Max-Sharpe star. Asset labels on the chart show the ticker symbol.

### Key-portfolio table and weights table

Same structure as v1, but column headers are the ticker symbols instead of A, B, C, F.

---

## Notebook companion (`portfolio_v2.ipynb`)

Also create a Jupyter notebook that does the same calculation server-side using `yfinance`:

```
Cell 1: markdown header (title, Colab badge, model description)
Cell 2: install guard (yfinance + cvxpy + clarabel, only in Colab)
Cell 3: imports
Cell 4: USER CONFIG block — TICKERS, PERIOD, RF_RATE, NO_SHORT, N_PTS
Cell 5: yf.download(TICKERS, period=PERIOD, auto_adjust=True, progress=False)
        prices = raw["Close"].dropna()
Cell 6: log returns → ann_ret, ann_cov; display a stats summary table
Cell 7: same _qp / solve_qp function as v1
Cell 8: frontier sweep
Cell 9: matplotlib plot (same style as v1)
Cell 10: key portfolios table
```

Include a Colab badge pointing to:
`https://colab.research.google.com/github/frankhuettner/ManSciDA-Excel-to-app/blob/main/portfolio-app-v2/portfolio_v2.ipynb`

Default tickers: `AAPL`, `MSFT`, `GOOGL`, `AMZN`
Default period: `2y`
Default `RF_RATE`: `0.045`

---

## Deliver

Two files:
1. `portfolio-app-v2/index.html` — complete self-contained browser app, opens directly from disk
2. `portfolio-app-v2/portfolio_v2.ipynb` — Jupyter notebook, runnable in Colab and locally with `uv`
