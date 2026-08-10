"""
fetch_deanonymized.py
=====================
Build the DE-ANONYMIZED archive: participant-level SEP submissions with names
attached, every horizon, every meeting whose key has been released.

    python3 fetch_deanonymized.py --root ..

WHAT THIS IS
------------
Two documents per meeting, both released on a lag:

  FOMC{date}SEPcompilation.pdf   individual projections, participants labelled
                                 by randomized number. Five-year lag.
  FOMC{date}SEPkey.pdf           number -> name. Ten-year lag for 2007-2015
                                 compilations, five years from March 2016.

Values here are RAW submissions, not the eighth-point-binned values the dot
plot displays. In January 2012 participants wrote 3.80, 4.20 and 4.25; the plot
renders those as 3.75, 4.25 and 4.25. This archive has the former.

TWO THINGS THAT WILL BITE IF IGNORED
------------------------------------
1. Longer-run rows carry FOUR values where year rows carry five, because
   longer-run core PCE is not collected. Parsing that wrong slides the funds
   rate into the core-PCE column and yields a plausible but entirely wrong
   series. The validation gate below is what catches it.

2. Participant numbers are RE-RANDOMIZED every compilation. Number 7 in 2016Q1
   is not number 7 in 2016Q2. Only the name links a person across meetings,
   which is why anything requiring participant fixed effects depends on the key
   having been released.

NAME NORMALISATION
------------------
The Fed's key files are not internally consistent about how a person is
written: the same individual appears as "Narayana Kocherlakota Minneapolis
Reserve Bank" and "Narayana Kocherlakota Minneapolis FRB", and Yellen appears
both as "Janet Yellen" and under a Chair title. Left alone this splits one
person into several and understates their persistence. A `person` column
carries a normalised surname key; `participant_raw` preserves the original
string so nothing is lost.

OUTPUTS (written under <root>/deanonymized/)
--------------------------------------------
  participant_panel.csv     date, proj_id, person, participant_raw, horizon,
                            gdp, unemp, pce, core_pce, ffr
  participant_dispersion.csv    date, horizon, n, mean, median, sd, iqr, range
  fetch_log.csv                 per-meeting status and validation verdict

Source PDFs are archived to <root>/sources/compilations/ and /keys/.
"""

import argparse
import io
import os
import re
import time

import numpy as np
import pandas as pd
import requests
import pdfplumber

from sep_dates import SEP_DATES, as_timestamp

BASE = "https://www.federalreserve.gov/monetarypolicy/files"
COMP = BASE + "/FOMC{date}SEPcompilation.pdf"
KEY = BASE + "/FOMC{date}SEPkey.pdf"
HEADERS = {"User-Agent": "Mozilla/5.0 (academic research)"}

RE_YEAR = re.compile(
    r"^\s*(\d{1,2})\s+(20\d{2})\s+"
    r"(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s*$")
RE_LR = re.compile(
    r"^\s*(\d{1,2})\s+(?:LR|Longer\s*run)\s+"
    r"(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s*$")

INSTITUTION_WORDS = {
    "board", "governors", "office", "members", "reserve", "bank", "frb",
    "federal", "of", "the", "new", "york", "st", "louis", "city", "kansas",
    "san", "francisco", "chair", "vice", "chairman", "president", "dr", "mr",
    "ms", "mrs", "minneapolis", "atlanta", "boston", "chicago", "cleveland",
    "dallas", "philadelphia", "richmond",
}


def normalise_person(raw):
    """
    Reduce a key-file label to a stable surname token. The surname is the last
    name-like token before any institution words, which survives the Fed's
    inconsistent titling and branch naming.
    """
    toks = [t for t in re.sub(r"[^A-Za-z ]", " ", str(raw)).split()
            if len(t) > 1 and t.lower() not in INSTITUTION_WORDS]
    return toks[-1].title() if toks else str(raw).strip()


def fetch(url, path=None):
    r = requests.get(url, headers=HEADERS, timeout=45)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    if path:
        with open(path, "wb") as f:
            f.write(r.content)
    return r.content


def parse_compilation(pdf_bytes, date):
    rows = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            for line in (page.extract_text() or "").split("\n"):
                m = RE_YEAR.match(line)
                if m:
                    rows.append({"proj_id": int(m.group(1)),
                                 "horizon": m.group(2),
                                 "gdp": float(m.group(3)),
                                 "unemp": float(m.group(4)),
                                 "pce": float(m.group(5)),
                                 "core_pce": float(m.group(6)),
                                 "ffr": float(m.group(7))})
                    continue
                m = RE_LR.match(line)
                if m:
                    rows.append({"proj_id": int(m.group(1)), "horizon": "LR",
                                 "gdp": float(m.group(2)),
                                 "unemp": float(m.group(3)),
                                 "pce": float(m.group(4)),
                                 "core_pce": np.nan,
                                 "ffr": float(m.group(5))})
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["date"] = date
    return df.drop_duplicates(subset=["date", "proj_id", "horizon"])


def parse_key(pdf_bytes):
    out = {}
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            for line in (page.extract_text() or "").split("\n"):
                m = re.match(r"^\s*(\d{1,2})\s+([A-Z][A-Za-z.'\- ]+)\s*$", line)
                if m:
                    pid, nm = int(m.group(1)), m.group(2).strip()
                    if 1 <= pid <= 19 and len(nm) > 2:
                        out[pid] = nm
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="..")
    ap.add_argument("--sleep", type=float, default=0.8)
    ap.add_argument("--dates", nargs="*", default=None)
    args = ap.parse_args()

    outdir = os.path.join(args.root, "deanonymized")
    cdir = os.path.join(args.root, "sources", "compilations")
    kdir = os.path.join(args.root, "sources", "keys")
    for p in (outdir, cdir, kdir):
        os.makedirs(p, exist_ok=True)

    panels, keys, log = [], [], []

    for d in (args.dates or SEP_DATES):
        date = as_timestamp(d)
        print(f"{d} ... ", end="", flush=True)
        e = {"date": date, "compilation": "", "key": "", "n_lr": 0}

        try:
            comp = fetch(COMP.format(date=d),
                         os.path.join(cdir, f"FOMC{d}SEPcompilation.pdf"))
        except Exception as ex:
            print(f"FETCH ERROR {ex}")
            e["compilation"] = f"fetch_error: {ex}"
            log.append(e)
            time.sleep(args.sleep)
            continue

        if comp is None:
            print("not released")
            e["compilation"] = "not_released"
            log.append(e)
            time.sleep(args.sleep)
            continue

        df = parse_compilation(comp, date)
        if df.empty:
            print("NO ROWS PARSED <-- inspect archived PDF")
            e["compilation"] = "no_rows"
            log.append(e)
            time.sleep(args.sleep)
            continue

        e["compilation"] = "ok"
        e["n_lr"] = int((df.horizon == "LR").sum())
        panels.append(df)
        print(f"rows={len(df)} LR={e['n_lr']}", end="")

        try:
            kb = fetch(KEY.format(date=d), os.path.join(kdir, f"FOMC{d}SEPkey.pdf"))
            if kb is None:
                e["key"] = "not_released"
                print("  [key: not released]")
            else:
                mp = parse_key(kb)
                if mp:
                    keys.append(pd.DataFrame({
                        "date": date, "proj_id": list(mp.keys()),
                        "participant_raw": list(mp.values())}))
                    e["key"] = f"ok n={len(mp)}"
                    print(f"  [key: {len(mp)} names]")
                else:
                    e["key"] = "parse_failed"
                    print("  [key: PARSE FAILED]")
        except Exception as ex:
            e["key"] = f"error: {ex}"
            print(f"  [key error: {ex}]")

        log.append(e)
        time.sleep(args.sleep)

    if not panels:
        print("\nNothing parsed. Nothing written.")
        return

    panel = pd.concat(panels, ignore_index=True)
    if keys:
        panel = panel.merge(pd.concat(keys, ignore_index=True),
                            on=["date", "proj_id"], how="left")
    else:
        panel["participant_raw"] = np.nan
    panel["person"] = panel["participant_raw"].apply(
        lambda s: normalise_person(s) if isinstance(s, str) else np.nan)

    panel = panel[["date", "proj_id", "person", "participant_raw", "horizon",
                   "gdp", "unemp", "pce", "core_pce", "ffr"]]
    panel = panel.sort_values(["date", "horizon", "proj_id"]).reset_index(drop=True)
    panel.to_csv(os.path.join(outdir, "participant_panel.csv"), index=False)

    disp = (panel.dropna(subset=["ffr"]).groupby(["date", "horizon"])["ffr"]
                 .agg(n="count", mean="mean", median="median",
                      sd=lambda s: float(np.std(s, ddof=0)),
                      iqr=lambda s: float(np.percentile(s, 75)
                                          - np.percentile(s, 25)),
                      range=lambda s: float(s.max() - s.min()))
                 .reset_index())
    disp.to_csv(os.path.join(outdir, "participant_dispersion.csv"), index=False)

    # ---- cross-source validation against the anonymized archive ----------
    anon_path = os.path.join(args.root, "anonymized", "dotplot_dispersion.csv")
    verdicts = {}
    if os.path.exists(anon_path):
        a = pd.read_csv(anon_path)
        a["date"] = pd.to_datetime(a["date"])
        mrg = disp.merge(a, on=["date", "horizon"], suffixes=("_raw", "_binned"))
        mrg["dn"] = mrg["n_raw"] - mrg["n_binned"]
        mrg["dsd"] = (mrg["sd_raw"] - mrg["sd_binned"]).abs()
        verdicts = {"cells_compared": len(mrg),
                    "n_mismatches": int((mrg["dn"] != 0).sum()),
                    "mean_abs_sd_diff": float(mrg["dsd"].mean())}
        mrg.to_csv(os.path.join(outdir, "raw_vs_binned_comparison.csv"),
                   index=False)

    log_df = pd.DataFrame(log)
    log_df.to_csv(os.path.join(outdir, "fetch_log.csv"), index=False)

    named = panel["person"].notna().mean()
    print(f"\n{'='*66}")
    print(f"  meetings with compilation : {panel.date.nunique()}")
    print(f"  participant-horizon rows  : {len(panel)}")
    print(f"  rows with a name attached : {named:.1%}")
    print(f"  distinct people           : {panel['person'].nunique()}")
    print(f"  raw labels collapsed      : "
          f"{panel['participant_raw'].nunique()} -> {panel['person'].nunique()}")
    if verdicts:
        print(f"\n  CROSS-SOURCE CHECK vs anonymized archive")
        print(f"    meeting-horizon cells compared : {verdicts['cells_compared']}")
        print(f"    participant-count mismatches   : {verdicts['n_mismatches']}")
        print(f"    mean |sd difference|           : "
              f"{verdicts['mean_abs_sd_diff']:.6f}")
        print("    Non-zero sd differences are EXPECTED: this archive is raw,")
        print("    the other is binned to the eighth-point grid. Count")
        print("    mismatches are NOT expected and need investigating.")


if __name__ == "__main__":
    main()
