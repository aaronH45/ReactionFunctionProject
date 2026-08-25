"""
Prediction 2: the composition restriction on the TIPS split.

    real endpoint gap / breakeven gap = phi_pi - 1

Three designs, because the timing problem of section 5.1 applies here too.

 (A) WINDOW ON dF  -- the real/breakeven composition of a DOT REVISION.
     Model: a dot revision moves the published endpoint one-for-one in the REAL
     dimension (pi* is 2.0 always), and moves delta by -dF, which feeds back
     through Lambda split (phi-1)/phi real and 1/phi inflation:
         b_real(dF) = 1 - Lambda(n,a)*(phi-1)/phi
         b_bei (dF) =   - Lambda(n,a)/phi
     So breakevens should be NEGATIVE and their size is an alpha thermometer.
 (B) INTERMEETING ON dM -- the clean Prediction-2 test. dM moves delta only,
     and does not touch the published endpoint:
         b_real(dM) = +Lambda(n,a)*(phi-1)/phi
         b_bei (dM) = +Lambda(n,a)/phi
         ratio = phi - 1
 (C) WINDOW ON d_delta -- the paper's literal specification, reported to show
     it is dominated by (A).

Ratios use Fieller intervals off a jointly-estimated HAC covariance, not the
delta method: the denominator is imprecise and the delta method lies there.
"""
import json
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

D = "/home/claude/tests/data/clean_reactionFunction"
rev = pd.read_csv("/home/claude/tests/rev_panel.csv", parse_dates=["date"])
OUT = json.load(open("/home/claude/tests/results_tests.json"))
PHI, KAPPA, MU = 1.5, 0.10, 0.103

def Lam(n, a):
    j = np.arange(0, int(n * 12))
    return ((PHI/(PHI-1))*(1-np.exp(-KAPPA*j))*(a+(1-a)*(1-MU)**j)).mean()

# ---------------------------------------------------------------- curves ----
def load_fed_csv(path):
    with open(path) as fh:
        for i, line in enumerate(fh):
            if line.startswith("Date,"):
                skip = i; break
    d = pd.read_csv(path, skiprows=skip, na_values="NA")
    d["date"] = pd.to_datetime(d["Date"])
    return d.sort_values("date").reset_index(drop=True)

tips = load_fed_csv(f"{D}/feds200805.csv")
gsw = load_fed_csv(f"{D}/feds200628.csv")
cur = tips.merge(gsw[["date"] + [f"SVENF{n:02d}" for n in range(2, 11)]
                     + ["SVENY05", "SVENY10"]], on="date", how="left")
cur["NOMF5F5"] = (10*cur["SVENY10"] - 5*cur["SVENY05"]) / 5
print(f"TIPS curve: {len(tips)} days, {tips.date.min().date()} -> {tips.date.max().date()}")

# additivity check: nominal fwd = real fwd + breakeven fwd?
chk = (cur["SVENF10"] - cur["TIPSF10"] - cur["BKEVENF10"]).abs()
print(f"additivity |SVENF10 - TIPSF10 - BKEVENF10|: max {chk.max():.2e}, "
      f"mean {chk.mean():.2e}  (n={chk.notna().sum()})")

cidx = cur["date"].searchsorted
def win(dt, col, k0=-1, k1=1):
    p = cidx(dt)
    if p >= len(cur) or cur["date"].iloc[p] != dt: return np.nan
    if p+k0 < 0 or p+k1 >= len(cur): return np.nan
    v = cur[col].iloc[p+k1] - cur[col].iloc[p+k0]
    return v*100.0 if np.isfinite(v) else np.nan

REAL = [f"TIPSF{n:02d}" for n in range(2, 11)] + ["TIPS5F5"]
BEI = [f"BKEVENF{n:02d}" for n in range(2, 11)] + ["BKEVEN5F05"]
NOM = [f"SVENF{n:02d}" for n in range(2, 11)] + ["NOMF5F5"]
for c in REAL + BEI + NOM:
    rev["w_" + c] = rev["date"].map(lambda d: win(d, c))

# intermeeting: close(t-2) minus close(prev meeting +1)
def inter_change(i, col):
    d0, d1 = rev.date.iloc[i-1], rev.date.iloc[i]
    p0, p1 = cidx(d0), cidx(d1)
    if p0 >= len(cur) or p1 >= len(cur): return np.nan
    if cur["date"].iloc[p0] != d0 or cur["date"].iloc[p1] != d1: return np.nan
    v = cur[col].iloc[p1-2] - cur[col].iloc[p0+1]
    return v*100.0 if np.isfinite(v) else np.nan
for c in REAL + BEI + NOM:
    rev["i_" + c] = [np.nan] + [inter_change(i, c) for i in range(1, len(rev))]

# ------------------------------------------------------------ estimation ----
def joint(y1, y2, x, lags=4):
    """Two equations, same regressor. Returns (b1,b2,V) with V the 2x2 HAC
    covariance of the slopes, including the cross-equation term."""
    ok = np.isfinite(y1) & np.isfinite(y2) & np.isfinite(x)
    y1, y2, x = y1[ok], y2[ok], x[ok]
    n = len(x)
    X = np.column_stack([np.ones(n), x])
    XtXi = np.linalg.inv(X.T @ X)
    b1 = XtXi @ X.T @ y1
    b2 = XtXi @ X.T @ y2
    e1, e2 = y1 - X @ b1, y2 - X @ b2
    # stacked scores, Newey-West
    S = np.zeros((4, 4))
    g = np.column_stack([X * e1[:, None], X * e2[:, None]])
    S += g.T @ g
    for L in range(1, lags+1):
        w = 1 - L/(lags+1)
        G = g[L:].T @ g[:-L]
        S += w * (G + G.T)
    B = np.zeros((4, 4)); B[:2, :2] = XtXi; B[2:, 2:] = XtXi
    V = B @ S @ B
    idx = [1, 3]
    return b1[1], b2[1], V[np.ix_(idx, idx)], n

def fieller(b1, b2, V, alpha=0.05):
    """95% set for theta = b1/b2 from (b1 - theta b2)^2 = z^2 Var(b1 - theta b2)"""
    z = stats.norm.ppf(1 - alpha/2)
    v11, v12, v22 = V[0, 0], V[0, 1], V[1, 1]
    A = b2**2 - z**2 * v22
    B = -2*(b1*b2 - z**2 * v12)
    C = b1**2 - z**2 * v11
    disc = B**2 - 4*A*C
    if disc < 0:
        return None, "empty (no theta consistent)"
    r = np.sqrt(disc)
    if A > 0:
        lo, hi = (-B - r)/(2*A), (-B + r)/(2*A)
        return (float(lo), float(hi)), "bounded"
    return ((-B + r)/(2*A), (-B - r)/(2*A)), "UNBOUNDED (exclusive of interior)"

def tab(regr, prefix, lab):
    print(f"\n{lab}   (bp per pp, HAC(4))")
    print(f"  {'fwd':>6} {'real':>17} {'breakeven':>17} {'nominal':>17} "
          f"{'ratio r/b':>10} {'Fieller 95%':>26}")
    res = {}
    for rc, bc, nc, nm in zip(REAL, BEI, NOM,
                              [f"{n}y" for n in range(2, 11)] + ["5y5y"]):
        br, bb, V, n = joint(rev[prefix+rc].values, rev[prefix+bc].values,
                             rev[regr].values)
        bn, _, Vn, _ = joint(rev[prefix+nc].values, rev[prefix+nc].values,
                             rev[regr].values)
        tr, tb = br/np.sqrt(V[0, 0]), bb/np.sqrt(V[1, 1])
        tn = bn/np.sqrt(Vn[0, 0])
        ci, kind = fieller(br, bb, V)
        cis = "n/a" if ci is None else (f"[{ci[0]:+.2f}, {ci[1]:+.2f}]"
                                        + ("" if kind == "bounded" else " *unb"))
        res[nm] = dict(real=(float(br), float(tr)), bei=(float(bb), float(tb)),
                       nominal=(float(bn), float(tn)),
                       ratio=float(br/bb) if abs(bb) > 1e-9 else None,
                       fieller=ci, fieller_kind=kind, n=int(n))
        print(f"  {nm:>6} {br:+9.1f} (t{tr:+5.2f}) {bb:+9.1f} (t{tb:+5.2f}) "
              f"{bn:+9.1f} (t{tn:+5.2f}) {br/bb if abs(bb)>1e-9 else np.nan:+10.2f} "
              f"{cis:>26}")
    return res

print("\n" + "="*100)
print("(A) ANNOUNCEMENT WINDOW ON THE DOT REVISION dF")
print("    model: b_real = 1 - Lambda(phi-1)/phi ;  b_bei = -Lambda/phi")
print("="*100)
A = tab("dF", "w_", "window [t-1,t+1] ~ dF")
print("\n  model predictions (bp per pp):")
print(f"  {'alpha':>6} {'real 5y':>9} {'bei 5y':>9} {'real 10y':>9} {'bei 10y':>9}")
for a in (0.0, 0.1, 0.25, 0.5, 1.0):
    print(f"  {a:6.2f} {100*(1-Lam(5,a)*(PHI-1)/PHI):9.1f} {-100*Lam(5,a)/PHI:9.1f} "
          f"{100*(1-Lam(10,a)*(PHI-1)/PHI):9.1f} {-100*Lam(10,a)/PHI:9.1f}")

# alpha bound from the breakeven response to dF
print("\n  alpha admissible from b_bei(dF) at 95%:")
alphas = np.linspace(0, 1, 1001)
ab = {}
for nm, nyr in [("5y", 5), ("10y", 10), ("5y5y", 7.5)]:
    bb, tb = A[nm]["bei"]
    se = abs(bb/tb) if tb != 0 else np.inf
    ok = [a for a in alphas if abs(bb - (-100*Lam(nyr, a)/PHI)) / se < 1.96]
    ab[nm] = [float(min(ok)), float(max(ok))] if ok else None
    print(f"    {nm:>5}: b_bei = {bb:+6.1f} (se {se:4.1f})  -> alpha in "
          + (f"[{min(ok):.2f}, {max(ok):.2f}]" if ok else "EMPTY"))
OUT["tips_alpha_from_bei"] = ab

print("\n" + "="*100)
print("(B) INTERMEETING ON THE DEALER REVISION dM  -- the clean Prediction 2 test")
print("    model: b_real = +Lambda(phi-1)/phi ; b_bei = +Lambda/phi ; ratio = phi-1")
print("="*100)
B = tab("dM", "i_", "intermeeting ~ dM")

print("\n" + "="*100)
print("(C) THE PAPER'S LITERAL SPECIFICATION: window ~ d_delta")
print("="*100)
C = tab("d_delta", "w_", "window [t-1,t+1] ~ d_delta")

# ------------------------------------------------ observed-volatility power --
print("\n" + "="*100)
print("POWER, RE-DONE WITH OBSERVED REAL/BREAKEVEN WINDOW VOLATILITY")
print("="*100)
sd_dd = rev.d_delta.std(); sd_dM = rev.dM.std()
for nm, rc, bc in [("5y5y", "TIPS5F5", "BKEVEN5F05"),
                   ("10y fwd", "TIPSF10", "BKEVENF10")]:
    sr = rev["w_"+rc].std(); sb = rev["w_"+bc].std()
    ir = rev["i_"+rc].std(); ib = rev["i_"+bc].std()
    print(f"  {nm}: window sd real {sr:5.1f} bei {sb:5.1f} bp | "
          f"intermeeting sd real {ir:5.1f} bei {ib:5.1f} bp")
    for lab, s, sx, n in [("window on d_delta", (sr, sb), sd_dd, rev.d_delta.notna().sum()),
                          ("intermeeting on dM", (ir, ib), sd_dM, rev.dM.notna().sum()-1)]:
        mder = 2.8*s[0]/(sx*np.sqrt(n)); mdeb = 2.8*s[1]/(sx*np.sqrt(n))
        print(f"      {lab:22s} MDE real {mder:6.1f}  MDE bei {mdeb:6.1f} bp/pp")
OUT["tips_power"] = dict(
    sd_window_real_5y5y=float(rev["w_TIPS5F5"].std()),
    sd_window_bei_5y5y=float(rev["w_BKEVEN5F05"].std()),
    sd_inter_real_5y5y=float(rev["i_TIPS5F5"].std()),
    sd_inter_bei_5y5y=float(rev["i_BKEVEN5F05"].std()))

# ------------------------------------------------------------ robustness ----
print("\n" + "="*100)
print("ROBUSTNESS ON (A): 10y forward, dF")
print("="*100)
for lab, msk in [("full", rev.date.notna()),
                 ("ex 2020", ~rev.date.dt.year.isin([2020])),
                 ("2013-2019", rev.date < "2020-01-01"),
                 ("2020-2026", rev.date >= "2020-01-01")]:
    s = rev[msk]
    br, bb, V, n = joint(s["w_TIPSF10"].values, s["w_BKEVENF10"].values, s["dF"].values)
    print(f"  {lab:10s} n={n:3d}  real {br:+7.1f} (t{br/np.sqrt(V[0,0]):+5.2f})  "
          f"bei {bb:+7.1f} (t{bb/np.sqrt(V[1,1]):+5.2f})")
# 1-day window
for c in ["TIPSF10", "BKEVENF10", "TIPS5F5", "BKEVEN5F05"]:
    rev["w1_"+c] = rev["date"].map(lambda d: win(d, c, -1, 0))
br, bb, V, n = joint(rev["w1_TIPSF10"].values, rev["w1_BKEVENF10"].values, rev["dF"].values)
print(f"  1-day     n={n:3d}  real {br:+7.1f} (t{br/np.sqrt(V[0,0]):+5.2f})  "
      f"bei {bb:+7.1f} (t{bb/np.sqrt(V[1,1]):+5.2f})")

OUT["tips_A_window_dF"] = A
OUT["tips_B_intermeeting_dM"] = B
OUT["tips_C_window_ddelta"] = C
json.dump(OUT, open("/home/claude/tests/results_tests.json", "w"), indent=1,
          default=lambda o: None)
rev.to_csv("/home/claude/tests/rev_panel_tips.csv", index=False)
print("\nsaved.")
