# SEP dot plot archive

Every FOMC Summary of Economic Projections dot, from the first dot plot in
January 2012 through March 2026, in two archives that differ in what they can
support.

## Run order

```bash
cd code
pip install requests beautifulsoup4 pdfplumber pandas numpy

# 1. download once  -> sources/
python3 fetch_anonymized.py   --root ..    # 57 pages, a few minutes
python3 fetch_deanonymized.py --root ..    # 36 PDF pairs, ~15 min, ~86 MB
python3 build_manifest.py     --root ..

# 2. build data from the archive  -> anonymized/, deanonymized/
python3 parse_archive.py --root ..         # offline, ~3 min, re-runnable
```

**Fetching and parsing are deliberately separate.** The fetch scripts only
populate `sources/`. Everything downstream is built by `parse_archive.py`,
which reads the archive and touches the network not at all.

Two reasons this matters. A partial re-fetch must not be able to clobber a
complete dataset — running `fetch_anonymized.py --dates 20121212 20220316` to
pick up two stragglers rewrote the anonymized CSVs with only those two meetings
in them. `parse_archive.py` always reads every file present, so its output is a
function of the archive rather than of whichever subset was last requested. And
fixing a parser bug should not mean re-downloading 86MB from the Fed: sources
are immutable once archived, parsing is the part that changes.

Re-run `parse_archive.py` freely. It is deterministic and idempotent.

## The two archives

| | `anonymized/` | `deanonymized/` |
|---|---|---|
| Source | published projections page (HTML) | SEP compilation + participant key (PDF) |
| Coverage | all 57 meetings, 2012-01 → 2026-03 | whatever the release lag allows, currently through 2020-12 |
| Identities | none, and none recoverable | full names |
| Values | binned to the eighth-point grid | raw as submitted |
| Matching | none — it's a histogram | within *and* across meetings |

**The distinction that matters.** The anonymized archive is a histogram. It
tells you how many participants submitted 2.5% for the longer run, but not
*which* participant, so dot *i* in the 2026 column cannot be linked to dot *i*
in the longer-run column. Anything requiring a participant's own submissions to
be matched across variables or horizons — a reaction function, a belief panel,
participant fixed effects — needs the de-anonymized archive and is therefore
capped at 2020.

**Binned versus raw.** The Fed's note on Figure 2 reads: *"Each shaded circle
indicates the value (rounded to the nearest 1/8 percentage point)..."* The
compilation records what participants actually wrote. In January 2012 they
submitted 3.80, 4.20 and 4.25, which the plot renders as 3.75, 4.25 and 4.25.
Where both exist, prefer the compilation. The difference in dispersion averages
0.0018pp, reaching 0.0034 across 2012–2015 when 13.5% of submissions sat off
the grid, and falling to 0.0005 across 2016–2020 when only 3.7% did.

Do not pool the two without saying so. `raw_vs_binned_comparison.csv` quantifies
the gap on every overlapping meeting-horizon cell.

## Release lags

Individual projections with randomized participant numbers appear after five
years. The key linking numbers to names follows ten years behind for 2007–2015
compilations and five years from March 2016 onward. Both scripts log
`not_released` rather than skipping silently, so re-running later picks up
whatever has since appeared.

## Files

```
anonymized/
  dotplot_dots_long.csv        one row per dot: date, horizon, dot
  dotplot_counts_long.csv      date, horizon, rate_level, count
  dotplot_dispersion.csv       date, horizon, n, mean, median, sd, iqr, range
  fetch_log.csv

deanonymized/
  participant_panel.csv        date, proj_id, person, participant_raw,
                               horizon, gdp, unemp, pce, core_pce,
                               ffr, ffr_exact          <-- PRIMARY DATASET
  participant_dispersion.csv   date, horizon, n, mean, median, sd, iqr, range
  raw_vs_binned_comparison.csv
  fetch_log.csv

sep_dispersion_combined.csv    Table 2 where available, Figure 2 for 2021+,
                               with a `source` column

sources/
  projections/    fomcprojtabl{date}.htm
  compilations/   FOMC{date}SEPcompilation.pdf
  keys/           FOMC{date}SEPkey.pdf

manifest.csv      every source file: URL, retrieval date, size, SHA-256
parse_report.csv  per meeting: projections-HTML and compilation parse status
```

## Current contents

| | |
|---|---|
| Anonymized | 57 meetings, 4,466 dots, 256 meeting-horizon cells, 18 horizons |
| De-anonymized | 36 meetings, 2,748 participant-horizon rows, 37 people, 100% named |
| Sources | 57 HTML, 36 compilation PDFs, 36 key PDFs, 86 MB |

Validation at last build: zero dots off the eighth-point grid; zero
participant-count mismatches across 162 overlapping meeting-horizon cells; zero
cells where the two archives disagree on the mean by more than 0.02pp. Mean
absolute raw-versus-binned differences are 0.0009 in dispersion and 0.0039 in
level, and 0.0018 in dispersion at the longer run. The longer-run series
reproduces the earlier 56-meeting series exactly on all 56 overlapping
meetings.

`horizon` is a four-digit calendar year or `LR` for the longer run, in both
archives.

## Table 2 is the primary source

Compilation **Table 2** — not the Figure 2 histogram — is the authoritative
record wherever it exists. It gives, for each participant and each horizon, all
five projections side by side:

```
Projection  Year   real GDP   Unemployment   PCE   Core PCE   Federal funds rate
    1       2016     2.3          4.8        1.2     1.6            0.88
    1        LR      2.1          4.8        2.0      --            3.25
```

Three reasons it beats reading dots off the plot. One convention throughout, so
no 2014 break. Every variable participant-matched, which is what backing out a
reaction function requires — the histogram cannot tell you *whose* inflation
forecast sits beside *whose* rate projection. And unbinned values, so genuinely
off-grid submissions survive.

`participant_panel.csv` carries all of it: `gdp`, `unemp`, `pce`, `core_pce`,
`ffr`, `ffr_exact`, by `person` and `horizon`.

Figure 2 is used only for 2021 onward, where no compilation has been released.
`sep_dispersion_combined.csv` stitches the two with a `source` column marking
which supplied each cell.

### Table 2 prints only two decimals

A submission on the eighth-point grid loses its third decimal: 0.875 prints as
`0.88`, 0.125 as `0.13`, 2.375 as `2.38`. This affects 1,759 of 2,748
funds-rate cells — 64% of them.

Restoring is unambiguous. The endings `.13`, `.38`, `.63`, `.88` cannot arise
any other way, because the SEP grid is eighths; and the 45 genuinely off-grid
submissions that do exist (3.8, 4.2, 1.9 and others) are all written to *one*
decimal and never end in those pairs. Verified across all 2,748 rows with no
collisions.

`ffr` is as printed; **`ffr_exact` is restored and is the column to use.**

Note this reverses a natural assumption: for values on the grid, the Figure 2
histogram is the *more* precise source, since it prints 0.875 in full. Table 2
wins only where a submission was genuinely off-grid.

### What the two archives still disagree about

After restoration, 18 of 162 overlapping meeting-horizon cells differ — and
every one contains a genuine off-grid submission that the plot binned away.
January 2012's longer run is the clearest case:

```
Table 2      3.8, 4.0 ×7, 4.2, 4.2, 4.25, 4.5 ×6
Figure 2    3.75, 4.0 ×7, 4.25, 4.25, 4.25, 4.5 ×6
```

Those are not errors in either archive. Table 2 simply knows more.

## The funds-rate convention changed in 2014

The Fed relabelled the Figure 2 rows between the June and September 2014 SEPs:

| | Label | ZLB submission recorded as |
|---|---|---|
| through 2014-06-18 (11 meetings) | "Target Federal Funds Rate at Year-End" | **0.25** — top of the 0–0.25% range |
| from 2014-09-17 (46 meetings) | "Midpoint of target range or target level" | **0.125** — the midpoint |

The compilation PDFs use the midpoint convention throughout. So for
zero-lower-bound observations before September 2014, an archive built from
Figure 2 sits 0.125 above one built from the compilation — for the same
participant making the same submission.

Only 0.25 is affected. It was shorthand for the ZLB range; every higher level
in that era was a point target and means the same thing under both conventions.
Verified: 0.25 is the only level below 0.5 in the target-rate era, and counts at
0.5, 0.75 and 1.0 agree across both archives.

`dotplot_dots_long.csv` therefore carries three columns: `dot` as published,
`dot_midpoint` restated to the midpoint convention, and `convention` recording
which applied. **Use `dot_midpoint` for anything spanning 2014.** Summary
statistics in `dotplot_dispersion.csv` are computed from it.

This matters most for near-term horizons during the ZLB, which is exactly where
a σ(dot, year+2) series lives. It barely touches the longer run, whose values
sit far above zero.

**How this was nearly missed.** Standard deviation is invariant to a constant
shift, and at the ZLB most participants sit on the same value, so an sd-only
comparison across the two archives showed almost nothing. The cross-source check
now compares means as well, which is what surfaces a level convention change.

## Sparse horizon cells

In the early SEPs, participants who expected policy firming only in a later year
supplied projections for that year as well. That produces horizon cells with one
or two observations — for instance 2012-01-25 has two participants projecting
2015 and one projecting 2016. These are genuine individual submissions, not
parse errors, and are kept in `participant_panel.csv`.

Dispersion computed on n=1 is meaningless, so both dispersion files carry a
`full_cross_section` flag (n ≥ 5). Six de-anonymized cells fail it; filter on it
before constructing any series.

## Two traps

**Longer-run rows have one fewer column.** Longer-run core PCE inflation is not
collected, so an LR row carries four values where a year row carries five.
Parsing that wrong slides the funds rate into the core-PCE slot and produces a
plausible, wholly incorrect series. The parser handles the two cases with
separate patterns, and the cross-source check against the anonymized dispersion
is what would catch a regression.

**Participant numbers are re-randomized every compilation.** Number 7 in 2016Q1
is not number 7 in 2016Q2. Only `person` links an individual across meetings.
Never use `proj_id` as a panel identifier.

## Name normalisation

The key files are inconsistent: the same person appears as "Narayana
Kocherlakota Minneapolis Reserve Bank" and "Narayana Kocherlakota Minneapolis
FRB", and Yellen appears both under her own name and under a Chair title. Left
alone this splits one individual into several and understates their persistence.
`person` holds a normalised surname; `participant_raw` preserves the original
string. On the 2012–2020 block this collapses 66 raw labels to 41 people.

## Verification performed before first run

- All-horizon parser tested against the real March 2021 Figure 2 table:
  recovers n=18 for each year horizon and n=17 for the longer run, matching the
  Fed's footnote that one participant did not submit longer-run projections.
  Longer-run dispersion reproduces 0.250863560429882 exactly.
- Table identification is structural, not caption-based, and was confirmed to
  reject two decoys that also carry a "Longer run" header: Table 1, which puts
  variable names in the first column, and the Figure 3 series, which uses range
  bins such as `2.00-2.24`.
- Compilation row patterns tested against real Table 2 lines including page
  footers and continuation headers: no false positives.
- Name normalisation tested on nine real key-file labels including both
  Kocherlakota variants and both Yellen forms.
