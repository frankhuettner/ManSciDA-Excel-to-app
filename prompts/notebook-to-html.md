# Prompt: Jupyter Notebook → Browser App (HTML)

**How to use**
1. Open an AI assistant — [claude.ai](https://claude.ai), [ChatGPT](https://chat.openai.com), or [Gemini](https://gemini.google.com)
2. Attach your `.ipynb` notebook file
3. Copy everything below the line and send it

---

I have a Jupyter notebook (attached) that contains a working Python optimization solver. Convert it into a single-file browser app.

## Step 1 — Understand the notebook

Read the notebook and identify:

- **The solver function** — the self-contained Python function that takes parameters and returns results
- **The data** — the default parameter values used in the notebook
- **The results** — what the function returns (decision variables, objective value, breakdown)
- **The packages** — which libraries are imported (scipy, cvxpy, numpy, etc.)

Then select the correct Pyodide package call:

| Library used in notebook | Pyodide loadPackage call |
|---|---|
| `scipy.optimize.linprog` or `milp` | `await pyodide.loadPackage(["numpy", "scipy"])` |
| `cvxpy` | `await pyodide.loadPackage(["cvxpy-base", "clarabel"])` |

Note: on PyPI the package is `cvxpy`; in Pyodide it is `cvxpy-base`. The `import cvxpy` statement is identical in both.

## Step 2 — Stack

| Layer | Technology |
|---|---|
| Python runtime in browser | Pyodide v0.29.3 (WebAssembly) |
| Packages | `pyodide.loadPackage([...])` |
| UI | Vanilla HTML + CSS + JavaScript |
| Output | One self-contained `index.html` file |

## Step 3 — index.html structure

Embed the solver function from the notebook as a string constant in the HTML:

```html
<script src="https://cdn.jsdelivr.net/pyodide/v0.29.3/full/pyodide.js"></script>
<script>
const PYTHON = `
import json, numpy as np
# paste solver function from notebook here — keep it identical

def run_from_js(raw):
    p = json.loads(raw)
    # call solver function with parameters from p
    return json.dumps({ ... })   # see serialisation rules
`;

let pyodide = null;
(async () => {
  pyodide = await loadPyodide();
  await pyodide.loadPackage([...]);
  await pyodide.runPythonAsync(PYTHON);
  // hide loading message, show form
})();

async function solve() {
  const data = { /* read inputs from form */ };
  pyodide.globals.set("_payload", JSON.stringify(data));
  const raw = await pyodide.runPythonAsync("run_from_js(_payload)");
  const result = JSON.parse(raw);
  // render results into DOM
}
</script>
```

## Step 4 — App requirements

- Create one editable input field per parameter, pre-filled with the default values from the notebook
- Show a loading message while Pyodide initialises (~15 s first visit, cached after)
- After solving, show:
  1. Optimal values of all decision variables
  2. Objective value
  3. Breakdown of objective components (e.g. fixed vs variable cost)
- Show a clear error message if the solver reports infeasibility

## Step 5 — Serialisation rules (mandatory)

The solver function in the notebook returns numpy types. These must be converted before passing to `json.dumps`:

```python
# numpy array → plain Python list
result_array = np_array.tolist()

# numpy scalar → plain Python float
result_scalar = float(np_scalar)

# correct return
return json.dumps({"values": result_array, "total": result_scalar})
```

The solver function body itself does **not** need to change — only the `run_from_js` wrapper needs the conversions.

## Deliver

One complete `index.html`. No separate files. No build step. Must open directly from disk without a server.
