"""
Build the delta panel: signed Fed-minus-market disagreement about the
longer-run funds rate, at matched SEP meetings, with revisions.

Paper conventions (Reaction_Function_Update_Final.pdf):
    delta_t = r*_market - r*_Fed          (eq. 7; delta>0 = Fed below market)
The archive's wedge_spd = r*_Fed - r*_spd, so delta = -wedge_spd, except
that for the paper's Fact-2 gap the Fed side is the dot released AT the
meeting (both series netted of 2.0, which cancels in the difference).

Two revision variables:
    d_spd  : dealer revision  = rstar_spd_t   - rstar_spd_{t-1}   (pre-window)
    d_fed  : dot revision     = rstar_fed_at_t- rstar_fed_at_{t-1} (in-window)
    d_delta = d_spd - d_fed
"""
import numpy as np
import pandas as pd

D = "/home/claude/tests/data/clean_reactionFunction"
ev = pd.read_csv(f"{D}/wedge/event_panel.csv", parse_dates=["meeting"])

sep = ev[ev.is_sep & ev.rstar_spd.notna() & ev.rstar_fed_at.notna()].copy()
sep = sep.sort_values("meeting").reset_index(drop=True)

# Fact-2 objects: contemporaneous gap at the meeting
sep["delta"] = sep["rstar_spd"] - sep["rstar_fed_at"]      # market - Fed
sep["d_spd"] = sep["rstar_spd"].diff()
sep["d_fed"] = sep["rstar_fed_at"].diff()
sep["d_delta"] = sep["delta"].diff()
# pre-meeting variant (Fed side = previous SEP, as in build_wedge)
sep["delta_pre"] = -sep["wedge_spd"]

print(f"matched SEP meetings: {len(sep)}  "
      f"{sep.meeting.min().date()} -> {sep.meeting.max().date()}")
print(f"delta: mean {sep.delta.mean():+.3f}  sd {sep.delta.std():.3f}  "
      f"range [{sep.delta.min():+.2f}, {sep.delta.max():+.2f}]")
print(f"|delta|>=0.25 share: {(sep.delta.abs()>=0.25).mean():.3f}")
r = sep.delta
rho = r.autocorr()
print(f"AR(1) of delta: {rho:.3f}")
print(f"d_delta: n {sep.d_delta.notna().sum()}  sd {sep.d_delta.std():.4f}")
print(f"d_spd:   sd {sep.d_spd.std():.4f}   d_fed: sd {sep.d_fed.std():.4f}")
print(f"corr(d_spd, d_fed): {sep[['d_spd','d_fed']].corr().iloc[0,1]:.3f}")

sep.to_csv("/home/claude/tests/delta_panel.csv", index=False)
print("\nwrote delta_panel.csv with", len(sep.columns), "cols")
