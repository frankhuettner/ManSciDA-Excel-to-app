# Prompt: Facility Location App — v2 (expanded)

I have a working single-file browser app (attached) that solves a facility location MILP using Pyodide. Expand it into a more capable v2. Keep the architecture identical: one self-contained `index.html`, Pyodide v0.29.3, no server, no build step.

## What to keep unchanged

- The `run_from_js()` / `_payload` bridge pattern
- `scipy.optimize.milp` as the solver
- Pyodide v0.29.3 and the `loadPackage(["numpy", "scipy"])` call

## Model — cost-minimising facility location

Keep the original cost-minimisation model. Rename "facilities" → "servers" and "customers" → "demand nodes" throughout.

**New parameters (added to existing ones):**
- `(sx[j], sy[j])`: x/y coordinates of server j (map only)
- `(nx[i], ny[i])`: x/y coordinates of demand node i (map only)

Keep `c[i][j]` (service cost matrix), `f[j]` (fixed opening cost), `cap[j]` (capacity), `d[i]` (demand).

**Objective:**

```
min  Σ_j f[j] · y[j]  +  Σ_{i,j} c[i][j] · x[i][j]
```

subject to:
- `Σ_j x[i][j] = d[i]`             (all demand must be met)
- `Σ_i x[i][j] ≤ cap[j] · y[j]`   (server capacity × open/closed)
- `y[j] ∈ {0,1}`,  `x[i][j] ≥ 0`

JSON result fields: `y`, `x`, `fixed_cost`, `var_cost`, `total_cost`.

**Default values** — a 3-server × 3-node example with a non-trivial solution (not all servers needed):

Servers: fixed costs `[80, 150, 100]`, capacities `[300, 100, 200]`, coordinates `[(1,4), (5,7), (8,3)]`

Demand nodes: demands `[100, 60, 240]`, coordinates `[(2,5), (6,6), (7,2)]`

Service cost matrix (server rows × demand-node columns):
```
          Node A  Node B  Node C
Server 1    1.0     2.5     3.5
Server 2    2.0     0.5     2.0
Server 3    3.5     2.0     0.9
```

## Addition 0 — Dynamic servers and demand nodes

Replace the hardcoded 3 × 3 input grid with a fully dynamic one.

**Servers table** — each row has: name, x, y, fixed cost, capacity, and a **✕ Remove** button.
An **"+ Add server"** button appends a new row with sensible defaults.
Adding a server also appends a new **column** to the cost matrix; removing a server removes that column.

**Demand nodes table** — same pattern: name, x, y, revenue, demand, and a **✕ Remove** button.
An **"+ Add node"** button appends a new row. Adding a node appends a new **row** to the cost matrix; removing a node removes that row.

**Cost matrix** — rendered as an editable table that grows and shrinks automatically. Column headers are server names; row headers are node names. Both update immediately when names are edited.

**Payload builder** — iterate over all current rows/columns dynamically. No hardcoded input IDs. Use `data-server` and `data-node` attributes on each cell.

Re-draw the canvas and rebuild the cost matrix whenever a server or node is added or removed.

## Addition 1 — Map: geographic visualisation

Add an HTML5 Canvas panel (no CDN needed) beside the inputs showing:

- **Demand nodes**: circles at `(nx[i], ny[i])`, radius proportional to `d[i]`, labelled with name and demand
- **Servers**: square markers at `(sx[j], sy[j])`, labelled; grey when closed, coloured when open
- **Solution overlay** (shown after each solve): lines from each open server to the nodes it serves, width proportional to units served; unserved nodes shaded differently

Re-draw the canvas whenever inputs change and after each solve.

## Addition 2 — CSV / XLSX data import

Add two buttons in a toolbar above the input section:

Use SheetJS CDN (`https://cdn.jsdelivr.net/npm/xlsx/dist/xlsx.full.min.js`) for both download and upload.

**"Download template"** — generates and immediately downloads `fl-data-template.xlsx` using `XLSX.utils.aoa_to_sheet` + `XLSX.writeFile`. The workbook has three named sheets:

- **servers** — columns: `name`, `map_x`, `map_y`, `fixed_cost`, `capacity`
- **demand_nodes** — columns: `name`, `map_x`, `map_y`, `demand`
- **cost_matrix** — row 1: `["", "Server 1", "Server 2", …]`; subsequent rows: `["Node A", cost0, cost1, …]`

Column names must be descriptive (`map_x`/`map_y` not bare `x`/`y`).

**"Upload data"** — file input (`.xlsx`). Read with `XLSX.read(buf)`, expect the same three named sheets. If a sheet is missing, show a clear error naming the missing sheet. Populate all input fields and re-draw the canvas.

## Testing

Replace the `EXCEL_*` block with reference values for the cost-minimising model. After solving with the default data, record the exact optimum (open servers, fixed cost, variable cost, total cost) and assert against them. Add one edge-case: when all demands are set to zero, verify that no server is opened and total cost = 0.

## Deliver

One complete `index.html`. No separate files. No build step. Must open directly from disk.
