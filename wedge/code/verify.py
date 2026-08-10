"""
verify.py
=========
The check-8 ACM result is significant.  Before it is allowed to mean
anything it has to survive the heuristic from section 3 of the handoff:
is the relationship a free parameter of the construction?

r*_ACM  is built from the ACM risk-neutral curve at t-1.
d rn_t  is the change in the ACM risk-neutral curve from t-1 to t+1.

ACM fits a STATIONARY VAR to yield principal components.  A stationary VAR
mechanically produces a negative level-on-change relationship.  So a
regression of the announcement-window change on a pre-meeting level built
from the same fitted state can be pure mean reversion in the ACM state
vector, with no announcement content at all.

Four diagnostics:
  A. Placebo    -- run the identical regression on every non-FOMC trading
                   day.  If the coefficient survives, the FOMC window is
                   doing no work.
  B. Randomised -- 5,000 draws of 115 random non-FOMC dates; where does the
                   FOMC coefficient sit in that distribution?
  C. Horse race -- enter r*_Fed and r*_Mkt separately instead of imposing
                   the -1 coefficient the wedge assumes.
  D. Inference  -- block bootstrap, and a wedge-in-differences specification
                   that does not lean on a near-unit-root regressor.
"""
import json
import numpy as np
import pandas as pd
import statsmodels.api as sm

OUT = "/home/claude/rstar_wedge/results"
RNG = np.random.default_rng(20260810)
V = {}


def hdr(s):
    print("\n" + "=" * 74)
    print(s)
    print("=" * 74)


def fit(y, X, lags=4):
    d = pd.concat([y, X], axis=1).dropna()
    if len(d) < 10:
        return None
    m = sm.OLS(d.iloc[:, 0], sm.add_constant(d.iloc[:, 1:],
                                             has_constant="add")).fit(
        cov_type="HAC", cov_kwds={"maxlags": lags})
    return m


ev = pd.read_csv(f"{OUT}/event_panel.csv", parse_dates=["meeting"])
acm = pd.read_csv(f"{OUT}/acm_derived.csv", parse_dates=["date"])
full = pd.read_excel("/mnt/user-data/uploads/ReactionFunctionProject/"
                     "ACMTermPremium.xls", "ACM Daily")
full["date"] = pd.to_datetime(full["DATE"], format="%d-%b-%Y")
full = full.drop(columns=["DATE"]).sort_values("date").reset_index(drop=True)
full["rstar_acm"] = (10 * full["ACMRNY10"] - 9 * full["ACMRNY09"]) - 2.0

# restrict to the event-study sample period
lo, hi = ev["meeting"].min(), ev["meeting"].max()
full = full[(full["date"] >= lo) & (full["date"] <= hi)].reset_index(drop=True)

# Fed-side r* as a step function over calendar time (last SEP published)
fed = pd.read_csv(f"{OUT}/fed_rstar.csv", parse_dates=["date"])
full = pd.merge_asof(full.sort_values("date"),
                     fed[["date", "rstar_fed"]].rename(
                         columns={"date": "sep_date"}).sort_values("sep_date"),
                     left_on="date", right_on="sep_date",
                     direction="backward")

# 2-day changes with the SAME timing convention as the event study:
# regressor at i-1, change from i-1 to i+1
for n in [2, 5, 10]:
    for kind, pre in [("y", "ACMY"), ("rn", "ACMRNY"), ("tp", "ACMTP")]:
        full[f"d{kind}{n}"] = (full[f"{pre}{n:02d}"].shift(-1)
                               - full[f"{pre}{n:02d}"].shift(1)) * 100
full["w_pre"] = full["rstar_fed"].shift(1) - full["rstar_acm"].shift(1)
full["is_fomc"] = full["date"].isin(ev["meeting"])
full = full.dropna(subset=["w_pre", "dy10"]).reset_index(drop=True)

fomc = full[full["is_fomc"]]
placebo = full[~full["is_fomc"]]
print(f"sample {full['date'].min().date()} to {full['date'].max().date()}"
      f"   FOMC days {len(fomc)}   non-FOMC days {len(placebo)}")

# ==========================================================================
hdr("A.  PLACEBO -- the same regression on every non-FOMC trading day")
# ==========================================================================
V["placebo"] = {}
print("            FOMC days                    non-FOMC days")
print("   var      b       t      n          b       t       n     ratio")
for n in [2, 5, 10]:
    for kind in ["y", "rn", "tp"]:
        c = f"d{kind}{n}"
        mf, mp = fit(fomc[c], fomc[["w_pre"]]), fit(placebo[c], placebo[["w_pre"]])
        bf, bp = mf.params["w_pre"], mp.params["w_pre"]
        print(f"  {n:2d}y {kind:2s}  {bf:+6.2f}  {mf.tvalues['w_pre']:+6.2f} "
              f"{int(mf.nobs):5d}     {bp:+6.2f}  {mp.tvalues['w_pre']:+6.2f} "
              f"{int(mp.nobs):6d}   {bf/bp if bp else np.nan:6.2f}")
        V["placebo"][f"{n}y_{kind}"] = {
            "fomc_b": float(bf), "fomc_t": float(mf.tvalues["w_pre"]),
            "fomc_n": int(mf.nobs), "placebo_b": float(bp),
            "placebo_t": float(mp.tvalues["w_pre"]), "placebo_n": int(mp.nobs),
            "ratio": float(bf / bp) if bp else None}

# ==========================================================================
hdr("B.  RANDOMISATION -- FOMC coefficient vs 5,000 random date sets")
# ==========================================================================
V["randomisation"] = {}
k = len(fomc)
pl = placebo.reset_index(drop=True)
for n in [10]:
    for kind in ["y", "rn", "tp"]:
        c = f"d{kind}{n}"
        obs = fit(fomc[c], fomc[["w_pre"]]).params["w_pre"]
        draws = np.empty(5000)
        x_all = pl["w_pre"].to_numpy()
        y_all = pl[c].to_numpy()
        ok = ~np.isnan(x_all) & ~np.isnan(y_all)
        x_all, y_all = x_all[ok], y_all[ok]
        for i in range(5000):
            s = RNG.choice(len(x_all), size=k, replace=False)
            x, y = x_all[s], y_all[s]
            xm, ym = x.mean(), y.mean()
            draws[i] = ((x - xm) @ (y - ym)) / ((x - xm) @ (x - xm))
        pct = float((draws < obs).mean())
        print(f"  {n}y {kind:2s}  observed b={obs:+6.2f}   "
              f"random-date mean={draws.mean():+6.2f}  sd={draws.std():5.2f}   "
              f"percentile={pct:6.1%}   two-sided p={2*min(pct,1-pct):.3f}")
        V["randomisation"][f"{n}y_{kind}"] = {
            "observed": float(obs), "null_mean": float(draws.mean()),
            "null_sd": float(draws.std()), "percentile": pct,
            "p_two_sided": float(2 * min(pct, 1 - pct))}

# ==========================================================================
hdr("C.  HORSE RACE -- is the wedge, or just the ACM level, doing the work?")
# ==========================================================================
V["horserace"] = {}
e = ev.copy()
for kind in ["y", "rn", "tp"]:
    c = f"d{kind}10_d2"
    m_w = fit(e[c], e[["wedge_acm"]])
    m_m = fit(e[c], e[["rstar_acm"]])
    m_f = fit(e[c], e[["rstar_fed"]])
    m_b = fit(e[c], e[["rstar_fed", "rstar_acm"]])
    print(f"\n  10y {kind}")
    print(f"    ~ wedge            b={m_w.params['wedge_acm']:+7.3f} "
          f"(t {m_w.tvalues['wedge_acm']:+5.2f})   R2={m_w.rsquared:.3f}")
    print(f"    ~ r*_Mkt alone     b={m_m.params['rstar_acm']:+7.3f} "
          f"(t {m_m.tvalues['rstar_acm']:+5.2f})   R2={m_m.rsquared:.3f}")
    print(f"    ~ r*_Fed alone     b={m_f.params['rstar_fed']:+7.3f} "
          f"(t {m_f.tvalues['rstar_fed']:+5.2f})   R2={m_f.rsquared:.3f}")
    print(f"    ~ both             Fed {m_b.params['rstar_fed']:+7.3f} "
          f"(t {m_b.tvalues['rstar_fed']:+5.2f})   "
          f"Mkt {m_b.params['rstar_acm']:+7.3f} "
          f"(t {m_b.tvalues['rstar_acm']:+5.2f})   R2={m_b.rsquared:.3f}")
    # does the wedge restriction (equal and opposite) hold?
    try:
        w = m_b.f_test("rstar_fed + rstar_acm = 0")
        print(f"    F-test of the wedge restriction (b_F = -b_M): "
              f"F={float(np.squeeze(w.fvalue)):.2f}  p={float(np.squeeze(w.pvalue)):.3f}")
        pval = float(np.squeeze(w.pvalue))
    except Exception as exc:
        pval = None
        print(f"    F-test failed: {exc}")
    V["horserace"][kind] = {
        "wedge_b": float(m_w.params["wedge_acm"]),
        "wedge_t": float(m_w.tvalues["wedge_acm"]),
        "wedge_r2": float(m_w.rsquared),
        "mkt_only_b": float(m_m.params["rstar_acm"]),
        "mkt_only_t": float(m_m.tvalues["rstar_acm"]),
        "mkt_only_r2": float(m_m.rsquared),
        "fed_only_b": float(m_f.params["rstar_fed"]),
        "fed_only_t": float(m_f.tvalues["rstar_fed"]),
        "fed_only_r2": float(m_f.rsquared),
        "both_fed_b": float(m_b.params["rstar_fed"]),
        "both_mkt_b": float(m_b.params["rstar_acm"]),
        "both_r2": float(m_b.rsquared),
        "wedge_restriction_p": pval}

# ==========================================================================
hdr("D.  INFERENCE -- block bootstrap and a differenced specification")
# ==========================================================================
V["inference"] = {}
for kind in ["rn", "tp"]:
    c = f"d{kind}10_d2"
    d = e[[c, "wedge_acm"]].dropna().reset_index(drop=True)
    y, x = d[c].to_numpy(), d["wedge_acm"].to_numpy()
    b_obs = np.polyfit(x, y, 1)[0]
    # moving-block bootstrap, block length 8 (about one year of meetings)
    L, nb = 8, int(np.ceil(len(d) / 8))
    bs = np.empty(4000)
    for i in range(4000):
        st = RNG.integers(0, len(d) - L, size=nb)
        idx = np.concatenate([np.arange(s, s + L) for s in st])[:len(d)]
        bs[i] = np.polyfit(x[idx], y[idx], 1)[0]
    lo_, hi_ = np.percentile(bs, [2.5, 97.5])
    print(f"  10y {kind}  b={b_obs:+6.3f}   block-bootstrap 95% CI "
          f"[{lo_:+6.3f}, {hi_:+6.3f}]   "
          f"{'excludes' if lo_ > 0 or hi_ < 0 else 'INCLUDES'} zero")
    V["inference"][f"{kind}_block_bootstrap"] = {
        "b": float(b_obs), "ci_lo": float(lo_), "ci_hi": float(hi_),
        "excludes_zero": bool(lo_ > 0 or hi_ < 0)}

    # differenced: change in the wedge since the previous meeting
    e2 = e.sort_values("meeting").copy()
    e2["dwedge"] = e2["wedge_acm"].diff()
    m = fit(e2[c], e2[["dwedge"]])
    print(f"          differenced wedge: b={m.params['dwedge']:+6.3f} "
          f"(t {m.tvalues['dwedge']:+5.2f})  R2={m.rsquared:.3f}  n={int(m.nobs)}")
    V["inference"][f"{kind}_differenced"] = {
        "b": float(m.params["dwedge"]), "t": float(m.tvalues["dwedge"]),
        "r2": float(m.rsquared), "n": int(m.nobs)}

# ==========================================================================
hdr("E.  SPD longer-run inflation: measured vs assumed")
# ==========================================================================
spd = pd.read_csv(f"{OUT}/spd_rstar.csv", parse_dates=["date"])
g = spd.groupby("pi_source_spd")["pi_star_spd"].agg(["size", "min", "max",
                                                     "nunique"])
print(g.to_string())
V["spd_pi_source"] = g.to_dict()

with open(f"{OUT}/verification.json", "w") as fh:
    json.dump(V, fh, indent=2, default=str)
print(f"\nWrote {OUT}/verification.json")
