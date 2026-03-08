"""
Solver test for the Portfolio Efficient Frontier.
Run with:  uv run --with cvxpy --with clarabel python3 solver_test.py
"""
import numpy as np
import cvxpy as cp

# ── Data (from portfolio-efficient-frontier-solution.xlsx) ───────────────────
r    = np.array([0.12, 0.09, 0.05, 0.03])   # A, B, C, F
sig  = np.array([0.22, 0.14, 0.08, 0.0])
corr = np.array([[1.0, 0.5, 0.2],
                 [0.5, 1.0, 0.5],
                 [0.2, 0.5, 1.0]])

n, n_r = 4, 3
rf = float(r[-1])

# Build covariance matrix (F row/col = 0 — risk-free)
Sigma = np.zeros((n, n))
for i in range(n_r):
    for j in range(n_r):
        Sigma[i, j] = corr[i, j] * sig[i] * sig[j]

# ── Helper ───────────────────────────────────────────────────────────────────
def solve_qp(r_target, no_short=True, allow_borrow=True):
    w = cp.Variable(n)
    cons = [cp.sum(w) == 1, r @ w >= r_target]
    if no_short:    cons.append(w[:n_r] >= 0)
    if not allow_borrow: cons.append(w[n_r:] >= 0)
    prob = cp.Problem(cp.Minimize(cp.quad_form(w, Sigma)), cons)
    prob.solve(solver=cp.CLARABEL)
    assert prob.status in ("optimal", "optimal_inaccurate"), f"Solver failed: {prob.status}"
    return w.value, float(r @ w.value), float(np.sqrt(w.value @ Sigma @ w.value))

# ── Test 1: Known Excel solution at 13% target ───────────────────────────────
wv, ret, std = solve_qp(0.13, no_short=True, allow_borrow=True)
print(f"Test 1 — target 13%")
print(f"  Weights  A={wv[0]:.4f}  B={wv[1]:.4f}  C={wv[2]:.4f}  F={wv[3]:.4f}")
print(f"  Return   {ret*100:.2f}%   (Excel: 13.00%)")
print(f"  Std Dev  {std*100:.2f}%   (Excel: 20.52%)")
print(f"  Sharpe   {(ret-rf)/std:.4f}  (Excel: 0.487)")

assert abs(ret  - 0.13)   < 1e-4, f"Return mismatch: {ret}"
assert abs(std  - 0.2052) < 1e-3, f"Std mismatch: {std}"
assert abs(wv[0] - 0.5055) < 1e-3, "Weight A mismatch"
assert abs(wv[3] - (-0.6428)) < 1e-3, "Weight F mismatch (borrowing)"
print("  PASS\n")

# ── Test 2: Min-variance portfolio (solve at r_target = rf + ε) ──────────────
wv_mv, ret_mv, std_mv = solve_qp(rf + 1e-4)
print(f"Test 2 — minimum variance portfolio")
print(f"  Return   {ret_mv*100:.2f}%")
print(f"  Std Dev  {std_mv*100:.2f}%")
print(f"  Weights  A={wv_mv[0]:.4f}  B={wv_mv[1]:.4f}  C={wv_mv[2]:.4f}  F={wv_mv[3]:.4f}")
assert std_mv < std, "Min-var should have lower std than 13%-target portfolio"
print("  PASS\n")

# ── Test 3: No borrowing constraint pushes F >= 0 ───────────────────────────
wv_nb, ret_nb, std_nb = solve_qp(0.10, no_short=True, allow_borrow=False)
print(f"Test 3 — no borrowing, target 10%")
print(f"  Weights  A={wv_nb[0]:.4f}  B={wv_nb[1]:.4f}  C={wv_nb[2]:.4f}  F={wv_nb[3]:.4f}")
assert wv_nb[3] >= -1e-6, f"F should be >= 0 with no-borrow constraint: {wv_nb[3]}"
print("  PASS\n")

# ── Efficient frontier sweep ─────────────────────────────────────────────────
print("Efficient frontier (10 points, no-short, allow-borrow):")
print(f"  {'Return':>8}  {'Std Dev':>8}  {'Sharpe':>8}")
for r_tgt in np.linspace(rf + 0.001, 0.13, 10):
    wv_f, ret_f, std_f = solve_qp(r_tgt)
    shp = (ret_f - rf) / std_f if std_f > 1e-9 else 0
    print(f"  {ret_f*100:>7.2f}%  {std_f*100:>7.2f}%  {shp:>8.4f}")

print("\nAll tests PASSED.")
