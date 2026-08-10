"""
fetch_spd.py
============
Archive the NY Fed Survey of Market Expectations -- the Survey of Primary
Dealers (SPD) and Survey of Market Participants (SMP) -- to build a market-side
counterpart to the SEP dot archive.

    python3 fetch_spd.py --root ..

WHY THIS SURVEY
---------------
The SPD questionnaire mirrors SEP Table 2 almost exactly. Question 2a asks each
dealer for longer-run projections of real GDP growth, the unemployment rate,
PCE inflation and the federal funds rate -- with core PCE marked NA at the
longer-run horizon, the same omission the SEP makes. So

    r*_dealer = (longer-run federal funds rate) - (longer-run PCE inflation)

is constructed exactly as it is for FOMC participants, from the same four
columns, at meeting frequency.

DO NOT ASSUME 2 PERCENT ON THE MARKET SIDE
------------------------------------------
For the FOMC, pi* = 2.0 is a commitment and the published longer-run range
collapses to a point: every participant submits 2.0. For dealers it is a
FORECAST and may differ. Imposing 2.0 would relabel inflation-credibility
disagreement as real-rate disagreement, which is precisely the confusion this
project exists to remove. Question 2a supplies dealer longer-run PCE directly,
so the subtraction can be done properly. The gap between the assumed and the
actual is itself a measure of perceived credibility.

WHAT THE SURVEY HAS THAT THE DOT PLOT DOES NOT
----------------------------------------------
Question 2e asks for a full subjective probability distribution over the longer
run funds rate, in ten bins from "<= 0.50%" to ">= 4.51%", using wording
identical to the SEP definition -- "the level the target federal funds rate
would be expected to converge to under appropriate monetary policy and in the
absence of further shocks to the economy."

That permits a decomposition unavailable for the FOMC:

    disagreement   dispersion of point estimates ACROSS dealers
    uncertainty    spread of each dealer's OWN distribution

The dots are point estimates only, so committee "disagreement" cannot be
separated from individual uncertainty. On the market side it can. Note 2e is
asked only periodically -- the March 2026 survey records that it was last put
in September 2025 -- so coverage must be checked survey by survey rather than
assumed.

Question 2b separately asks for the average funds rate over the next ten years,
which differs from the longer-run level by the expected transition path.
Questions 8c and 8d give five-year and five-year-forward CPI distributions.

OUTPUT
------
    <root>/spd/data/       machine-readable survey files (.xlsx / .xls)
    <root>/spd/results/    published results PDFs
    <root>/spd/questions/  questionnaires
    <root>/spd/spd_manifest.csv

Files are named by their survey date where the page provides one, and otherwise
keep the Fed's own filename. Nothing is renamed silently.
"""

import argparse
import os
import re
import time
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

INDEX = "https://www.newyorkfed.org/markets/market-intelligence/survey-of-market-expectations"
HEADERS = {"User-Agent": "Mozilla/5.0 (academic research)"}

MONTHS = {m.lower(): i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}


def classify(url):
    u = url.lower()
    if u.endswith((".xlsx", ".xls")):
        return "data"
    if "result" in u:
        return "results"
    if "survey" in u or "question" in u:
        return "questions"
    return None


def survey_date(url):
    """Recover (year, month) from the Fed's inconsistent filenames."""
    m = re.search(r"/survey/(\d{4})/", url)
    year = int(m.group(1)) if m else None
    fn = url.rsplit("/", 1)[-1].lower()
    mon = None
    for name, num in MONTHS.items():
        if re.search(rf"\b{name}", fn):
            mon = num
            break
    return year, mon


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="..")
    ap.add_argument("--sleep", type=float, default=0.5)
    ap.add_argument("--kinds", nargs="*", default=["data", "results", "questions"])
    args = ap.parse_args()

    base = os.path.join(args.root, "spd")
    for k in ("data", "results", "questions"):
        os.makedirs(os.path.join(base, k), exist_ok=True)

    print("fetching index ...", end=" ", flush=True)
    r = requests.get(INDEX, headers=HEADERS, timeout=45)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    links = []
    for a in soup.find_all("a", href=True):
        href = urljoin(INDEX, a["href"])
        if "/markets/survey/" not in href:
            continue
        kind = classify(href)
        if kind is None or kind not in args.kinds:
            continue
        links.append((kind, href))
    links = sorted(set(links))
    print(f"{len(links)} files listed")

    rows = []
    for kind, url in links:
        y, m = survey_date(url)
        fn = url.rsplit("/", 1)[-1].split("?")[0]
        stem = f"{y}-{m:02d}_" if (y and m) else (f"{y}_" if y else "")
        path = os.path.join(base, kind, stem + fn)

        if os.path.exists(path):
            rows.append({"kind": kind, "year": y, "month": m,
                         "url": url, "path": path,
                         "bytes": os.path.getsize(path), "status": "cached"})
            continue

        try:
            resp = requests.get(url, headers=HEADERS, timeout=60)
            resp.raise_for_status()
            with open(path, "wb") as f:
                f.write(resp.content)
            status = "ok"
            print(f"  {kind:9s} {y}-{str(m).zfill(2)}  {fn}  "
                  f"{len(resp.content)/1e3:.0f} KB")
        except Exception as e:
            status = f"error: {e}"
            print(f"  {kind:9s} {y}-{str(m).zfill(2)}  {fn}  FAILED {e}")
        rows.append({"kind": kind, "year": y, "month": m, "url": url,
                     "path": path,
                     "bytes": os.path.getsize(path) if os.path.exists(path) else 0,
                     "status": status})
        time.sleep(args.sleep)

    man = pd.DataFrame(rows).sort_values(["kind", "year", "month"])
    man.to_csv(os.path.join(base, "spd_manifest.csv"), index=False)

    print(f"\n{'='*60}")
    print(f"  files      {len(man)}")
    print(f"  total      {man['bytes'].sum()/1e6:.1f} MB")
    for k, g in man.groupby("kind"):
        yrs = g["year"].dropna()
        span = f"{int(yrs.min())}-{int(yrs.max())}" if len(yrs) else "?"
        print(f"  {k:10s} {len(g):3d} files   {span}")
    bad = man[~man["status"].isin(["ok", "cached"])]
    if len(bad):
        print(f"\n  FAILED: {len(bad)}")
        print(bad[["kind", "year", "month", "status"]].to_string(index=False))
    print(f"\n  manifest -> {base}/spd_manifest.csv")
    print("\n  Next: inspect one file under spd/data/ to establish whether it")
    print("  holds INDIVIDUAL dealer responses or only summary statistics.")
    print("  That determines whether a dealer-level panel is possible or only")
    print("  a median/IQR series.")


if __name__ == "__main__":
    main()
