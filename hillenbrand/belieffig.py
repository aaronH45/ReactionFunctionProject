import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.dates as mdates
import pandas as pd, numpy as np, statsmodels.api as sm
SURF='#fcfcfb'; INK='#0b0b0b'; INK2='#52514e'; MUTED='#9a998f'
BLUE='#2a78d6'; ORANGE='#eb6834'; AQUA='#1baf7a'; DARK='#6f6e66'; RED='#c33c3c'
plt.rcParams['font.family']='DejaVu Sans'
U='/mnt/user-data/uploads/clean_reactionFunction/wedge/'
s=pd.read_csv(U+'spd_rstar.csv',parse_dates=['date']).sort_values('date')
f=pd.read_csv(U+'fed_rstar.csv',parse_dates=['date']).sort_values('date')
m=pd.merge_asof(f[['date','rstar_fed_mean','rstar_fed']],s[['date','rstar_spd','i_star_iqr_spd']],
                on='date',direction='backward',tolerance=pd.Timedelta('120D')).dropna()
m['gap']=m.rstar_fed_mean-m.rstar_spd
m['dF']=m.rstar_fed_mean.diff(); m['dM']=m.rstar_spd.diff()
d=m.dropna(subset=['dF','dM'])

def beta(X,Y):
    z=pd.concat([X.rename('x'),Y.rename('y')],axis=1).dropna()
    r=sm.OLS(z.y.values,sm.add_constant(z.x.values)).fit(cov_type='HAC',cov_kwds={'maxlags':2})
    return r.params[1],r.tvalues[1]
# timing: SPD is fielded ~2 weeks BEFORE meeting t, so dM_t spans meeting t-1
b1,t1=beta(m.dF.shift(1),m.dM)   # dealers follow the Fed's revision at t-1
b2,t2=beta(m.dM,m.dF)            # Fed follows the dealer move known before t

fig,axes=plt.subplots(1,3,figsize=(6.6,2.65)); fig.patch.set_facecolor(SURF)
for ax in axes:
    ax.set_facecolor(SURF); ax.grid(axis='y',color='#eae9e4',lw=0.7,zorder=0)
    for sp in ('top','right'): ax.spines[sp].set_visible(False)
    for sp in ('left','bottom'): ax.spines[sp].set_color('#d5d4cd')
    ax.tick_params(colors=INK2,labelsize=8.0,length=3)

def head(ax,title,sub):
    ax.text(0,1.012,sub,transform=ax.transAxes,fontsize=7.6,color=INK2,va='bottom')
    ax.set_title(title,fontsize=8.5,color=INK,loc='left',pad=18)

# --- A: the two beliefs
ax=axes[0]
ax.fill_between(m.date,m.rstar_fed_mean,m.rstar_spd,color='#e9e8e2',zorder=2,label='gap')
ax.plot(m.date,m.rstar_fed_mean,'-o',color=AQUA,ms=2.4,lw=1.6,zorder=4,label='FOMC (SEP longer-run $-$ 2)')
ax.plot(m.date,m.rstar_spd,'-o',color=BLUE,ms=2.4,lw=1.6,zorder=3,label='dealers (SPD longer-run $-$ 2)')
head(ax,'Two beliefs about $r^{*}$','SEP meetings, 2013–2026')
ax.set_ylabel('Percent',fontsize=8.2,color=INK2); ax.set_ylim(0.1,2.85)
ax.xaxis.set_major_locator(mdates.YearLocator(4)); ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax.legend(loc='upper right',frameon=False,fontsize=6.8,labelcolor=INK2,handlelength=1.4,borderaxespad=0.1)

# --- B: the gap
ax=axes[1]
sd=m.gap.std()
ax.axhspan(-sd,sd,color='#eef6f2',zorder=0)
ax.plot(m.date,m.gap,'-o',color=DARK,ms=2.4,lw=1.3,zorder=3)
ax.axhline(0,color='#b9b8b0',lw=0.9,zorder=1)
head(ax,'The gap never opens','FOMC $-$ dealers')
ax.set_ylabel('pp',fontsize=8.2,color=INK2); ax.set_ylim(-0.55,0.55)
ax.xaxis.set_major_locator(mdates.YearLocator(4)); ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax.text(0.03,0.05,f'sd = {sd:.2f} pp\nrange {m.gap.min():+.2f} to {m.gap.max():+.2f}',
        transform=ax.transAxes,fontsize=7.6,color=INK,fontweight='600',linespacing=1.5,va='bottom')

# --- C: lead-lag
ax=axes[2]
ax.bar([0,1],[b1,b2],0.5,color=[BLUE,MUTED],zorder=3)
ax.axhline(0,color='#b9b8b0',lw=0.9,zorder=1)
for i,(b_,t_) in enumerate([(b1,t1),(b2,t2)]):
    ax.text(i,b_+0.035,f'{b_:+.2f}',ha='center',fontsize=8.6,color=INK,fontweight='600')
    ax.text(i,b_+0.11,f'($t$ {t_:+.2f})',ha='center',fontsize=7.4,color=INK2)
ax.set_xticks([0,1])
ax.set_xticklabels(['dealers on\nthe Fed','the Fed on\ndealers'],fontsize=7.6,color=INK2)
ax.set_ylim(-0.05,1.12); ax.set_ylabel('regression coefficient',fontsize=8.2,color=INK2)
head(ax,'Transmission is asymmetric','Revisions, HAC(2)')
fig.subplots_adjust(left=0.075,right=0.975,top=0.80,bottom=0.20,wspace=0.34)
fig.savefig('s_beliefs.png',dpi=230,facecolor=SURF)
print('s_beliefs.png  b1=%.3f t=%.2f  b2=%.3f t=%.2f  sd_gap=%.3f'%(b1,t1,b2,t2,sd))
