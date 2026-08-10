"""
build_committee_rstar.py
========================
Committee-level r* for the full sample, January 2012 to March 2026.

    python3 build_committee_rstar.py --root ..

CONSTRUCTION
------------
    r*_t = (longer-run federal funds dot) - pi*

Dots come from the best available source for each meeting:

  2012-01 to 2020-12   Table 2 of the SEP compilation. Raw submissions, one
                       convention throughout, and off-grid values preserved.
  2021-03 to 2026-03   Figure 2 of the published projections page. Binned to
                       the eighth-point grid; no compilation released yet.

pi* = 2.0 throughout. This is not an approximation. For every meeting the
published longer-run PCE inflation figure has a median, a central tendency AND
a RANGE all equal to 2.0 -- the range collapsing to a point means every single
participant submitted 2.0. Verified directly against the archived 2021, 2023
and 2026 pages, and against all 594 participant-level observations in the
compilation block. So r* is the longer-run dot minus a constant, and every
dispersion statistic is identical between the two.

TWO THINGS THAT DO NOT BITE HERE
--------------------------------
The 2014 target-rate/midpoint convention change affects only the value 0.25,
which is the zero-lower-bound shorthand. The longer-run dot never goes near it
-- its minimum across the whole sample is well above 1 -- so the longer-run
series is untouched by that break.

The binning difference between sources matters little at this horizon: mean
absolute difference in longer-run dispersion between raw and binned is 0.0018
where both exist. It is still recorded per meeting via the `source` column,
because the measurement basis changes in 2021 and any structural break test
should know that.

OUTPUTS (written under <root>/analysis/)
-----------------------------------------
  committee_rstar.csv     per meeting: n, mean, median, sd, iqr, range,
                          min, max, source
  committee_rstar.png     the series with its cross-sectional range
"""

import argparse
import os

import numpy as np
import pandas as pd

PI_STAR = 2.0


def load_dots(root):
    """One row per dot, best source per meeting, expressed as r*."""
    # primary: compilation Table 2
    p = pd.read_csv(os.path.join(root, "deanonymized", "participant_panel.csv"))
    p["date"] = pd.to_datetime(p["date"])
    t2 = p[p["horizon"].astype(str) == "LR"].dropna(subset=["ffr_exact"]).copy()
    t2 = t2[["date", "ffr_exact"]].rename(columns={"ffr_exact": "dot"})
    t2["source"] = "table2_compilation"

    # fallback: published dot plot
    a = pd.read_csv(os.path.join(root, "anonymized", "dotplot_dots_long.csv"))
    a["date"] = pd.to_datetime(a["date"])
    f2 = a[a["horizon"].astype(str) == "LR"].copy()
    f2 = f2[["date", "dot_midpoint"]].rename(columns={"dot_midpoint": "dot"})
    f2["source"] = "figure2_dotplot"
    f2 = f2[~f2["date"].isin(set(t2["date"]))]

    dots = pd.concat([t2, f2], ignore_index=True)
    dots["rstar"] = dots["dot"] - PI_STAR
    return dots.sort_values(["date", "rstar"]).reset_index(drop=True)


def summarise(dots):
    g = (dots.groupby(["date", "source"])["rstar"]
             .agg(n="count", mean="mean", median="median",
                  sd=lambda s: float(np.std(s, ddof=0)),
                  iqr=lambda s: float(np.percentile(s, 75)
                                      - np.percentile(s, 25)),
                  min="min", max="max")
             .reset_index())
    g["range"] = g["max"] - g["min"]
    return g.sort_values("date").reset_index(drop=True)


def chart(s, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(11, 5.6))
    ax.fill_between(s["date"], s["min"], s["max"], color="#c0392b",
                    alpha=0.10, lw=0, label="Range across participants")
    ax.fill_between(s["date"], s["median"] - s["iqr"] / 2,
                    s["median"] + s["iqr"] / 2, color="#c0392b",
                    alpha=0.18, lw=0, label="Interquartile band")
    ax.plot(s["date"], s["median"], lw=2.6, color="#c0392b", label="Median r*")
    ax.plot(s["date"], s["mean"], lw=1.2, color="#2c3e50", ls="--",
            label="Mean r*")

    # mark where the source changes
    sw = s[s["source"] == "figure2_dotplot"]
    if len(sw):
        x = sw["date"].min()
        ax.axvline(x, color="#7f8c8d", lw=0.9, ls=":")
        ax.annotate("compilation ends;\ndot plot thereafter", (x, ax.get_ylim()[1]),
                    xytext=(6, -14), textcoords="offset points",
                    fontsize=7.5, color="#7f8c8d", va="top")

    ax.axhline(0, color="#7f8c8d", lw=0.7)
    ax.set_ylabel("r*  (longer-run funds rate minus 2%), pp")
    ax.set_title("FOMC committee r*, 2012-2026", loc="left", fontsize=12)
    ax.legend(frameon=False, fontsize=8, loc="upper right", ncol=2)
    ax.grid(alpha=0.25, lw=0.5)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=170)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="..")
    args = ap.parse_args()
    out = os.path.join(args.root, "analysis")
    os.makedirs(out, exist_ok=True)

    dots = load_dots(args.root)
    s = summarise(dots)
    s.to_csv(os.path.join(out, "committee_rstar.csv"), index=False)
    chart(s, os.path.join(out, "committee_rstar.png"))

    print("=" * 66)
    print("COMMITTEE r*, FULL SAMPLE")
    print("=" * 66)
    print(f"  meetings {len(s)}   {s.date.min().date()} to {s.date.max().date()}")
    print("  " + "   ".join(f"{k}: {v}" for k, v in
                            s.source.value_counts().items()))

    print("\n  year   median    mean      sd     range     n   source")
    for y in sorted(s.date.dt.year.unique()):
        r = s[s.date.dt.year == y].iloc[-1]
        print(f"  {y}   {r['median']:+6.3f}  {r['mean']:+6.3f}  "
              f"{r['sd']:.3f}   {r['range']:.3f}   {int(r['n']):2d}   "
              f"{'T2' if r['source'].startswith('table2') else 'F2'}")

    peak, trough = s.loc[s["median"].idxmax()], s.loc[s["median"].idxmin()]
    print(f"\n  peak    {peak['median']:+.3f}  ({peak['date'].date()})")
    print(f"  trough  {trough['median']:+.3f}  ({trough['date'].date()})")
    print(f"  latest  {s.iloc[-1]['median']:+.3f}  ({s.iloc[-1]['date'].date()})")

    pre = s[s.date <= "2020-12-31"]
    post = s[s.date > "2020-12-31"]
    print(f"\n  2012-01 -> 2020-12  {pre.iloc[0]['median']:+.3f} to "
          f"{pre.iloc[-1]['median']:+.3f}   ({pre.iloc[-1]['median']-pre.iloc[0]['median']:+.3f} pp)")
    print(f"  2020-12 -> 2026-03  {pre.iloc[-1]['median']:+.3f} to "
          f"{post.iloc[-1]['median']:+.3f}   ({post.iloc[-1]['median']-pre.iloc[-1]['median']:+.3f} pp)")

    print("\n  DISPERSION (unaffected by subtracting pi*)")
    for lo, hi, lab in [(2012, 2017, "2012-2016"), (2017, 2021, "2017-2020"),
                        (2021, 2027, "2021-2026")]:
        w = s[(s.date.dt.year >= lo) & (s.date.dt.year < hi)]
        print(f"    {lab}: sd {w['sd'].mean():.3f}   iqr {w['iqr'].mean():.3f}"
              f"   range {w['range'].mean():.3f}")

    print(f"\n  Wrote {out}/committee_rstar.csv and .png")


if __name__ == "__main__":
    main()
