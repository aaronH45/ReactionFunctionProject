"""
Part 2: formal tests around the split regression.

  drn(n) = a + b_dM * dM + b_dF * dF + e
Model (eq 13, market knows i*F... adapted for the dot reveal):
  dF moves the published endpoint (flat load ~1) and delta (load -Lambda(n))
  dM moves delta only (load +Lambda(n))
  => b_dM = 100*Lambda(n),  b_dM + b_dF = 100*(1 + stance terms) ... in bp/pp
The clean model object testable regardless of how the dot passes through:
  b_dM + b_dF  identifies  100*Lambda(n) + (pass-through - 100)*0 ... no.
Cleanest: b_dM alone would be 100*Lambda(n) IF dealers' pre-window revision
were not also the market's forecast of the dot. Since it is, write the window
response as  w = s*(dF - dM) + 100*Lambda(n)*(dM - dF)*0 + 100*Lambda(n)*dM ...
We therefore report:
  (i)  Wald test of the SURPRISE RESTRICTION b_dM = -b_dF   (pure dot-surprise
       pricing, Lambda = 0)
  (ii) the sum b_dM + b_dF with HAC se: under the restriction-augmented model
       response = s*(dF-dM) + 100*Lambda(n)*dM, the sum identifies 100*Lambda(n).
  (iii) alpha bound: grid over alpha, compute Lambda_alpha(n) from eq (11),
       kappa=0.10/mo, mu=0.103/mo, phi=1.5; find alphas not rejected.
Also: forwards split, d1-window robustness, subsamples.
"""
import json
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

rev = pd.read_csv("/home/claude/tests/rev_panel.csv", parse_dates=["date"])
OUT = json.load(open("/home/claude/tests/results_tests.json"))

PHI, KAPPA, MU = 1.5, 0.10, 0.103

def Lambda(n_years, alpha):
    """average monthly lambda_j over horizon n (paper eq 11 + averaging)"""
    j = np.arange(0, int(n_years * 12))
    lam = (PHI / (PHI - 1)) * (1 - np.exp(-KAPPA * j)) * (
        alpha + (1 - alpha) * (1 - MU) ** j)
    return lam.mean()

# sanity vs the paper's table
chk = {a: [round(Lambda(n, a), 2) for n in (2, 5, 10)] for a in (0, .1, .25, .5, 1)}
print("Lambda check vs paper table 4.5 (2y,5y,10y):")
for a, v in chk.items():
    print(f"  alpha={a:4}: {v}")

def hac(y, X, lags=4):
    return sm.OLS(y, sm.add_constant(X)).fit(cov_type="HAC",
                                             cov_kwds={"maxlags": lags})

print("\n" + "=" * 84)
print("SURPRISE RESTRICTION AND THE SUM  b_dM + b_dF  (risk-neutral, 2-day window)")
print("=" * 84)
print(f" {'n':>3} {'b_dM':>9} {'b_dF':>9} {'sum':>8} {'se(sum)':>8} "
      f"{'t(sum)':>7} {'p(b_dM=-b_dF)':>14}  Lambda*100: a=0 a=.25 a=.5")
sumres = {}
for n in range(1, 11):
    z = rev.dropna(subset=[f"drn{n}_d2", "dM", "dF"])
    r = hac(z[f"drn{n}_d2"].values, z[["dM", "dF"]].values)
    L = np.zeros(len(r.params)); L[1] = 1; L[2] = 1
    s = float(L @ r.params)
    se = float(np.sqrt(L @ r.cov_params() @ L))
    tt = s / se
    w = r.wald_test(np.array([[0, 1, 1]]), scalar=True)  # H0: b_dM + b_dF = 0
    p = float(w.pvalue)
    sumres[n] = dict(b_dM=float(r.params[1]), b_dF=float(r.params[2]),
                     sum=s, se_sum=se, p_surprise=p)
    print(f" {n:3d} {r.params[1]:+9.2f} {r.params[2]:+9.2f} {s:+8.2f} {se:8.2f} "
          f"{tt:+7.2f} {p:14.3f}   "
          f"{100*Lambda(n,0):5.0f} {100*Lambda(n,.25):5.0f} {100*Lambda(n,.5):5.0f}")
OUT["sum_tests"] = sumres

# ---- alpha bound: joint fit of sum(n) to 100*Lambda_alpha(n), n=2,5,10 ------
# use 2,5,10 to limit cross-maturity correlation issues; per-maturity Wald too
print("\nalpha bound from the sum profile (per-maturity 95% test):")
alphas = np.linspace(0, 1, 201)
admiss = {}
for n in (2, 5, 10):
    s, se = sumres[n]["sum"], sumres[n]["se_sum"]
    ok = [a for a in alphas if abs(s - 100 * Lambda(n, a)) / se < 1.96]
    admiss[n] = (min(ok), max(ok)) if ok else None
    lo = f"[{min(ok):.3f}, {max(ok):.3f}]" if ok else "EMPTY - all alpha rejected"
    print(f"  n={n:2d}y: sum={s:+6.2f} (se {se:.2f})  admissible alpha: {lo}")
OUT["alpha_bound"] = {str(k): v for k, v in admiss.items()}

# what does alpha=0 predict vs data? formal rejection of even pure learning
print("\nH0: sum = 100*Lambda_alpha0(n)  (alpha=0, the SMALLEST model effect):")
for n in (2, 5, 10):
    s, se = sumres[n]["sum"], sumres[n]["se_sum"]
    t0 = (s - 100 * Lambda(n, 0)) / se
    print(f"  n={n:2d}y: predicted {100*Lambda(n,0):+6.1f}  estimated {s:+6.2f}  "
          f"t = {t0:+.2f}")

# ---------------- forwards split: where does the dot surprise load? ----------
print("\n" + "=" * 84)
print("GSW FORWARDS ~ dM + dF   (dot-surprise loading by forward maturity)")
print("=" * 84)
fsplit = {}
for nn in range(1, 11):
    col = f"w_SVENF{nn:02d}"
    z = rev.dropna(subset=[col, "dM", "dF"])
    r = hac(z[col].values, z[["dM", "dF"]].values)
    w = r.wald_test(np.array([[0, 1, 1]]), scalar=True)
    fsplit[nn] = dict(b_dM=(float(r.params[1]), float(r.tvalues[1])),
                      b_dF=(float(r.params[2]), float(r.tvalues[2])),
                      p_surprise=float(w.pvalue))
    print(f"  f{nn:02d}: b_dM {r.params[1]:+8.2f} (t{r.tvalues[1]:+5.2f})  "
          f"b_dF {r.params[2]:+8.2f} (t{r.tvalues[2]:+5.2f})  "
          f"p(sum=0) {float(w.pvalue):.3f}")
OUT["forward_split"] = fsplit

# ---------------- robustness ------------------------------------------------
print("\n" + "=" * 84)
print("ROBUSTNESS")
print("=" * 84)
rob = {}
# 1-day window
z = rev.dropna(subset=["drn10_d1", "dM", "dF"])
r = hac(z["drn10_d1"].values, z[["dM", "dF"]].values)
rob["d1_rn10"] = dict(b_dM=(float(r.params[1]), float(r.tvalues[1])),
                      b_dF=(float(r.params[2]), float(r.tvalues[2])))
print(f"  1-day window, rn10:  b_dM {r.params[1]:+.2f} (t {r.tvalues[1]:+.2f})  "
      f"b_dF {r.params[2]:+.2f} (t {r.tvalues[2]:+.2f})  n={int(r.nobs)}")
# subsamples
for lab, mask in [("2013-2019", rev.date < "2020-01-01"),
                  ("2020-2026", rev.date >= "2020-01-01")]:
    z = rev[mask].dropna(subset=["drn10_d2", "dM", "dF"])
    if len(z) > 10:
        r = hac(z["drn10_d2"].values, z[["dM", "dF"]].values)
        rob[lab] = dict(n=int(r.nobs),
                        b_dM=(float(r.params[1]), float(r.tvalues[1])),
                        b_dF=(float(r.params[2]), float(r.tvalues[2])))
        print(f"  {lab}, rn10:  b_dM {r.params[1]:+.2f} (t {r.tvalues[1]:+.2f})  "
              f"b_dF {r.params[2]:+.2f} (t {r.tvalues[2]:+.2f})  n={int(r.nobs)}")
# median dots instead of mean
z = rev.copy()
z["dF_med"] = z.rstar_fed.diff() if "rstar_fed" in z else np.nan
z2 = z.dropna(subset=["drn10_d2", "dM", "dF_med"])
r = hac(z2["drn10_d2"].values, z2[["dM", "dF_med"]].values)
rob["median_dots"] = dict(n=int(r.nobs),
                          b_dM=(float(r.params[1]), float(r.tvalues[1])),
                          b_dF=(float(r.params[2]), float(r.tvalues[2])))
print(f"  median dots, rn10:  b_dM {r.params[1]:+.2f} (t {r.tvalues[1]:+.2f})  "
      f"b_dF {r.params[2]:+.2f} (t {r.tvalues[2]:+.2f})  n={int(r.nobs)}")
# moving-block bootstrap on the 10y sum (L=6)
z = rev.dropna(subset=["drn10_d2", "dM", "dF"]).reset_index(drop=True)
RNG = np.random.default_rng(7)
L, B = 6, 2000
nb = len(z)
sums = []
for _ in range(B):
    starts = RNG.integers(0, nb - L + 1, size=int(np.ceil(nb / L)))
    ii = np.concatenate([np.arange(s, s + L) for s in starts])[:nb]
    zz = z.iloc[ii]
    try:
        rr = sm.OLS(zz["drn10_d2"].values,
                    sm.add_constant(zz[["dM", "dF"]].values)).fit()
        sums.append(rr.params[1] + rr.params[2])
    except Exception:
        pass
lo, hi = np.percentile(sums, [2.5, 97.5])
rob["bootstrap_sum_rn10"] = dict(ci=[float(lo), float(hi)])
print(f"  block bootstrap (L=6) 95% CI for sum at 10y rn: [{lo:+.2f}, {hi:+.2f}]")

OUT["robustness2"] = rob
json.dump(OUT, open("/home/claude/tests/results_tests.json", "w"), indent=1)
print("\nsaved.")
