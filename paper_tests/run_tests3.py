"""
Part 3:
 (a) Identification caveat resolution: if the market prices its own belief with
     loading Lambda(n), dealer revisions move yields BETWEEN meetings, not in
     the announcement window. Regress intermeeting RN changes on dM.
 (b) Flatness test of the dot-surprise loading across forward maturities
     (Prediction 4: endpoint revision loads flat at one).
 (c) Figures.
"""
import json
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

D = "/home/claude/tests/data/clean_reactionFunction"
rev = pd.read_csv("/home/claude/tests/rev_panel.csv", parse_dates=["date"])
OUT = json.load(open("/home/claude/tests/results_tests.json"))

PHI, KAPPA, MU = 1.5, 0.10, 0.103
def Lambda(n_years, alpha):
    j = np.arange(0, int(n_years * 12))
    lam = (PHI/(PHI-1))*(1-np.exp(-KAPPA*j))*(alpha+(1-alpha)*(1-MU)**j)
    return lam.mean()

def hac(y, X, lags=4):
    return sm.OLS(y, sm.add_constant(X)).fit(cov_type="HAC",
                                             cov_kwds={"maxlags": lags})

# ---------------- (a) intermeeting regression --------------------------------
acm = pd.read_excel(f"{D}/ACMTermPremium.xls", sheet_name="ACM Daily")
acm["date"] = pd.to_datetime(acm["DATE"], format="%d-%b-%Y")
acm = acm.sort_values("date").reset_index(drop=True)
aidx = acm["date"].searchsorted

def close_before(dt, col, k=-1):
    """ACM value at close of trading day (t + k) relative to event day."""
    p = aidx(dt)
    if p >= len(acm): return np.nan
    if acm["date"].iloc[p] != dt:      # dt not a trading day: previous close
        p = p - 1 if k < 0 else p
    return acm[col].iloc[p + k] if 0 <= p + k < len(acm) else np.nan

print("=" * 80)
print("(a) INTERMEETING TEST: if Lambda>0, dealer revisions move yields between")
print("    meetings. LHS: rn(n) change, close(t-2) minus close(prev_t+1), bp.")
print("=" * 80)
inter = {}
rr = rev.reset_index(drop=True)
print(f" {'n':>3} {'b_dM':>10} {'t':>7} {'se':>7} {'n':>4}   pred a=.25  a=.10")
for n in (2, 5, 10):
    col = f"ACMRNY{n:02d}"
    ys, xs = [], []
    for i in range(1, len(rr)):
        d0, d1 = rr.date.iloc[i-1], rr.date.iloc[i]
        y0 = close_before(d0, col, k=+1)     # close day AFTER previous meeting
        y1 = close_before(d1, col, k=-2)     # close two days before this one
        if np.isfinite(y0) and np.isfinite(y1) and pd.notna(rr.dM.iloc[i]):
            ys.append((y1 - y0) * 100); xs.append(rr.dM.iloc[i])
    r = hac(np.array(ys), np.array(xs)[:, None])
    inter[n] = dict(b=float(r.params[1]), t=float(r.tvalues[1]),
                    se=float(r.bse[1]), n=int(r.nobs))
    print(f" {n:3d} {r.params[1]:+10.2f} {r.tvalues[1]:+7.2f} {r.bse[1]:7.1f} "
          f"{int(r.nobs):4d}   {100*Lambda(n,.25):+7.0f} {100*Lambda(n,.10):+7.0f}")
OUT["intermeeting"] = inter

# alpha bound combining window sum and intermeeting estimate at 10y
print("\n  alpha admissible from intermeeting b at each maturity (95%):")
alphas = np.linspace(0, 1, 501)
for n in (2, 5, 10):
    b, se = inter[n]["b"], inter[n]["se"]
    ok = [a for a in alphas if abs(b - 100*Lambda(n, a))/se < 1.96]
    print(f"   n={n:2d}y: [{min(ok):.2f}, {max(ok):.2f}]" if ok else f"   n={n}y: EMPTY")
    OUT.setdefault("alpha_bound_inter", {})[str(n)] = (
        [float(min(ok)), float(max(ok))] if ok else None)

# ---------------- (b) flatness of the surprise loading in forwards -----------
print("\n" + "=" * 80)
print("(b) PREDICTION 4 TEST: dot-surprise loading flat across forward maturity?")
print("    surprise := dF - dM ;  w_f(n) = a + s(n)*surprise")
print("=" * 80)
rev["surp"] = rev.dF - rev.dM
sload = {}
for nn in range(1, 11):
    col = f"w_SVENF{nn:02d}"
    z = rev.dropna(subset=[col, "surp"])
    r = hac(z[col].values, z[["surp"]].values)
    sload[nn] = (float(r.params[1]), float(r.tvalues[1]))
print("  s(n): " + "  ".join(f"{nn}y {sload[nn][0]:+.0f}" for nn in range(1, 11)))
# flatness contrasts
fl = {}
for (n1, n2) in [(1, 4), (4, 10), (1, 10)]:
    d = rev[f"w_SVENF{n2:02d}"] - rev[f"w_SVENF{n1:02d}"]
    z = pd.concat([d.rename("d"), rev.surp], axis=1).dropna()
    r = hac(z["d"].values, z[["surp"]].values)
    fl[f"{n2}m{n1}"] = (float(r.params[1]), float(r.tvalues[1]))
    print(f"  s({n2}y)-s({n1}y) = {r.params[1]:+7.2f} (t {r.tvalues[1]:+5.2f})")
# test loading = 1 (100 bp/pp) at the far end
z = rev.dropna(subset=["w_SVENF10", "surp"])
r = hac(z["w_SVENF10"].values, z[["surp"]].values)
t1 = (r.params[1] - 100) / r.bse[1]
print(f"  s(10y) = {r.params[1]:+.1f} (se {r.bse[1]:.1f});  H0 flat-at-one: t = {t1:+.2f}")
OUT["surprise_loading"] = dict(s=sload, contrasts=fl,
                               s10_vs_one_t=float(t1))

# ---------------- (c) figures ------------------------------------------------
fig, axes = plt.subplots(1, 3, figsize=(12.5, 3.8))
ns = np.arange(1, 11)

ax = axes[0]
bM = [OUT["maturity_split"][str(n)]["b_dM"][0] if str(n) in OUT["maturity_split"]
      else OUT["maturity_split"][n]["b_dM"][0] for n in ns]
bF = [OUT["maturity_split"][str(n)]["b_dF"][0] if str(n) in OUT["maturity_split"]
      else OUT["maturity_split"][n]["b_dF"][0] for n in ns]
ax.plot(ns, bF, "-o", ms=4, label="dot revision $dF$")
ax.plot(ns, bM, "-o", ms=4, label="dealer revision $dM$")
ax.plot(ns, np.array(bM)+np.array(bF), "-s", ms=4, color="k",
        label="sum ($=100\\,\\Lambda(n)$ if $dM$ pre-priced)")
for a, c in [(0.0, "#bbb"), (0.25, "#888")]:
    ax.plot(ns, [100*Lambda(n, a) for n in ns], "--", color=c, lw=1,
            label=f"model $100\\Lambda$, $\\alpha$={a}")
ax.axhline(0, color="#ccc", lw=0.8)
ax.set_title("ACM expectations component, 2-day window", fontsize=9)
ax.set_xlabel("maturity (years)"); ax.set_ylabel("bp per pp")
ax.legend(fontsize=6.5, frameon=False)

ax = axes[1]
s = [sload[n][0] for n in ns]
ax.plot(ns, s, "-o", ms=4, color="#2a78d6", label="estimated $s(n)$")
ax.axhline(100, color="#c33c3c", ls="--", lw=1, label="model: endpoint loads flat at 1")
ax.axhline(0, color="#ccc", lw=0.8)
ax.set_title("GSW forwards on dot surprise $(dF-dM)$", fontsize=9)
ax.set_xlabel("forward maturity (years)"); ax.set_ylabel("bp per pp")
ax.legend(fontsize=7, frameon=False)

ax = axes[2]
for n, c in [(2, "#2a78d6"), (5, "#1baf7a"), (10, "#eb6834")]:
    ax.plot([0], [0])  # spacing
    b, se = inter[n]["b"], inter[n]["se"]
    ax.errorbar([n], [b], yerr=[1.96*se], fmt="o", color=c, capsize=4,
                label=f"intermeeting $b_{{dM}}$, {n}y")
al = np.array([0, .1, .25, .5])
for a, c in zip(al, ["#ddd", "#bbb", "#999", "#666"]):
    ax.plot([2, 5, 10], [100*Lambda(n, a) for n in (2, 5, 10)], "--", color=c, lw=1)
    ax.text(10.1, 100*Lambda(10, a), f"$\\alpha$={a}", fontsize=7, va="center")
ax.axhline(0, color="#ccc", lw=0.8)
ax.set_xlim(1, 12); ax.set_title("Intermeeting pricing of dealer revisions\nvs model $100\\Lambda(n,\\alpha)$", fontsize=9)
ax.set_xlabel("maturity (years)"); ax.set_ylabel("bp per pp")
ax.legend(fontsize=7, frameon=False, loc="lower left")

fig.tight_layout()
fig.savefig("/home/claude/tests/fig_tests.png", dpi=200)
print("\nsaved fig_tests.png")

json.dump(OUT, open("/home/claude/tests/results_tests.json", "w"), indent=1)
