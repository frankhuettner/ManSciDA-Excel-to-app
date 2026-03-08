# Prompt: Excel → Browser App (HTML)

**How to use**
1. Open an AI assistant — [claude.ai](https://claude.ai), [ChatGPT](https://chat.openai.com), or [Gemini](https://gemini.google.com)
2. Attach your Excel file (`.xlsx`)
3. Copy everything below the line and send it

---

I have an Excel optimization model (attached). Convert it into a single-file browser app.

## Step 1 — Understand the model

Read all sheets. State explicitly:

- **Parameters** — the fixed inputs (numbers the user provides: costs, distances, capacities, etc.)
- **Decision variables** — the cells Excel Solver changes; are they continuous, binary (0 or 1), or integer?
- **Objective** — what is minimized or maximized; write the formula in plain math
- **Constraints** — list each one with its type (≤, ≥, =) and what it means

Then pick the solver:

| Problem type | Objective | Solver |
|---|---|---|
| All variables continuous | Linear | `scipy.optimize.linprog` |
| All variables continuous | Quadratic / conic | CVXPY + Clarabel |
| Any binary or integer variables | Linear | `scipy.optimize.milp` |

## Step 2 — Stack

| Layer | Technology |
|---|---|
| Python runtime in browser | Pyodide v0.29.3 (WebAssembly) |
| Packages | `pyodide.loadPackage([...])` — see table below |
| UI | Vanilla HTML + CSS + JavaScript |
| Output | One self-contained `index.html` file |

Package names for `loadPackage`:

| Solver | Call |
|---|---|
| `scipy.optimize.linprog` or `milp` | `await pyodide.loadPackage(["numpy", "scipy"])` |
| CVXPY + Clarabel | `await pyodide.loadPackage(["cvxpy-base", "clarabel"])` |

## Step 3 — index.html structure

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>...</title>
  <style>/* all CSS inline */</style>
</head>
<body>
  <!-- input form: one editable field per parameter -->
  <!-- loading message (shown while Pyodide boots) -->
  <!-- results area (filled by JS after solving) -->

  <script src="https://cdn.jsdelivr.net/pyodide/v0.29.3/full/pyodide.js"></script>
  <script>
  const PYTHON = `
  import json, numpy as np
  # ... solver code ...
  def run_from_js(raw):
      p = json.loads(raw)
      # solve
      return json.dumps({ ... })   # see serialisation rules below
  `;

  let pyodide = null;
  (async () => {
    pyodide = await loadPyodide();
    await pyodide.loadPackage([...]);
    await pyodide.runPythonAsync(PYTHON);
    // hide loading message, show form
  })();

  async function solve() {
    const data = { /* read all input values from the form */ };
    pyodide.globals.set("_payload", JSON.stringify(data));
    const raw = await pyodide.runPythonAsync("run_from_js(_payload)");
    const result = JSON.parse(raw);
    // render result tables into the DOM
  }
  </script>
</body>
</html>
```

## Step 4 — App requirements

- Pre-fill every input with the **default values from the Excel file**
- All inputs editable — users explore scenarios by changing numbers
- **Loading message** while Pyodide initialises (~15 s first visit, then browser-cached)
- After solving, show:
  1. The optimal values of all decision variables
  2. The objective value
  3. A breakdown of the components that make up the objective
- Clear **error message** when the problem is infeasible (e.g. demand exceeds capacity)

## Step 5 — Serialisation rules (mandatory)

Numpy types crash `json.dumps`. Always convert before returning:

```python
# arrays  →  .tolist()  (converts every element to plain Python int/float)
weights = w.value.tolist()

# scalars  →  float()
total = float(result.fun)

# correct return pattern
return json.dumps({"weights": weights, "total": total, ...})
```

## Deliver

One complete `index.html`. No separate files. No build step. Must open directly from disk.
