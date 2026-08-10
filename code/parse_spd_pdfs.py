"""
parse_spd_pdfs.py
=================
Extract the longer-run federal funds rate from the survey results PDFs, to
extend the market-side series back well beyond the machine-readable files.

    python3 parse_spd_pdfs.py --root ..

WHY BOTHER WITH THE PDFS
------------------------
The .xlsx files only start in July 2023, and only the funds rate goes back that
far -- longer-run PCE, GDP and unemployment begin in January 2025. That is 23
surveys, or 12 with inflation. The results PDFs carry the longer-run funds rate
question from October 2013, which is 105 SPD surveys and 68 SMP surveys.

Requires pdftotext (poppler-utils).

THE QUESTION AND ITS TWO LAYOUTS
--------------------------------
"In addition, provide your estimate of the longer[-]run target federal funds
rate and your expectation for the average federal funds rate over the next 10
years." Note the hyphen is inconsistent across years -- "longer run" and
"longer-run" both appear -- which is why the pattern allows either.

The answer table appears in two shapes:

  2014-style   a wide table of half-year columns ending in Longer Run and
               10-yr Average FF Rate
  2019-style   a compact two-column table, Longer Run then 10-yr Average

In BOTH, the longer-run figure is the second-to-last value on each percentile
row and the ten-year average is the last. That is what the extractor keys on,
and every parsed row is checked against it.

WHAT COMES OUT
--------------
25th percentile, median and 75th percentile of the longer-run target funds
rate -- the same three statistics the .xlsx files carry, so the two sources
splice without a change of definition.

ON THE 2 PERCENT ASSUMPTION
---------------------------
These PDFs give the nominal longer-run rate. Longer-run PCE is not asked before
2025, so converting to r* requires assuming pi*. In the 12 surveys where it IS
observed, market longer-run PCE is exactly 2.00 with an interquartile range of
zero -- so the assumption is exact there. It should NOT be assumed exact
earlier: 2013-2015 ran persistently below target and 2021-2023 well above, and
long-run expectations may have drifted. Output therefore keeps the nominal rate
as the primary column and marks r* as assumption-dependent.
"""

import argparse
import os
import re
import subprocess

import numpy as np
import pandas as pd

# The phrase "longer run target federal funds rate" also appears in narrative
# commentary -- "several dealers expected lower projections for the longer run
# target federal funds rate" -- and anchoring on it grabs whichever percentile
# table happens to follow, which in June 2015 was the macro projections table
# (it has a "Longer" column too). The question is always IMPERATIVE, so the
# anchor requires "provide ... your estimate".
QUESTION = re.compile(
    r"provide\s+(?:your|the)\s+(?:firm'?s\s+)?estimate\s+of\s+the\s+"
    r"longer[\s\-]*run\s+target\s+federal\s+funds\s+rate", re.I | re.S)

# 2013 and earlier phrased it as one combined question.
QUESTION_EARLY = re.compile(
    r"federal\s+funds\s+target\s+rate\s+or\s*(?:range)?\s*"
    r"at\s+the\s+end\s+of\s+each\s+half[\s\-]*year\s+period\s+and\s+over\s+"
    r"the\s+longer\s+run", re.I | re.S)
PCTL = re.compile(r"^\s*(25th\s*Pctl|Median|75th\s*Pctl)\b(.*)$", re.I)
VALUE = re.compile(r"(-?\d+(?:\.\d+)?)\s*%")
ASSUMED_PI = 2.0


def text_of(path):
    try:
        return subprocess.run(["pdftotext", "-layout", path, "-"],
                              capture_output=True, timeout=90
                              ).stdout.decode("utf8", "ignore")
    except Exception:
        return ""


HEADER = re.compile(r"longer\s*$|longer\s+run|10.?yr|10.?year", re.I)


def extract(text, window=26, lookback=14):
    """
    Return ({25,50,75} longer-run values, {25,50,75} ten-year values) or None.

    Anchoring on the question sentence alone fails in 2013-2014, where the
    wording wraps across lines ("...estimate of the longer run target federal /
    funds rate..."). So the table is located structurally instead: find a
    complete set of percentile rows carrying at least two percentage values,
    then confirm the preceding lines contain the Longer Run / 10-yr Average
    header. In every layout the longer-run figure is second-to-last on the row
    and the ten-year average is last.
    """
    lines = text.split("\n")

    # Locate the imperative question, tolerating line wraps, then restrict the
    # search for percentile rows to the lines that follow it.
    joined, offs = "", []
    for i, ln in enumerate(lines):
        offs.append(len(joined))
        joined += ln + " "
    m = QUESTION.search(joined) or QUESTION_EARLY.search(joined)
    if m is None:
        return None, None
    qline = max(i for i, o in enumerate(offs) if o <= m.start())

    # The answer table can sit up to ~35 lines below the question, because the
    # near-term target-rate paths are printed in between. The window is only a
    # coarse guard against drifting into another section; the header and
    # column-count checks below are what actually enforce correctness.
    idx = [i for i, ln in enumerate(lines)
           if PCTL.match(ln) and qline <= i <= qline + 45]

    for start in idx:
        got, tenyr, rows_used = {}, {}, []
        for j in range(start, min(start + window, len(lines))):
            m = PCTL.match(lines[j])
            if not m:
                continue
            key = m.group(1).lower().replace(" ", "")
            key = 25 if key.startswith("25") else (75 if key.startswith("75") else 50)
            if key in got:
                continue
            vals = VALUE.findall(m.group(2))
            if len(vals) < 2:
                continue
            got[key] = float(vals[-2])
            tenyr[key] = float(vals[-1])
            rows_used.append(j)
        if len(got) != 3:
            continue

        head = " ".join(lines[max(0, start - lookback):start])
        ctx = " ".join(lines[max(0, start - 40):start])
        if not re.search(r"longer", head, re.I):
            continue

        # Column count is the reliable discriminator. In the post-2013 layout
        # the longer-run table has exactly TWO columns, Longer Run and 10-yr
        # Average FF Rate. The near-term target-rate paths that sit just above
        # it on the same page have ten or more, and matching one of those was
        # what corrupted the June 2015 SMP observation. Before October 2013
        # there is no 10-yr column and Longer Run is the last of many, so the
        # count restriction applies only to the modern layout.
        modern = bool(re.search(r"10.?yr|10.?year|average\s*ff", head, re.I))
        if modern and any(len(VALUE.findall(PCTL.match(lines[j]).group(2))) != 2
                          for j in rows_used):
            continue
        # must be the funds-rate question, not the 10-year Treasury or mortgage
        # question, both of which also have a "Longer Run" column
        if not re.search(r"federal\s*funds", ctx, re.I):
            continue
        if re.search(r"treasury\s*yield|mortgage", ctx[-400:], re.I):
            continue

        # The "10-yr Average FF Rate" column was only added in October 2013.
        # Before that the table ends at Longer Run, so the longer-run figure is
        # the LAST value on the row rather than the second-to-last. Reading it
        # one column left silently returns a near-term half-year projection --
        # which is what produced an implausible 1.19pp interquartile range for
        # early 2013 before this check existed.
        has_10y = bool(re.search(r"10.?yr|10.?year|next\s*10\s*years",
                                 head + " " + ctx[-600:], re.I))
        if not has_10y:
            for k in got:
                got[k] = tenyr[k]
            tenyr = {k: np.nan for k in tenyr}
        return got, tenyr
    return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="..")
    args = ap.parse_args()

    rdir = os.path.join(args.root, "spd", "results")
    out = os.path.join(args.root, "analysis")
    os.makedirs(out, exist_ok=True)

    rows, failed = [], []
    files = sorted(f for f in os.listdir(rdir) if f.lower().endswith(".pdf"))
    print(f"parsing {len(files)} result PDFs ...")

    for f in files:
        m = re.match(r"(\d{4})-(\d{2})_", f)
        if not m:
            failed.append((f, "undated filename"))
            continue
        y, mo = int(m.group(1)), int(m.group(2))
        # SMP filenames are inconsistent: "smp", "-mp.", "results-mp" and,
        # in 2015, "_mp-January-result.pdf" with mp BEFORE the month. Missing
        # that last form silently relabelled 8 SMP surveys as SPD, producing
        # duplicate dates and a spurious spike in the 2015 series.
        panel = ("SMP" if re.search(
            r"smp|market[\s._-]*participant|(^|[_\-])mp[_\-]|[_\-]mp\.", f, re.I)
            else "SPD")
        t = text_of(os.path.join(rdir, f))
        if not t:
            failed.append((f, "no text (scanned image?)"))
            continue
        lr, ten = extract(t)
        if lr is None:
            failed.append((f, "question not found"))
            continue
        if not (lr[25] <= lr[50] <= lr[75]):
            failed.append((f, f"percentiles not ordered: {lr}"))
            continue
        rows.append({"date": pd.Timestamp(year=y, month=mo, day=1),
                     "panel": panel, "file": f,
                     "i_star_p25": lr[25], "i_star_med": lr[50],
                     "i_star_p75": lr[75],
                     "ff10y_p25": ten[25], "ff10y_med": ten[50],
                     "ff10y_p75": ten[75]})

    if not rows:
        raise SystemExit("Nothing parsed.")

    d = pd.DataFrame(rows).sort_values(["panel", "date"]).reset_index(drop=True)
    d["i_star_iqr"] = d["i_star_p75"] - d["i_star_p25"]
    d["rstar_med_assumed"] = d["i_star_med"] - ASSUMED_PI
    d.to_csv(os.path.join(out, "market_rstar_from_pdfs.csv"), index=False)

    print(f"\n  parsed  {len(d)} surveys")
    for p, g in d.groupby("panel"):
        print(f"    {p}: {len(g):3d}   {g.date.min().date()} to {g.date.max().date()}")
    print(f"  failed  {len(failed)}")

    print("\n  median longer-run funds rate, SPD panel, by year")
    spd = d[d.panel == "SPD"]
    for y, g in spd.groupby(spd.date.dt.year):
        print(f"    {y}:  n={len(g)}  i* {g.i_star_med.mean():.2f}   "
              f"IQR {g.i_star_iqr.mean():.2f}   "
              f"r*(assumed) {g.rstar_med_assumed.mean():+.2f}")

    if failed:
        print("\n  FAILURES (need attention):")
        seen = {}
        for f, why in failed:
            seen.setdefault(why, []).append(f)
        for why, fs in seen.items():
            print(f"    {len(fs):3d}  {why}")
            for f in fs[:4]:
                print(f"         {f}")

    print(f"\n  Wrote {out}/market_rstar_from_pdfs.csv")
    print("  i_star_* is the NOMINAL longer-run rate and is the reliable column.")
    print("  rstar_med_assumed imposes pi*=2.0 and is only as good as that.")


if __name__ == "__main__":
    main()
