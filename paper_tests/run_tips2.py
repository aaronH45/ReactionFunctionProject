"""
Addendum to the TIPS tests:
  1. alpha bound from the breakeven response to dF, all maturities, with the
     t-statistic against the model's SMALLEST prediction (alpha = 0).
  2. the composition ratio in phi_pi units, with Fieller intervals.
  3. formal same-sign test in specification (C).
  4. macro-news robustness for (B): condition the intermeeting regression on the
     near-term nominal forward move, which absorbs the common cycle.
"""
import json
import numpy as np
import pandas as pd
from scipy import stats

rev = pd.read_csv("/home/claude/tests/rev_panel_tips.csv", parse_dates=["date"])
OUT = json.load(open("/home/claude/tests/results_tests.json"))
PHI, KAPPA, MU = 1.5, 0.10, 0.103
def Lam(n, a):
    j = np.arange(0, int(n*12))
    return ((PHI/(PHI-1))*(1-np.exp(-KAPPA*j))*(a+(1-a)*(1-MU)**j)).mean()

def joint(Y, x, lags=4):
    """k equations sharing regressor x. Returns slopes and their HAC covariance."""
    ok = np.isfinite(x) & np.all(np.isfinite(Y), axis=1)
    Y, x = Y[ok], x[ok]; n = len(x); k = Y.shape[1]
    X = np.column_stack([np.ones(n), x]); XtXi = np.linalg.inv(X.T @ X)
    B = np.array([XtXi @ X.T @ Y[:, j] for j in range(k)])
    E = np.column_stack([Y[:, j] - X @ B[j] for j in range(k)])
    g = np.hstack([X * E[:, [j]] for j in range(k)])
    S = g.T @ g
    for L in range(1, lags+1):
        w = 1 - L/(lags+1); G = g[L:].T @ g[:-L]; S += w*(G + G.T)
    Bd = np.zeros((2*k, 2*k))
    for j in range(k): Bd[2*j:2*j+2, 2*j:2*j+2] = XtXi
    V = Bd @ S @ Bd
    idx = [2*j+1 for j in range(k)]
    return B[:, 1], V[np.ix_(idx, idx)], n

def joint_mv(Y, Xm, lags=4):
    """k equations sharing regressor MATRIX Xm; returns slope on col 0 of Xm."""
    ok = np.all(np.isfinite(Xm), axis=1) & np.all(np.isfinite(Y), axis=1)
    Y, Xm = Y[ok], Xm[ok]; n = len(Y); k = Y.shape[1]
    X = np.column_stack([np.ones(n), Xm]); p = X.shape[1]
    XtXi = np.linalg.inv(X.T @ X)
    B = np.array([XtXi @ X.T @ Y[:, j] for j in range(k)])
    E = np.column_stack([Y[:, j] - X @ B[j] for j in range(k)])
    g = np.hstack([X * E[:, [j]] for j in range(k)])
    S = g.T @ g
    for L in range(1, lags+1):
        w = 1 - L/(lags+1); G = g[L:].T @ g[:-L]; S += w*(G + G.T)
    Bd = np.zeros((p*k, p*k))
    for j in range(k): Bd[p*j:p*j+p, p*j:p*j+p] = XtXi
    V = Bd @ S @ Bd
    idx = [p*j+1 for j in range(k)]
    return B[:, 1], V[np.ix_(idx, idx)], n

def fieller(b1, b2, V, a=0.05):
    z = stats.norm.ppf(1-a/2)
    A = b2**2 - z**2*V[1, 1]
    Bq = -2*(b1*b2 - z**2*V[0, 1])
    C = b1**2 - z**2*V[0, 0]
    disc = Bq**2 - 4*A*C
    if disc < 0: return None, "empty"
    r = np.sqrt(disc)
    if A > 0: return (float((-Bq-r)/(2*A)), float((-Bq+r)/(2*A))), "bounded"
    return (float((-Bq+r)/(2*A)), float((-Bq-r)/(2*A))), "unbounded"

MATS = [(f"TIPSF{n:02d}", f"BKEVENF{n:02d}", f"{n}y", n) for n in range(2, 11)]
MATS += [("TIPS5F5", "BKEVEN5F05", "5y5y", 7.5)]

print("="*94)
print("1. ALPHA FROM THE BREAKEVEN RESPONSE TO A DOT REVISION")
print("   model: b_bei(dF) = -100*Lambda(n,alpha)/phi   (negative, growing in alpha)")
print("="*94)
print(f"  {'fwd':>6} {'b_bei':>9} {'se':>6} {'model a=0':>10} {'t vs a=0':>9} "
      f"{'a=0.25':>8} {'t vs .25':>9}   admissible alpha")
alphas = np.linspace(0, 1, 2001); abnd = {}
for rc, bc, nm, nyr in MATS:
    b, V, n = joint(rev[["w_"+rc, "w_"+bc]].values, rev["dF"].values)
    bb, se = b[1], np.sqrt(V[1, 1])
    p0, p25 = -100*Lam(nyr, 0)/PHI, -100*Lam(nyr, .25)/PHI
    ok = [a for a in alphas if abs(bb-(-100*Lam(nyr, a)/PHI))/se < 1.96]
    abnd[nm] = [float(min(ok)), float(max(ok))] if ok else None
    s = f"[{min(ok):.2f}, {max(ok):.2f}]" if ok else "EMPTY (all rejected)"
    print(f"  {nm:>6} {bb:+9.1f} {se:6.1f} {p0:10.1f} {(bb-p0)/se:+9.2f} "
          f"{p25:8.1f} {(bb-p25)/se:+9.2f}   {s}")
OUT["alpha_from_bei_dF"] = abnd

print("\n" + "="*94)
print("2. THE COMPOSITION RATIO, IN PHI_PI UNITS   (ratio = phi_pi - 1)")
print("   intermeeting regression on dM: the alpha-free test")
print("="*94)
print(f"  {'fwd':>6} {'b_real':>9} {'b_bei':>9} {'ratio':>7} {'Fieller 95% (ratio)':>22} "
      f"{'implied phi_pi':>22}")
ratres = {}
for rc, bc, nm, nyr in MATS:
    b, V, n = joint(rev[["i_"+rc, "i_"+bc]].values, rev["dM"].values)
    ci, kind = fieller(b[0], b[1], V)
    rat = b[0]/b[1] if abs(b[1]) > 1e-9 else np.nan
    cs = "n/a" if ci is None else (f"[{ci[0]:+.2f}, {ci[1]:+.2f}]"
                                   + ("" if kind == "bounded" else "*"))
    ps = "n/a" if ci is None else (f"[{1+ci[0]:+.2f}, {1+ci[1]:+.2f}]"
                                   + ("" if kind == "bounded" else "*"))
    ratres[nm] = dict(b_real=float(b[0]), b_bei=float(b[1]), ratio=float(rat),
                      fieller=ci, kind=kind, n=int(n))
    print(f"  {nm:>6} {b[0]:+9.1f} {b[1]:+9.1f} {rat:+7.2f} {cs:>22} {ps:>22}")
OUT["composition_ratio"] = ratres
print("  * = unbounded set (denominator too imprecise); bounded rows are the informative ones")

print("\n" + "="*94)
print("3. SAME-SIGN REQUIREMENT (model: real and breakeven move TOGETHER)")
print("="*94)
for lab, pre, reg in [("window ~ dF", "w_", "dF"),
                      ("window ~ d_delta (paper's literal spec)", "w_", "d_delta"),
                      ("intermeeting ~ dM", "i_", "dM")]:
    b, V, n = joint(rev[["%sTIPSF10" % pre, "%sBKEVENF10" % pre]].values,
                    rev[reg].values)
    same = "SAME" if b[0]*b[1] > 0 else "OPPOSITE"
    # Wald that the two coefficients are equal-signed is not a linear test;
    # report the difference and its se instead
    L = np.array([1.0, -1.0]); d = L @ b; sd = np.sqrt(L @ V @ L)
    print(f"  {lab:42s} real {b[0]:+7.1f}  bei {b[1]:+7.1f}  -> {same:8s}"
          f"   real-bei {d:+7.1f} (t {d/sd:+.2f})")

print("\n" + "="*94)
print("4. MACRO-NEWS ROBUSTNESS FOR THE INTERMEETING TEST")
print("   control: intermeeting change in the 2y nominal forward (common cycle)")
print("="*94)
for rc, bc, nm, nyr in [("TIPSF10", "BKEVENF10", "10y", 10),
                        ("TIPS5F5", "BKEVEN5F05", "5y5y", 7.5)]:
    for lab, Xm in [("unconditional", rev[["dM"]].values),
                    ("+ 2y nominal fwd", rev[["dM", "i_SVENF02"]].values),
                    ("+ 2y and 3y fwd", rev[["dM", "i_SVENF02", "i_SVENF03"]].values)]:
        b, V, n = joint_mv(rev[["i_"+rc, "i_"+bc]].values, Xm)
        ci, kind = fieller(b[0], b[1], V)
        cs = "n/a" if ci is None else (f"[{ci[0]:+.2f}, {ci[1]:+.2f}]"
                                       + ("" if kind == "bounded" else "*"))
        print(f"  {nm:>5} {lab:20s} n={n:3d}  real {b[0]:+7.1f} "
              f"(t{b[0]/np.sqrt(V[0,0]):+5.2f})  bei {b[1]:+6.1f} "
              f"(t{b[1]/np.sqrt(V[1,1]):+5.2f})  ratio {b[0]/b[1]:+6.2f}  {cs}")
    # ex-2020
    m = ~rev.date.dt.year.isin([2020])
    b, V, n = joint(rev.loc[m, ["i_"+rc, "i_"+bc]].values, rev.loc[m, "dM"].values)
    ci, kind = fieller(b[0], b[1], V)
    cs = "n/a" if ci is None else (f"[{ci[0]:+.2f}, {ci[1]:+.2f}]"
                                   + ("" if kind == "bounded" else "*"))
    print(f"  {nm:>5} {'ex 2020':20s} n={n:3d}  real {b[0]:+7.1f} "
          f"(t{b[0]/np.sqrt(V[0,0]):+5.2f})  bei {b[1]:+6.1f} "
          f"(t{b[1]/np.sqrt(V[1,1]):+5.2f})  ratio {b[0]/b[1]:+6.2f}  {cs}")

json.dump(OUT, open("/home/claude/tests/results_tests.json", "w"), indent=1,
          default=lambda o: None)
print("\nsaved.")
