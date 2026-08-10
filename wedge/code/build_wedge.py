"""
build_wedge.py
==============
Assembles the three series the pre-committed checks need, and writes one
tidy panel that every downstream check reads.  Nothing is retyped anywhere.

    r*_Fed   SEP longer-run federal funds median  minus  longer-run PCE
    r*_Mkt   two candidates, run side by side:
               spd  : SPD/SMP longer-run funds rate median minus longer-run PCE
               acm  : ACM 9y1y risk-neutral forward         minus 2.0

    wedge    Delta_t = r*_Fed - r*_Mkt, measured STRICTLY BEFORE the meeting.

Outputs -> results/
"""
import os
import numpy as np
import pandas as pd

UP = "/mnt/user-data/uploads/ReactionFunctionProject"
OUT = "/home/claude/rstar_wedge/results"
os.makedirs(OUT, exist_ok=True)

# --------------------------------------------------------------------------
# FOMC announcement calendar.  Announcement date = final day of the meeting.
# Scheduled meetings only; unscheduled conference calls and notation votes
# (2013-10-16, 2014-03-04, 2019-10-04, 2020-03-02/15/19/23/31, 2020-08-27,
# 2025-08-22) are excluded, as are the cancelled 2020-03-17/18 dates.
# Source: federalreserve.gov FOMC historical calendars, 2012-2026.
# --------------------------------------------------------------------------
FOMC = [
    "2012-01-25", "2012-03-13", "2012-04-25", "2012-06-20", "2012-08-01",
    "2012-09-13", "2012-10-24", "2012-12-12",
    "2013-01-30", "2013-03-20", "2013-05-01", "2013-06-19", "2013-07-31",
    "2013-09-18", "2013-10-30", "2013-12-18",
    "2014-01-29", "2014-03-19", "2014-04-30", "2014-06-18", "2014-07-30",
    "2014-09-17", "2014-10-29", "2014-12-17",
    "2015-01-28", "2015-03-18", "2015-04-29", "2015-06-17", "2015-07-29",
    "2015-09-17", "2015-10-28", "2015-12-16",
    "2016-01-27", "2016-03-16", "2016-04-27", "2016-06-15", "2016-07-27",
    "2016-09-21", "2016-11-02", "2016-12-14",
    "2017-02-01", "2017-03-15", "2017-05-03", "2017-06-14", "2017-07-26",
    "2017-09-20", "2017-11-01", "2017-12-13",
    "2018-01-31", "2018-03-21", "2018-05-02", "2018-06-13", "2018-08-01",
    "2018-09-26", "2018-11-08", "2018-12-19",
    "2019-01-30", "2019-03-20", "2019-05-01", "2019-06-19", "2019-07-31",
    "2019-09-18", "2019-10-30", "2019-12-11",
    "2020-01-29", "2020-04-29", "2020-06-10", "2020-07-29", "2020-09-16",
    "2020-11-05", "2020-12-16",
    "2021-01-27", "2021-03-17", "2021-04-28", "2021-06-16", "2021-07-28",
    "2021-09-22", "2021-11-03", "2021-12-15",
    "2022-01-26", "2022-03-16", "2022-05-04", "2022-06-15", "2022-07-27",
    "2022-09-21", "2022-11-02", "2022-12-14",
    "2023-02-01", "2023-03-22", "2023-05-03", "2023-06-14", "2023-07-26",
    "2023-09-20", "2023-11-01", "2023-12-13",
    "2024-01-31", "2024-03-20", "2024-05-01", "2024-06-12", "2024-07-31",
    "2024-09-18", "2024-11-07", "2024-12-18",
    "2025-01-29", "2025-03-19", "2025-05-07", "2025-06-18", "2025-07-30",
    "2025-09-17", "2025-10-29", "2025-12-10",
    "2026-01-28", "2026-03-18", "2026-04-29", "2026-06-17", "2026-07-29",
]
FOMC = pd.to_datetime(FOMC)


def load_fed():
    """SEP longer-run r*, all 57 dot-plot meetings."""
    f = pd.read_csv(f"{UP}/analysis/committee_rstar.csv", parse_dates=["date"])
    f = f[["date", "source", "n", "median", "mean", "sd", "iqr"]].rename(
        columns={"median": "rstar_fed", "mean": "rstar_fed_mean",
                 "sd": "rstar_fed_sd", "iqr": "rstar_fed_iqr",
                 "n": "n_fed", "source": "fed_source"})
    return f.sort_values("date").reset_index(drop=True)


def load_participants():
    """Participant-level longer-run submissions, 2012-2020 (de-anonymised)."""
    p = pd.read_csv(f"{UP}/deanonymized/participant_panel.csv",
                    parse_dates=["date"])
    return p[p["horizon"] == "LR"].copy()


def load_spd():
    """SPD/SMP longer-run market r*.  Survey dates before 2023-07 are
    first-of-month placeholders derived from the release filename; the
    survey itself runs ~1-2 weeks ahead of that month's FOMC meeting."""
    m = pd.read_csv(f"{UP}/analysis/market_rstar_long.csv", parse_dates=["date"])
    m = m.rename(columns={"rstar_med": "rstar_spd",
                          "i_star_med": "i_star_spd",
                          "pi_star_med": "pi_star_spd",
                          "i_star_iqr": "i_star_iqr_spd",
                          "pi_source": "pi_source_spd"})
    return m.sort_values("date").reset_index(drop=True)


def load_acm():
    """ACM daily.  9y1y risk-neutral forward = 10*RNY10 - 9*RNY09."""
    d = pd.read_excel(f"{UP}/ACMTermPremium.xls", "ACM Daily")
    d["date"] = pd.to_datetime(d["DATE"], format="%d-%b-%Y")
    d = d.drop(columns=["DATE"]).sort_values("date").reset_index(drop=True)
    d["rn_fwd_9y1y"] = 10 * d["ACMRNY10"] - 9 * d["ACMRNY09"]
    d["tp_fwd_9y1y"] = 10 * d["ACMTP10"] - 9 * d["ACMTP09"]
    d["rstar_acm"] = d["rn_fwd_9y1y"] - 2.0      # long-run pi* = 2.0
    return d


def main():
    fed = load_fed()
    spd = load_spd()
    acm = load_acm()

    ev = pd.DataFrame({"meeting": FOMC})
    ev["is_sep"] = ev["meeting"].isin(fed["date"])

    # ---- Fed side, strictly pre-meeting -----------------------------------
    # The SEP is released AT the announcement, so the wedge a trader could
    # have formed on the morning of meeting t uses the PREVIOUS SEP.
    ev = pd.merge_asof(
        ev.sort_values("meeting"),
        fed.rename(columns={"date": "fed_date"}).sort_values("fed_date"),
        left_on="meeting", right_on="fed_date",
        direction="backward", allow_exact_matches=False)

    # ...and the SEP released AT meeting t, for the revision variable.
    ev = pd.merge_asof(
        ev.sort_values("meeting"),
        fed[["date", "rstar_fed"]].rename(
            columns={"date": "fed_date_at", "rstar_fed": "rstar_fed_at"}
        ).sort_values("fed_date_at"),
        left_on="meeting", right_on="fed_date_at",
        direction="forward", tolerance=pd.Timedelta("0D"))
    ev["sep_revision"] = ev["rstar_fed_at"] - ev["rstar_fed"]

    # ---- Market side A: SPD, matched within the meeting month -------------
    spd_m = spd.copy()
    spd_m["ym"] = spd_m["date"].dt.to_period("M")
    spd_m = spd_m.groupby("ym").last().reset_index()
    ev["ym"] = ev["meeting"].dt.to_period("M")
    ev = ev.merge(spd_m[["ym", "rstar_spd", "i_star_spd", "pi_star_spd",
                         "i_star_iqr_spd", "pi_source_spd"]],
                  on="ym", how="left")

    # ---- Market side B: ACM, last trading day strictly before the meeting --
    acm_cols = ["date", "rstar_acm", "rn_fwd_9y1y", "tp_fwd_9y1y"]
    ev = pd.merge_asof(
        ev.sort_values("meeting"),
        acm[acm_cols].rename(columns={"date": "acm_date"}).sort_values("acm_date"),
        left_on="meeting", right_on="acm_date",
        direction="backward", allow_exact_matches=False)

    ev["wedge_spd"] = ev["rstar_fed"] - ev["rstar_spd"]
    ev["wedge_acm"] = ev["rstar_fed"] - ev["rstar_acm"]

    # ---- Announcement-window yield changes, 1-day and 2-day ---------------
    a = acm.set_index("date")
    idx = a.index
    for lbl, (lo, hi) in {"d1": (-1, 0), "d2": (-1, 1)}.items():
        for n in range(1, 11):
            for kind, pre in [("y", "ACMY"), ("rn", "ACMRNY"), ("tp", "ACMTP")]:
                col = f"{pre}{n:02d}"
                vals = []
                for m in ev["meeting"]:
                    pos = idx.searchsorted(m)
                    # pos = first trading day >= meeting date
                    i0, i1 = pos + lo, pos + hi
                    if pos >= len(idx) or i0 < 0 or i1 >= len(idx) \
                       or idx[pos] != m:
                        vals.append(np.nan)
                    else:
                        vals.append(a[col].iloc[i1] - a[col].iloc[i0])
                ev[f"d{kind}{n}_{lbl}"] = np.array(vals) * 100.0   # -> bp

    ev = ev.drop(columns=["ym"])
    ev.to_csv(f"{OUT}/event_panel.csv", index=False)

    fed.to_csv(f"{OUT}/fed_rstar.csv", index=False)
    spd.to_csv(f"{OUT}/spd_rstar.csv", index=False)
    acm[acm["date"] >= "2011-01-01"][
        ["date", "rstar_acm", "rn_fwd_9y1y", "tp_fwd_9y1y",
         "ACMY10", "ACMRNY10", "ACMTP10"]
    ].to_csv(f"{OUT}/acm_derived.csv", index=False)

    print(f"event_panel.csv  {len(ev)} FOMC meetings  "
          f"{ev['meeting'].min().date()} to {ev['meeting'].max().date()}")
    print(f"  SEP meetings              {ev['is_sep'].sum()}")
    print(f"  wedge_spd non-missing     {ev['wedge_spd'].notna().sum()}")
    print(f"  wedge_acm non-missing     {ev['wedge_acm'].notna().sum()}")
    print(f"  dy10_d2 non-missing       {ev['dy10_d2'].notna().sum()}")


if __name__ == "__main__":
    main()
