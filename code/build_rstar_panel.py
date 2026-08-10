"""
build_rstar_panel.py
====================
Extract each FOMC participant's longer-run real neutral rate, meeting by
meeting, and characterise how it moved.

    python3 build_rstar_panel.py --root ..

DEFINITION
----------
    r*_{i,t} = i*_{i,t} - pi*_{i,t}

where i* is participant i's longer-run federal funds rate projection at meeting
t and pi* is that same participant's longer-run PCE inflation projection.

pi* equals 2.0 for all 594 longer-run observations in the sample -- it is the
Committee's stated target, not a forecast, and nobody deviates from it. So r*
is i* minus a constant, and every dispersion statistic is identical between the
two. The subtraction is done anyway because it is the economically meaningful
object and because a future participant may yet break from 2.0, at which point
silently using the nominal dot would be wrong.

OUTPUTS (written under <root>/analysis/)
-----------------------------------------
  rstar_panel_long.csv    date, person, i_star, pi_star, rstar, and that
                          participant's own longer-run GDP and unemployment
  rstar_panel_wide.csv    one row per person, one column per meeting
  rstar_by_meeting.csv    committee median, mean, sd, range, n
  rstar_revisions.csv     every change: who, when, from, to, size
  rstar_decomposition.csv per meeting-pair, the change in committee median
                          split into revision by incumbents and turnover
  rstar_trajectories.png  individual paths against the committee median
"""

import argparse
import os

import numpy as np
import pandas as pd

MIN_MEETINGS_FOR_LABEL = 12


def build(root):
    p = pd.read_csv(os.path.join(root, "deanonymized", "participant_panel.csv"))
    p["date"] = pd.to_datetime(p["date"])
    lr = p[p["horizon"].astype(str) == "LR"].copy()
    lr = lr.dropna(subset=["ffr_exact", "pce", "person"])

    lr = lr.rename(columns={"ffr_exact": "i_star", "pce": "pi_star",
                            "gdp": "lr_gdp", "unemp": "lr_unemp"})
    lr["rstar"] = lr["i_star"] - lr["pi_star"]
    return lr[["date", "person", "i_star", "pi_star", "rstar",
               "lr_gdp", "lr_unemp"]].sort_values(["date", "person"])


def revisions(panel):
    """Every meeting-to-meeting change in a sitting participant's r*."""
    rows = []
    for who, g in panel.sort_values("date").groupby("person"):
        g = g.reset_index(drop=True)
        for a, b in zip(g.itertuples(), g.iloc[1:].itertuples()):
            rows.append({"person": who, "from_date": a.date, "to_date": b.date,
                         "from": a.rstar, "to": b.rstar,
                         "change": b.rstar - a.rstar,
                         "gap_days": (b.date - a.date).days})
    r = pd.DataFrame(rows)
    # only consecutive-meeting pairs are revisions; a longer gap means the
    # person was off the committee in between
    return r[r["gap_days"] <= 110].reset_index(drop=True)


def decompose(panel):
    """
    Split the change in the committee's median r* between consecutive meetings
    into what sitting members did and what turnover did.

      revision  : median among people present at BOTH meetings, differenced
      turnover  : the remainder

    The two need not be independent, but the revision term is the part
    attributable to minds changing rather than to seats changing.
    """
    dates = sorted(panel["date"].unique())
    rows = []
    for a, b in zip(dates[:-1], dates[1:]):
        A = panel[panel.date == a].set_index("person")["rstar"]
        B = panel[panel.date == b].set_index("person")["rstar"]
        both = A.index.intersection(B.index)
        if len(both) < 5:
            continue
        total = B.median() - A.median()
        incumbent = B[both].median() - A[both].median()
        rows.append({"date": pd.Timestamp(b),
                     "n_prev": len(A), "n_now": len(B), "n_both": len(both),
                     "n_entered": len(B.index.difference(A.index)),
                     "n_left": len(A.index.difference(B.index)),
                     "d_median_total": float(total),
                     "d_median_revision": float(incumbent),
                     "d_median_turnover": float(total - incumbent),
                     "n_revised": int((B[both] != A[both]).sum())})
    return pd.DataFrame(rows)


def chart(panel, by_meeting, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(11.5, 6.4))
    counts = panel.groupby("person").size()

    labels = []
    for who, g in panel.sort_values("date").groupby("person"):
        g = g.sort_values("date")
        lab = counts.get(who, 0) >= MIN_MEETINGS_FOR_LABEL
        ax.plot(g["date"], g["rstar"], lw=1.1 if lab else 0.7,
                alpha=0.75 if lab else 0.35,
                color="#2c3e50" if lab else "#95a5a6", zorder=2)
        if lab:
            last = g.iloc[-1]
            labels.append([last["date"], float(last["rstar"]), who])

    # spread labels vertically so co-located endpoints stay readable
    labels.sort(key=lambda z: z[1])
    span = panel["rstar"].max() - panel["rstar"].min()
    gap = span * 0.038
    for i in range(1, len(labels)):
        if labels[i][1] - labels[i - 1][1] < gap:
            labels[i][1] = labels[i - 1][1] + gap
    for x, y, who in labels:
        ax.annotate(who, (x, y), xytext=(6, 0), textcoords="offset points",
                    fontsize=7.5, va="center", color="#2c3e50",
                    annotation_clip=False)

    ax.plot(by_meeting["date"], by_meeting["median"], lw=2.8,
            color="#c0392b", zorder=3, label="Committee median")
    ax.fill_between(by_meeting["date"], by_meeting["min"], by_meeting["max"],
                    color="#c0392b", alpha=0.07, zorder=1,
                    label="Range across participants")

    ax.set_ylabel("r*  (longer-run funds rate minus longer-run PCE), pp")
    ax.set_title("FOMC participants' longer-run real neutral rate, 2012-2020",
                 loc="left", fontsize=12)
    ax.legend(frameon=False, fontsize=8, loc="lower left")
    ax.grid(alpha=0.25, lw=0.5)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.margins(x=0.02)
    fig.subplots_adjust(right=0.88)
    fig.tight_layout(rect=(0, 0, 0.90, 1))
    fig.savefig(path, dpi=170)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="..")
    args = ap.parse_args()
    out = os.path.join(args.root, "analysis")
    os.makedirs(out, exist_ok=True)

    panel = build(args.root)
    panel.to_csv(os.path.join(out, "rstar_panel_long.csv"), index=False)

    wide = panel.pivot_table(index="person", columns="date", values="rstar")
    wide.to_csv(os.path.join(out, "rstar_panel_wide.csv"))

    bym = (panel.groupby("date")["rstar"]
                .agg(n="count", mean="mean", median="median",
                     sd=lambda s: float(np.std(s, ddof=0)),
                     min="min", max="max")
                .reset_index())
    bym["range"] = bym["max"] - bym["min"]
    bym.to_csv(os.path.join(out, "rstar_by_meeting.csv"), index=False)

    rev = revisions(panel)
    rev.to_csv(os.path.join(out, "rstar_revisions.csv"), index=False)

    dec = decompose(panel)
    dec.to_csv(os.path.join(out, "rstar_decomposition.csv"), index=False)

    chart(panel, bym, os.path.join(out, "rstar_trajectories.png"))

    # ---------------------------------------------------------------- report
    print("=" * 68)
    print("r* PANEL")
    print("=" * 68)
    print(f"  observations {len(panel)}   people {panel.person.nunique()}   "
          f"meetings {panel.date.nunique()}")
    print(f"  span {panel.date.min().date()} to {panel.date.max().date()}")

    print("\nCOMMITTEE MEDIAN r*")
    first, last = bym.iloc[0], bym.iloc[-1]
    print(f"  {first['date'].date()}  {first['median']:.3f}   "
          f"(range {first['min']:.2f} to {first['max']:.2f}, n={int(first['n'])})")
    print(f"  {last['date'].date()}  {last['median']:.3f}   "
          f"(range {last['min']:.2f} to {last['max']:.2f}, n={int(last['n'])})")
    print(f"  total change {last['median'] - first['median']:+.3f} pp")

    print("\nREVISION BEHAVIOUR")
    moved = rev[rev["change"] != 0]
    print(f"  consecutive-meeting observations {len(rev)}")
    print(f"  of which a change was made       {len(moved)} "
          f"({len(moved)/len(rev):.0%})")
    print(f"  mean absolute change when moved  {moved['change'].abs().mean():.3f} pp")
    print(f"  downward {int((moved['change'] < 0).sum())}   "
          f"upward {int((moved['change'] > 0).sum())}")
    print(f"  largest single revision          "
          f"{moved.loc[moved['change'].abs().idxmax(), 'change']:+.2f} pp "
          f"({moved.loc[moved['change'].abs().idxmax(), 'person']}, "
          f"{moved.loc[moved['change'].abs().idxmax(), 'to_date'].date()})")

    print("\nDECOMPOSITION OF THE CHANGE IN COMMITTEE MEDIAN")
    print(f"  meeting pairs {len(dec)}")
    print(f"  cumulative total    {dec['d_median_total'].sum():+.3f} pp")
    print(f"  from revision       {dec['d_median_revision'].sum():+.3f} pp")
    print(f"  from turnover       {dec['d_median_turnover'].sum():+.3f} pp")
    c = np.corrcoef(dec["d_median_total"], dec["d_median_revision"])[0, 1]
    print(f"  corr(total, revision) = {c:.3f}")

    print("\nWHO MOVED MOST (sum of absolute revisions, >=8 meetings)")
    cnt = panel.groupby("person").size()
    act = (moved.groupby("person")["change"]
                .agg(total_abs=lambda s: s.abs().sum(),
                     net="sum", n_revisions="count"))
    act = act[act.index.isin(cnt[cnt >= 8].index)]
    print(act.sort_values("total_abs", ascending=False).head(8).round(3).to_string())

    print(f"\nWrote {out}/")


if __name__ == "__main__":
    main()
