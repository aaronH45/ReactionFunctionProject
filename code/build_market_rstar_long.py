"""
build_market_rstar_long.py
==========================
Splice the PDF-parsed and spreadsheet-derived market series into one long
market r*, and set it beside the FOMC.

    python3 build_market_rstar_long.py --root ..

SOURCES AND THE SEAM
--------------------
    2013-01 to 2022-09   results PDFs      (25th/median/75th, text tables)
    2023-07 to 2026-06   survey .xlsx      (same three statistics)
    2022-10 to 2023-06   NOT AVAILABLE

The hole is not an oversight. From late 2022 the results PDFs render their
tables as images, so nothing can be extracted by text tools, and the .xlsx
files only begin in July 2023. Recovering the nine-month gap would need OCR on
about a dozen documents. It is left explicitly empty rather than interpolated.

Both sources report the identical three statistics, so the splice does not
change definitions -- only the delivery format.

THE INFLATION ASSUMPTION
------------------------
Longer-run PCE is only asked from January 2025. Before that, converting the
nominal longer-run rate to r* requires assuming pi*. In all 12 surveys where it
is observed, market longer-run PCE is exactly 2.00 with an interquartile range
of zero. That justifies the assumption within the observed window; it does not
prove it held in 2013-2015, when inflation ran persistently below target, or in
2021-2022, when it ran far above. The `pi_source` column records for every
observation whether pi* was measured or imposed, so any result can be re-run on
the measured subsample alone.
"""

import argparse
import os

import numpy as np
import pandas as pd

ASSUMED_PI = 2.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="..")
    ap.add_argument("--panel", default="SPD")
    args = ap.parse_args()
    out = os.path.join(args.root, "analysis")

    # ---- PDF block ----
    p = pd.read_csv(os.path.join(out, "market_rstar_from_pdfs.csv"))
    p["date"] = pd.to_datetime(p["date"])
    p = p[p["panel"] == args.panel].copy()
    p = p[["date", "i_star_p25", "i_star_med", "i_star_p75"]]
    p["pi_star_med"] = ASSUMED_PI
    p["pi_source"] = "assumed"
    p["source"] = "results_pdf"

    # ---- spreadsheet block ----
    x = pd.read_csv(os.path.join(out, "market_rstar_combined.csv"))
    x["date"] = pd.to_datetime(x["date"])
    x = x[["date", "i_star_p25", "i_star_med", "i_star_p75", "pi_star_med"]].copy()
    x["pi_source"] = np.where(x["pi_star_med"].notna(), "measured", "assumed")
    x["pi_star_med"] = x["pi_star_med"].fillna(ASSUMED_PI)
    x["source"] = "survey_xlsx"

    d = (pd.concat([p, x], ignore_index=True)
           .sort_values("date").reset_index(drop=True))
    d["rstar_med"] = d["i_star_med"] - d["pi_star_med"]
    d["i_star_iqr"] = d["i_star_p75"] - d["i_star_p25"]
    d.to_csv(os.path.join(out, "market_rstar_long.csv"), index=False)

    # ---- FOMC ----
    f = pd.read_csv(os.path.join(out, "committee_rstar.csv"))
    f["date"] = pd.to_datetime(f["date"])

    print("=" * 66)
    print(f"MARKET r*, LONG SERIES  ({args.panel} + combined xlsx)")
    print("=" * 66)
    print(f"  surveys {len(d)}   {d.date.min().date()} to {d.date.max().date()}")
    print("  " + "   ".join(f"{k}: {v}" for k, v in d.source.value_counts().items()))
    print(f"  pi* measured in {int((d.pi_source=='measured').sum())} of {len(d)}")

    gap = d["date"].diff().dt.days
    big = d.loc[gap > 150, "date"]
    if len(big):
        print(f"  gap: no data between "
              f"{d.loc[big.index[0]-1,'date'].date()} and {big.iloc[0].date()}")

    m = pd.merge_asof(d.sort_values("date"),
                      f[["date", "median"]].sort_values("date")
                       .rename(columns={"median": "fomc_rstar"}),
                      on="date", direction="nearest",
                      tolerance=pd.Timedelta("60D")).dropna(subset=["fomc_rstar"])
    m["gap_vs_fomc"] = m["rstar_med"] - m["fomc_rstar"]
    m.to_csv(os.path.join(out, "market_vs_fomc_long.csv"), index=False)

    print("\n  year   market r*   FOMC r*    gap    market IQR")
    for y, g in m.groupby(m.date.dt.year):
        print(f"  {y}    {g.rstar_med.mean():+6.2f}    {g.fomc_rstar.mean():+6.2f}"
              f"   {g.gap_vs_fomc.mean():+6.2f}     {g.i_star_iqr.mean():.2f}")

    pre = m[m.date < "2023-01-01"]
    post = m[m.date >= "2023-01-01"]
    print(f"\n  mean gap 2013-2022 {pre.gap_vs_fomc.mean():+.3f} pp"
          f"   |  2023-2026 {post.gap_vs_fomc.mean():+.3f} pp")
    print(f"  corr(market r*, FOMC r*) = "
          f"{np.corrcoef(m.rstar_med, m.fomc_rstar)[0,1]:.3f}")

    # ---- chart ----
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 7), sharex=True,
                                 gridspec_kw={"height_ratios": [2, 1]})
    for src, mk in [("results_pdf", "o"), ("survey_xlsx", "s")]:
        s = d[d.source == src]
        a1.plot(s.date, s.rstar_med, lw=1.8, marker=mk, ms=3,
                color="#2c3e50", label=f"Market r* ({src})")
        a1.fill_between(s.date, s.i_star_p25 - s.pi_star_med,
                        s.i_star_p75 - s.pi_star_med,
                        color="#2c3e50", alpha=0.10, lw=0)
    a1.plot(f.date, f["median"], lw=2.2, color="#c0392b", ls="--",
            label="FOMC r* (SEP median)")
    a1.set_ylabel("r*, pp")
    a1.set_title("Market versus FOMC longer-run r*, 2012-2026", loc="left",
                 fontsize=12)
    a1.legend(frameon=False, fontsize=8)
    a1.grid(alpha=0.25, lw=0.5)

    a2.axhline(0, color="#7f8c8d", lw=0.8)
    a2.plot(m.date, m.gap_vs_fomc, lw=1.6, color="#8e44ad", marker="o", ms=3)
    a2.set_ylabel("Market minus FOMC, pp")
    a2.grid(alpha=0.25, lw=0.5)
    for ax in (a1, a2):
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
    fig.tight_layout()
    png = os.path.join(out, "market_vs_fomc_long.png")
    fig.savefig(png, dpi=170)
    plt.close(fig)
    print(f"\n  Wrote market_rstar_long.csv, market_vs_fomc_long.csv, "
          f"{os.path.basename(png)}")


if __name__ == "__main__":
    main()
