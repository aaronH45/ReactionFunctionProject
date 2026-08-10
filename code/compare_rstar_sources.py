"""
compare_rstar_sources.py
========================
Put the four r* series on one chart: Laubach-Williams (two vintage concepts),
the FOMC, and the market.

    python3 compare_rstar_sources.py --root ..

THE VINTAGE DISTINCTION, WHICH IS THE WHOLE POINT
-------------------------------------------------
The HLW download contains two very different objects, and using the wrong one
answers a different question.

  CURRENT VINTAGE   the model re-estimated today over the full sample. Its
                    value for 2015 embeds everything learned since 2015. Nobody
                    could have known it in 2015.

  REAL TIME         what the model actually produced at each date, from the
                    vintage files (2005q1 ... 2026q1). This is the number that
                    existed when FOMC participants and dealers were forming
                    their own views.

Comparing 2015 FOMC beliefs against the CURRENT estimate of 2015 r* only tells
you they were wrong with hindsight, which is uninteresting. Comparing them
against the REAL-TIME estimate tells you whether they were slow relative to
information that was actually available -- which is the sluggish-updating
claim. Both are plotted; the real-time series is the one that carries the
argument.

Two further cautions. HLW one-sided estimates are filtered rather than
smoothed, so they are the right real-time analogue; two-sided estimates use
future data and are shown only for reference. And the vintage files jump from
2020q2 to 2022q4 because the model was suspended during the pandemic
distortions -- that gap is real and is left empty.

WHAT IS BEING COMPARED
----------------------
HLW estimates a SHORT-RUN natural rate: the real rate consistent with output at
potential and stable inflation now. The SEP dot and the SPD longer-run question
are LONG-RUN anchors: where the rate settles under appropriate policy absent
shocks. These are not the same object -- and the SPD's own "neutral real
federal funds rate" question, which IS short-run, sat about 0.4pp below its
longer-run anchor over 2016-2020. So level gaps between HLW and the surveys
partly reflect horizon, not disagreement. Comovement is the meaningful
comparison, not the level.
"""

import argparse
import os
import re

import numpy as np
import pandas as pd


def _rstar_col(df):
    """First column literally named rstar -- the one-sided estimate."""
    for c in df.columns:
        if str(c).strip().lower() == "rstar":
            return c
    return None


def load_current(path):
    d = pd.read_excel(path, sheet_name="data", header=5)
    d = d.rename(columns={d.columns[0]: "Date"})
    cols = [c for c in d.columns if str(c).strip().lower() == "rstar"]
    out = pd.DataFrame({"date": pd.to_datetime(d["Date"], errors="coerce")})
    out["hlw_onesided_current"] = pd.to_numeric(d[cols[0]], errors="coerce")
    if len(cols) > 1:
        out["hlw_twosided_current"] = pd.to_numeric(d[cols[1]], errors="coerce")
    return out.dropna(subset=["date"]).reset_index(drop=True)


def load_realtime(path):
    """One point per vintage: the estimate for that vintage's own quarter."""
    xl = pd.ExcelFile(path)
    rows = []
    for sh in xl.sheet_names:
        m = re.fullmatch(r"(\d{4})q([1-4])", sh.strip().lower())
        if not m:
            continue
        y, q = int(m.group(1)), int(m.group(2))
        d = xl.parse(sh, header=5)
        d = d.rename(columns={d.columns[0]: "Date"})
        c = _rstar_col(d)
        if c is None:
            continue
        d["Date"] = pd.to_datetime(d["Date"], errors="coerce")
        d[c] = pd.to_numeric(d[c], errors="coerce")
        d = d.dropna(subset=["Date", c])
        if d.empty:
            continue
        rows.append({"vintage": pd.Timestamp(year=y, month=q * 3, day=1),
                     "hlw_realtime": float(d[c].iloc[-1]),
                     "last_obs": d["Date"].iloc[-1]})
    return pd.DataFrame(rows).sort_values("vintage").reset_index(drop=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="..")
    args = ap.parse_args()
    H = os.path.join(args.root, "HLW")
    A = os.path.join(args.root, "analysis")

    cur = load_current(os.path.join(H, "Laubach_Williams_current_estimates.xlsx"))
    rt = load_realtime(os.path.join(H, "Laubach_Williams_real_time_estimates.xlsx"))

    fomc = pd.read_csv(os.path.join(A, "committee_rstar.csv"))
    fomc["date"] = pd.to_datetime(fomc["date"])
    mkt = pd.read_csv(os.path.join(A, "market_rstar_long.csv"))
    mkt["date"] = pd.to_datetime(mkt["date"])

    print("=" * 68)
    print("r* SOURCES")
    print("=" * 68)
    print(f"  HLW current vintage : {len(cur)} quarters "
          f"{cur.date.min().date()} to {cur.date.max().date()}")
    print(f"  HLW real time       : {len(rt)} vintages "
          f"{rt.vintage.min().date()} to {rt.vintage.max().date()}")
    g = rt["vintage"].diff().dt.days
    if (g > 200).any():
        i = g.idxmax()
        print(f"      gap: {rt.loc[i-1,'vintage'].date()} to "
              f"{rt.loc[i,'vintage'].date()}  (model suspended in the pandemic)")
    print(f"  FOMC                : {len(fomc)} meetings")
    print(f"  Market (SPD)        : {len(mkt)} surveys")

    # ---- align everything to FOMC meeting dates ----
    comp = fomc[["date", "median"]].rename(columns={"median": "fomc"}).copy()
    comp = pd.merge_asof(comp.sort_values("date"),
                         cur.sort_values("date"), on="date",
                         direction="nearest", tolerance=pd.Timedelta("60D"))
    comp = pd.merge_asof(comp.sort_values("date"),
                         rt.rename(columns={"vintage": "date"})
                           .sort_values("date")[["date", "hlw_realtime"]],
                         on="date", direction="backward",
                         tolerance=pd.Timedelta("200D"))
    comp = pd.merge_asof(comp.sort_values("date"),
                         mkt.sort_values("date")[["date", "rstar_med"]]
                            .rename(columns={"rstar_med": "market"}),
                         on="date", direction="nearest",
                         tolerance=pd.Timedelta("60D"))
    comp.to_csv(os.path.join(A, "rstar_all_sources.csv"), index=False)

    print("\n  year   FOMC   market   HLW real-time   HLW current")
    for y, g2 in comp.groupby(comp.date.dt.year):
        def f(c):
            v = g2[c].mean()
            return "   n/a" if pd.isna(v) else f"{v:+6.2f}"
        print(f"  {y}  {f('fomc')}  {f('market')}      {f('hlw_realtime')}"
              f"        {f('hlw_onesided_current')}")

    print("\n  CORRELATIONS (levels, FOMC meeting frequency)")
    for a, b in [("fomc", "market"), ("fomc", "hlw_realtime"),
                 ("fomc", "hlw_onesided_current"),
                 ("market", "hlw_realtime")]:
        s = comp[[a, b]].dropna()
        if len(s) > 4:
            print(f"    {a:22s} vs {b:22s} {np.corrcoef(s[a], s[b])[0,1]:+.3f}"
                  f"   (n={len(s)})")

    print("\n  MEAN LEVEL GAPS")
    for c in ["market", "hlw_realtime", "hlw_onesided_current"]:
        s = comp[["fomc", c]].dropna()
        if len(s):
            print(f"    FOMC minus {c:22s} {(s['fomc']-s[c]).mean():+.3f} pp")

    # ---- chart ----
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(11.5, 6.2))
    c2 = cur[(cur.date >= "2011-06-01") & (cur.date <= "2026-09-01")]
    ax.plot(c2.date, c2.hlw_onesided_current, lw=1.4, color="#95a5a6",
            label="HLW one-sided, current vintage (hindsight)")
    ax.plot(rt.vintage, rt.hlw_realtime, lw=2.0, color="#16a085",
            marker="o", ms=3, label="HLW one-sided, real time")
    ax.plot(fomc.date, fomc["median"], lw=2.6, color="#c0392b",
            label="FOMC r* (SEP median)")
    ax.plot(mkt.date, mkt.rstar_med, lw=1.8, color="#2c3e50", ls="--",
            label="Market r* (SPD longer run minus pi*)")
    ax.axhline(0, color="#7f8c8d", lw=0.7)
    ax.set_xlim(pd.Timestamp("2011-06-01"), pd.Timestamp("2026-09-01"))
    ax.set_ylabel("r*, pp")
    ax.set_title("Four estimates of r*: model, policymakers, market",
                 loc="left", fontsize=12)
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    ax.grid(alpha=0.25, lw=0.5)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    png = os.path.join(A, "rstar_all_sources.png")
    fig.savefig(png, dpi=170)
    plt.close(fig)
    print(f"\n  Wrote rstar_all_sources.csv and {os.path.basename(png)}")


if __name__ == "__main__":
    main()
