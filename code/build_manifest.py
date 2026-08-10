"""
build_manifest.py
=================
Inventory every archived source file with a checksum, so the extracted CSVs can
always be traced back to the bytes they came from.

    python3 build_manifest.py --root ..

Writes <root>/manifest.csv with one row per archived file:
    path, kind, meeting_date, source_url, bytes, sha256, retrieved

`retrieved` is the file's modification time, which is when it was downloaded.
Re-running is safe and idempotent; it rebuilds the manifest from whatever is
currently on disk rather than appending.
"""

import argparse
import datetime as dt
import hashlib
import os
import re

import pandas as pd

BASE = "https://www.federalreserve.gov/monetarypolicy"

KINDS = {
    "projections": ("projections_html",
                    BASE + "/fomcprojtabl{date}.htm"),
    "compilations": ("sep_compilation_pdf",
                     BASE + "/files/FOMC{date}SEPcompilation.pdf"),
    "keys": ("sep_key_pdf",
             BASE + "/files/FOMC{date}SEPkey.pdf"),
}


def sha256(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="..")
    args = ap.parse_args()

    rows = []
    for sub, (kind, tmpl) in KINDS.items():
        d = os.path.join(args.root, "sources", sub)
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            p = os.path.join(d, fn)
            if not os.path.isfile(p):
                continue
            m = re.search(r"(\d{8})", fn)
            date = (f"{m.group(1)[:4]}-{m.group(1)[4:6]}-{m.group(1)[6:]}"
                    if m else "")
            rows.append({
                "path": os.path.relpath(p, args.root).replace("\\", "/"),
                "kind": kind,
                "meeting_date": date,
                "source_url": tmpl.format(date=m.group(1)) if m else "",
                "bytes": os.path.getsize(p),
                "sha256": sha256(p),
                "retrieved": dt.datetime.fromtimestamp(
                    os.path.getmtime(p)).strftime("%Y-%m-%d"),
            })

    if not rows:
        print("No archived sources found. Run the fetch scripts first.")
        return

    man = pd.DataFrame(rows).sort_values(["kind", "meeting_date"])
    out = os.path.join(args.root, "manifest.csv")
    man.to_csv(out, index=False)

    print(f"manifest -> {out}")
    print(f"  files      {len(man)}")
    print(f"  total size {man['bytes'].sum()/1e6:.1f} MB")
    print()
    for k, g in man.groupby("kind"):
        print(f"  {k:22s} {len(g):3d} files  "
              f"{g['bytes'].sum()/1e6:7.1f} MB  "
              f"{g.meeting_date.min()} to {g.meeting_date.max()}")

    dupes = man[man.duplicated("sha256", keep=False)]
    if len(dupes):
        print("\n  WARNING: identical checksums across different meetings --")
        print("  a download may have returned the same file twice.")
        print(dupes[["path", "meeting_date"]].to_string(index=False))


if __name__ == "__main__":
    main()
