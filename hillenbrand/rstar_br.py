import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.dates as mdates
import pandas as pd, numpy as np
SURF='#fcfcfb'; INK='#0b0b0b'; INK2='#52514e'; MUTED='#9a998f'
ORANGE='#eb6834'; AQUA='#1baf7a'; BLUE='#2a78d6'; DARK='#6f6e66'
plt.rcParams['font.family']='DejaVu Sans'

b=pd.read_csv('/mnt/user-data/uploads/clean_reactionFunction/falling-stars-fig4.csv',parse_dates=['date']).sort_values('date')
h=pd.read_csv('rstar_hlw.csv',parse_dates=['date']).sort_values('date')
m=pd.merge_asof(b,h,on='date',direction='nearest',tolerance=pd.Timedelta('60D')).dropna()
m['pi']=m['istar.rt']-m.rstar_hlw

fig,axes=plt.subplots(1,2,figsize=(7.4,3.05),gridspec_kw={'width_ratios':[1.45,1]})
fig.patch.set_facecolor(SURF)
for ax in axes:
    ax.set_facecolor(SURF); ax.grid(axis='y',color='#eae9e4',lw=0.8,zorder=0)
    for s in ('top','right'): ax.spines[s].set_visible(False)
    for s in ('left','bottom'): ax.spines[s].set_color('#d5d4cd')
    ax.tick_params(colors=INK2,labelsize=8.4,length=3)
def head(ax,t,s):
    ax.text(0,1.012,s,transform=ax.transAxes,fontsize=8.0,color=INK2,va='bottom')
    ax.set_title(t,fontsize=9.4,color=INK,loc='left',pad=17)

# ---- A: levels
ax=axes[0]
ax.fill_between(b.date,b['istar.lb'],b['istar.ub'],color='#dfe8f4',zorder=1,
                label='BR shifting-endpoint 90% band')
ax.plot(b.date,b['istar.rt'],color=BLUE,lw=1.9,zorder=4,label='Bauer--Rudebusch $i^{*}$ (real time)')
ax.plot(b.date,b['istar.ese'],color=BLUE,lw=1.2,ls=(0,(4,2.5)),zorder=4,label='Bauer--Rudebusch $i^{*}$ (ESE)')
ax.plot(h[h.date>='1971-01-01'].date,h[h.date>='1971-01-01'].rstar_hlw,color=ORANGE,lw=1.9,zorder=5,
        label='HLW $r^{*}$ (real)')
ax.axhline(0,color='#b9b8b0',lw=0.9,zorder=2)
head(ax,'A nominal star and a real star','Quarterly; BR ends 2018Q1, HLW runs to 2026')
ax.set_ylabel('Percent',fontsize=8.8,color=INK2)
ax.set_xlim(pd.Timestamp('1971-01-01'),pd.Timestamp('2027-06-01')); ax.set_ylim(-0.6,10.2)
ax.xaxis.set_major_locator(mdates.YearLocator(10)); ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax.legend(loc='upper right',frameon=False,fontsize=7.6,labelcolor=INK2,handlelength=1.7)

# ---- B: the implied wedge
ax=axes[1]
ax.plot(m.date,m.pi,color=DARK,lw=1.8,zorder=3)
ax.axhline(2.0,color=AQUA,lw=1.2,ls=(0,(4,3)),zorder=2)
ax.axhline(0,color='#b9b8b0',lw=0.9,zorder=1)
ax.text(pd.Timestamp('1974-01-01'),2.22,'2% target',fontsize=7.8,color=AQUA,fontweight='600')
head(ax,'The gap between them','BR $i^{*}$ minus HLW $r^{*}$ — an implied $\\pi^{*}$')
ax.set_ylabel('Percentage points',fontsize=8.8,color=INK2)
ax.set_xlim(pd.Timestamp('1971-01-01'),pd.Timestamp('2019-06-01')); ax.set_ylim(-0.6,6.4)
ax.xaxis.set_major_locator(mdates.YearLocator(10)); ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
for yr,lab in [(1980,'1980'),(2000,'2000'),(2017,'2017')]:
    v=m[m.date.dt.year==yr].pi.mean()
    ax.annotate(f'{v:.2f}',xy=(pd.Timestamp(f'{yr}-06-30'),v),xytext=(0,7),textcoords='offset points',
                ha='center',fontsize=7.8,color=INK,fontweight='600')
fig.subplots_adjust(left=0.070,right=0.985,top=0.815,bottom=0.125,wspace=0.28)
fig.savefig('s_rstar_br.png',dpi=230,facecolor=SURF)
print('corr(levels) %.3f  corr(4q changes) %.3f  n=%d'%(
    m['istar.rt'].corr(m.rstar_hlw),m['istar.rt'].diff(4).corr(m.rstar_hlw.diff(4)),len(m)))
print('implied pi*: 1980 %.2f  2000 %.2f  2017 %.2f'%(
    m[m.date.dt.year==1980].pi.mean(),m[m.date.dt.year==2000].pi.mean(),m[m.date.dt.year==2017].pi.mean()))
print('BR band width 2017: %.2f pp'%(b[b.date.dt.year==2017]['istar.ub'].mean()-b[b.date.dt.year==2017]['istar.lb'].mean()))
