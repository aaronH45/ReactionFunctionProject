"""
robustness.py
=============
Three things the main table cannot settle.

  F. Comparable units -- the SPD wedge has one sixth the standard deviation
     of the ACM wedge, so a null SPD coefficient may be low power rather
     than disagreement.  Report bp per standard deviation of the wedge.
  G. Beyond the expectations channel -- Hillenbrand predicts the
     risk-neutral component moves.  Does the term premium still respond
     once the announcement's own expectations move is controlled for?
  H. Subsamples -- ZLB (2012-2015), normalisation (2016-2019),
     pandemic and after (2020-2026).
"""
import json
import numpy as np
import pandas as pd
import statsmodels.api as sm

OUT = "/home/claude/rstar_wedge/results"
B = {}


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


ev = pd.read_csv(f"{OUT}/event_panel.csv", parse_dates=["meeting"])

# ==========================================================================
hdr("F.  COMPARABLE UNITS -- bp per standard deviation of the wedge")
# ==========================================================================
B["standardised"] = {}
for tag, w in [("ACM", "wedge_acm"), ("SPD", "wedge_spd")]:
    sd = ev[w].std()
    print(f"\n  {tag}   sd(Delta) = {sd:.3f} pp   n = {ev[w].notna().sum()}")
    for kind, lbl in [("y", "total"), ("rn", "risk-neutral"),
                      ("tp", "term premium")]:
        m = fit(ev[f"d{kind}10_d2"], ev[[w]])
        if m is None:
            continue
        b = m.params[w] * sd
        se = m.bse[w] * sd
        print(f"    10y {lbl:13s}  {b:+6.2f} bp per sd   "
              f"(se {se:5.2f}, t {m.tvalues[w]:+5.2f})")
        B["standardised"][f"{tag}_{kind}"] = {
            "bp_per_sd": float(b), "se_per_sd": float(se),
            "t": float(m.tvalues[w]), "sd_wedge": float(sd),
            "n": int(m.nobs)}

# ==========================================================================
hdr("G.  BEYOND THE EXPECTATIONS CHANNEL")
# ==========================================================================
# Hillenbrand's prediction is about the expectations component.  Condition on
# the announcement's own 1y risk-neutral move -- the cleanest available proxy
# for the near-term policy surprise -- and see whether the wedge still moves
# the term premium.
B["conditional"] = {}
for tag, w in [("ACM", "wedge_acm"), ("SPD", "wedge_spd")]:
    print(f"\n  wedge = {tag}")
    m0 = fit(ev["dtp10_d2"], ev[[w]])
    m1 = fit(ev["dtp10_d2"], ev[[w, "drn1_d2"]])
    m2 = fit(ev["dtp10_d2"], ev[[w, "drn1_d2", "drn2_d2"]])
    if m0 is None:
        continue
    print(f"    10y TP ~ wedge                      "
          f"b={m0.params[w]:+6.3f} (t {m0.tvalues[w]:+5.2f})  R2={m0.rsquared:.3f}")
    print(f"    10y TP ~ wedge + d rn 1y            "
          f"b={m1.params[w]:+6.3f} (t {m1.tvalues[w]:+5.2f})  R2={m1.rsquared:.3f}")
    print(f"    10y TP ~ wedge + d rn 1y + d rn 2y  "
          f"b={m2.params[w]:+6.3f} (t {m2.tvalues[w]:+5.2f})  R2={m2.rsquared:.3f}")
    B["conditional"][tag] = {
        "uncond_b": float(m0.params[w]), "uncond_t": float(m0.tvalues[w]),
        "cond1_b": float(m1.params[w]), "cond1_t": float(m1.tvalues[w]),
        "cond2_b": float(m2.params[w]), "cond2_t": float(m2.tvalues[w])}

# ==========================================================================
hdr("H.  SUBSAMPLES")
# ==========================================================================
B["subsamples"] = {}
cuts = {"2012-2015 ZLB": ("2012-01-01", "2015-12-31"),
        "2016-2019 normalisation": ("2016-01-01", "2019-12-31"),
        "2020-2026 pandemic on": ("2020-01-01", "2026-12-31")}
for name, (a, b_) in cuts.items():
    s = ev[(ev["meeting"] >= a) & (ev["meeting"] <= b_)]
    print(f"\n  {name}   n = {len(s)}")
    for kind, lbl in [("y", "total"), ("rn", "risk-neutral"),
                      ("tp", "term premium")]:
        m = fit(s[f"d{kind}10_d2"], s[["wedge_acm"]])
        if m is None:
            print(f"    10y {lbl:13s}  too few observations")
            continue
        print(f"    10y {lbl:13s}  b={m.params['wedge_acm']:+7.3f} "
              f"(t {m.tvalues['wedge_acm']:+5.2f})  R2={m.rsquared:.3f}  "
              f"n={int(m.nobs)}")
        B["subsamples"][f"{name}|{kind}"] = {
            "b": float(m.params["wedge_acm"]),
            "t": float(m.tvalues["wedge_acm"]),
            "r2": float(m.rsquared), "n": int(m.nobs)}

# ==========================================================================
hdr("I.  SEP MEETINGS ONLY versus ALL MEETINGS")
# ==========================================================================
B["sep_only"] = {}
for lbl, s in [("all meetings", ev), ("SEP meetings", ev[ev["is_sep"]]),
               ("non-SEP meetings", ev[~ev["is_sep"]])]:
    row = [f"  {lbl:18s}"]
    for kind in ["y", "rn", "tp"]:
        m = fit(s[f"d{kind}10_d2"], s[["wedge_acm"]])
        if m is None:
            row.append("      .        ")
            continue
        row.append(f"  {kind}: {m.params['wedge_acm']:+6.2f}"
                   f"({m.tvalues['wedge_acm']:+5.2f})")
        B["sep_only"][f"{lbl}|{kind}"] = {
            "b": float(m.params["wedge_acm"]),
            "t": float(m.tvalues["wedge_acm"]), "n": int(m.nobs)}
    row.append(f"   n={len(s)}")
    print("".join(row))

with open(f"{OUT}/robustness.json", "w") as fh:
    json.dump(B, fh, indent=2, default=str)
print(f"\nWrote {OUT}/robustness.json")
