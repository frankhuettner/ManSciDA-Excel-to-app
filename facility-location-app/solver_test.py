"""
Solver test for the Facility Location Problem.
Run with:  uv run --with scipy python3 solver_test.py
"""
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds

BIG_M = 1e5

# Input data (from Excel template)
c_mat = np.array([
    [1,    0.4,    2.4],   # R1
    [BIG_M, 0.5,  0.8],   # R2  (West unavailable)
    [1.3,  BIG_M, 1.4],   # R3  (North unavailable)
])
f   = np.array([80,  150, 100])   # fixed opening cost
cap = np.array([300, 100, 200])   # capacity
d   = np.array([100,  60, 240])   # demand

FACILITIES = ["West", "North", "East"]
CUSTOMERS  = ["R1",   "R2",   "R3"]

# ── Build MILP ────────────────────────────────────────────────────────────────
n_f, n_c = 3, 3
nv = n_f + n_c * n_f   # 3 binary y_j  +  9 continuous x_ij

obj = np.zeros(nv)
obj[:n_f] = f
for i in range(n_c):
    obj[n_f + i*n_f : n_f + (i+1)*n_f] = c_mat[i]

rows, lo, hi = [], [], []

# demand:   sum_j x_{ij}  >=  d_i
for i in range(n_c):
    r = np.zeros(nv)
    r[n_f + i*n_f : n_f + (i+1)*n_f] = 1.0
    rows.append(r); lo.append(d[i]); hi.append(np.inf)

# capacity: sum_i x_{ij} - cap_j * y_j  <=  0
for j in range(n_f):
    r = np.zeros(nv); r[j] = -cap[j]
    for i in range(n_c):
        r[n_f + i*n_f + j] = 1.0
    rows.append(r); lo.append(-np.inf); hi.append(0.0)

lb = np.zeros(nv)
ub = np.full(nv, np.inf); ub[:n_f] = 1.0
integ = np.zeros(nv); integ[:n_f] = 1

# ── Solve ─────────────────────────────────────────────────────────────────────
res = milp(
    obj,
    constraints=LinearConstraint(np.array(rows), lo, hi),
    integrality=integ,
    bounds=Bounds(lb, ub),
)

assert res.status == 0, f"Solver failed: {res.message}"

y = np.round(res.x[:n_f]).astype(int)
x = res.x[n_f:].reshape(n_c, n_f)

# ── Assertions (known optimum) ────────────────────────────────────────────────
assert list(y) == [1, 0, 1],          f"Wrong open facilities: {y}"
assert abs(res.fun - 644.0) < 0.01,   f"Wrong total cost: {res.fun}"
assert abs(x[0, 0] - 100.0) < 0.01,  "R1 should be served by West"
assert abs(x[1, 2] -  60.0) < 0.01,  "R2 should be served by East"

# ── Print solution ────────────────────────────────────────────────────────────
open_facs = [FACILITIES[j] for j in range(n_f) if y[j]]
print(f"PASS  open={open_facs}  total_cost={res.fun:.2f}\n")

print(f"{'':8s}" + "".join(f"{f:>10s}" for f in FACILITIES))
for i in range(n_c):
    print(f"{CUSTOMERS[i]:8s}" + "".join(f"{x[i,j]:>10.2f}" for j in range(n_f)))

mask = c_mat < BIG_M * 0.9
print(f"\nFixed cost   : {(f * y).sum():>8.2f}")
print(f"Variable cost: {(c_mat * x * mask).sum():>8.2f}")
print(f"Total cost   : {res.fun:>8.2f}")
