"""
parse_archive.py
================
Build every dataset from the ARCHIVED SOURCES. No network access.

    python3 parse_archive.py --root ..

WHY THIS IS SEPARATE FROM THE FETCH SCRIPTS
-------------------------------------------
Downloading and parsing are different jobs with different failure modes, and
mixing them causes two concrete problems.

First, a partial re-run overwrites a complete dataset. Re-fetching two missing
meetings with --dates rewrote the anonymized CSVs with only those two meetings
in them. Parsing from the archive cannot do that: it always reads every file
present, so the output is a function of the archive rather than of whichever
subset was last requested.

Second, fixing a parser bug should not mean re-downloading 86MB from the Fed.
Sources are immutable once archived; parsing is the part that changes.

So: fetch_*.py populate sources/ and nothing else matters about them.
parse_archive.py turns sources/ into data, deterministically, offline, and is
safe to re-run any number of times.

INPUTS
    sources/projections/fomcprojtabl{meeting_date}.htm    (all meetings)
    sources/compilations/FOMC{meeting_date}SEPcompilation.pdf
    sources/keys/FOMC{meeting_date}SEPkey.pdf

Archived filenames always carry the MEETING date, even where the Fed's own URL
used a release date (December 2012) or a variant spelling (March 2022). The
date in the filename is the date in the output.

OUTPUTS
    anonymized/dotplot_dots_long.csv, dotplot_counts_long.csv,
               dotplot_dispersion.csv
    deanonymized/participant_panel.csv, participant_dispersion.csv,
               raw_vs_binned_comparison.csv
    parse_report.csv   one row per meeting: what was found, what was parsed
"""

import argparse
import os
import re
import sys

import numpy as np
import pandas as pd
import pdfplumber

from fetch_anonymized import parse_all_horizons
from fetch_deanonymized import parse_compilation, parse_key, normalise_person
from sep_dates import SEP_DATES, as_timestamp


def detect_convention(html):
    """
    Which convention does this meeting's Figure 2 use for the funds rate?

    The Fed changed the row labels of that table between the June and September
    2014 SEPs:

      up to 2014-06-18   "Target Federal Funds Rate at Year-End (Percent)"
      from 2014-09-17    "Midpoint of target range or target level (Percent)"

    Under the older label, a participant at the zero lower bound is recorded at
    0.25 -- the TOP of the 0 to 0.25 percent target range. Under the newer one
    the same submission is recorded at 0.125, the midpoint. The compilation PDFs
    use the midpoint convention throughout, which is why an archive built from
    Figure 2 disagrees with one built from the compilation for exactly those
    observations.

    Only 0.25 is affected. It was shorthand for the ZLB range; every higher
    level in that era was a point target and means the same thing under both
    conventions. Verified: in the target-rate era 0.25 is the only level below
    0.5, and counts at 0.5, 0.75 and 1.0 agree across archives.
    """
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    for t in soup.find_all("table"):
        rows = t.find_all("tr")
        if not rows:
            continue
        hdr = [c.get_text(" ", strip=True) for c in rows[0].find_all(["td", "th"])]
        if not hdr or not hdr[0]:
            continue
        if not any("longer" in h.lower() and "run" in h.lower() for h in hdr):
            continue
        first = hdr[0].lower()
        if "midpoint" in first:
            return "midpoint"
        if "target" in first:
            return "target_rate"
    return "unknown"


def to_midpoint(dot, convention):
    """Restate a published value under the midpoint convention."""
    if convention == "target_rate" and abs(dot - 0.25) < 1e-9:
        return 0.125
    return dot


def parse_projections(srcdir):
    dots, counts, rep = [], [], {}
    for d in SEP_DATES:
        p = os.path.join(srcdir, f"fomcprojtabl{d}.htm")
        if not os.path.exists(p):
            rep[d] = "missing_file"
            continue
        with open(p, encoding="utf-8", errors="replace") as f:
            raw = f.read()
        h = parse_all_horizons(raw)
        if not h:
            rep[d] = "parse_failed"
            continue
        conv = detect_convention(raw)
        date = as_timestamp(d)
        for hz, vals in h.items():
            for v in vals:
                dots.append({"date": date, "horizon": hz,
                             "dot": float(v),
                             "dot_midpoint": to_midpoint(float(v), conv),
                             "convention": conv})
            for lvl in sorted(set(vals)):
                counts.append({"date": date, "horizon": hz,
                               "rate_level": float(lvl),
                               "count": int(sum(1 for x in vals if x == lvl)),
                               "convention": conv})
        rep[d] = f"ok ({len(h)} horizons, {conv})"
    return pd.DataFrame(dots), pd.DataFrame(counts), rep


def parse_compilations(cdir, kdir):
    panels, keys, rep = [], [], {}
    for d in SEP_DATES:
        cp = os.path.join(cdir, f"FOMC{d}SEPcompilation.pdf")
        if not os.path.exists(cp):
            rep[d] = "not_released"
            continue
        date = as_timestamp(d)
        try:
            with open(cp, "rb") as f:
                df = parse_compilation(f.read(), date)
        except Exception as e:
            rep[d] = f"pdf_error: {e}"
            continue
        if df.empty:
            rep[d] = "no_rows"
            continue
        panels.append(df)

        kp = os.path.join(kdir, f"FOMC{d}SEPkey.pdf")
        note = f"ok ({len(df)} rows"
        if os.path.exists(kp):
            try:
                with open(kp, "rb") as f:
                    mp = parse_key(f.read())
                if mp:
                    keys.append(pd.DataFrame({
                        "date": date, "proj_id": list(mp.keys()),
                        "participant_raw": list(mp.values())}))
                    note += f", {len(mp)} names)"
                else:
                    note += ", key parse failed)"
            except Exception as e:
                note += f", key error {e})"
        else:
            note += ", no key)"
        rep[d] = note
    return panels, keys, rep


MIN_CROSS_SECTION = 5

# Compilation Table 2 prints the funds rate to TWO decimals, so a submission on
# the eighth-point grid loses its third decimal: 0.875 prints as "0.88", 0.125
# as "0.13", 2.375 as "2.38". Restoring them is unambiguous because .13, .38,
# .63 and .88 cannot arise any other way -- the SEP grid is eighths, and the
# genuinely off-grid submissions that do exist (3.8, 4.2, 1.9 and 42 others)
# are all written to ONE decimal and never end in those pairs. Verified across
# all 2,748 rows: no collisions.
_EIGHTH_FROM_2DP = {13: 0.125, 12: 0.125, 38: 0.375, 37: 0.375,
                    63: 0.625, 62: 0.625, 88: 0.875, 87: 0.875}


def restore_eighth(v):
    """Undo the compilation's two-decimal printing for eighth-grid values."""
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return v
    cents = int(round(v * 100)) % 100
    if cents in _EIGHTH_FROM_2DP:
        return float(int(v)) + _EIGHTH_FROM_2DP[cents]
    return float(v)


def dispersion(df, value, by=("date", "horizon")):
    """
    Per meeting-horizon summary statistics.

    `full_cross_section` flags whether every participant answered. In the early
    SEPs, participants who expected policy firming only in a later year supplied
    projections for that year too, which produces horizon cells with one or two
    observations. Those are genuine individual submissions, not parse errors,
    but dispersion computed on n=1 is meaningless and must not enter any series.
    """
    out = (df.dropna(subset=[value]).groupby(list(by))[value]
             .agg(n="count", mean="mean", median="median",
                  sd=lambda s: float(np.std(s, ddof=0)),
                  iqr=lambda s: float(np.percentile(s, 75)
                                      - np.percentile(s, 25)),
                  range=lambda s: float(s.max() - s.min()))
             .reset_index())
    out["full_cross_section"] = out["n"] >= MIN_CROSS_SECTION
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="..")
    args = ap.parse_args()

    R = args.root
    anon = os.path.join(R, "anonymized")
    deanon = os.path.join(R, "deanonymized")
    os.makedirs(anon, exist_ok=True)
    os.makedirs(deanon, exist_ok=True)

    print("=" * 70)
    print("PARSING FROM ARCHIVE (offline)")
    print("=" * 70)

    # ---------------- anonymized ----------------
    dots, counts, rep_a = parse_projections(
        os.path.join(R, "sources", "projections"))
    if dots.empty:
        print("No projections parsed. Check sources/projections/.")
        sys.exit(1)

    dots = dots.sort_values(["date", "horizon", "dot"])
    counts = counts.sort_values(["date", "horizon", "rate_level"])
    # summary statistics use the midpoint-restated series so that the
    # 2014 convention change does not put a step in the level
    disp_a = dispersion(dots, "dot_midpoint")

    dots.to_csv(os.path.join(anon, "dotplot_dots_long.csv"), index=False)
    counts.to_csv(os.path.join(anon, "dotplot_counts_long.csv"), index=False)
    disp_a.to_csv(os.path.join(anon, "dotplot_dispersion.csv"), index=False)

    print(f"\nANONYMIZED")
    print(f"  meetings parsed        {dots.date.nunique()} / {len(SEP_DATES)}")
    print(f"  dots                   {len(dots)}")
    print(f"  meeting-horizon cells  {len(disp_a)}")

    # every dot must sit on the eighth-point grid
    off = (~np.isclose(dots["dot"] * 8, np.round(dots["dot"] * 8))).sum()
    print(f"  dots off the 1/8 grid  {off}   (must be 0 -- these are binned)")

    # ---------------- de-anonymized ----------------
    panels, keys, rep_d = parse_compilations(
        os.path.join(R, "sources", "compilations"),
        os.path.join(R, "sources", "keys"))

    if panels:
        panel = pd.concat(panels, ignore_index=True)
        if keys:
            panel = panel.merge(pd.concat(keys, ignore_index=True),
                                on=["date", "proj_id"], how="left")
        else:
            panel["participant_raw"] = np.nan
        panel["person"] = panel["participant_raw"].apply(
            lambda s: normalise_person(s) if isinstance(s, str) else np.nan)
        panel["ffr_exact"] = panel["ffr"].apply(restore_eighth)
        panel = panel[["date", "proj_id", "person", "participant_raw",
                       "horizon", "gdp", "unemp", "pce", "core_pce",
                       "ffr", "ffr_exact"]]
        panel = panel.sort_values(["date", "horizon", "proj_id"]).reset_index(drop=True)
        panel.to_csv(os.path.join(deanon, "participant_panel.csv"), index=False)

        nrest = int((panel["ffr"] != panel["ffr_exact"]).sum())
        print(f"  eighth-grid values restored {nrest} "
              f"({nrest/panel['ffr'].notna().sum():.0%} of funds-rate cells)")

        disp_d = dispersion(panel, "ffr_exact")
        disp_d.to_csv(os.path.join(deanon, "participant_dispersion.csv"),
                      index=False)

        print(f"\nDE-ANONYMIZED")
        print(f"  meetings               {panel.date.nunique()}")
        print(f"  participant-horizon rows {len(panel)}")
        print(f"  rows with a name       {panel['person'].notna().mean():.1%}")
        print(f"  raw labels -> people   "
              f"{panel['participant_raw'].nunique()} -> {panel['person'].nunique()}")

        # -------- cross-source validation --------
        m = disp_d.merge(disp_a, on=["date", "horizon"],
                         suffixes=("_raw", "_binned"))
        m["dn"] = m["n_raw"] - m["n_binned"]
        m["dsd"] = (m["sd_raw"] - m["sd_binned"]).abs()
        m["dmean"] = (m["mean_raw"] - m["mean_binned"]).abs()
        m.to_csv(os.path.join(deanon, "raw_vs_binned_comparison.csv"),
                 index=False)

        nmis = int((m["dn"] != 0).sum())
        big = int((m["dmean"] > 0.02).sum())
        print(f"\nCROSS-SOURCE CHECK")
        print(f"  cells compared               {len(m)}")
        print(f"  participant-count mismatches {nmis}"
              f"   {'OK' if nmis == 0 else '<-- INVESTIGATE'}")
        print(f"  mean |sd difference|         {m['dsd'].mean():.6f}")
        print(f"  mean |MEAN difference|       {m['dmean'].mean():.6f}")
        print(f"  cells with |mean diff|>0.02  {big}"
              f"   {'OK' if big == 0 else '<-- INVESTIGATE'}")
        lr = m[m.horizon == "LR"]
        if len(lr):
            print(f"  mean |sd difference|, LR     {lr['dsd'].mean():.6f}")
        print("  Levels are compared as well as dispersion, deliberately:")
        print("  standard deviation is invariant to a constant shift, so a")
        print("  convention change that moves every ZLB dot by 0.125 is")
        print("  invisible to an sd-only check. Comparing means catches it.")
    else:
        print("\nDE-ANONYMIZED: no compilations found.")

    # ---------------- combined series ----------------
    # Table 2 is primary wherever it exists: one convention throughout, and
    # every variable participant-matched. Figure 2 fills the tail, where no
    # compilation has been released yet.
    if panels:
        prim = disp_d.copy()
        prim["source"] = "table2_compilation"
        keys_have = set(zip(prim["date"], prim["horizon"]))
        fill = disp_a[~disp_a.apply(
            lambda r: (r["date"], r["horizon"]) in keys_have, axis=1)].copy()
        fill["source"] = "figure2_dotplot"
        combined = (pd.concat([prim, fill], ignore_index=True)
                      .sort_values(["date", "horizon"]).reset_index(drop=True))
        combined.to_csv(os.path.join(R, "sep_dispersion_combined.csv"),
                        index=False)
        print(f"\nCOMBINED SERIES -> sep_dispersion_combined.csv")
        print(f"  {len(combined)} cells   "
              + "   ".join(f"{k}: {v}" for k, v in
                           combined.source.value_counts().items()))
        lrc = combined[combined.horizon == "LR"]
        print(f"  longer-run cells: {len(lrc)}  "
              f"{lrc.date.min().date()} to {lrc.date.max().date()}")

    # ---------------- report ----------------
    rows = []
    for d in SEP_DATES:
        rows.append({"meeting_date": as_timestamp(d).date(),
                     "projections_html": rep_a.get(d, "missing_file"),
                     "compilation_pdf": rep_d.get(d, "not_released")})
    rpt = pd.DataFrame(rows)
    rpt.to_csv(os.path.join(R, "parse_report.csv"), index=False)

    bad = rpt[~rpt.projections_html.str.startswith("ok")]
    print(f"\nparse_report.csv written")
    if len(bad):
        print("  MEETINGS WITHOUT USABLE PROJECTIONS HTML:")
        print(bad.to_string(index=False))
    else:
        print(f"  All {len(SEP_DATES)} meetings parsed from the anonymized archive.")


if __name__ == "__main__":
    main()
