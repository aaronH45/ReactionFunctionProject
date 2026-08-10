"""
fig_br_vs_fed.py
================
BR i* converted to r* by removing the same 2.0 the Fed side removes, plotted
against the SEP longer-run r*.  Both are then r*, in the same units.

    r*_BR  = i*_BR  - 2.0      (rt and ese, with the ese band)
    r*_Fed = SEP longer-run median - 2.0
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

UP = "/mnt/user-data/uploads/ReactionFunctionProject"
OUT = "/home/claude/rstar_wedge/results"
DUKE, RED, TEAL, GREY = "#2c3e50", "#c0392b", "#16a085", "#7f8c8d"
PI = 2.0

br = pd.read_csv(f"{UP}/falling-stars-fig4.csv", parse_dates=["date"]).rename(
    columns={"istar.rt": "i_rt", "istar.ese": "i_ese",
             "istar.lb": "i_lb", "istar.ub": "i_ub"})
for a, b in [("i_rt", "r_rt"), ("i_ese", "r_ese"),
             ("i_lb", "r_lb"), ("i_ub", "r_ub")]:
    br[b] = br[a] - PI

fed = pd.read_csv(f"{OUT}/fed_rstar.csv", parse_dates=["date"])
acm = pd.read_csv(f"{OUT}/acm_derived.csv", parse_dates=["date"])
acm = acm[acm["date"] >= "2012-01-01"]


def clean(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(alpha=0.25, lw=0.5)
    ax.axhline(0, color="0.55", lw=0.8, zorder=1)


fig = plt.figure(figsize=(11, 8.4))
gs = fig.add_gridspec(3, 3, height_ratios=[1.15, 1.15, 1.0], hspace=0.42,
                      wspace=0.32)

# ---- Panel A: the full BR history -----------------------------------------
axA = fig.add_subplot(gs[0, :])
axA.fill_between(br["date"], br["r_lb"], br["r_ub"], color=DUKE, alpha=0.10,
                 lw=0, label="BR model 95% band")
axA.plot(br["date"], br["r_ese"], lw=1.7, color=DUKE,
         label="r* BR, model estimate")
axA.plot(br["date"], br["r_rt"], lw=1.4, color=TEAL, ls="--",
         label="r* BR, real time")
axA.step(fed["date"], fed["rstar_fed"], where="post", lw=2.2, color=RED,
         label="r* Fed (SEP longer-run median $-$ 2.0)")
axA.set_ylabel("per cent")
axA.set_title("A.  Bauer–Rudebusch r* over its full sample, with the SEP where it exists",
              loc="left", fontsize=11)
axA.legend(fontsize=8, loc="upper right", frameon=True, facecolor="white",
           framealpha=0.9, edgecolor="none", ncol=2)
clean(axA)

# ---- Panel B: the overlap --------------------------------------------------
lo, hi = pd.Timestamp("2011-10-01"), pd.Timestamp("2018-09-30")
b2 = br[(br["date"] >= lo) & (br["date"] <= hi)]
f2 = fed[(fed["date"] >= lo) & (fed["date"] <= hi)]
a2 = acm[(acm["date"] >= lo) & (acm["date"] <= hi)]

axB = fig.add_subplot(gs[1, :])
axB.fill_between(b2["date"], b2["r_lb"], b2["r_ub"], color=DUKE, alpha=0.10, lw=0)
axB.plot(a2["date"], a2["rstar_acm"], lw=1.0, color=GREY, alpha=0.9,
         label="r* ACM 9y1y (for reference)")
axB.plot(b2["date"], b2["r_ese"], lw=2.0, color=DUKE, marker="o", ms=3,
         label="r* BR, model estimate")
axB.plot(b2["date"], b2["r_rt"], lw=1.7, color=TEAL, ls="--", marker="s", ms=3,
         label="r* BR, real time")
axB.step(f2["date"], f2["rstar_fed"], where="post", lw=2.4, color=RED,
         label="r* Fed")
axB.set_xlim(lo, hi)
axB.set_ylabel("per cent")
axB.set_title("B.  The overlap, 2012–2018Q1 — where the wedge would have to be identified",
              loc="left", fontsize=11)
axB.legend(fontsize=8, loc="lower left", frameon=True, facecolor="white",
           framealpha=0.9, edgecolor="none", ncol=2)
clean(axB)

# ---- Panel C: r* against r*, at FOMC meetings ------------------------------
W = pd.read_csv(f"{OUT}/br_matched_panel.csv", parse_dates=["meeting"])
W["r_fed"] = W["istar_fed"] - PI
W["r_br_rt"] = W["istar_rt"] - PI
W["r_br_ese"] = W["istar_ese"] - PI
W["r_acm"] = W["istar_acm"] - PI

axC = fig.add_subplot(gs[2, 0])
lim = [-0.6, 2.4]
axC.plot(lim, lim, color="0.6", lw=1, ls=":", zorder=1)
sc = axC.scatter(W["r_fed"], W["r_br_rt"], c=W["meeting"].map(lambda d: d.year),
                 cmap="viridis", s=26, zorder=3, edgecolor="white", lw=0.4)
axC.set_xlabel("r* Fed"); axC.set_ylabel("r* BR, real time")
axC.set_xlim(lim); axC.set_ylim(lim); axC.set_aspect("equal")
axC.set_title("C.  r* vs r*, real time", loc="left", fontsize=10)
clean(axC)
cb = fig.colorbar(sc, ax=axC, fraction=0.046, pad=0.03)
cb.ax.tick_params(labelsize=7)

axD = fig.add_subplot(gs[2, 1])
axD.plot(lim, lim, color="0.6", lw=1, ls=":", zorder=1)
axD.scatter(W["r_fed"], W["r_br_ese"], c=W["meeting"].map(lambda d: d.year),
            cmap="viridis", s=26, zorder=3, edgecolor="white", lw=0.4)
axD.set_xlabel("r* Fed"); axD.set_ylabel("r* BR, model")
axD.set_xlim(lim); axD.set_ylim(lim); axD.set_aspect("equal")
axD.set_title("D.  r* vs r*, model", loc="left", fontsize=10)
clean(axD)

axE = fig.add_subplot(gs[2, 2])
axE.axhline(0, color="0.55", lw=0.8)
axE.plot(W["meeting"], W["r_fed"] - W["r_br_rt"], lw=1.6, color=TEAL,
         marker="s", ms=3, label=r"$\Delta$ vs BR real time")
axE.plot(W["meeting"], W["r_fed"] - W["r_br_ese"], lw=1.6, color=DUKE,
         marker="o", ms=3, label=r"$\Delta$ vs BR model")
axE.plot(W["meeting"], W["r_fed"] - W["r_acm"], lw=1.2, color=GREY,
         label=r"$\Delta$ vs ACM")
axE.set_ylabel("pp")
axE.set_title("E.  The wedges", loc="left", fontsize=10)
axE.legend(fontsize=7, frameon=False, loc="upper right")
axE.tick_params(axis="x", labelsize=7)
clean(axE)

fig.suptitle("Fed and Bauer–Rudebusch r*, both net of a 2.0 longer-run inflation rate",
             x=0.008, ha="left", fontsize=13)
fig.tight_layout(rect=[0, 0, 1, 0.965])
fig.savefig(f"{OUT}/fig4_br_vs_fed.png", dpi=170)
plt.close(fig)

# ---- numbers ---------------------------------------------------------------
print("Overlap at FOMC meetings, n =", len(W))
for lab, c in [("BR real time", "r_br_rt"), ("BR model", "r_br_ese"),
               ("ACM 9y1y", "r_acm")]:
    d = W[["r_fed", c]].dropna()
    print(f"  {lab:14s} mean r* {d[c].mean():+.3f}   Fed mean "
          f"{d['r_fed'].mean():+.3f}   mean wedge "
          f"{(d['r_fed']-d[c]).mean():+.3f}pp   "
          f"corr {d['r_fed'].corr(d[c]):+.3f}   "
          f"sd(wedge) {(d['r_fed']-d[c]).std():.3f}")
print("\nLevels at the ends of the overlap")
for c, lab in [("r_fed", "Fed"), ("r_br_rt", "BR rt"), ("r_br_ese", "BR ese"),
               ("r_acm", "ACM")]:
    print(f"  {lab:7s} 2012-03 {W[c].iloc[0]:+.2f}   2018-06 {W[c].iloc[-1]:+.2f}"
          f"   change {W[c].iloc[-1]-W[c].iloc[0]:+.2f}")
b12 = br[br["date"] >= "2012-01-01"]
print(f"\nBR model band in r* units, 2012+: mean width "
      f"{(b12['r_ub']-b12['r_lb']).mean():.2f}pp  "
      f"[{b12['r_lb'].mean():+.2f}, {b12['r_ub'].mean():+.2f}]")
print("figure written: fig4_br_vs_fed.png")
