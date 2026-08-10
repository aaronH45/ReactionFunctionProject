"""
run_checks.py
=============
The pre-committed gate (checks 1-7) and the post-gate tests (8-10).
Every number printed here is also written to results/results.json so that
nothing has to be retyped into a slide.
"""
import json
import os
import numpy as np
import pandas as pd
import statsmodels.api as sm

UP = "/mnt/user-data/uploads/ReactionFunctionProject"
OUT = "/home/claude/rstar_wedge/results"
R = {}


def hdr(s):
    print("\n" + "=" * 74)
    print(s)
    print("=" * 74)


def ols(y, X, names, lags=4):
    """OLS with Newey-West HAC standard errors."""
    d = pd.concat([y, X], axis=1).dropna()
    if len(d) < 8:
        return None
    yy = d.iloc[:, 0]
    XX = sm.add_constant(d.iloc[:, 1:], has_constant="add")
    m = sm.OLS(yy, XX).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return {"n": int(m.nobs), "r2": float(m.rsquared),
            "coef": {k: float(v) for k, v in m.params.items()},
            "se": {k: float(v) for k, v in m.bse.items()},
            "t": {k: float(v) for k, v in m.tvalues.items()},
            "p": {k: float(v) for k, v in m.pvalues.items()},
            "names": names, "model": m}


def show(res, label, key):
    if res is None:
        print(f"  {label:34s}  insufficient observations")
        return
    b = res["coef"][key]
    se = res["se"][key]
    print(f"  {label:34s}  b={b:+8.3f}  se={se:6.3f}  "
          f"t={res['t'][key]:+6.2f}  p={res['p'][key]:.3f}  "
          f"R2={res['r2']:.3f}  n={res['n']}")


ev = pd.read_csv(f"{OUT}/event_panel.csv", parse_dates=["meeting", "fed_date"])
fed = pd.read_csv(f"{OUT}/fed_rstar.csv", parse_dates=["date"])
spd = pd.read_csv(f"{OUT}/spd_rstar.csv", parse_dates=["date"])
part = pd.read_csv(f"{UP}/deanonymized/participant_panel.csv",
                   parse_dates=["date"])
part_lr = part[part["horizon"] == "LR"].copy()

# ==========================================================================
hdr("CHECK 1  --  pi* dispersion across FOMC participants")
# ==========================================================================
g = part_lr.groupby("date")["pce"].agg(["size", "mean", "std", "min", "max"])
print(f"  meetings with participant-level longer-run PCE : {len(g)} "
      f"({g.index.min().date()} to {g.index.max().date()})")
print(f"  participant-horizon rows                       : {len(part_lr)}")
print(f"  distinct values submitted                      : "
      f"{sorted(part_lr['pce'].unique())}")
print(f"  max within-meeting SD                          : {g['std'].max():.6f}")
print(f"  meetings with SD > 0                           : "
      f"{int((g['std'] > 0).sum())} of {len(g)}")
mkt_pi = spd["pi_star_spd"].dropna() if "pi_star_spd" in spd else spd["pi_star_med"]
print(f"  SPD longer-run PCE median, distinct values      : "
      f"{sorted(mkt_pi.unique())}  (n={len(mkt_pi)})")
R["check1"] = {
    "n_meetings": int(len(g)), "n_rows": int(len(part_lr)),
    "distinct_pce_values": sorted(map(float, part_lr["pce"].unique())),
    "max_within_meeting_sd": float(g["std"].max()),
    "n_meetings_sd_gt0": int((g["std"] > 0).sum()),
    "spd_pi_distinct": sorted(map(float, mkt_pi.unique())),
    "verdict": "FAIL" if g["std"].max() == 0 else "PASS",
}
print(f"\n  VERDICT: {R['check1']['verdict']} -- "
      f"{'pi* dispersion is identically zero; r*_i,t is the longer-run dot minus a constant. The extraction is a relabelling.' if R['check1']['verdict']=='FAIL' else 'genuine pi* dispersion exists'}")

# ==========================================================================
hdr("CHECK 2  --  wedge variance decomposition")
# ==========================================================================
R["check2"] = {}
for tag, wcol, mcol in [("SPD", "wedge_spd", "rstar_spd"),
                        ("ACM", "wedge_acm", "rstar_acm")]:
    d = ev[["rstar_fed", mcol, wcol]].dropna()
    vF, vM = d["rstar_fed"].var(ddof=1), d[mcol].var(ddof=1)
    cov = d["rstar_fed"].cov(d[mcol])
    vD = d[wcol].var(ddof=1)
    tot = vF + vM
    print(f"\n  {tag}   n={len(d)}")
    print(f"    var(r*_Fed)={vF:.5f}   var(r*_Mkt)={vM:.5f}   "
          f"cov={cov:+.5f}")
    print(f"    var(Delta) ={vD:.5f}   (identity check "
          f"{vF + vM - 2*cov:.5f})")
    print(f"    var(r*_Fed) / [var(F)+var(M)] = {vF/tot:6.1%}   "
          f"threshold 15%")
    print(f"    corr(F, M) = {d['rstar_fed'].corr(d[mcol]):+.3f}")
    R["check2"][tag] = {"n": int(len(d)), "var_fed": float(vF),
                        "var_mkt": float(vM), "cov": float(cov),
                        "var_wedge": float(vD),
                        "fed_share": float(vF / tot),
                        "corr": float(d["rstar_fed"].corr(d[mcol])),
                        "verdict": "PASS" if vF / tot >= 0.15 else "FAIL"}
    print(f"    VERDICT: {R['check2'][tag]['verdict']}")

# ==========================================================================
hdr("CHECK 3  --  R2 of the wedge on each side alone")
# ==========================================================================
R["check3"] = {}
for tag, wcol, mcol in [("SPD", "wedge_spd", "rstar_spd"),
                        ("ACM", "wedge_acm", "rstar_acm")]:
    d = ev[["rstar_fed", mcol, wcol]].dropna()
    r2f = ols(d[wcol], d[["rstar_fed"]], ["fed"])["r2"]
    r2m = ols(d[wcol], d[[mcol]], ["mkt"])["r2"]
    print(f"  {tag}   Delta ~ r*_Fed  R2 = {r2f:.3f}      "
          f"Delta ~ r*_Mkt  R2 = {r2m:.3f}   n={len(d)}")
    hi = max(r2f, r2m)
    v = "PASS" if hi < 0.5 else ("BORDERLINE" if hi < 0.9 else "FAIL")
    R["check3"][tag] = {"r2_on_fed": r2f, "r2_on_mkt": r2m,
                        "n": int(len(d)), "verdict": v}
    note = ""
    if v == "BORDERLINE":
        note = ("  (both sides ~0.8: the two series are NEGATIVELY correlated, "
                "so each alone explains most of Delta. Not the degenerate "
                "var(F)=0 case check 3 was written to catch, but the wedge is "
                "close to a linear function of either side.)")
    elif v == "FAIL":
        note = "  (one side mechanically determines the wedge)"
    print(f"          VERDICT: {v}{note}")

# ==========================================================================
hdr("CHECK 4  --  effective sample size")
# ==========================================================================
f = fed.sort_values("date").reset_index(drop=True)
chg = f["rstar_fed"].diff()
n_chg = int((chg.fillna(0) != 0).sum())
print(f"  SEP meetings                              : {len(f)}")
print(f"  distinct values of the SEP longer-run r*   : "
      f"{f['rstar_fed'].nunique()}  -> {sorted(f['rstar_fed'].unique())}")
print(f"  meetings at which the median CHANGED       : {n_chg}")
print(f"  longest run without a change               : "
      f"{int((f['rstar_fed'].groupby((chg.fillna(0) != 0).cumsum()).size()).max())}")
print(f"  FOMC meetings in the event panel           : {len(ev)}")
print(f"  -> effective N for anything driven by the Fed-side level is "
      f"{n_chg}, not {len(ev)}")
R["check4"] = {"n_sep_meetings": int(len(f)),
               "n_distinct_values": int(f["rstar_fed"].nunique()),
               "distinct_values": sorted(map(float, f["rstar_fed"].unique())),
               "n_changes": n_chg, "n_fomc_meetings": int(len(ev)),
               "verdict": "BINDING"}

# also: how many distinct wedge values
for tag, wcol in [("SPD", "wedge_spd"), ("ACM", "wedge_acm")]:
    w = ev[wcol].dropna()
    print(f"  distinct values of Delta ({tag:3s})              : "
          f"{w.round(6).nunique()} over {len(w)} meetings")
    R["check4"][f"distinct_wedge_{tag}"] = int(w.round(6).nunique())

# ==========================================================================
hdr("CHECK 5  --  first differences: do both sides track a common signal?")
# ==========================================================================
R["check5"] = {}
# Fed side changes only at SEP meetings; use the SEP-meeting subsample.
sub = ev[ev["is_sep"]].copy().sort_values("meeting")
for tag, mcol in [("SPD", "rstar_spd"), ("ACM", "rstar_acm")]:
    d = sub[["meeting", "rstar_fed", mcol]].dropna().copy()
    d["dF"] = d["rstar_fed"].diff()
    d["dM"] = d[mcol].diff()
    d = d.dropna()
    c = d["dF"].corr(d["dM"])
    print(f"  {tag}  corr(d r*_Fed, d r*_Mkt) = {c:+.3f}   n={len(d)}"
          f"   sd(dF)={d['dF'].std():.3f}  sd(dM)={d['dM'].std():.3f}")
    R["check5"][tag] = {"corr": float(c), "n": int(len(d)),
                        "sd_dF": float(d["dF"].std()),
                        "sd_dM": float(d["dM"].std()),
                        "verdict": "FAIL" if c > 0.7 else "PASS"}
    print(f"        VERDICT: {R['check5'][tag]['verdict']}")

# ==========================================================================
hdr("CHECK 6  --  persistence of the wedge")
# ==========================================================================
R["check6"] = {}
for tag, wcol in [("SPD", "wedge_spd"), ("ACM", "wedge_acm")]:
    w = ev.sort_values("meeting")[wcol].dropna().reset_index(drop=True)
    d = pd.DataFrame({"w": w, "wl": w.shift(1)}).dropna()
    m = ols(d["w"], d[["wl"]], ["lag"])
    rho = m["coef"]["wl"]
    hl = np.log(0.5) / np.log(abs(rho)) if 0 < abs(rho) < 1 else np.inf
    print(f"  {tag}  AR(1) rho = {rho:+.3f}  (se {m['se']['wl']:.3f})   "
          f"half-life {hl:.1f} meetings   mean {w.mean():+.3f}  "
          f"sd {w.std():.3f}   n={m['n']}")
    v = "FAIL" if rho > 0.95 else "PASS"
    R["check6"][tag] = {"rho": float(rho), "se": float(m["se"]["wl"]),
                        "half_life_meetings": float(hl),
                        "mean": float(w.mean()), "sd": float(w.std()),
                        "n": m["n"], "verdict": v}
    print(f"        VERDICT: {v}")

# ==========================================================================
hdr("CHECK 7  --  Mercatus replication: SEP vs SPD longer-run funds rate")
# ==========================================================================
sep_nom = fed.copy()
sep_nom["i_star_fed"] = sep_nom["rstar_fed"] + 2.0
sp = spd[["date", "i_star_spd"]].dropna().copy()
sp["ym"] = sp["date"].dt.to_period("M")
sep_nom["ym"] = sep_nom["date"].dt.to_period("M")
mm = sep_nom.merge(sp.groupby("ym")["i_star_spd"].last().reset_index(),
                   on="ym", how="inner")
mm["gap_bp"] = (mm["i_star_fed"] - mm["i_star_spd"]) * 100
print(f"  SEP meetings with a same-month SPD survey : {len(mm)} "
      f"({mm['date'].min().date()} to {mm['date'].max().date()})")
print(f"  mean |gap|   {mm['gap_bp'].abs().mean():6.1f} bp")
print(f"  median |gap| {mm['gap_bp'].abs().median():6.1f} bp")
print(f"  max |gap|    {mm['gap_bp'].abs().max():6.1f} bp   on "
      f"{mm.loc[mm['gap_bp'].abs().idxmax(), 'date'].date()}")
print(f"  share |gap| <= 13 bp : {(mm['gap_bp'].abs() <= 13).mean():.1%}")
print(f"  share |gap| <= 42 bp : {(mm['gap_bp'].abs() <= 42).mean():.1%}")
R["check7"] = {"n": int(len(mm)),
               "mean_abs_bp": float(mm["gap_bp"].abs().mean()),
               "median_abs_bp": float(mm["gap_bp"].abs().median()),
               "max_abs_bp": float(mm["gap_bp"].abs().max()),
               "max_date": str(mm.loc[mm["gap_bp"].abs().idxmax(), "date"].date()),
               "share_le_13bp": float((mm["gap_bp"].abs() <= 13).mean()),
               "share_le_42bp": float((mm["gap_bp"].abs() <= 42).mean())}
mm[["date", "i_star_fed", "i_star_spd", "gap_bp"]].to_csv(
    f"{OUT}/mercatus_replication.csv", index=False)

# ==========================================================================
hdr("FALLBACK  --  cross-sectional dispersion of the SEP r* panel")
# ==========================================================================
disp = fed[["date", "rstar_fed_sd", "rstar_fed_iqr", "fed_source"]].dropna()
print(f"  SD of the longer-run r* panel: mean {disp['rstar_fed_sd'].mean():.3f}"
      f"  sd {disp['rstar_fed_sd'].std():.3f}  "
      f"range [{disp['rstar_fed_sd'].min():.3f}, {disp['rstar_fed_sd'].max():.3f}]")
print(f"  distinct SD values: {disp['rstar_fed_sd'].round(6).nunique()} "
      f"over {len(disp)} meetings")
d2 = disp.set_index("date")["rstar_fed_sd"]
dd = pd.DataFrame({"w": d2.values, "wl": pd.Series(d2.values).shift(1)}).dropna()
mdisp = ols(dd["w"], dd[["wl"]], ["lag"])
print(f"  AR(1) rho of the dispersion series: {mdisp['coef']['wl']:+.3f}")
R["fallback_dispersion"] = {
    "mean_sd": float(disp["rstar_fed_sd"].mean()),
    "sd_of_sd": float(disp["rstar_fed_sd"].std()),
    "min": float(disp["rstar_fed_sd"].min()),
    "max": float(disp["rstar_fed_sd"].max()),
    "n_distinct": int(disp["rstar_fed_sd"].round(6).nunique()),
    "ar1_rho": float(mdisp["coef"]["wl"])}

# ==========================================================================
hdr("CHECK 8  --  announcement-window decomposition on the pre-meeting wedge")
# ==========================================================================
R["check8"] = {}
for win in ["d1", "d2"]:
    for tag, wcol in [("SPD", "wedge_spd"), ("ACM", "wedge_acm")]:
        print(f"\n  window {win}   wedge = {tag}")
        for n in [2, 5, 10]:
            for kind, lbl in [("y", "total yield"), ("rn", "risk-neutral"),
                              ("tp", "term premium")]:
                col = f"d{kind}{n}_{win}"
                res = ols(ev[col], ev[[wcol]], [wcol])
                key = f"{win}|{tag}|{n}y|{kind}"
                show(res, f"{n}y {lbl:14s}", wcol)
                if res:
                    R["check8"][key] = {k: res[k] for k in
                                        ("n", "r2", "coef", "se", "t", "p")}
            print()

# additive identity check
chk = (ev["dy10_d2"] - ev["drn10_d2"] - ev["dtp10_d2"]).abs().max()
print(f"  identity |dy - drn - dtp| max = {chk:.2e} bp  (should be ~0)")
R["check8_identity_max_bp"] = float(chk)

# low-revision subsample: meetings where the SEP r* did not move
lowrev = ev[(ev["is_sep"]) & (ev["sep_revision"].fillna(0).abs() < 1e-9)]
print(f"\n  low-revision SEP meetings (median unchanged): {len(lowrev)}")
for tag, wcol in [("ACM", "wedge_acm"), ("SPD", "wedge_spd")]:
    for kind in ["rn", "tp"]:
        res = ols(lowrev[f"d{kind}10_d2"], lowrev[[wcol]], [wcol])
        show(res, f"low-rev 10y {kind} ({tag})", wcol)
        if res:
            R["check8"][f"lowrev|{tag}|10y|{kind}"] = {
                k: res[k] for k in ("n", "r2", "coef", "se", "t", "p")}

# ==========================================================================
hdr("CHECK 9  --  maturity signature")
# ==========================================================================
R["check9"] = {}
for tag, wcol in [("ACM", "wedge_acm"), ("SPD", "wedge_spd")]:
    print(f"\n  wedge = {tag}   (2-day window, coefficient in bp per pp of wedge)")
    print("     n     total      risk-neutral   term premium")
    for n in range(1, 11):
        row = [f"    {n:2d}"]
        rec = {}
        for kind in ["y", "rn", "tp"]:
            res = ols(ev[f"d{kind}{n}_d2"], ev[[wcol]], [wcol])
            if res:
                row.append(f"  {res['coef'][wcol]:+7.2f}({res['t'][wcol]:+5.2f})")
                rec[kind] = {"b": res["coef"][wcol], "t": res["t"][wcol],
                             "se": res["se"][wcol], "p": res["p"][wcol]}
            else:
                row.append("        .      ")
        print("".join(row))
        R["check9"][f"{tag}|{n}y"] = rec

# ==========================================================================
hdr("CHECK 10  --  signed versus absolute wedge")
# ==========================================================================
R["check10"] = {}
for tag, wcol in [("ACM", "wedge_acm"), ("SPD", "wedge_spd")]:
    e = ev.copy()
    e["abs_w"] = e[wcol].abs()
    e["pos_w"] = e[wcol].clip(lower=0)
    e["neg_w"] = (-e[wcol]).clip(lower=0)
    print(f"\n  wedge = {tag}")
    for kind in ["y", "rn", "tp"]:
        c = f"d{kind}10_d2"
        r_s = ols(e[c], e[[wcol]], ["signed"])
        r_a = ols(e[c], e[["abs_w"]], ["abs"])
        r_b = ols(e[c], e[["pos_w", "neg_w"]], ["pos", "neg"])
        show(r_s, f"10y {kind} ~ signed", wcol)
        show(r_a, f"10y {kind} ~ |wedge|", "abs_w")
        if r_b:
            print(f"      asymmetric: pos b={r_b['coef']['pos_w']:+7.3f} "
                  f"(t {r_b['t']['pos_w']:+5.2f})   "
                  f"neg b={r_b['coef']['neg_w']:+7.3f} "
                  f"(t {r_b['t']['neg_w']:+5.2f})   R2={r_b['r2']:.3f}")
        R["check10"][f"{tag}|{kind}"] = {
            "signed": {k: r_s[k] for k in ("n", "r2", "coef", "t", "p")} if r_s else None,
            "abs": {k: r_a[k] for k in ("n", "r2", "coef", "t", "p")} if r_a else None,
            "asym": {k: r_b[k] for k in ("n", "r2", "coef", "t", "p")} if r_b else None}

# ==========================================================================
with open(f"{OUT}/results.json", "w") as fh:
    json.dump(R, fh, indent=2, default=str)
print(f"\n\nWrote {OUT}/results.json")
