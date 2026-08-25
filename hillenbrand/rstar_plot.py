import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.dates as mdates
import pandas as pd, numpy as np
SURF='#fcfcfb'; INK='#0b0b0b'; INK2='#52514e'; MUTED='#9a998f'
BLUE='#2a78d6'; ORANGE='#eb6834'; AQUA='#1baf7a'; VIOLET='#4a3aa7'
plt.rcParams['font.family']='DejaVu Sans'

acm=pd.read_csv('rstar_acm_daily.csv',parse_dates=['date'])
fed=pd.read_csv('rstar_fed.csv',parse_dates=['date'])
hlw=pd.read_csv('rstar_hlw.csv',parse_dates=['date'])
spd=pd.read_csv('rstar_spd.csv',parse_dates=['date'])

def frame(ax,ttl,sub=None):
    ax.set_title(ttl,fontsize=11,color=INK,loc='left',pad=(16 if sub else 7),fontweight='600')
    if sub: ax.text(0,1.012,sub,transform=ax.transAxes,fontsize=9,color=INK2,va='bottom')
    ax.grid(axis='y',color='#eae9e4',lw=0.8,zorder=0); ax.axhline(0,color='#b9b8b0',lw=1.0,zorder=1)
    for s in ('top','right'): ax.spines[s].set_visible(False)
    for s in ('left','bottom'): ax.spines[s].set_color('#d5d4cd')
    ax.tick_params(colors=INK2,labelsize=9.5,length=3)
    ax.set_ylabel('Percent',fontsize=9.5,color=INK2)

fig=plt.figure(figsize=(13.0,10.0)); fig.patch.set_facecolor(SURF)
gs=fig.add_gridspec(2,2,height_ratios=[1,1],hspace=0.34,wspace=0.19,
                    left=0.062,right=0.975,top=0.845,bottom=0.115)
axA=fig.add_subplot(gs[0,:]); axB=fig.add_subplot(gs[1,0]); axC=fig.add_subplot(gs[1,1])
for ax in (axA,axB,axC): ax.set_facecolor(SURF)

# --- A: the measures, 1990-2026
m=acm[acm.date>='1990-01-01']
axA.plot(m.date,m.rstar_acm,color=BLUE,lw=1.5,zorder=3,label='ACM-implied r* (9y1y risk-neutral forward − 2.0), daily')
axA.plot(hlw[hlw.date>='1990-01-01'].date,hlw[hlw.date>='1990-01-01'].rstar_hlw,color=ORANGE,lw=2.0,zorder=4,
         label='Holston–Laubach–Williams r*, quarterly')
axA.plot(fed.date,fed.rstar_fed,color=AQUA,lw=2.0,zorder=5,marker='o',ms=3.2,label='FOMC SEP r* (longer-run median dot − 2.0)')
axA.plot(spd.date,spd.rstar_spd,color=VIOLET,lw=1.6,zorder=4,ls=(0,(4,2)),label='Primary-dealer survey r* (SPD longer-run − 2.0)')
frame(axA,'A.  Four measures of r*, 1990–2026',
      'The ACM-implied series is the market leg of the wedge. It is four times more volatile than HLW and tracks the cycle, not a trend.')
axA.set_xlim(pd.Timestamp('1990-01-01'),pd.Timestamp('2027-06-30')); axA.set_ylim(-2.2,5.6)
axA.xaxis.set_major_locator(mdates.YearLocator(5)); axA.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
axA.legend(loc='upper right',frameon=False,fontsize=9.2,labelcolor=INK2,handlelength=2.0)
axA.axvspan(pd.Timestamp('2012-01-01'),pd.Timestamp('2027-06-30'),color='#f4f4f2',zorder=0)
axA.text(pd.Timestamp('2012-04-01'),-1.95,'wedge sample',fontsize=8.6,color=MUTED,va='bottom',style='italic')

# --- B: zoom on the wedge period
m2=acm[acm.date>='2012-01-01']
axB.fill_between(m2.date,m2.rstar_acm,0,color=BLUE,alpha=0.06,zorder=1)
axB.plot(m2.date,m2.rstar_acm,color=BLUE,lw=1.5,zorder=3,label='ACM-implied r* (market leg)')
axB.plot(fed.date,fed.rstar_fed,color=AQUA,lw=2.2,marker='o',ms=3.6,zorder=5,label='SEP r*, median dot (Fed leg)')
axB.plot(fed.date,fed.rstar_fed_mean,color=AQUA,lw=1.2,ls=(0,(3,2)),zorder=4,label='SEP r*, mean of dots')
axB.plot(spd.date,spd.rstar_spd,color=VIOLET,lw=1.5,ls=(0,(4,2)),zorder=4,label='Primary-dealer survey r*')
axB.plot(hlw[hlw.date>='2012-01-01'].date,hlw[hlw.date>='2012-01-01'].rstar_hlw,color=ORANGE,lw=1.8,zorder=3,label='HLW r*')
frame(axB,'B.  The wedge sample, 2012–2026',
      'Wedge = Fed leg − market leg. The Fed leg takes 12 values; the market leg is a different animal.')
axB.set_xlim(pd.Timestamp('2012-01-01'),pd.Timestamp('2026-12-31')); axB.set_ylim(-2.2,3.0)
axB.xaxis.set_major_locator(mdates.YearLocator(3)); axB.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
axB.legend(loc='lower left',frameon=False,fontsize=8.6,labelcolor=INK2,handlelength=2.0,ncol=1)

# --- C: the contamination
axC.plot(m.date,m.fwd_rn_9y1y,color=BLUE,lw=1.5,zorder=3,label='9y1y risk-neutral forward (ACM)')
axC.plot(m.date,m.ACMY01,color=MUTED,lw=1.3,zorder=2,label='1-year yield (the current cycle)')
frame(axC,'C.  Why: the 9y1y forward is a damped copy of the short rate',
      'corr(levels) = +0.984 · corr(4-quarter changes) = +0.944 · β on Δ1y = 0.287, R² = 0.83')
axC.set_xlim(pd.Timestamp('1990-01-01'),pd.Timestamp('2026-12-31')); axC.set_ylim(-0.6,10.2)
axC.xaxis.set_major_locator(mdates.YearLocator(5)); axC.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
axC.legend(loc='upper right',frameon=False,fontsize=8.8,labelcolor=INK2,handlelength=2.0)

fig.suptitle('The market leg of the wedge is not an r* estimate — it is 29% of the current short rate',
             fontsize=13.5,color=INK,x=0.062,ha='left',y=0.984,fontweight='600')
fig.text(0.062,0.952,'ACM fits a stationary VAR, so a fraction of every current shock survives to the 9-year horizon. '
         'That fraction is the β in panel C: 0.287.\nHLW r*, by contrast, has β = 0.057 on the same regression (R² = 0.07).',
         fontsize=9.6,color=INK2,ha='left',va='top')
fig.text(0.062,0.012,'Sources: ACM daily term-structure decomposition (ACMRNY09/ACMRNY10); FOMC SEP dot-plot archive; NY Fed Holston–Laubach–Williams current estimates; NY Fed Survey of Primary Dealers.',
         fontsize=8.2,color=MUTED,ha='left',va='bottom')
fig.savefig('rstar_comparison.png',dpi=200,facecolor=SURF)
print('ok')
