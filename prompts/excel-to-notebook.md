# Prompt: Excel → Jupyter Notebook

**How to use**
1. Open an AI assistant — [claude.ai](https://claude.ai), [ChatGPT](https://chat.openai.com), or [Gemini](https://gemini.google.com)
2. Attach your Excel file (`.xlsx`)
3. Copy everything below the line and send it

---

I have an Excel optimization model (attached). Convert it into a Jupyter notebook.

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

## Step 2 — Notebook structure

Produce a `.ipynb` notebook with these cells in order:

1. **Install cell** (first cell, always include):
   ```python
   import sys
   if "google.colab" in sys.modules:
       %pip install cvxpy clarabel -q   # adjust packages to match chosen solver
   ```

2. **Imports** — numpy, pandas, the chosen solver library, matplotlib if plotting

3. **Data** — all parameters as named variables with comments; include a `pd.DataFrame` display of any matrix inputs

4. **Solver function** — a clean Python function that takes parameters and returns results; identical logic to what would go in a browser app

5. **Solve and test** — call the function with the default values; add `assert` statements to verify the output matches the Excel solution

6. **Results** — display output as `pd.DataFrame` tables with clear labels

7. **Sensitivity analysis** (if applicable) — re-solve for a range of one key parameter to show how the solution changes

## Step 3 — Code quality

- Use descriptive variable names that match the Excel sheet labels
- Add a brief markdown cell before each section explaining what it does
- The solver function must be self-contained (no global state) so it can be copy-pasted into other files

## Deliver

One complete `.ipynb` notebook. The notebook must:
- Run top-to-bottom without errors in Google Colab (after the install cell)
- Reproduce the exact numerical solution from the Excel file
- All assertions must pass
