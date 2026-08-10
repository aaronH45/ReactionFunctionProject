import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import statsmodels.api as sm

OUT = "/home/claude/rstar_wedge/results"
DUKE = "#2c3e50"
RED = "#c0392b"
TEAL = "#16a085"

ev = pd.read_csv(f"{OUT}/event_panel.csv", parse_dates=["meeting"])
acm = pd.read_csv(f"{OUT}/acm_derived.csv", parse_dates=["date"])
fed = pd.read_csv(f"{OUT}/fed_rstar.csv", parse_dates=["date"])
spd = pd.read_csv(f"{OUT}/spd_rstar.csv", parse_dates=["date"])
acm = acm[acm["date"] >= "2012-01-01"]


def clean(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(alpha=0.25, lw=0.5)


# ---- Figure 1: the two wedges -------------------------------------------
fig, (a1, a2) = plt.subplots(2, 1, figsize=(9.5, 6.6), sharex=True,
                             gridspec_kw={"height_ratios": [3, 2]})
a1.step(fed["date"], fed["rstar_fed"], where="post", lw=2.2, color=RED,
        label="r* Fed  (SEP longer-run median $-$ 2.0)")
a1.plot(acm["date"], acm["rstar_acm"], lw=1.0, color=DUKE, alpha=0.85,
        label="r* Mkt  (ACM 9y1y risk-neutral forward $-$ 2.0)")
a1.plot(spd["date"], spd["rstar_spd"], lw=1.6, color=TEAL, ls="--",
        marker="o", ms=2.5, label="r* Mkt  (SPD longer-run funds rate $-$ 2.0)")
a1.set_ylabel("per cent")
a1.set_title("Fed and market longer-run r*", loc="left", fontsize=12)
a1.legend(fontsize=8.5, loc="upper right", facecolor="white",
          framealpha=0.92, edgecolor="none")
clean(a1)

a2.axhline(0, color="0.5", lw=0.8)
a2.plot(ev["meeting"], ev["wedge_acm"], lw=1.4, color=DUKE, marker="o", ms=2.5,
        label=r"$\Delta_t$ using ACM")
a2.plot(ev["meeting"], ev["wedge_spd"], lw=1.6, color=TEAL, ls="--",
        marker="s", ms=2.5, label=r"$\Delta_t$ using SPD")
a2.set_ylabel("pp")
a2.set_title(r"Pre-meeting signed wedge  $\Delta_t = r^*_{Fed} - r^*_{Mkt}$",
             loc="left", fontsize=12)
a2.legend(frameon=False, fontsize=8.5, loc="upper left")
clean(a2)
fig.tight_layout()
fig.savefig(f"{OUT}/fig1_wedges.png", dpi=170)
plt.close(fig)

# ---- Figure 2: maturity signature ---------------------------------------
rows = []
for n in range(1, 11):
    for kind in ["y", "rn", "tp"]:
        d = ev[[f"d{kind}{n}_d2", "wedge_acm"]].dropna()
        m = sm.OLS(d.iloc[:, 0], sm.add_constant(d.iloc[:, 1:])).fit(
            cov_type="HAC", cov_kwds={"maxlags": 4})
        rows.append({"n": n, "kind": kind, "b": m.params["wedge_acm"],
                     "se": m.bse["wedge_acm"]})
mt = pd.DataFrame(rows)

fig, ax = plt.subplots(figsize=(8.6, 4.8))
style = {"y": (DUKE, "-", "o", "Total yield"),
         "rn": (TEAL, "--", "s", "Risk-neutral component"),
         "tp": (RED, "-.", "^", "Term premium component")}
for k, (c, ls, mk, lab) in style.items():
    s = mt[mt["kind"] == k]
    ax.plot(s["n"], s["b"], color=c, ls=ls, marker=mk, ms=5, lw=2, label=lab)
    ax.fill_between(s["n"], s["b"] - 1.96 * s["se"], s["b"] + 1.96 * s["se"],
                    color=c, alpha=0.11, lw=0)
ax.axhline(0, color="0.5", lw=0.8)
ax.set_xlabel("maturity, years")
ax.set_ylabel("bp per pp of pre-meeting wedge")
ax.set_xticks(range(1, 11))
ax.set_title("Maturity signature of the announcement-window response\n"
             "2-day window, 116 FOMC meetings 2012-2026, ACM wedge",
             loc="left", fontsize=11.5)
ax.legend(frameon=False, fontsize=9)
clean(ax)
fig.tight_layout()
fig.savefig(f"{OUT}/fig2_maturity.png", dpi=170)
plt.close(fig)
mt.to_csv(f"{OUT}/maturity_signature.csv", index=False)

# ---- Figure 3: placebo ---------------------------------------------------
full = pd.read_excel("/mnt/user-data/uploads/ReactionFunctionProject/"
                     "ACMTermPremium.xls", "ACM Daily")
full["date"] = pd.to_datetime(full["DATE"], format="%d-%b-%Y")
full = full.drop(columns=["DATE"]).sort_values("date").reset_index(drop=True)
full["rstar_acm"] = (10 * full["ACMRNY10"] - 9 * full["ACMRNY09"]) - 2.0
full = full[(full["date"] >= ev["meeting"].min())
            & (full["date"] <= ev["meeting"].max())].reset_index(drop=True)
full = pd.merge_asof(full, fed[["date", "rstar_fed"]].rename(
    columns={"date": "sep_date"}), left_on="date", right_on="sep_date",
    direction="backward")
for n, pre in [(10, "ACMTP"), (10, "ACMRNY")]:
    pass
full["dtp10"] = (full["ACMTP10"].shift(-1) - full["ACMTP10"].shift(1)) * 100
full["drn10"] = (full["ACMRNY10"].shift(-1) - full["ACMRNY10"].shift(1)) * 100
full["w_pre"] = full["rstar_fed"].shift(1) - full["rstar_acm"].shift(1)
full["is_fomc"] = full["date"].isin(ev["meeting"])
full = full.dropna(subset=["w_pre", "dtp10"])

rng = np.random.default_rng(20260810)
fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
for ax, col, lab in zip(axes, ["drn10", "dtp10"],
                        ["10y risk-neutral", "10y term premium"]):
    pl = full[~full["is_fomc"]]
    x, y = pl["w_pre"].to_numpy(), pl[col].to_numpy()
    k = int(full["is_fomc"].sum())
    draws = np.empty(5000)
    for i in range(5000):
        s = rng.choice(len(x), size=k, replace=False)
        xx, yy = x[s], y[s]
        draws[i] = ((xx - xx.mean()) @ (yy - yy.mean())) / \
                   ((xx - xx.mean()) @ (xx - xx.mean()))
    fo = full[full["is_fomc"]]
    xo, yo = fo["w_pre"].to_numpy(), fo[col].to_numpy()
    obs = ((xo - xo.mean()) @ (yo - yo.mean())) / ((xo - xo.mean()) @ (xo - xo.mean()))
    ax.hist(draws, bins=45, color="0.72", edgecolor="white", lw=0.4)
    ax.axvline(obs, color=RED, lw=2.2)
    ax.annotate(f"FOMC days\n{obs:+.2f} bp/pp", xy=(obs, ax.get_ylim()[1] * 0.82),
                xytext=(6, 0), textcoords="offset points", color=RED,
                fontsize=9, va="top")
    ax.set_title(f"{lab}", loc="left", fontsize=11)
    ax.set_xlabel("coefficient on the pre-meeting wedge, bp per pp")
    clean(ax)
axes[0].set_ylabel("5,000 random draws of 114 non-FOMC days")
fig.suptitle("Placebo: the wedge does nothing on days without an announcement",
             x=0.01, ha="left", fontsize=12)
fig.tight_layout(rect=[0, 0, 1, 0.94])
fig.savefig(f"{OUT}/fig3_placebo.png", dpi=170)
plt.close(fig)
print("figures written")
print(mt.pivot(index="n", columns="kind", values="b").round(3).to_string())
