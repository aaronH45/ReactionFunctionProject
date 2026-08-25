"""Both test figures, in the house style of belieffig.py."""
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SURF, INK, INK2 = '#fcfcfb', '#0b0b0b', '#52514e'
BLUE, ORANGE, AQUA, DARK, RED = '#2a78d6', '#eb6834', '#1baf7a', '#6f6e66', '#c33c3c'
MUTED = '#9a998f'
plt.rcParams['font.family'] = 'DejaVu Sans'

rev = pd.read_csv("/home/claude/tests/rev_panel_tips.csv", parse_dates=["date"])
OUT = json.load(open("/home/claude/tests/results_tests.json"))
PHI, KAPPA, MU = 1.5, 0.10, 0.103
def Lam(n, a):
    j = np.arange(0, int(n*12))
    return ((PHI/(PHI-1))*(1-np.exp(-KAPPA*j))*(a+(1-a)*(1-MU)**j)).mean()
def lam(n, a):
    j = 12.0*n
    return (PHI/(PHI-1))*(1-np.exp(-KAPPA*j))*(a+(1-a)*(1-MU)**j)

def joint(Y, x, lags=4):
    ok = np.isfinite(x) & np.all(np.isfinite(Y), axis=1)
    Y, x = Y[ok], x[ok]; n = len(x); k = Y.shape[1]
    X = np.column_stack([np.ones(n), x]); XtXi = np.linalg.inv(X.T @ X)
    B = np.array([XtXi @ X.T @ Y[:, j] for j in range(k)])
    E = np.column_stack([Y[:, j] - X @ B[j] for j in range(k)])
    g = np.hstack([X*E[:, [j]] for j in range(k)])
    S = g.T @ g
    for L in range(1, lags+1):
        w = 1-L/(lags+1); G = g[L:].T @ g[:-L]; S += w*(G+G.T)
    Bd = np.zeros((2*k, 2*k))
    for j in range(k): Bd[2*j:2*j+2, 2*j:2*j+2] = XtXi
    V = Bd @ S @ Bd; idx = [2*j+1 for j in range(k)]
    return B[:, 1], V[np.ix_(idx, idx)], n

def style(ax):
    ax.set_facecolor(SURF)
    ax.grid(axis='y', color='#eae9e4', lw=0.7, zorder=0)
    for sp in ('top', 'right'): ax.spines[sp].set_visible(False)
    for sp in ('left', 'bottom'): ax.spines[sp].set_color('#d5d4cd')
    ax.tick_params(colors=INK2, labelsize=8.0, length=3)
def head(ax, title, sub):
    ax.text(0, 1.012, sub, transform=ax.transAxes, fontsize=7.4, color=INK2, va='bottom')
    ax.set_title(title, fontsize=8.5, color=INK, loc='left', pad=18)

# =====================================================================
# FIGURE 1 (nominal): split regression, forward loading, intermeeting alpha
# =====================================================================
fig, axes = plt.subplots(1, 3, figsize=(9.6, 2.95)); fig.patch.set_facecolor(SURF)
for ax in axes: style(ax)
ns = np.arange(1, 11)

ax = axes[0]
ms = OUT["maturity_split"]
bM = [ms[str(n)]["b_dM"][0] for n in ns]; bF = [ms[str(n)]["b_dF"][0] for n in ns]
ax.axhline(0, color='#b9b8b0', lw=0.9, zorder=1)
ax.plot(ns, bF, '-o', ms=3.2, lw=1.6, color=BLUE, zorder=4, label='dot revision $dF$')
ax.plot(ns, bM, '-o', ms=3.2, lw=1.6, color=ORANGE, zorder=4, label='dealer revision $dM$')
ax.plot(ns, np.array(bM)+np.array(bF), '-s', ms=3.2, lw=1.4, color=DARK, zorder=5,
        label='sum')
head(ax, 'The window prices the dot surprise', 'ACM expectations component, 2-day window')
ax.set_xlabel('maturity (years)', fontsize=8.2, color=INK2)
ax.set_ylabel('bp per pp', fontsize=8.2, color=INK2)
ax.set_ylim(-31, 47)
ax.legend(loc='upper right', frameon=False, fontsize=7, labelcolor=INK2,
          handlelength=1.5)
ax.text(0.97, 0.20, '$b_{dM}=-b_{dF}$ never rejected', transform=ax.transAxes,
        fontsize=7.2, color=INK, ha='right')

ax = axes[1]
bs, lo, hi = [], [], []
for n in ns:
    b, V, _ = joint(rev[[f"w_SVENF{n:02d}"]].values,
                    (rev.dF - rev.dM).values) if False else (None, None, None)
for n in ns:
    z = rev.dropna(subset=[f"w_SVENF{n:02d}", "dM", "dF"])
    import statsmodels.api as sm
    r = sm.OLS(z[f"w_SVENF{n:02d}"].values,
               sm.add_constant(z[["dM", "dF"]].values)).fit(
        cov_type="HAC", cov_kwds={"maxlags": 4})
    bs.append(r.params[2]); lo.append(r.params[2]-1.96*r.bse[2]); hi.append(r.params[2]+1.96*r.bse[2])
ax.fill_between(ns, lo, hi, color=BLUE, alpha=0.13, lw=0, zorder=2)
ax.axhline(0, color='#b9b8b0', lw=0.9, zorder=1)
ax.axhline(100, color=RED, ls='--', lw=1.1, zorder=3, label='model: loads flat at one')
ax.plot(ns, bs, '-o', ms=3.2, lw=1.7, color=BLUE, zorder=4, label='estimated $b_{dF}(n)$')
head(ax, 'Endpoint pass-through is about one half',
     'GSW instantaneous forwards, 95% band')
ax.set_xlabel('forward maturity (years)', fontsize=8.2, color=INK2)
ax.set_ylabel('bp per pp', fontsize=8.2, color=INK2)
ax.set_ylim(-20, 132)
ax.legend(loc='lower left', frameon=False, fontsize=7, labelcolor=INK2, handlelength=1.5)
ax.text(5.5, 112, '$t=-2.5$ against one at 10y', fontsize=7.2, color=INK, ha='center')

ax = axes[2]
inter = OUT["intermeeting"]
for n, c in [(2, BLUE), (5, AQUA), (10, ORANGE)]:
    b, se = inter[str(n)]["b"], inter[str(n)]["se"]
    ax.errorbar([n], [b], yerr=[1.96*se], fmt='o', ms=4, color=c, capsize=3, lw=1.4, zorder=4)
for a, c in zip([0, .25, .5, 1.0], ['#dedcd4', '#b7b5ab', '#8d8b81', '#5f5e56']):
    ax.plot([2, 5, 10], [100*Lam(n, a) for n in (2, 5, 10)], '--', color=c, lw=1, zorder=2)
    ax.text(10.2, 100*Lam(10, a), f'$\\alpha$={a}', fontsize=7, color=INK2, va='center')
ax.axhline(0, color='#b9b8b0', lw=0.9, zorder=1)
ax.set_xlim(1, 13); ax.set_ylim(-110, 300)
head(ax, 'Belief revisions price between meetings',
     'ACM expectations component vs $100\\,\\Lambda(n,\\alpha)$')
ax.set_xlabel('maturity (years)', fontsize=8.2, color=INK2)
ax.set_ylabel('bp per pp', fontsize=8.2, color=INK2)
fig.subplots_adjust(left=0.065, right=0.985, top=0.795, bottom=0.175, wspace=0.30)
fig.savefig("/home/claude/tests/fig_tests.png", dpi=230, facecolor=SURF)
print("fig_tests.png")

# =====================================================================
# FIGURE 2 (TIPS): composition
# =====================================================================
fig, axes = plt.subplots(1, 3, figsize=(9.6, 2.95)); fig.patch.set_facecolor(SURF)
for ax in axes: style(ax)
fw = np.arange(2, 11)

def band(ax, pre, reg, col, color, label):
    b, l, h = [], [], []
    for n in fw:
        bb, V, _ = joint(rev[[f"{pre}{col}{n:02d}"]].values, rev[reg].values)
        s = np.sqrt(V[0, 0])
        b.append(bb[0]); l.append(bb[0]-1.96*s); h.append(bb[0]+1.96*s)
    ax.fill_between(fw, l, h, color=color, alpha=0.13, lw=0, zorder=2)
    ax.plot(fw, b, '-o', ms=3.2, lw=1.7, color=color, zorder=4, label=label)
    return np.array(b)

ax = axes[0]
ax.axhline(0, color='#b9b8b0', lw=0.9, zorder=1)
band(ax, "w_", "dF", "TIPSF", BLUE, 'real (TIPS) forward')
band(ax, "w_", "dF", "BKEVENF", ORANGE, 'breakeven forward')
head(ax, 'A dot revision is priced as real', 'window $[t-1,t+1]$ on $dF$, 95% bands')
ax.set_xlabel('forward maturity (years)', fontsize=8.2, color=INK2)
ax.set_ylabel('bp per pp', fontsize=8.2, color=INK2)
ax.legend(loc='upper left', frameon=False, fontsize=7, labelcolor=INK2, handlelength=1.5)

ax = axes[1]
ax.axhline(0, color='#b9b8b0', lw=0.9, zorder=1)
band(ax, "i_", "dM", "TIPSF", BLUE, 'real (TIPS) forward')
band(ax, "i_", "dM", "BKEVENF", ORANGE, 'breakeven forward')
ax.plot(fw, [100*lam(n, .25)*(PHI-1)/PHI for n in fw], '--', color=BLUE, lw=1, zorder=3)
ax.plot(fw, [100*lam(n, .25)/PHI for n in fw], '--', color=ORANGE, lw=1, zorder=3)
head(ax, 'Both legs move together, as required',
     'intermeeting on $dM$; dashed: model at $\\alpha=0.25$')
ax.set_xlabel('forward maturity (years)', fontsize=8.2, color=INK2)
ax.set_ylabel('bp per pp', fontsize=8.2, color=INK2)
ax.legend(loc='upper left', frameon=False, fontsize=7, labelcolor=INK2, handlelength=1.5)

ax = axes[2]
af = OUT["alpha_from_forwards"]
labs = [("10y fwd breakeven", 'breakeven 10y'),
        ("9y fwd breakeven", 'breakeven 9y'),
        ("10y fwd nominal", 'nominal 10y'),
        ("10y fwd real", 'real 10y')]
ys = np.arange(len(labs))[::-1]
for y, (k, lb) in zip(ys, labs):
    d = af[k]
    ax.plot([d["ci"][0], d["ci"][1]], [y, y], '-', color=MUTED, lw=1.5, zorder=3)
    ax.plot([d["alpha"]], [y], 'o', ms=5, color=BLUE if 'breakeven' in k else DARK, zorder=4)
ax.axvline(0, color=RED, ls='--', lw=1.0, zorder=2)
ax.axvline(1, color=RED, ls='--', lw=1.0, zorder=2)
ax.text(0.03, -0.42, 'pure learning', fontsize=6.6, color=RED, va='bottom')
ax.text(0.97, -0.42, 'steady state', fontsize=6.6, color=RED, va='bottom', ha='right')
ax.set_yticks(ys); ax.set_yticklabels([l for _, l in labs], fontsize=7.4, color=INK2)
ax.set_xlim(-0.35, 1.42); ax.set_ylim(-0.75, len(labs)-0.35); ax.grid(axis='y', lw=0)
ax.grid(axis='x', color='#eae9e4', lw=0.7, zorder=0)
head(ax, 'The permanent share $\\alpha$', 'implied by each far-forward loading, 95%')
ax.set_xlabel('$\\alpha$', fontsize=9, color=INK2)
fig.subplots_adjust(left=0.062, right=0.988, top=0.795, bottom=0.175, wspace=0.40)
fig.savefig("/home/claude/tests/fig_tips.png", dpi=230, facecolor=SURF)
print("fig_tips.png")
