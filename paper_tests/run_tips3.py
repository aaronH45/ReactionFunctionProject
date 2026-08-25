"""
Correct mapping for FORWARD-rate regressions, and the alpha reading.

The model's Lambda(n) is the loading of the n-year YIELD's expectations
component (an average of lambda_j over j<n). The GSW/TIPS regressors used in
the composition test are INSTANTANEOUS FORWARDS, whose loading is lambda_j
itself at j = 12n months:

    lambda_j = phi/(phi-1) * (1 - e^{-kappa j}) * [alpha + (1-alpha)(1-mu)^j]

At j = 120 months the transient term (1-mu)^j = 0.897^120 = 2e-6 is dead, so

    lambda_120 -> phi/(phi-1) * alpha = 3 alpha        (phi = 1.5)

The ten-year instantaneous forward is therefore a near-pure reading of the
permanent share alpha -- far sharper than the yield-level Lambda, where the
transient still contributes. Splitting:

    real forward loading  = lambda_j (phi-1)/phi = 100 alpha  (bp per pp)
    bkeven forward loading= lambda_j / phi       = 200 alpha
    nominal               = lambda_j             = 300 alpha

And for a dot revision dF, with in-window belief adoption theta (unobserved,
bounded above by the 0.82 of Fact 2):

    real   = 100 [1 - (1-theta) lambda_j (phi-1)/phi]
    bkeven =    -100 (1-theta) lambda_j / phi
"""
import json
import numpy as np
import pandas as pd
from scipy import stats

rev = pd.read_csv("/home/claude/tests/rev_panel_tips.csv", parse_dates=["date"])
OUT = json.load(open("/home/claude/tests/results_tests.json"))
PHI, KAPPA, MU = 1.5, 0.10, 0.103

def lam(nyears, a):
    j = 12.0 * nyears
    return (PHI/(PHI-1))*(1-np.exp(-KAPPA*j))*(a + (1-a)*(1-MU)**j)

def joint(Y, x, lags=4):
    ok = np.isfinite(x) & np.all(np.isfinite(Y), axis=1)
    Y, x = Y[ok], x[ok]; n = len(x); k = Y.shape[1]
    X = np.column_stack([np.ones(n), x]); XtXi = np.linalg.inv(X.T @ X)
    B = np.array([XtXi @ X.T @ Y[:, j] for j in range(k)])
    E = np.column_stack([Y[:, j] - X @ B[j] for j in range(k)])
    g = np.hstack([X*E[:, [j]] for j in range(k)])
    S = g.T @ g
    for L in range(1, lags+1):
        w = 1 - L/(lags+1); G = g[L:].T @ g[:-L]; S += w*(G+G.T)
    Bd = np.zeros((2*k, 2*k))
    for j in range(k): Bd[2*j:2*j+2, 2*j:2*j+2] = XtXi
    V = Bd @ S @ Bd; idx = [2*j+1 for j in range(k)]
    return B[:, 1], V[np.ix_(idx, idx)], n

print("lambda_j at the 10y forward (near-pure alpha reading):")
for a in (0, .1, .25, .5, 1.0):
    print(f"   alpha={a:4.2f}:  lambda_120 = {lam(10,a):.3f}   "
          f"nominal {100*lam(10,a):6.1f}  real {100*lam(10,a)*(PHI-1)/PHI:6.1f} "
          f" bkeven {100*lam(10,a)/PHI:6.1f}  bp per pp")

print("\n" + "="*92)
print("ALPHA FROM INTERMEETING FAR-FORWARD LOADINGS ON THE DEALER REVISION dM")
print("="*92)
rows = [("10y fwd nominal", "i_SVENF10", 300.0),
        ("10y fwd real", "i_TIPSF10", 100.0),
        ("10y fwd breakeven", "i_BKEVENF10", 200.0),
        ("9y fwd breakeven", "i_BKEVENF09", 200.0*lam(9, 1)/lam(10, 1)),
        ("8y fwd breakeven", "i_BKEVENF08", 200.0*lam(8, 1)/lam(10, 1))]
res = {}
print(f"  {'series':20s} {'b':>8} {'se':>7} {'implied alpha':>14} {'95% CI for alpha':>22}")
for lab, col, scale in rows:
    b, V, n = joint(rev[[col]].values, rev["dM"].values)
    bb, se = b[0], np.sqrt(V[0, 0])
    a_hat, a_se = bb/scale, se/scale
    lo, hi = a_hat-1.96*a_se, a_hat+1.96*a_se
    res[lab] = dict(b=float(bb), se=float(se), alpha=float(a_hat),
                    ci=[float(lo), float(hi)], n=int(n))
    print(f"  {lab:20s} {bb:+8.1f} {se:7.1f} {a_hat:14.2f}   "
          f"[{lo:+.2f}, {hi:+.2f}]")
print("  (alpha is a share in [0,1]; intervals reaching outside are uninformative there)")

print("\n  with cycle control (intermeeting 2y nominal forward), breakeven 10y:")
def joint_mv(Y, Xm, lags=4):
    ok = np.all(np.isfinite(Xm), axis=1) & np.all(np.isfinite(Y), axis=1)
    Y, Xm = Y[ok], Xm[ok]; n = len(Y); k = Y.shape[1]
    X = np.column_stack([np.ones(n), Xm]); p = X.shape[1]
    XtXi = np.linalg.inv(X.T @ X)
    B = np.array([XtXi @ X.T @ Y[:, j] for j in range(k)])
    E = np.column_stack([Y[:, j] - X @ B[j] for j in range(k)])
    g = np.hstack([X*E[:, [j]] for j in range(k)])
    S = g.T @ g
    for L in range(1, lags+1):
        w = 1-L/(lags+1); G = g[L:].T @ g[:-L]; S += w*(G+G.T)
    Bd = np.zeros((p*k, p*k))
    for j in range(k): Bd[p*j:p*j+p, p*j:p*j+p] = XtXi
    V = Bd @ S @ Bd; idx = [p*j+1 for j in range(k)]
    return B[:, 1], V[np.ix_(idx, idx)], n
for lab, Xm in [("unconditional", rev[["dM"]].values),
                ("+2y fwd", rev[["dM", "i_SVENF02"]].values),
                ("+2y,3y fwd", rev[["dM", "i_SVENF02", "i_SVENF03"]].values)]:
    b, V, n = joint_mv(rev[["i_BKEVENF10"]].values, Xm)
    a_hat = b[0]/200; a_se = np.sqrt(V[0, 0])/200
    print(f"    {lab:14s} alpha = {a_hat:5.2f}  95% CI "
          f"[{a_hat-1.96*a_se:+.2f}, {a_hat+1.96*a_se:+.2f}]")
m = ~rev.date.dt.year.isin([2020])
b, V, n = joint(rev.loc[m, ["i_BKEVENF10"]].values, rev.loc[m, "dM"].values)
a_hat = b[0]/200; a_se = np.sqrt(V[0, 0])/200
print(f"    {'ex 2020':14s} alpha = {a_hat:5.2f}  95% CI "
      f"[{a_hat-1.96*a_se:+.2f}, {a_hat+1.96*a_se:+.2f}]")
OUT["alpha_from_forwards"] = res

print("\n" + "="*92)
print("ALPHA FROM THE WINDOW BREAKEVEN RESPONSE TO dF, AS A FUNCTION OF")
print("IN-WINDOW BELIEF ADOPTION theta   (model: b_bei = -(1-theta) 200 alpha)")
print("="*92)
b, V, n = joint(rev[["w_BKEVENF10"]].values, rev["dF"].values)
bb, se = b[0], np.sqrt(V[0, 0])
print(f"  observed b_bei(dF) at the 10y forward: {bb:+.1f} (se {se:.1f}), n={n}")
print(f"  {'theta':>7} {'implied alpha':>14} {'95% upper bound on alpha':>26}")
tha = {}
for th in (0.0, 0.25, 0.5, 0.82):
    sc = -(1-th)*200.0
    a_hat = bb/sc; a_se = se/abs(sc)
    tha[th] = [float(a_hat), float(a_hat+1.96*a_se)]
    print(f"  {th:7.2f} {a_hat:14.2f} {a_hat+1.96*a_se:26.2f}")
print("  theta = 0.82 is the Fact-2 survey-to-survey adoption coefficient, the")
print("  most generous case; theta = 0 assumes no belief update inside the window.")
OUT["alpha_theta_grid"] = {str(k): v for k, v in tha.items()}

json.dump(OUT, open("/home/claude/tests/results_tests.json", "w"), indent=1,
          default=lambda o: None)
print("\nsaved.")
