import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.dates as mdates
import pandas as pd, numpy as np
SURF='#fcfcfb'; INK='#0b0b0b'; INK2='#52514e'; MUTED='#9a998f'
ORANGE='#eb6834'; AQUA='#1baf7a'; BLUE='#2a78d6'; DARK='#6f6e66'; RED='#c33c3c'
plt.rcParams['font.family']='DejaVu Sans'
P='/mnt/user-data/uploads/clean_reactionFunction/HLW/Laubach_Williams_current_estimates.xlsx'

h=pd.read_excel(P,sheet_name='data',skiprows=5)[['Date','rstar']].dropna().rename(columns={'Date':'date','rstar':'hlw'})
inp=pd.read_excel(P,sheet_name='input data'); inp['Date']=pd.to_datetime(inp['Date'])
inp=inp.rename(columns={'Date':'date'})
f=pd.read_csv('fig9_data.csv',parse_dates=['date']).sort_values('date')
m=pd.merge_asof(f[['date','lr_mean']],h,on='date',direction='backward',tolerance=pd.Timedelta('120D')).dropna()
m['pi']=m.lr_mean-m.hlw
q=pd.merge_asof(m,inp[['date','inflation']],on='date',direction='backward',tolerance=pd.Timedelta('200D'))

fig,axes=plt.subplots(1,2,figsize=(7.4,3.05))
fig.patch.set_facecolor(SURF)
for ax in axes:
    ax.set_facecolor(SURF); ax.grid(axis='y',color='#eae9e4',lw=0.8,zorder=0)
    for s in ('top','right'): ax.spines[s].set_visible(False)
    for s in ('left','bottom'): ax.spines[s].set_color('#d5d4cd')
    ax.tick_params(colors=INK2,labelsize=8.4,length=3)
def head(ax,t,s):
    ax.text(0,1.012,s,transform=ax.transAxes,fontsize=8.0,color=INK2,va='bottom')
    ax.set_title(t,fontsize=9.4,color=INK,loc='left',pad=17)

# ---- A: construction
ax=axes[0]
ax.fill_between(m.date,m.hlw,m.lr_mean,color='#f3e6de',zorder=1)
ax.plot(m.date,m.lr_mean,'-o',color=AQUA,ms=2.4,lw=1.8,zorder=4,label='FOMC longer-run dot (nominal)')
ax.plot(m.date,m.hlw,color=ORANGE,lw=1.8,zorder=3,label='HLW $r^{*}$ (real)')
ax.text(pd.Timestamp('2012-10-01'),2.02,'the shaded gap is\nthe implied $\\pi^{*}$',
        fontsize=8.0,color=INK2,linespacing=1.4,va='top')
head(ax,'Where the implied $\\pi^{*}$ comes from','FOMC nominal endpoint less HLW real endpoint')
ax.set_ylabel('Percent',fontsize=8.8,color=INK2)
ax.set_xlim(pd.Timestamp('2011-09-01'),pd.Timestamp('2026-12-31')); ax.set_ylim(0.0,4.9)
ax.xaxis.set_major_locator(mdates.YearLocator(4)); ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax.legend(loc='upper right',frameon=False,fontsize=7.6,labelcolor=INK2,handlelength=1.6,bbox_to_anchor=(1.0,1.0))

# ---- B: the implied series against realised inflation
ax=axes[1]
ax.axhspan(1.5,2.5,color='#eef6f2',zorder=0)
ax.axhline(2.0,color=AQUA,lw=1.1,ls=(0,(4,3)),zorder=2)
ax.plot(q.date,q.inflation,color=MUTED,lw=1.4,zorder=3,label='realised inflation')
ax.plot(m.date,m.pi,'-o',color=RED,ms=2.6,lw=2.0,zorder=4,label='implied $\\pi^{*}$')
ax.axhline(0,color='#b9b8b0',lw=0.9,zorder=1)
mx=m.loc[m.pi.idxmax()]; mn=m.loc[m.pi.idxmin()]
ax.annotate(f'{mx.pi:.2f}',xy=(mx.date,mx.pi),xytext=(4,4),textcoords='offset points',
            fontsize=8.2,color=RED,fontweight='600')
ax.annotate(f'{mn.pi:.2f}, {mn.date:%b %Y}',xy=(mn.date,mn.pi),xytext=(7,-9),textcoords='offset points',
            fontsize=8.2,color=RED,fontweight='600',ha='left')
ax.text(pd.Timestamp('2026-11-01'),2.18,'2% objective',fontsize=7.8,color=AQUA,fontweight='600',ha='right')
head(ax,'It is not an inflation expectation','Range 0.20 to 3.46 — a 3.26 pp swing')
ax.set_ylabel('Percent',fontsize=8.8,color=INK2)
ax.set_xlim(pd.Timestamp('2011-09-01'),pd.Timestamp('2026-12-31')); ax.set_ylim(-1.2,6.9)
ax.xaxis.set_major_locator(mdates.YearLocator(4)); ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax.legend(loc='upper right',frameon=False,fontsize=7.6,labelcolor=INK2,handlelength=1.6)

fig.subplots_adjust(left=0.070,right=0.985,top=0.815,bottom=0.125,wspace=0.24)
fig.savefig('s_implied_pi.png',dpi=230,facecolor=SURF)
print('implied pi*: min %.2f (%s)  max %.2f (%s)  swing %.2f'%(
    m.pi.min(),mn.date.strftime('%Y-%m'),m.pi.max(),mx.date.strftime('%Y-%m'),m.pi.max()-m.pi.min()))
print('at the trough, realised inflation was %.2f%%'%q.loc[q.pi.idxmin(),'inflation'])
print('share of meetings with implied pi* outside 1.5-2.5: %.0f%%'%(100*((m.pi<1.5)|(m.pi>2.5)).mean()))
