# Prompt: Portfolio Efficient Frontier App — v3 (SQLite scenario storage)

I have a working single-file browser app (`portfolio-app-v2/index.html`, attached) that fetches live Yahoo Finance prices and solves a portfolio efficient-frontier QP using Pyodide. Expand it into a v3 that lets users **save, load, and compare named scenarios** using an in-browser SQLite database. Keep the architecture identical: one self-contained `index.html`, Pyodide v0.29.3, no server, no build step.

## What to keep unchanged

- Everything in v2: ticker tag UI, Yahoo Finance fetch via corsproxy.io, `process_and_optimize` Python function, Chart.js frontier chart, key-portfolio table, clickable weights table
- `loadPackage(["cvxpy-base", "clarabel"])` — no extra packages needed (`sqlite3` is part of Python's standard library and works in Pyodide)

## What changes

After computing a frontier the user can save the full result as a named scenario. Scenarios are stored in an **in-memory SQLite database** that lives for the duration of the browser session. The database can be downloaded as a `.db` file and re-uploaded in a later session to restore all scenarios.

---

## SQLite schema

One table, created on startup:

```sql
CREATE TABLE IF NOT EXISTS scenarios (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  name       TEXT    NOT NULL,
  created_at TEXT    NOT NULL,   -- ISO-8601, e.g. "2025-03-09T14:32:00"
  tickers    TEXT    NOT NULL,   -- JSON array, e.g. ["AAPL","MSFT","GOOGL"]
  period     TEXT    NOT NULL,   -- "1y" / "2y" / "3y" / "5y"
  rf         REAL    NOT NULL,
  no_short   INTEGER NOT NULL,   -- 0 or 1
  ann_ret    TEXT    NOT NULL,   -- JSON array of annualised returns (%)
  ann_std    TEXT    NOT NULL,   -- JSON array of annualised std devs (%)
  n_obs      INTEGER NOT NULL,
  frontier   TEXT    NOT NULL,   -- JSON array of frontier points
  i_mv       INTEGER NOT NULL,
  i_ms       INTEGER NOT NULL
)
```

---

## Python additions

Add three new entry-point functions alongside `process_and_optimize`. All take and return JSON strings, using the same `pyodide.globals.set` / `runPythonAsync` bridge.

### `db_init()`
Creates the `scenarios` table if it does not exist. Call once at boot after Pyodide is ready. Returns `"ok"`.

### `db_save(raw)`
Inserts one row. Payload:
```json
{
  "name": "Tech 2y",
  "created_at": "2025-03-09T14:32:00",
  "tickers":  ["AAPL", "MSFT", "GOOGL"],
  "period":   "2y",
  "rf":       0.045,
  "no_short": true,
  "ann_ret":  [18.2, 14.1, 12.3],
  "ann_std":  [28.1, 22.4, 25.0],
  "n_obs":    503,
  "frontier": [...],
  "i_mv":     7,
  "i_ms":     22
}
```
Returns `{ "id": <new row id> }`.

### `db_list()`
Returns all rows as a JSON array, ordered by `id` descending, with all columns **except `frontier`** (to keep the payload small):
```json
[
  { "id": 2, "name": "Tech 2y", "created_at": "...", "tickers": [...],
    "period": "2y", "rf": 0.045, "no_short": 1,
    "ann_ret": [...], "ann_std": [...], "n_obs": 503, "i_mv": 7, "i_ms": 22 },
  ...
]
```

### `db_load(raw)`
Payload: `{ "id": 2 }`. Returns the full row including `frontier`.

### `db_delete(raw)`
Payload: `{ "id": 2 }`. Deletes the row. Returns `"ok"`.

### `db_export()`
Returns the entire database as a **base-64 encoded string** of the binary `.db` file, so JavaScript can decode and offer it as a download.

### `db_import(raw)`
Payload: `{ "b64": "<base64 string>" }`. Replaces the current in-memory database with the uploaded one. Returns `"ok"` or `{ "error": "..." }`.

**Implementation note:** Use Python's `sqlite3` module with an in-memory database (`conn = sqlite3.connect(":memory:")`). Keep the connection in a module-level variable so all functions share it. For `db_export`, use `conn.serialize()` (available in Python 3.11+ / Pyodide) to get the raw bytes, then `base64.b64encode`.

---

## UI additions

### Save panel (appears after a successful compute)

Below the status bar, show a compact save row:

```
Scenario name: [_______________]   [Save]
```

Pre-fill the name with `"{tickers joined by /"}  {period}"` (e.g. `"AAPL/MSFT/GOOGL  2y"`). Clicking **Save** calls `db_save`, then refreshes the scenarios table.

### Scenarios table

A persistent panel (always visible once `db_init` runs, even before any compute) titled **"Saved scenarios"**. Rendered as a table:

| # | Name | Tickers | Period | rf | Max-Sharpe r | Max-Sharpe σ | | |
|---|---|---|---|---|---|---|---|---|
| 1 | Tech 2y | AAPL MSFT GOOGL | 2y | 4.5% | 18.2% | 22.4% | Load | Delete |

- **Load**: restores the ticker tags, period, rf, no-short checkbox to the saved values; immediately renders the chart and tables from the stored frontier (no re-fetch needed)
- **Delete**: removes the row and refreshes the table
- Show "No scenarios saved yet." when the table is empty

### DB toolbar (above the scenarios table)

Two small buttons:

- **Download .db** — calls `db_export()`, decodes the base-64 string in JavaScript, and triggers a browser download of `portfolio-scenarios.db`
- **Upload .db** — file input (`.db`), reads with `FileReader.readAsArrayBuffer`, base-64 encodes in JavaScript, calls `db_import()`; on success refreshes the scenarios table

---

## Layout

Place the save row and scenarios panel in the **right column**, below the weights table. The left column (inputs) is unchanged.

---

## Deliver

One complete `portfolio-app-v3/index.html`. No separate files. No build step. Must open directly from disk.
