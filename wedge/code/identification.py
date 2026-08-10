"""
identification.py
=================
The BR stress test showed that on 2012-2018 the wedge is nearly collinear
with the Fed's own longer-run level (R2 0.93-0.96), so "the market prices
the wedge" cannot be told apart from "the market responds to the SEP level."

Question: is there a window where the wedge IS separately identified --
i.e. where the market side moves and the Fed side does not -- and does
anything survive there?
"""
import json
import numpy as np
import pandas as pd
import statsmodels.api as sm

OUT = "/home/claude/rstar_wedge/results"
I = {}


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


ev = pd.read_csv(f"{OUT}/event_panel.csv", parse_dates=["meeting"])
ev["istar_fed"] = ev["rstar_fed"] + 2.0
ev["istar_acm"] = ev["rstar_acm"] + 2.0

ERAS = {"2012-2018 (BR window)": ("2012-01-01", "2018-06-30"),
        "2019-2026": ("2019-01-01", "2026-12-31"),
        "2020-2026": ("2020-01-01", "2026-12-31"),
        "full 2012-2026": ("2012-01-01", "2026-12-31")}

# ==========================================================================
hdr("1.  Which side moves, era by era")
# ==========================================================================
I["variation"] = {}
print(f"  {'era':24s} {'sd(Fed)':>9s} {'sd(Mkt)':>9s} {'corr':>7s} "
      f"{'R2 wedge|Fed':>13s} {'R2 wedge|Mkt':>13s}  n")
for name, (a, b) in ERAS.items():
    s = ev[(ev["meeting"] >= a) & (ev["meeting"] <= b)]
    d = s[["istar_fed", "istar_acm", "wedge_acm"]].dropna()
    r2f = fit(d["wedge_acm"], d[["istar_fed"]]).rsquared
    r2m = fit(d["wedge_acm"], d[["istar_acm"]]).rsquared
    print(f"  {name:24s} {d['istar_fed'].std():9.3f} "
          f"{d['istar_acm'].std():9.3f} "
          f"{d['istar_fed'].corr(d['istar_acm']):+7.3f} "
          f"{r2f:13.3f} {r2m:13.3f}  {len(d)}")
    I["variation"][name] = {"sd_fed": float(d["istar_fed"].std()),
                            "sd_mkt": float(d["istar_acm"].std()),
                            "corr": float(d["istar_fed"].corr(d["istar_acm"])),
                            "r2_on_fed": float(r2f), "r2_on_mkt": float(r2m),
                            "n": int(len(d))}

# ==========================================================================
hdr("2.  Does each result survive controlling for the Fed's own level?")
# ==========================================================================
I["controlled"] = {}
for name, (a, b) in ERAS.items():
    s = ev[(ev["meeting"] >= a) & (ev["meeting"] <= b)]
    print(f"\n  {name}   n={len(s)}")
    for kind, lbl in [("rn", "10y risk-neutral"), ("tp", "10y term premium")]:
        m0 = fit(s[f"d{kind}10_d2"], s[["wedge_acm"]])
        m1 = fit(s[f"d{kind}10_d2"], s[["wedge_acm", "istar_fed"]])
        m2 = fit(s[f"d{kind}10_d2"], s[["istar_fed"]])
        m3 = fit(s[f"d{kind}10_d2"], s[["istar_acm"]])
        if m0 is None:
            continue
        print(f"    {lbl:18s} wedge alone   {m0.params['wedge_acm']:+7.3f} "
              f"(t {m0.tvalues['wedge_acm']:+5.2f})")
        print(f"    {'':18s} + Fed level   {m1.params['wedge_acm']:+7.3f} "
              f"(t {m1.tvalues['wedge_acm']:+5.2f})    "
              f"Fed {m1.params['istar_fed']:+6.2f} "
              f"(t {m1.tvalues['istar_fed']:+5.2f})")
        print(f"    {'':18s} Fed only      {m2.params['istar_fed']:+7.3f} "
              f"(t {m2.tvalues['istar_fed']:+5.2f})   "
              f"Mkt only {m3.params['istar_acm']:+7.3f} "
              f"(t {m3.tvalues['istar_acm']:+5.2f})")
        I["controlled"][f"{name}|{kind}"] = {
            "wedge_alone_b": float(m0.params["wedge_acm"]),
            "wedge_alone_t": float(m0.tvalues["wedge_acm"]),
            "wedge_ctrl_b": float(m1.params["wedge_acm"]),
            "wedge_ctrl_t": float(m1.tvalues["wedge_acm"]),
            "fed_only_t": float(m2.tvalues["istar_fed"]),
            "mkt_only_t": float(m3.tvalues["istar_acm"])}

# ==========================================================================
hdr("3.  Flat-Fed meetings: the SEP median unchanged for 3+ consecutive SEPs")
# ==========================================================================
# Where the Fed side is constant, all wedge variation is market-side, so the
# wedge is identified off the market alone.
fed = pd.read_csv(f"{OUT}/fed_rstar.csv", parse_dates=["date"]).sort_values("date")
fed["run"] = (fed["rstar_fed"].diff() != 0).cumsum()
runs = fed.groupby("run").agg(start=("date", "min"), end=("date", "max"),
                              n=("date", "size"), val=("rstar_fed", "first"))
long_runs = runs[runs["n"] >= 3]
print("  Stretches with an unchanged SEP longer-run median (3+ SEPs):")
for _, r in long_runs.iterrows():
    print(f"    {r['start'].date()} to {r['end'].date()}   "
          f"{r['n']} SEPs at r*={r['val']:.3f}")

mask = np.zeros(len(ev), dtype=bool)
for _, r in long_runs.iterrows():
    mask |= ((ev["meeting"] >= r["start"]) & (ev["meeting"] <= r["end"])).values
flat = ev[mask]
print(f"\n  FOMC meetings inside those stretches: {len(flat)}")
d = flat[["istar_fed", "istar_acm", "wedge_acm"]].dropna()
print(f"  sd(Fed)={d['istar_fed'].std():.3f}   sd(Mkt)={d['istar_acm'].std():.3f}"
      f"   R2(wedge|Fed)={fit(d['wedge_acm'], d[['istar_fed']]).rsquared:.3f}")
I["flat_fed"] = {"n": int(len(flat)),
                 "sd_fed": float(d["istar_fed"].std()),
                 "sd_mkt": float(d["istar_acm"].std())}
for kind, lbl in [("y", "10y total"), ("rn", "10y risk-neutral"),
                  ("tp", "10y term premium")]:
    m = fit(flat[f"d{kind}10_d2"], flat[["wedge_acm"]])
    if m is None:
        continue
    print(f"    {lbl:18s} b={m.params['wedge_acm']:+7.3f} "
          f"(t {m.tvalues['wedge_acm']:+5.2f})  R2={m.rsquared:.3f}  "
          f"n={int(m.nobs)}")
    I["flat_fed"][kind] = {"b": float(m.params["wedge_acm"]),
                           "t": float(m.tvalues["wedge_acm"]),
                           "r2": float(m.rsquared), "n": int(m.nobs)}

with open(f"{OUT}/identification.json", "w") as fh:
    json.dump(I, fh, indent=2, default=str)
print(f"\nWrote {OUT}/identification.json")
