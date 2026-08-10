"""
build_market_rstar.py
=====================
Market-side r* from the NY Fed Survey of Market Expectations.

    python3 build_market_rstar.py --root ..

WHAT THE SURVEY FILES CONTAIN
-----------------------------
Summary statistics, not individual responses. Each survey-question-panel cell
carries count, avg, pctl25, pctl50 and pctl75. So a respondent-level panel
analogous to the FOMC one is NOT possible; a median-and-IQR series is.

That is not a serious loss for the horse race. The Philadelphia Fed's SPF
dispersion measure is D1 = P75 - P25, the same interquartile statistic, so the
two market-side measures are directly comparable in units without conversion.

THREE PANELS, REPORTED SEPARATELY
---------------------------------
    Dealer        primary dealers          (n about 25)
    Participant   buy-side participants    (n about 35)
    Combined      both pooled              (n about 61)

Keeping them apart matters: dealers and asset managers face different
incentives, and any gap between them is itself informative.

THE THREE OBJECTS
-----------------
The survey asks respondents for two distinct longer-run funds rate numbers, and
the SEP supplies a third:

    fed_funds_target_range              what the respondent thinks r* IS
    sep_median_fed_funds_target_range   what the respondent thinks the FOMC
                                        will SAY r* is
    (SEP longer-run median)             what the FOMC actually says

The difference between the first two is genuine disagreement with the Fed about
the neutral rate. The difference between the second and third is misperception
of the Fed's own view. Existing work conflates them; separating them is what
makes the Caballero-Simsek channel -- disagreement between the Fed and the
market, as opposed to within the market -- actually measurable rather than
assumed.

CONSTRUCTING r*
---------------
    r*_market = (longer-run funds rate) - (longer-run headline PCE)

pi* is taken from the survey, NOT assumed to be 2.0. For the FOMC that
assumption is exact, because the target is a commitment and the published
longer-run range collapses to a point. For market respondents longer-run
inflation is a forecast and may differ. Imposing 2.0 would relabel
inflation-credibility disagreement as real-rate disagreement.

Percentiles do not subtract cleanly -- the 75th percentile of a difference is
not the difference of 75th percentiles -- so the level series uses medians and
the dispersion series is reported for the nominal rate only, with the inflation
IQR alongside so the reader can see how much of it could possibly come from
inflation disagreement.

OUTPUT
------
    <root>/analysis/market_rstar.csv
    <root>/analysis/market_vs_fomc_rstar.png
"""

import argparse
import glob
import os

import numpy as np
import pandas as pd

FFR = "fed_funds_target_range"
SEP_FFR = "sep_median_fed_funds_target_range"
PCE = "headline_pce"


def load(root):
    frames = []
    for f in sorted(glob.glob(os.path.join(root, "spd", "data", "*.xlsx"))):
        try:
            d = pd.read_excel(f, sheet_name="Sheet1", header=0)
        except Exception as e:
            print(f"  skipped {os.path.basename(f)}: {e}")
            continue
        d["file"] = os.path.basename(f)
        frames.append(d)
    if not frames:
        raise SystemExit("No survey data files. Run fetch_spd.py first.")
    d = pd.concat(frames, ignore_index=True)
    d["date"] = pd.to_datetime(d["survey_release_date"])
    return d[d["value_tag"].astype(str).str.contains("longerrun", na=False)]


def pick(d, subject, panel, agg):
    """
    Values arrive as decimals (0.0313 = 3.13 percent) and the column is object
    dtype -- some survey files store counts as text -- so it is coerced rather
    than assumed numeric.
    """
    s = d[(d["subject"] == subject) & (d["panel_type"] == panel)
          & (d["aggregation"] == agg)].copy()
    s["v"] = pd.to_numeric(s["aggregation_value"], errors="coerce")
    return (s.groupby("date")["v"].first() * 100).astype(float).rename(agg)


def chart(df, merged, panel, path):
    """Two stacked panels: levels on top, dispersion below."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7.2), sharex=True,
                                   gridspec_kw={"height_ratios": [2, 1]})

    ax1.fill_between(df.index, df["i_star_p25"] - df["pi_star_med"],
                     df["i_star_p75"] - df["pi_star_med"],
                     color="#2c3e50", alpha=0.12, lw=0,
                     label="Market interquartile range")
    ax1.plot(df.index, df["rstar_med"], lw=2.4, color="#2c3e50",
             marker="o", ms=3.5, label=f"Market r* ({panel})")
    ax1.plot(df.index, df["sep_fcst_med"] - df["pi_star_med"], lw=1.3,
             color="#8e44ad", ls="-.", marker="s", ms=3,
             label="Market's forecast of the SEP median")
    if merged is not None and merged["fomc_rstar"].notna().any():
        ax1.plot(merged["date"], merged["fomc_rstar"], lw=2.0, color="#c0392b",
                 ls="--", marker="^", ms=3.5, label="FOMC r* (SEP median)")
    ax1.set_ylabel("r*, pp")
    ax1.set_title(f"Market versus FOMC longer-run r*  --  {panel} panel",
                  loc="left", fontsize=12)
    ax1.legend(frameon=False, fontsize=8, loc="upper left")
    ax1.grid(alpha=0.25, lw=0.5)

    ax2.plot(df.index, df["i_star_iqr"], lw=2.0, color="#2c3e50",
             marker="o", ms=3.5, label="Market IQR of longer-run funds rate")
    if merged is not None and merged["fomc_iqr"].notna().any():
        ax2.plot(merged["date"], merged["fomc_iqr"], lw=2.0, color="#c0392b",
                 ls="--", marker="^", ms=3.5, label="FOMC IQR")
    ax2.plot(df.index, df["pi_star_iqr"], lw=1.2, color="#16a085", ls=":",
             label="Market IQR of longer-run inflation")
    ax2.set_ylabel("Interquartile range, pp")
    ax2.set_ylim(bottom=-0.02)
    ax2.legend(frameon=False, fontsize=8, loc="upper left")
    ax2.grid(alpha=0.25, lw=0.5)

    for ax in (ax1, ax2):
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=170)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="..")
    ap.add_argument("--panel", default="Dealer",
                    choices=["Dealer", "Participant", "Combined"])
    args = ap.parse_args()
    out = os.path.join(args.root, "analysis")
    os.makedirs(out, exist_ok=True)

    d = load(args.root)
    P = args.panel

    df = pd.DataFrame({
        "n":            pick(d, FFR, P, "count") / 100,
        "i_star_p25":   pick(d, FFR, P, "pctl25"),
        "i_star_med":   pick(d, FFR, P, "pctl50"),
        "i_star_p75":   pick(d, FFR, P, "pctl75"),
        "pi_star_med":  pick(d, PCE, P, "pctl50"),
        "pi_star_p25":  pick(d, PCE, P, "pctl25"),
        "pi_star_p75":  pick(d, PCE, P, "pctl75"),
        "sep_fcst_med": pick(d, SEP_FFR, P, "pctl50"),
    }).sort_index()

    df["rstar_med"] = df["i_star_med"] - df["pi_star_med"]
    df["i_star_iqr"] = df["i_star_p75"] - df["i_star_p25"]
    df["pi_star_iqr"] = df["pi_star_p75"] - df["pi_star_p25"]
    df["disagree_with_fed"] = df["i_star_med"] - df["sep_fcst_med"]
    df.index.name = "date"
    df["panel"] = P
    suf = "" if P == "Dealer" else f"_{P.lower()}"
    df.to_csv(os.path.join(out, f"market_rstar{suf}.csv"))

    print("=" * 68)
    print(f"MARKET r*  --  {P} panel")
    print("=" * 68)
    print(f"  surveys {len(df)}   {df.index.min().date()} to {df.index.max().date()}")
    print(f"  respondents per survey: {df['n'].min():.0f} to {df['n'].max():.0f}")

    print("\n  date         i*    pi*    r*    i* IQR  pi* IQR   SEPfcst   gap")
    for dt, r in df.iterrows():
        print(f"  {dt.date()}  {r['i_star_med']:5.2f}  {r['pi_star_med']:4.2f}  "
              f"{r['rstar_med']:5.2f}   {r['i_star_iqr']:5.2f}   "
              f"{r['pi_star_iqr']:5.2f}    {r['sep_fcst_med']:5.2f}  "
              f"{r['disagree_with_fed']:+5.2f}")

    print(f"\n  mean longer-run inflation forecast: {df['pi_star_med'].mean():.3f}")
    off = (df['pi_star_med'] - 2.0).abs()
    print(f"  mean |deviation from 2.0|:          {off.mean():.3f}"
          f"   max {off.max():.3f}")
    print("  -> this is how much a 2% assumption would have mismeasured r*")

    print(f"\n  mean gap vs their own SEP forecast:  "
          f"{df['disagree_with_fed'].mean():+.3f} pp")
    print(f"  mean IQR of i* (disagreement):       {df['i_star_iqr'].mean():.3f}")
    print(f"  mean IQR of pi* (inflation)  :       {df['pi_star_iqr'].mean():.3f}")

    # ---- compare with the FOMC ----
    fp = os.path.join(out, "committee_rstar.csv")
    if os.path.exists(fp):
        f = pd.read_csv(fp)
        f["date"] = pd.to_datetime(f["date"])
        merged = pd.merge_asof(
            df.reset_index().sort_values("date"),
            f[["date", "median", "iqr"]].sort_values("date").rename(
                columns={"median": "fomc_rstar", "iqr": "fomc_iqr"}),
            on="date", direction="nearest",
            tolerance=pd.Timedelta("45D"))
        merged.to_csv(os.path.join(out, f"market_vs_fomc_rstar{suf}.csv"),
                      index=False)
        m = merged.dropna(subset=["fomc_rstar"])
        print(f"\n  MATCHED TO NEAREST SEP MEETING ({len(m)} of {len(df)})")
        print(f"    market r* mean {m['rstar_med'].mean():+.3f}   "
              f"FOMC r* mean {m['fomc_rstar'].mean():+.3f}   "
              f"gap {(m['rstar_med']-m['fomc_rstar']).mean():+.3f} pp")
        print(f"    market IQR mean {m['i_star_iqr'].mean():.3f}   "
              f"FOMC IQR mean {m['fomc_iqr'].mean():.3f}")
        print("    HORSE RACE: which dispersion is larger, and does either")
        print("    move the term structure? Both now on the same statistic.")
    else:
        merged = None
        print("\n  (run build_committee_rstar.py first to enable the comparison)")

    png = os.path.join(out, f"market_vs_fomc_rstar{suf}.png")
    chart(df, merged, P, png)
    print(f"\n  Wrote {out}/market_rstar{suf}.csv and {os.path.basename(png)}")


if __name__ == "__main__":
    main()
