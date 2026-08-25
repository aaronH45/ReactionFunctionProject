import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.dates as mdates
import pandas as pd, numpy as np
SURF='#fcfcfb'; INK='#0b0b0b'; INK2='#52514e'; MUTED='#9a998f'
ORANGE='#eb6834'; AQUA='#1baf7a'
plt.rcParams['font.family']='DejaVu Sans'

h=pd.read_csv('rstar_hlw_both.csv',parse_dates=['date']).sort_values('date')
h['rstar_hlw']=h.one_sided
f=pd.read_csv('fig9_data.csv',parse_dates=['date']).sort_values('date')
f['rf']=f.lr_mean-2.0
m=pd.merge_asof(f[['date','rf']],h.rename(columns={'rstar_hlw':'hlw'}),on='date',
                direction='backward',tolerance=pd.Timedelta('120D')).dropna()
c=m.rf.corr(m.hlw); c2=m.rf.corr(m.two_sided)

fig,axes=plt.subplots(1,2,figsize=(7.4,3.1),gridspec_kw={'width_ratios':[1.55,1]})
fig.patch.set_facecolor(SURF)
for ax in axes:
    ax.set_facecolor(SURF); ax.grid(axis='y',color='#eae9e4',lw=0.8,zorder=0)
    for s in ('top','right'): ax.spines[s].set_visible(False)
    for s in ('left','bottom'): ax.spines[s].set_color('#d5d4cd')
    ax.tick_params(colors=INK2,labelsize=8.4,length=3)

def head(ax,t,s,pad=17):
    ax.text(0,1.012,s,transform=ax.transAxes,fontsize=8.0,color=INK2,va='bottom')
    ax.set_title(t,fontsize=9.4,color=INK,loc='left',pad=pad)

# ---------------- A: full sample ----------------
ax=axes[0]
ax.axvspan(f.date.min(),pd.Timestamp('2028-06-01'),color='#eef6f2',zorder=0)
ax.axhline(0,color='#b9b8b0',lw=0.9,zorder=1)
ax.plot(h.date,h.rstar_hlw,color=ORANGE,lw=1.8,zorder=3,label='HLW $r^{*}$ (one-sided)')
ax.plot(f.date,f.rf,'-o',color=AQUA,ms=2.6,lw=1.9,zorder=4,label='FOMC $r^{*}$ (SEP $-$ 2.0)')
ax.annotate(f'{h.rstar_hlw.iloc[-1]:.2f}%',xy=(h.date.iloc[-1],h.rstar_hlw.iloc[-1]),
            xytext=(6,6),textcoords='offset points',fontsize=8.2,color=ORANGE,fontweight='600')
ax.annotate(f'{f.rf.iloc[-1]:.2f}%',xy=(f.date.iloc[-1],f.rf.iloc[-1]),
            xytext=(6,-8),textcoords='offset points',fontsize=8.2,color=AQUA,fontweight='600')
ax.text(pd.Timestamp('2012-09-01'),0.12,'SEP era',fontsize=8.0,color=AQUA,fontweight='600')
head(ax,'The secular decline, and where the FOMC series starts',
     'HLW quarterly 1961--2026; FOMC from Jan 2012')
ax.set_ylabel('Percent',fontsize=8.8,color=INK2)
ax.set_xlim(pd.Timestamp('1960-06-01'),pd.Timestamp('2028-06-01')); ax.set_ylim(-0.3,5.9)
ax.xaxis.set_major_locator(mdates.YearLocator(10)); ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax.legend(loc='upper right',frameon=False,fontsize=8.0,labelcolor=INK2,handlelength=1.6,
          bbox_to_anchor=(1.0,0.90))

# ---------------- B: the overlap ----------------
ax=axes[1]
hz=h[h.date>=pd.Timestamp('2011-06-01')]
ax.plot(hz.date,hz.rstar_hlw,color=ORANGE,lw=1.9,zorder=3,label=f'HLW one-sided ({c:+.2f})')
ax.plot(hz.date,hz.two_sided,color=ORANGE,lw=1.1,ls=(0,(3.5,2.2)),alpha=0.85,zorder=3,label=f'HLW two-sided ({c2:+.2f})')
ax.plot(f.date,f.rf,'-o',color=AQUA,ms=2.6,lw=1.9,zorder=4,label='FOMC')
ax.axhline(0,color='#b9b8b0',lw=0.9,zorder=1)
ax.annotate('',xy=(pd.Timestamp('2021-06-01'),2.26),xytext=(pd.Timestamp('2012-06-01'),0.59),
            arrowprops=dict(arrowstyle='->',color=ORANGE,lw=1.0,alpha=0.55))
ax.annotate('',xy=(pd.Timestamp('2022-03-01'),0.42),xytext=(pd.Timestamp('2012-06-01'),2.21),
            arrowprops=dict(arrowstyle='->',color=AQUA,lw=1.0,alpha=0.55))
head(ax,'They move in opposite directions','57 SEP meetings; HLW one- and two-sided')
ax.set_ylabel('Percent',fontsize=8.8,color=INK2)
ax.set_xlim(pd.Timestamp('2011-06-01'),pd.Timestamp('2026-12-31')); ax.set_ylim(0.0,3.05)
ax.xaxis.set_major_locator(mdates.YearLocator(4)); ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax.text(0.035,0.035,'corr. with FOMC\nin parentheses',transform=ax.transAxes,fontsize=7.6,
        color=INK2,va='bottom',linespacing=1.4)
ax.legend(loc='upper right',frameon=False,fontsize=7.4,labelcolor=INK2,handlelength=1.6,bbox_to_anchor=(1.0,1.0))

fig.subplots_adjust(left=0.070,right=0.975,top=0.815,bottom=0.125,wspace=0.30)
fig.savefig('s_rstar_two.png',dpi=230,facecolor=SURF)
print('one-sided: corr(lvl) %.3f corr(chg) %.3f | two-sided: corr(lvl) %.3f corr(chg) %.3f | n=%d'%(
    c,m.rf.diff().corr(m.hlw.diff()),c2,m.rf.diff().corr(m.two_sided.diff()),len(m)))
print('FOMC 2012 %.2f -> Mar2022 %.2f -> 2026 %.2f'%(f.rf.iloc[0],f.rf.min(),f.rf.iloc[-1]))
print('HLW  2012 %.2f -> 2021 %.2f -> 2026 %.2f'%(
    h[h.date.dt.year==2012].rstar_hlw.iloc[-1],h.rstar_hlw[h.date.dt.year==2021].max(),h.rstar_hlw.iloc[-1]))
