"""
br_diagnostic.py
================
Does the announcement-window result survive when the market-side endpoint
comes from a model that HAS an endpoint?

ACM is a stationary VAR on yield PCs, so its endpoint is the sample mean --
a constant.  Bauer-Rudebusch use a shifting endpoint, so i* is genuinely
time-varying.  Two BR series are published in falling-stars-fig4.csv:

    istar.rt    real-time measure
    istar.ese   model-estimated, with istar.lb / istar.ub bands

Both are NOMINAL equilibrium short rates, and so is the SEP longer-run
median, so the wedge is defined on nominal endpoints directly and the
long-run inflation constant cancels:

    Delta = (i*_Fed - pi*) - (i*_Mkt - pi*) = i*_Fed - i*_Mkt

BR ends 2018-03-29.  Everything is therefore reported on the matched
2012-2018 window, with ACM re-run on the SAME window so the comparison is
apples to apples.
"""
import json
import numpy as np
import pandas as pd
import statsmodels.api as sm

UP = "/mnt/user-data/uploads/ReactionFunctionProject"
OUT = "/home/claude/rstar_wedge/results"
D = {}


def hdr(s):
    print("\n" + "=" * 74)
    print(s)
    print("=" * 74)


def fit(y, X, lags=4):
    d = pd.concat([y, X], axis=1).dropna()
    if len(d) < 10:
        return None
    return sm.OLS(d.iloc[:, 0], sm.add_constant(d.iloc[:, 1:],
                                                has_constant="add")).fit(
        cov_type="HAC", cov_kwds={"maxlags": lags})


def show(m, lab, key):
    if m is None:
        print(f"    {lab:32s}  too few obs")
        return None
    print(f"    {lab:32s}  b={m.params[key]:+7.3f}  se={m.bse[key]:6.3f}  "
          f"t={m.tvalues[key]:+5.2f}  p={m.pvalues[key]:.3f}  "
          f"R2={m.rsquared:.3f}  n={int(m.nobs)}")
    return {"b": float(m.params[key]), "se": float(m.bse[key]),
            "t": float(m.tvalues[key]), "p": float(m.pvalues[key]),
            "r2": float(m.rsquared), "n": int(m.nobs)}


br = pd.read_csv(f"{UP}/falling-stars-fig4.csv", parse_dates=["date"])
br = br.rename(columns={"istar.rt": "istar_rt", "istar.ese": "istar_ese",
                        "istar.lb": "istar_lb", "istar.ub": "istar_ub"})
br["band_width"] = br["istar_ub"] - br["istar_lb"]
print(f"BR series: {br['date'].min().date()} to {br['date'].max().date()}, "
      f"{len(br)} quarters")
print(f"  istar_rt  {br['istar_rt'].min():.2f} to {br['istar_rt'].max():.2f}")
print(f"  istar_ese {br['istar_ese'].min():.2f} to {br['istar_ese'].max():.2f}")
print(f"  band width mean {br['band_width'].mean():.2f}pp  "
      f"(2012+: {br[br['date']>='2012-01-01']['band_width'].mean():.2f}pp)")

ev = pd.read_csv(f"{OUT}/event_panel.csv", parse_dates=["meeting"])
# Fed side as a NOMINAL endpoint (SEP longer-run median), previous SEP
ev["istar_fed"] = ev["rstar_fed"] + 2.0
ev["istar_acm"] = ev["rstar_acm"] + 2.0

ev = pd.merge_asof(
    ev.sort_values("meeting"),
    br[["date", "istar_rt", "istar_ese", "band_width"]].rename(
        columns={"date": "br_date"}).sort_values("br_date"),
    left_on="meeting", right_on="br_date", direction="backward",
    tolerance=pd.Timedelta("120D"))

ev["wedge_br_rt"] = ev["istar_fed"] - ev["istar_rt"]
ev["wedge_br_ese"] = ev["istar_fed"] - ev["istar_ese"]

# matched window: meetings where BR is available
W = ev[ev["wedge_br_rt"].notna()].copy()
print(f"\nMatched window: {len(W)} FOMC meetings, "
      f"{W['meeting'].min().date()} to {W['meeting'].max().date()}")

# ==========================================================================
hdr("1.  Do the BR endpoints actually move? (the reason for doing this)")
# ==========================================================================
sub = br[br["date"] >= "2011-10-01"]
for c in ["istar_rt", "istar_ese"]:
    s = sub[c]
    print(f"  {c:10s}  sd={s.std():.3f}  range=[{s.min():.2f}, {s.max():.2f}]"
          f"  distinct={s.round(4).nunique()}/{len(s)}")
print(f"  {'ACM 9y1y':10s}  sd={W['istar_acm'].std():.3f}  "
      f"range=[{W['istar_acm'].min():.2f}, {W['istar_acm'].max():.2f}]")
print(f"  {'SEP LR':10s}  sd={W['istar_fed'].std():.3f}  "
      f"range=[{W['istar_fed'].min():.2f}, {W['istar_fed'].max():.2f}]")
D["endpoint_variation"] = {
    c: {"sd": float(sub[c].std()), "min": float(sub[c].min()),
        "max": float(sub[c].max())} for c in ["istar_rt", "istar_ese"]}

# ==========================================================================
hdr("2.  Gate checks on the BR wedges (matched window)")
# ==========================================================================
D["gate"] = {}
for tag, wcol, mcol in [("BR rt", "wedge_br_rt", "istar_rt"),
                        ("BR ese", "wedge_br_ese", "istar_ese"),
                        ("ACM", "wedge_acm", "istar_acm")]:
    d = W[["istar_fed", mcol, wcol]].dropna()
    vF, vM = d["istar_fed"].var(), d[mcol].var()
    cov = d["istar_fed"].cov(d[mcol])
    corr = d["istar_fed"].corr(d[mcol])
    r2f = fit(d[wcol], d[["istar_fed"]]).rsquared
    r2m = fit(d[wcol], d[[mcol]]).rsquared
    w = W.sort_values("meeting")[wcol].dropna().reset_index(drop=True)
    dd = pd.DataFrame({"w": w, "wl": w.shift(1)}).dropna()
    rho = fit(dd["w"], dd[["wl"]]).params["wl"]
    print(f"  {tag:7s} corr(F,M)={corr:+.3f}  var(wedge)={d[wcol].var():.4f}  "
          f"R2 on F/M = {r2f:.2f}/{r2m:.2f}  AR(1) rho={rho:+.3f}  "
          f"sd(Delta)={w.std():.3f}")
    D["gate"][tag] = {"corr": float(corr), "var_wedge": float(d[wcol].var()),
                      "r2_fed": float(r2f), "r2_mkt": float(r2m),
                      "rho": float(rho), "sd": float(w.std()),
                      "n": int(len(d))}

# ==========================================================================
hdr("3.  THE DIAGNOSTIC -- announcement window, matched 2012-2018 window")
# ==========================================================================
D["diagnostic"] = {}
for tag, wcol in [("ACM (fixed endpoint)", "wedge_acm"),
                  ("BR real-time", "wedge_br_rt"),
                  ("BR model estimate", "wedge_br_ese")]:
    print(f"\n  {tag}")
    for kind, lbl in [("y", "10y total"), ("rn", "10y risk-neutral"),
                      ("tp", "10y term premium")]:
        r = show(fit(W[f"d{kind}10_d2"], W[[wcol]]), lbl, wcol)
        if r:
            D["diagnostic"][f"{tag}|{kind}"] = r

# per-sd, so the three are comparable
hdr("4.  Same thing per standard deviation of the wedge")
print("                              10y total   10y risk-neutral  10y term prem")
D["per_sd"] = {}
for tag, wcol in [("ACM", "wedge_acm"), ("BR rt", "wedge_br_rt"),
                  ("BR ese", "wedge_br_ese")]:
    sd = W[wcol].std()
    row = [f"  {tag:8s} (sd={sd:.3f}pp)  "]
    for kind in ["y", "rn", "tp"]:
        m = fit(W[f"d{kind}10_d2"], W[[wcol]])
        if m is None:
            row.append("      .       ")
            continue
        row.append(f"  {m.params[wcol]*sd:+6.2f}({m.tvalues[wcol]:+5.2f})")
        D["per_sd"][f"{tag}|{kind}"] = {
            "bp_per_sd": float(m.params[wcol] * sd),
            "t": float(m.tvalues[wcol])}
    print("".join(row))

# ==========================================================================
hdr("5.  Horse race: BR and ACM wedges together")
# ==========================================================================
D["horse"] = {}
for kind, lbl in [("rn", "10y risk-neutral"), ("tp", "10y term premium")]:
    m = fit(W[f"d{kind}10_d2"], W[["wedge_acm", "wedge_br_rt"]])
    if m is None:
        continue
    print(f"  {lbl}:  ACM {m.params['wedge_acm']:+6.3f} "
          f"(t {m.tvalues['wedge_acm']:+5.2f})   "
          f"BR {m.params['wedge_br_rt']:+6.3f} "
          f"(t {m.tvalues['wedge_br_rt']:+5.2f})   R2={m.rsquared:.3f}")
    D["horse"][kind] = {"acm_b": float(m.params["wedge_acm"]),
                        "acm_t": float(m.tvalues["wedge_acm"]),
                        "br_b": float(m.params["wedge_br_rt"]),
                        "br_t": float(m.tvalues["wedge_br_rt"]),
                        "r2": float(m.rsquared)}

# ==========================================================================
hdr("6.  Bonus: does the BR uncertainty band matter? (a mini A-R test)")
# ==========================================================================
D["uncertainty"] = {}
W2 = W.copy()
W2["wedge_scaled"] = W2["wedge_br_ese"] / W2["band_width"]
for kind, lbl in [("rn", "10y risk-neutral"), ("tp", "10y term premium")]:
    r1 = show(fit(W2[f"d{kind}10_d2"], W2[["wedge_br_ese"]]),
              f"{lbl} ~ raw wedge", "wedge_br_ese")
    r2_ = show(fit(W2[f"d{kind}10_d2"], W2[["wedge_scaled"]]),
               f"{lbl} ~ wedge / band width", "wedge_scaled")
    D["uncertainty"][kind] = {"raw": r1, "scaled": r2_}

W.to_csv(f"{OUT}/br_matched_panel.csv", index=False)
with open(f"{OUT}/br_diagnostic.json", "w") as fh:
    json.dump(D, fh, indent=2, default=str)
print(f"\nWrote {OUT}/br_diagnostic.json and br_matched_panel.csv")
