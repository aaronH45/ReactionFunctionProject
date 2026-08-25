"""
Data tests from Reaction_Function_Update_Final.pdf (Sections 4.5-4.7).

Conventions (matching the paper's Fact 2 / belieffig.py):
  Fed side    : SEP longer-run funds-rate MEAN of dots at meeting t (rstar_fed_mean,
                already net of 2.0)
  Market side : SPD/SMP longer-run funds-rate median from the latest survey fielded
                before meeting t (rstar_spd, net of 2.0), asof-backward, 120d tol
  delta_t     = market - Fed   (paper eq. 7; delta>0 = Fed sits BELOW the market)
  dM, dF      : revisions of each side between consecutive matched SEP meetings
  d_delta     = dM - dF

Window changes: ACM 2-day [t-1, t+1] (d2) and 1-day (d1) from the event panel,
GSW instantaneous forwards computed here. All in bp; delta in pp.
"""
import json
import numpy as np
import pandas as pd
import statsmodels.api as sm

RNG = np.random.default_rng(42)
D = "/home/claude/tests/data/clean_reactionFunction"
OUT = {}

# ---------------------------------------------------------------- panel ----
fed = pd.read_csv(f"{D}/wedge/fed_rstar.csv", parse_dates=["date"]).sort_values("date")
spd = pd.read_csv(f"{D}/wedge/spd_rstar.csv", parse_dates=["date"]).sort_values("date")
m = pd.merge_asof(fed[["date", "rstar_fed_mean", "rstar_fed", "rstar_fed_sd"]],
                  spd[["date", "rstar_spd", "i_star_iqr_spd"]],
                  on="date", direction="backward",
                  tolerance=pd.Timedelta("120D")).dropna(subset=["rstar_spd"])
m["delta"] = m.rstar_spd - m.rstar_fed_mean            # market - Fed
m["dM"] = m.rstar_spd.diff()
m["dF"] = m.rstar_fed_mean.diff()
m["d_delta"] = m.delta.diff()
m = m.reset_index(drop=True)

print(f"matched SEP meetings: {len(m)}  {m.date.min().date()} -> {m.date.max().date()}")
print(f"gap (Fed-mkt): sd {(-m.delta).std():.3f}  range "
      f"[{(-m.delta).min():+.2f}, {(-m.delta).max():+.2f}]")
rho = m.delta.autocorr()
print(f"delta AR(1): {rho:.3f}   d_delta sd: {m.d_delta.std():.4f}  n_rev {m.d_delta.notna().sum()}")

# Fact-2 replication (validation of convention)
def _beta(x, y):
    z = pd.concat([x.rename("x"), y.rename("y")], axis=1).dropna()
    r = sm.OLS(z.y.values, sm.add_constant(z.x.values)).fit(
        cov_type="HAC", cov_kwds={"maxlags": 2})
    return float(r.params[1]), float(r.tvalues[1]), int(r.nobs)
b1 = _beta(m.dF.shift(1), m.dM)
b2 = _beta(m.dM, m.dF)
print(f"Fact2 check: dealers-on-Fed {b1[0]:+.2f} (t {b1[1]:+.2f}, n {b1[2]}) "
      f"| Fed-on-dealers {b2[0]:+.2f} (t {b2[1]:+.2f}, n {b2[2]})")
OUT["panel"] = dict(n=len(m), sd_gap=float(m.delta.std()),
                    rho_delta=float(rho), sd_ddelta=float(m.d_delta.std()),
                    fact2_dealers_on_fed=b1, fact2_fed_on_dealers=b2)

# ------------------------------------------------- window changes (ACM) ----
ev = pd.read_csv(f"{D}/wedge/event_panel.csv", parse_dates=["meeting"])
wcols = [f"d{k}{n}_{w}" for k in ("y", "rn", "tp") for n in range(1, 11)
         for w in ("d1", "d2")]
m = m.merge(ev[["meeting"] + wcols], left_on="date", right_on="meeting", how="left")

# ------------------------------------------------- window changes (GSW) ----
# instantaneous forwards SVENF01..F10 and 1y-forwards SVEN1F01/04/09
with open(f"{D}/feds200628.csv") as fh:
    for i, line in enumerate(fh):
        if line.startswith("Date,"):
            skip = i
            break
g = pd.read_csv(f"{D}/feds200628.csv", skiprows=skip, na_values="NA")
g["date"] = pd.to_datetime(g["Date"])
g = g.sort_values("date").reset_index(drop=True)
gidx = g["date"].searchsorted
FCOLS = [f"SVENF{n:02d}" for n in range(1, 11)] + ["SVEN1F01", "SVEN1F04", "SVEN1F09"]

def gsw_win(dt, col, k0=-1, k1=1):
    p = gidx(dt)
    if p >= len(g) or g["date"].iloc[p] != dt:
        return np.nan
    i0, i1 = p + k0, p + k1
    if i0 < 0 or i1 >= len(g):
        return np.nan
    return (g[col].iloc[i1] - g[col].iloc[i0]) * 100.0

for col in FCOLS:
    m["w_" + col] = m["date"].map(lambda d: gsw_win(d, col))

# 5y5y forward (nominal): (10*y10 - 5*y5)/5
g["f5y5y"] = (10 * g["SVENY10"] - 5 * g["SVENY05"]) / 5
m["w_f5y5y"] = m["date"].map(lambda d: gsw_win(d, "f5y5y"))

rev = m.dropna(subset=["d_delta", "drn10_d2"]).reset_index(drop=True)
print(f"revision sample with windows: n={len(rev)}")

def hac(y, X, lags=4):
    r = sm.OLS(y, sm.add_constant(X)).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return r

# ===================================================================
# TEST 1 - POWER CALCULATION for Prediction 2 (composition restriction)
# ===================================================================
print("\n" + "=" * 78)
print("TEST 1 - POWER CALCULATION (the paper requires this before Prediction 2)")
print("=" * 78)
sd_dd = rev.d_delta.std()
n_rev = len(rev)
# window-change noise: use total-variance of 2-day far-forward moves as sigma
sig_f = rev.w_f5y5y.std()          # nominal 5y5y fwd, bp, 2-day window
# real & BEI window noise unknown without TIPS; bracket with nominal split
for lab, sig in [("nominal 5y5y fwd (observed)", sig_f),
                 ("real leg if sigma = 0.8x nominal", 0.8 * sig_f),
                 ("BEI leg if sigma = 0.5x nominal", 0.5 * sig_f)]:
    se_b = sig / (sd_dd * np.sqrt(n_rev))
    mde = 2.8 * se_b               # 80% power, 5% two-sided
    print(f"  {lab:38s} sigma={sig:5.1f} bp  se(b)={se_b:5.1f}  MDE={mde:6.1f} bp/pp")
OUT["power"] = dict(sd_ddelta=float(sd_dd), n=n_rev, sigma_f5y5y_bp=float(sig_f),
                    se_b=float(sig_f / (sd_dd * np.sqrt(n_rev))),
                    mde_bp_per_pp=float(2.8 * sig_f / (sd_dd * np.sqrt(n_rev))))

# model-implied effect sizes (bp per pp of d_delta), Lambda table 4.5 at 10y-ish
print("\n  Model-implied REAL-leg coefficients (bp per pp), far-forward ~ Lambda:")
for alpha, lam10 in [(0.0, 0.11), (0.25, 0.77), (0.5, 1.42), (1.0, 2.74)]:
    b_real = lam10 * 100 / 3.0     # Lambda is nominal-endpoint loading = 3x delta
    # real dimension loading = Lambda/ (phi/(phi-1)) * 1 => delta loading /3
    print(f"    alpha={alpha:4.2f}: nominal endpoint loading {lam10:4.2f} "
          f"-> real leg ~{b_real:5.1f} bp/pp, BEI leg ~{2*b_real:5.1f} bp/pp")

# simulation: power for coefficients and for the ratio test  b_bei/b_real = 1/(phi-1)
print("\n  Simulated power (5,000 draws, n=%d, sd(d_delta)=%.3f):" % (n_rev, sd_dd))
def sim_power(b_real, phi=1.5, nsim=5000):
    b_bei = b_real / (phi - 1)
    x = rev.d_delta.values
    rej_real = rej_bei = 0
    ratio_ok = 0
    ratio_se_all = []
    for _ in range(nsim):
        yr = b_real * x + RNG.normal(0, 0.8 * sig_f, n_rev)
        yb = b_bei * x + RNG.normal(0, 0.5 * sig_f, n_rev)
        rr = sm.OLS(yr, sm.add_constant(x)).fit()
        rb = sm.OLS(yb, sm.add_constant(x)).fit()
        if abs(rr.tvalues[1]) > 1.96: rej_real += 1
        if abs(rb.tvalues[1]) > 1.96: rej_bei += 1
        br, bb = rr.params[1], rb.params[1]
        if abs(bb) > 1e-9:
            ratio = br / bb
            se_ratio = abs(ratio) * np.sqrt((rr.bse[1] / br) ** 2 +
                                            (rb.bse[1] / bb) ** 2) if br != 0 else np.inf
            ratio_se_all.append(se_ratio)
            # can we reject ratio = 0 AND distinguish from, e.g., ratio=2 (phi=3)?
            if se_ratio < 0.25:    # would separate 0.5 from 1.0 at ~2se
                ratio_ok += 1
    return rej_real / nsim, rej_bei / nsim, ratio_ok / nsim, float(np.median(ratio_se_all))

OUT["power_sim"] = {}
for b_real in [5, 15, 40, 90]:
    pr, pb, pq, med_se = sim_power(b_real)
    print(f"    b_real={b_real:3d} bp/pp: P(detect real)={pr:.2f}  P(detect BEI)={pb:.2f}"
          f"  P(se(ratio)<0.25)={pq:.2f}  med se(ratio)={med_se:.2f}")
    OUT["power_sim"][b_real] = dict(p_real=pr, p_bei=pb, p_ratio_tight=pq,
                                    med_se_ratio=med_se)

# ===================================================================
# TEST 2 - MATURITY PROFILE (Prediction 4, and the section-4.5 peak)
# ===================================================================
print("\n" + "=" * 78)
print("TEST 2 - MATURITY PROFILE: window changes on d_delta   (bp per pp, HAC4)")
print("=" * 78)
LAMB = {0.00: {2: 0.47, 5: 0.22, 10: 0.11}, 0.25: {2: 0.80, 5: 0.78, 10: 0.77},
        0.50: {2: 1.14, 5: 1.35, 10: 1.42}, 1.00: {2: 1.81, 5: 2.48, 10: 2.74}}
mat_res = {}
print(f"   {'n':>3} {'total':>18} {'risk-neutral':>18} {'term premium':>18}")
for n in range(1, 11):
    row = f"   {n:3d}"
    mat_res[n] = {}
    for k in ("y", "rn", "tp"):
        r = hac(rev[f"d{k}{n}_d2"].values, rev[["d_delta"]].values)
        b, t = r.params[1], r.tvalues[1]
        mat_res[n][k] = (float(b), float(t))
        row += f"  {b:+8.2f} (t{t:+5.2f})"
    print(row)
OUT["maturity_ddelta"] = mat_res

# split regressors: dealer revision (dM, pre-window) vs dot revision (dF, in-window)
# model (eq 13): coef on dM ~ +Lambda(n)  (hump);  coef on dF ~ 1 - Lambda(n) + stance
print("\n  Split: dy(n) ~ dM + dF   (expectations component drn, HAC4)")
print(f"   {'n':>3} {'b_dM (dealer rev)':>20} {'b_dF (dot rev)':>20}")
split_res = {}
for n in range(1, 11):
    z = rev.dropna(subset=[f"drn{n}_d2", "dM", "dF"])
    r = hac(z[f"drn{n}_d2"].values, z[["dM", "dF"]].values)
    split_res[n] = dict(b_dM=(float(r.params[1]), float(r.tvalues[1])),
                        b_dF=(float(r.params[2]), float(r.tvalues[2])))
    print(f"   {n:3d}  {r.params[1]:+10.2f} (t{r.tvalues[1]:+5.2f})"
          f"   {r.params[2]:+10.2f} (t{r.tvalues[2]:+5.2f})")
OUT["maturity_split"] = split_res

# GSW forward-rate profile on d_delta (lambda_j, where the hump peak lives)
print("\n  GSW instantaneous forwards ~ d_delta (lambda profile; peak test eq 12)")
fw_res = {}
for col in [f"SVENF{n:02d}" for n in range(1, 11)]:
    z = rev.dropna(subset=["w_" + col])
    r = hac(z["w_" + col].values, z[["d_delta"]].values)
    fw_res[col] = (float(r.params[1]), float(r.tvalues[1]), int(r.nobs))
    print(f"   {col}: {r.params[1]:+7.2f} (t {r.tvalues[1]:+5.2f}, n {int(r.nobs)})")
OUT["forward_profile"] = fw_res

# formal shape tests on the rn profile: flat (endpoint) vs 1/n decay vs hump
# SUR-style: stack maturities, test b(1)=b(10) [flat] and b(5)-b(1), b(10)-b(5)
from scipy import stats as st
def pairdiff(k, n1, n2):
    d = rev[f"d{k}{n2}_d2"] - rev[f"d{k}{n1}_d2"]
    z = pd.concat([d.rename("d"), rev.d_delta], axis=1).dropna()
    r = hac(z["d"].values, z[["d_delta"]].values)
    return float(r.params[1]), float(r.tvalues[1])
print("\n  Shape contrasts (difference regressions, HAC4):")
shape = {}
for k, lab in [("rn", "risk-neutral"), ("tp", "term premium"), ("y", "total")]:
    d51 = pairdiff(k, 1, 5); d105 = pairdiff(k, 5, 10)
    shape[k] = dict(b5_minus_b1=d51, b10_minus_b5=d105)
    print(f"   {lab:14s}  b(5)-b(1) = {d51[0]:+6.2f} (t {d51[1]:+5.2f})   "
          f"b(10)-b(5) = {d105[0]:+6.2f} (t {d105[1]:+5.2f})")
OUT["shape_tests"] = shape

# ===================================================================
# TEST 3 - SIGN SYMMETRY (Prediction 3: model is LINEAR in delta)
# ===================================================================
print("\n" + "=" * 78)
print("TEST 3 - SIGN SYMMETRY: the model predicts mirror-image responses")
print("=" * 78)
lev = m.dropna(subset=["delta", "dy10_d2"]).copy()
lev["pos"] = (lev.delta > 0).astype(float)
sign_res = {}
for k, lab in [("y", "total"), ("rn", "risk-neutral"), ("tp", "term premium")]:
    ycol = f"d{k}10_d2"
    # interaction: dY = a + b*delta + c*(delta x 1[delta>0])
    X = np.column_stack([lev.delta.values, lev.delta.values * lev.pos.values])
    r = hac(lev[ycol].values, X)
    sign_res[k] = dict(b_neg=(float(r.params[1]), float(r.tvalues[1])),
                       extra_pos=(float(r.params[2]), float(r.tvalues[2])),
                       p_sym=float(r.pvalues[2]), n=int(r.nobs))
    print(f"  {lab:14s} slope(delta<0) {r.params[1]:+6.2f} (t {r.tvalues[1]:+5.2f})"
          f"   extra slope for delta>0 {r.params[2]:+6.2f} (t {r.tvalues[2]:+5.2f})"
          f"   p(symmetric)={r.pvalues[2]:.3f}")
# and in revisions
lev2 = rev.copy(); lev2["pos"] = (lev2.d_delta > 0).astype(float)
for k, lab in [("rn", "risk-neutral rev"), ("tp", "term premium rev")]:
    X = np.column_stack([lev2.d_delta.values, lev2.d_delta.values * lev2.pos.values])
    r = hac(lev2[f"d{k}10_d2"].values, X)
    sign_res[k + "_rev"] = dict(b_neg=(float(r.params[1]), float(r.tvalues[1])),
                                extra_pos=(float(r.params[2]), float(r.tvalues[2])),
                                p_sym=float(r.pvalues[2]), n=int(r.nobs))
    print(f"  {lab:14s} slope(dd<0)   {r.params[1]:+6.2f} (t {r.tvalues[1]:+5.2f})"
          f"   extra slope for dd>0  {r.params[2]:+6.2f} (t {r.tvalues[2]:+5.2f})"
          f"   p(symmetric)={r.pvalues[2]:.3f}")
OUT["sign_symmetry"] = sign_res

# ===================================================================
# TEST 4 - DISPERSION AND THE PREMIUM (Prediction 6, proxy version)
# ===================================================================
print("\n" + "=" * 78)
print("TEST 4 - sigma_delta proxy (dealer longer-run IQR) and the ACM premium")
print("=" * 78)
acm = pd.read_excel(f"{D}/ACMTermPremium.xls", sheet_name="ACM Daily")
acm["date"] = pd.to_datetime(acm["DATE"], format="%d-%b-%Y")
acm = acm.sort_values("date").reset_index(drop=True)
spd2 = spd.dropna(subset=["i_star_iqr_spd"]).copy()
spd2 = pd.merge_asof(spd2, acm[["date"] + [f"ACMTP{n:02d}" for n in range(1, 11)]],
                     on="date", direction="backward")
spd2["d_iqr"] = spd2.i_star_iqr_spd.diff()
print(f"  surveys with IQR: {len(spd2)}  IQR mean {spd2.i_star_iqr_spd.mean():.3f} "
      f"sd {spd2.i_star_iqr_spd.std():.3f}  AR1 {spd2.i_star_iqr_spd.autocorr():.3f}")
disp_res = {}
print(f"   {'n':>3} {'levels b (HAC8)':>20} {'changes b (HAC4)':>20}")
for n in range(1, 11):
    tp = spd2[f"ACMTP{n:02d}"]
    zl = pd.concat([tp.rename("y"), spd2.i_star_iqr_spd.rename("x")], axis=1).dropna()
    rl = sm.OLS(zl.y.values, sm.add_constant(zl.x.values)).fit(
        cov_type="HAC", cov_kwds={"maxlags": 8})
    dc = pd.concat([tp.diff().rename("y"), spd2.d_iqr.rename("x")], axis=1).dropna()
    rc = sm.OLS(dc.y.values * 100, sm.add_constant(dc.x.values)).fit(
        cov_type="HAC", cov_kwds={"maxlags": 4})
    disp_res[n] = dict(level=(float(rl.params[1]), float(rl.tvalues[1])),
                       change_bp=(float(rc.params[1]), float(rc.tvalues[1])))
    print(f"   {n:3d}  {rl.params[1]:+10.2f} (t{rl.tvalues[1]:+5.2f})"
          f"   {rc.params[1]:+10.1f} (t{rc.tvalues[1]:+5.2f})")
OUT["dispersion_premium"] = disp_res

with open("/home/claude/tests/results_tests.json", "w") as fh:
    json.dump(OUT, fh, indent=1)
rev.to_csv("/home/claude/tests/rev_panel.csv", index=False)
print("\nsaved results_tests.json, rev_panel.csv")
