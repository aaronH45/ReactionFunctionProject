"""
br_stress.py
============
Three measures agree on the 2012-2018 window.  Before that counts as
robustness, rule out the obvious confounds.

  A. Is the wedge just "the SEP median falling"?  On this window the SEP
     longer-run median drops 4.20 -> 2.75 and R2(wedge on Fed side) is
     0.93-0.96, so the wedge is close to the Fed level with a sign flip.
  B. Is it the 2013 taper tantrum?  One large episode in a 51-meeting window.
  C. Placebo on non-FOMC days, as for ACM.
  D. Is the BR uncertainty band actually varying enough to test?
"""
import json
import numpy as np
import pandas as pd
import statsmodels.api as sm

UP = "/mnt/user-data/uploads/ReactionFunctionProject"
OUT = "/home/claude/rstar_wedge/results"
RNG = np.random.default_rng(20260810)
S = {}


def hdr(s):
    print("\n" + "=" * 74)
    print(s)
    print("=" * 74)


def fit(y, X, lags=4):
    d = pd.concat([y, X], axis=1).dropna()
    if len(d) < 8:
        return None
    return sm.OLS(d.iloc[:, 0], sm.add_constant(d.iloc[:, 1:],
                                                has_constant="add")).fit(
        cov_type="HAC", cov_kwds={"maxlags": lags})


W = pd.read_csv(f"{OUT}/br_matched_panel.csv", parse_dates=["meeting"])
br = pd.read_csv(f"{UP}/falling-stars-fig4.csv", parse_dates=["date"])
br = br.rename(columns={"istar.rt": "istar_rt", "istar.ese": "istar_ese",
                        "istar.lb": "istar_lb", "istar.ub": "istar_ub"})
br["band_width"] = br["istar_ub"] - br["istar_lb"]

WEDGES = [("ACM", "wedge_acm"), ("BR rt", "wedge_br_rt"),
          ("BR ese", "wedge_br_ese")]

# ==========================================================================
hdr("A.  Is it just the SEP median falling?")
# ==========================================================================
S["confound"] = {}
print("  10y term premium\n")
for tag, w in WEDGES:
    m0 = fit(W["dtp10_d2"], W[[w]])
    m1 = fit(W["dtp10_d2"], W[[w, "istar_fed"]])
    W["trend"] = np.arange(len(W))
    m2 = fit(W["dtp10_d2"], W[[w, "trend"]])
    m3 = fit(W["dtp10_d2"], W[["istar_fed"]])
    print(f"  {tag:7s} alone           b={m0.params[w]:+7.3f} "
          f"(t {m0.tvalues[w]:+5.2f})  R2={m0.rsquared:.3f}")
    print(f"  {'':7s} + Fed level     b={m1.params[w]:+7.3f} "
          f"(t {m1.tvalues[w]:+5.2f})  R2={m1.rsquared:.3f}   "
          f"[Fed b={m1.params['istar_fed']:+6.2f}, "
          f"t={m1.tvalues['istar_fed']:+5.2f}]")
    print(f"  {'':7s} + time trend    b={m2.params[w]:+7.3f} "
          f"(t {m2.tvalues[w]:+5.2f})  R2={m2.rsquared:.3f}")
    S["confound"][tag] = {
        "alone_b": float(m0.params[w]), "alone_t": float(m0.tvalues[w]),
        "ctrl_fed_b": float(m1.params[w]), "ctrl_fed_t": float(m1.tvalues[w]),
        "ctrl_trend_b": float(m2.params[w]),
        "ctrl_trend_t": float(m2.tvalues[w])}
print(f"\n  Fed level ALONE          b={m3.params['istar_fed']:+7.3f} "
      f"(t {m3.tvalues['istar_fed']:+5.2f})  R2={m3.rsquared:.3f}")
S["fed_alone"] = {"b": float(m3.params["istar_fed"]),
                  "t": float(m3.tvalues["istar_fed"]),
                  "r2": float(m3.rsquared)}

# ==========================================================================
hdr("B.  Is it the 2013 taper tantrum, or one or two big days?")
# ==========================================================================
S["influence"] = {}
big = W.reindex(W["dtp10_d2"].abs().sort_values(ascending=False).index).head(6)
print("  Largest |2-day 10y TP change| in the window:")
for _, r in big.iterrows():
    print(f"    {r['meeting'].date()}   dTP={r['dtp10_d2']:+7.2f}bp   "
          f"wedge_acm={r['wedge_acm']:+.2f}  wedge_br_rt={r['wedge_br_rt']:+.2f}")

print()
cuts = {"full window": W,
        "drop 2013": W[W["meeting"].dt.year != 2013],
        "drop top 3 |dTP|": W.drop(big.index[:3]),
        "2014 onward": W[W["meeting"] >= "2014-01-01"]}
for name, s in cuts.items():
    row = [f"  {name:20s} n={len(s):3d}"]
    for tag, w in WEDGES:
        m = fit(s["dtp10_d2"], s[[w]])
        row.append(f"   {tag}: {m.params[w]:+6.2f}({m.tvalues[w]:+5.2f})"
                   if m is not None else f"   {tag}:     .   ")
        if m is not None:
            S["influence"][f"{name}|{tag}"] = {
                "b": float(m.params[w]), "t": float(m.tvalues[w]),
                "n": int(m.nobs)}
    print("".join(row))

# ==========================================================================
hdr("C.  Placebo on non-FOMC days, BR wedges")
# ==========================================================================
S["placebo"] = {}
full = pd.read_excel(f"{UP}/ACMTermPremium.xls", "ACM Daily")
full["date"] = pd.to_datetime(full["DATE"], format="%d-%b-%Y")
full = full.drop(columns=["DATE"]).sort_values("date").reset_index(drop=True)
full = full[(full["date"] >= W["meeting"].min())
            & (full["date"] <= W["meeting"].max())].reset_index(drop=True)
fed = pd.read_csv(f"{OUT}/fed_rstar.csv", parse_dates=["date"])
full = pd.merge_asof(full, fed[["date", "rstar_fed"]].rename(
    columns={"date": "sep_date"}), left_on="date", right_on="sep_date",
    direction="backward")
full["istar_fed"] = full["rstar_fed"] + 2.0
full = pd.merge_asof(full, br[["date", "istar_rt", "istar_ese"]].rename(
    columns={"date": "br_date"}), left_on="date", right_on="br_date",
    direction="backward")
full["dtp10"] = (full["ACMTP10"].shift(-1) - full["ACMTP10"].shift(1)) * 100
full["w_rt"] = full["istar_fed"].shift(1) - full["istar_rt"].shift(1)
full["w_ese"] = full["istar_fed"].shift(1) - full["istar_ese"].shift(1)
full["is_fomc"] = full["date"].isin(W["meeting"])
full = full.dropna(subset=["dtp10", "w_rt"])
pl, fo = full[~full["is_fomc"]], full[full["is_fomc"]]
print(f"  FOMC days {len(fo)}   non-FOMC days {len(pl)}")
for lab, c in [("BR rt", "w_rt"), ("BR ese", "w_ese")]:
    mf, mp = fit(fo["dtp10"], fo[[c]]), fit(pl["dtp10"], pl[[c]])
    print(f"  {lab:7s} 10y TP   FOMC b={mf.params[c]:+6.2f} "
          f"(t {mf.tvalues[c]:+5.2f})    non-FOMC b={mp.params[c]:+6.2f} "
          f"(t {mp.tvalues[c]:+5.2f})")
    S["placebo"][lab] = {"fomc_b": float(mf.params[c]),
                         "fomc_t": float(mf.tvalues[c]),
                         "placebo_b": float(mp.params[c]),
                         "placebo_t": float(mp.tvalues[c])}

# ==========================================================================
hdr("D.  Does the BR uncertainty band vary enough to be a test?")
# ==========================================================================
b12 = br[br["date"] >= "2012-01-01"]["band_width"]
print(f"  band width 2012+: mean {b12.mean():.3f}  sd {b12.std():.3f}  "
      f"range [{b12.min():.3f}, {b12.max():.3f}]  "
      f"coefficient of variation {b12.std()/b12.mean():.3f}")
print("  -> a regressor rescaled by something this close to constant is not")
print("     an independent test of whether uncertainty matters.")
S["band_width"] = {"mean": float(b12.mean()), "sd": float(b12.std()),
                   "cv": float(b12.std() / b12.mean())}

with open(f"{OUT}/br_stress.json", "w") as fh:
    json.dump(S, fh, indent=2, default=str)
print(f"\nWrote {OUT}/br_stress.json")
