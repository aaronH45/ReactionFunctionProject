import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.dates as mdates
import pandas as pd, numpy as np

SURF='#fcfcfb'; INK='#0b0b0b'; INK2='#52514e'; MUTED='#9a998f'
BLUE='#2a78d6'; ORANGE='#eb6834'
plt.rcParams['font.family']='DejaVu Sans'

y = pd.read_csv('/home/claude/hb/fomc_window_panel.csv', parse_dates=['date'])
BASE = y.y10_pct.iloc[0] - y.dy10_bp.iloc[0]/100      # 10y level on 3 Jan 1989
for c in ['cum_in_3chg_pct','cum_out_3chg_pct','cum_in_2chg_pct','cum_out_2chg_pct','cum_total_pct']:
    y[c] = y[c] - BASE                                 # -> cumulative change, starts at 0

def label_stack(ax, items, minsep):
    items = sorted(items, key=lambda t: -t[0])
    pos = [it[0] for it in items]
    for i in range(1, len(pos)):
        if pos[i-1] - pos[i] < minsep:
            pos[i] = pos[i-1] - minsep
    xe = mdates.date2num(y.date.iloc[-1]); xt = xe + 150
    for (val, col, txt), ypos in zip(items, pos):
        ax.plot([xe], [val], 'o', ms=5, color=col, mec=SURF, mew=1.3, zorder=5, clip_on=False)
        if abs(ypos - val) > 0.05:
            ax.plot([xe, xt-25], [val, ypos], color=col, lw=0.8, alpha=0.55, zorder=4, clip_on=False)
        ax.text(xt, ypos, f'{txt}\n{val:+.2f} pp', va='center', ha='left', fontsize=9,
                color=col, linespacing=1.3, fontweight='600', clip_on=False, zorder=6)

def panel(ax, ic, oc, sub):
    ax.plot(y.date, y.cum_total_pct, color=MUTED, lw=1.3, zorder=1, label='Actual 10-year yield (total change)')
    ax.plot(y.date, y[oc], color=ORANGE, lw=2.0, zorder=2, label='Cumulative change OUTSIDE FOMC windows')
    ax.plot(y.date, y[ic], color=BLUE,   lw=2.0, zorder=3, label='Cumulative change IN 3-day FOMC windows')
    ax.set_title(sub, fontsize=10.5, color=INK, loc='left', pad=8)
    ax.set_ylabel('Cumulative change in 10y yield\nsince Jan 1989 (percentage points)', fontsize=9.5,
                  color=INK2, linespacing=1.6, labelpad=8)
    ax.grid(axis='y', color='#eae9e4', lw=0.8, zorder=0)
    for s in ('top','right'): ax.spines[s].set_visible(False)
    for s in ('left','bottom'): ax.spines[s].set_color('#d5d4cd')
    ax.tick_params(colors=INK2, labelsize=9.5, length=3)
    ax.set_xlim(y.date.iloc[0], y.date.iloc[-1])
    ax.set_ylim(-9.2, 3.2); ax.set_yticks(np.arange(-9, 3.1, 1.5))
    ax.axhline(0, color='#b9b8b0', lw=1.1, zorder=1)
    ax.xaxis.set_major_locator(mdates.YearLocator(5))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    label_stack(ax, [(y[ic].iloc[-1], BLUE, 'In FOMC windows'),
                     (y[oc].iloc[-1], ORANGE, 'Outside'),
                     (y.cum_total_pct.iloc[-1], MUTED, 'Actual 10y')], minsep=1.15)

fig, axes = plt.subplots(2, 1, figsize=(12.4, 9.4), sharex=True)
fig.patch.set_facecolor(SURF)
for ax in axes: ax.set_facecolor(SURF)

fig.suptitle('The decline in the 10-year Treasury yield happens in 3-day windows around FOMC announcements',
             fontsize=14, color=INK, x=0.052, ha='left', y=0.978, fontweight='600')
fig.text(0.052, 0.942,
  'Cumulative change in the 10-year yield since 3 Jan 1989, split into FOMC-window days and all other days. '
  'The two components sum to the actual change.',
  fontsize=10, color=INK2, ha='left', va='top')

panel(axes[0], 'cum_in_3chg_pct', 'cum_out_3chg_pct',
      'A.  Window = the daily changes on days t–1, t and t+1   (9.6% of all trading days)')
panel(axes[1], 'cum_in_2chg_pct', 'cum_out_2chg_pct',
      'B.  Window = change from the close of t–1 to the close of t+1, Hillenbrand’s convention   (6.4% of all trading days)')

h, l = axes[0].get_legend_handles_labels()
fig.legend(h, l, loc='lower left', bbox_to_anchor=(0.052, 0.048), frameon=False,
           fontsize=10, labelcolor=INK2, handlelength=1.9, ncol=3, columnspacing=2.2)
fig.text(0.052, 0.012,
  'Replication of Hillenbrand (2025). 10-year zero-coupon yield, Gürkaynak–Sack–Wright (SVENY10), 3 Jan 1989 – 31 Jul 2026.  '
  '300 regularly scheduled FOMC meetings; day t = final day of the meeting.\n'
  'Conference calls, notation votes and unscheduled meetings excluded.',
  fontsize=8.4, color=MUTED, ha='left', va='bottom', linespacing=1.5)
fig.subplots_adjust(left=0.088, right=0.855, top=0.885, bottom=0.115, hspace=0.24)
fig.savefig('/home/claude/hb/hillenbrand_fomc_windows.png', dpi=200, facecolor=SURF)
print('saved', float(y.cum_total_pct.iloc[-1]))
