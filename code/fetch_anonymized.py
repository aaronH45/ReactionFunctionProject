"""
fetch_anonymized.py
===================
Build the ANONYMIZED archive: the dot plot exactly as the public saw it on the
day, for every SEP meeting and every horizon.

    python3 fetch_anonymized.py --root ..

WHAT THIS IS
------------
The Fed publishes an accessible-HTML version of each SEP projections release.
Inside it, the Figure 2 table -- "Number of participants with projected midpoint
of target range or target level" -- gives, for each rate level and each horizon
column, how many participants submitted that value. Repeating each rate level
by its count reconstructs the full cross-section of dots.

There are no participant identities here and none can be recovered: the table
is a histogram. Dot i in the 2026 column cannot be linked to dot i in the
longer-run column. That is the defining limitation of this archive and the
reason the de-anonymized folder exists.

WHAT THESE VALUES ARE
---------------------
Binned. The Fed's note on Figure 2 reads: "Each shaded circle indicates the
value (rounded to the nearest 1/8 percentage point) of an individual
participant's judgment..." The SEP compilation records the unrounded
submission, but only after a five-year lag. Where both exist, prefer the
compilation; the difference in dispersion averages 0.0018 and reaches 0.0034
in 2012-2015, when off-grid submissions were common.

OUTPUTS (written under <root>/anonymized/)
------------------------------------------
  dotplot_dots_long.csv        one row per dot: date, horizon, dot
  dotplot_counts_long.csv      one row per (date, horizon, rate_level, count)
  dotplot_dispersion.csv       date, horizon, n, mean, median, sd, iqr, range
  fetch_log.csv                per-meeting parse status

Source HTML is archived to <root>/sources/projections/.
"""

import argparse
import os
import re
import time

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup

from sep_dates import SEP_DATES, as_timestamp

BASE = "https://www.federalreserve.gov/monetarypolicy"
HEADERS = {"User-Agent": "Mozilla/5.0 (academic research)"}

# The Fed's URL scheme is not perfectly consistent. Two documented departures:
#
#   "projtable" instead of "projtabl" -- a stray 'e' affecting March 2022.
#
#   Pages dated to the RELEASE rather than the MEETING. Before 2013 the SEP was
#   published as an addendum to the minutes about three weeks after the meeting,
#   and December 2012's page carries the release date, 17 December. The other
#   2012 meetings are dated to the meeting itself, so this is a one-off rather
#   than an era-wide rule and is handled by exception, not by guessing.
#
# The meeting date is always what gets recorded in the output, whatever the URL.
URL_DATE_EXCEPTIONS = {
    "20121212": "20121217",
}

URL_PATTERNS = [
    BASE + "/fomcprojtabl{date}.htm",
    BASE + "/fomcprojtable{date}.htm",
]


def candidate_urls(d):
    """URL forms to try for meeting date d, in order of likelihood."""
    dates = [d]
    if d in URL_DATE_EXCEPTIONS:
        dates.insert(0, URL_DATE_EXCEPTIONS[d])
    return [p.format(date=x) for x in dates for p in URL_PATTERNS]


def _cells(row):
    return [c.get_text(" ", strip=True).replace("\xa0", " ")
            for c in row.find_all(["td", "th"])]


def parse_all_horizons(html):
    """
    Locate the Figure 2 table and return {horizon: [dot values]}.

    Table identification is structural rather than caption-based, because
    captions have changed wording over the years. The Figure 2 table is the
    only one that has BOTH a horizon header row containing a 'Longer run'
    column AND a first column whose entries are bare numbers on an
    eighth-point grid. Table 1 puts variable names in column one; the
    Figure 3 series uses range bins such as '2.00-2.24'.
    """
    soup = BeautifulSoup(html, "html.parser")

    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if len(rows) < 5:
            continue

        # map column index -> horizon label from the header rows
        horizons, hdr_row = {}, None
        for ri, r in enumerate(rows[:3]):
            cs = _cells(r)
            found = {}
            for i, c in enumerate(cs):
                t = c.strip().lower()
                if re.fullmatch(r"20\d{2}", c.strip()):
                    found[i] = c.strip()
                elif "longer" in t and "run" in t:
                    found[i] = "LR"
            if any(v == "LR" for v in found.values()) and len(found) >= 2:
                horizons, hdr_row = found, ri
                break
        if not horizons:
            continue

        levels, out = [], {h: [] for h in horizons.values()}
        for r in rows[(hdr_row + 1):]:
            cs = _cells(r)
            if not cs:
                continue
            m = re.fullmatch(r"(\d+\.\d+)", cs[0].replace("%", "").strip())
            if not m:
                continue
            rate = float(m.group(1))
            if not (0.0 <= rate <= 12.0):
                continue
            levels.append(rate)
            for i, h in horizons.items():
                if i >= len(cs):
                    continue
                v = cs[i].strip()
                cm = re.fullmatch(r"(\d+)", v)
                if cm:
                    out[h].extend([rate] * int(cm.group(1)))

        if len(levels) < 8:
            continue
        if not all(abs(v * 8 - round(v * 8)) < 1e-9 for v in levels):
            continue          # not the eighth-point grid -> wrong table
        out = {h: sorted(v) for h, v in out.items() if v}
        if out:
            return out
    return {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="..")
    ap.add_argument("--sleep", type=float, default=0.6)
    ap.add_argument("--dates", nargs="*", default=None)
    args = ap.parse_args()

    outdir = os.path.join(args.root, "anonymized")
    srcdir = os.path.join(args.root, "sources", "projections")
    os.makedirs(outdir, exist_ok=True)
    os.makedirs(srcdir, exist_ok=True)

    dots_rows, count_rows, log = [], [], []

    for d in (args.dates or SEP_DATES):
        date = as_timestamp(d)
        print(f"{d} ... ", end="", flush=True)
        entry = {"date": date, "status": "", "url": "", "horizons": 0, "n_lr": 0}
        r, err = None, None
        for u in candidate_urls(d):
            try:
                resp = requests.get(u, headers=HEADERS, timeout=30)
                if resp.status_code == 404:
                    continue
                resp.raise_for_status()
                r, entry["url"] = resp, u
                break
            except Exception as e:
                err = e

        if r is None:
            if err is not None:
                print(f"FETCH ERROR {err}")
                entry["status"] = f"fetch_error: {err}"
            else:
                print("no accessible page (all URL variants 404)")
                entry["status"] = "404"
            log.append(entry)
            time.sleep(args.sleep)
            continue

        with open(os.path.join(srcdir, f"fomcprojtabl{d}.htm"), "w",
                  encoding="utf-8") as f:
            f.write(r.text)

        h = parse_all_horizons(r.text)
        if not h:
            print("PARSE FAILED <-- inspect archived HTML by hand")
            entry["status"] = "parse_failed"
            log.append(entry)
            time.sleep(args.sleep)
            continue

        for hz, vals in h.items():
            for v in vals:
                dots_rows.append({"date": date, "horizon": hz, "dot": float(v)})
            for lvl in sorted(set(vals)):
                count_rows.append({"date": date, "horizon": hz,
                                   "rate_level": float(lvl),
                                   "count": int(sum(1 for x in vals if x == lvl))})

        entry["status"] = "ok"
        entry["horizons"] = len(h)
        entry["n_lr"] = len(h.get("LR", []))
        log.append(entry)
        print(f"{len(h)} horizons  "
              + "  ".join(f"{k}:n={len(v)}" for k, v in sorted(h.items())))
        time.sleep(args.sleep)

    if not dots_rows:
        print("\nNothing parsed. Nothing written.")
        return

    dots = pd.DataFrame(dots_rows).sort_values(["date", "horizon", "dot"])
    counts = pd.DataFrame(count_rows).sort_values(["date", "horizon", "rate_level"])

    disp = (dots.groupby(["date", "horizon"])["dot"]
                .agg(n="count", mean="mean", median="median",
                     sd=lambda s: float(np.std(s, ddof=0)),
                     iqr=lambda s: float(np.percentile(s, 75)
                                         - np.percentile(s, 25)),
                     range=lambda s: float(s.max() - s.min()))
                .reset_index())

    dots.to_csv(os.path.join(outdir, "dotplot_dots_long.csv"), index=False)
    counts.to_csv(os.path.join(outdir, "dotplot_counts_long.csv"), index=False)
    disp.to_csv(os.path.join(outdir, "dotplot_dispersion.csv"), index=False)
    pd.DataFrame(log).to_csv(os.path.join(outdir, "fetch_log.csv"), index=False)

    ok = sum(1 for e in log if e["status"] == "ok")
    print(f"\n{'='*66}")
    print(f"  meetings parsed        {ok} / {len(log)}")
    print(f"  dots extracted         {len(dots)}")
    print(f"  meeting-horizon cells  {len(disp)}")
    print(f"  source HTML archived   {srcdir}")
    bad = [e for e in log if e["status"] != "ok"]
    if bad:
        print("\n  NEEDS ATTENTION:")
        for e in bad:
            print(f"    {e['date'].date()}  {e['status']}")


if __name__ == "__main__":
    main()
