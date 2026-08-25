import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.dates as mdates
import pandas as pd, numpy as np, statsmodels.api as sm, json
SURF='#fcfcfb'; INK='#0b0b0b'; INK2='#52514e'; MUTED='#9a998f'
BLUE='#2a78d6'; ORANGE='#eb6834'; AQUA='#1baf7a'; DARK='#6f6e66'; RED='#c33c3c'
plt.rcParams['font.family']='DejaVu Sans'
W,H=6.0,2.75

def frame(nc=1,h=H,w=W):
    fig,axes=plt.subplots(1,nc,figsize=(w,h)); fig.patch.set_facecolor(SURF)
    A=axes if nc>1 else [axes]
    for ax in A:
        ax.set_facecolor(SURF); ax.grid(axis='y',color='#eae9e4',lw=0.7,zorder=0)
        for s in ('top','right'): ax.spines[s].set_visible(False)
        for s in ('left','bottom'): ax.spines[s].set_color('#d5d4cd')
        ax.tick_params(colors=INK2,labelsize=8.2,length=3)
    return fig,(A if nc>1 else A[0])

def save(fig,name,**kw):
    fig.savefig(name,dpi=230,facecolor=SURF,**kw); plt.close(fig); print(name)

y=pd.read_csv('paper_spec_panel.csv',parse_dates=['date'])
y['cin']=np.where(y.in_win,y.dy,0).cumsum()/100
y['cout']=np.where(~y.in_win,y.dy,0).cumsum()/100
y['call']=y.dy.cumsum()/100

# ---------------- 1. the motivating fact (paper sample) -------------------
def factfig(end,name,shade=None,title=''):
    d=y[y.date<=end]
    fig,ax=frame()
    ax.plot(d.date,d.call,color=DARK,lw=1.3,label='10-year yield (actual)',zorder=3)
    ax.plot(d.date,d.cin,color=BLUE,lw=2.1,label='change inside 3-day FOMC windows',zorder=4)
    ax.plot(d.date,d.cout,color=ORANGE,lw=2.1,label='change outside those windows',zorder=4)
    ax.axhline(0,color='#b9b8b0',lw=0.9,zorder=1)
    if shade: ax.axvspan(pd.Timestamp(shade),pd.Timestamp(end),color='#f4efe6',zorder=0)
    lab3=[(d.cin.iloc[-1],BLUE),(d.cout.iloc[-1],ORANGE),(d.call.iloc[-1],DARK)]
    lab3.sort(key=lambda z:-z[0]); prev=None; off={}
    for v,c in lab3:
        yy=v if prev is None else min(v,prev-0.62); prev=yy; off[c]=yy
    for v,c in lab3:
        ax.annotate(f'{v:+.2f} pp',xy=(d.date.iloc[-1],off[c]),xytext=(7,0),textcoords='offset points',
                    fontsize=8.4,color=c,fontweight='600',va='center')
    ax.set_ylabel('Cumulative change (pp)',fontsize=8.6,color=INK2)
    ax.set_xlim(pd.Timestamp('1989-06-01'),pd.Timestamp(end)+pd.Timedelta(days=1500))
    ax.set_ylim(-8.8,4.4 if shade else 1.6)
    ax.xaxis.set_major_locator(mdates.YearLocator(5)); ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.legend(loc='lower left',frameon=False,fontsize=8.2,labelcolor=INK2,handlelength=1.6,
              bbox_to_anchor=(0.0,0.0))
    if title: ax.set_title(title,fontsize=8.4,color=INK2,loc='left',pad=6)
    fig.subplots_adjust(left=0.105,right=0.862,top=0.895 if title else 0.97,bottom=0.11)
    save(fig,name)

factfig('2021-06-30','s_fact.png',title='Base = 2 Jun 1989 (8.52%).  373 FOMC events; windows are 11.8% of trading days.')
factfig('2026-07-31','s_extend.png',shade='2022-03-01',
        title='Extended through 31 Jul 2026.  Shaded: the 2022–2026 tightening cycle.')

# ---------------- 2. event-list reconciliation ---------------------------
g=json.load(open('t1_grid.json'))
fig,axes=frame(2,w=W,h=2.7)
ax=axes[0]
cells=['A. Scheduled, 1994+','C. All events, 1994+','D. All events, 1989+']
lab=['scheduled only\nSep 1994+\n(Pan & Peng)','all events\nSep 1994+','all events\nJun 1989+']
x=np.arange(3); wd=0.34
tp=[g[c]['d_tp'][0] for c in cells]; rn=[g[c]['d_rn'][0] for c in cells]
ax.bar(x-wd/2,tp,wd,color=ORANGE,label='term premium',zorder=3)
ax.bar(x+wd/2,rn,wd,color=BLUE,label='expected short rates',zorder=3)
for i,(a_,b_) in enumerate(zip(tp,rn)):
    ax.text(i-wd/2,a_-0.045,f'{a_:.2f}',ha='center',va='top',fontsize=7.6,color=ORANGE,fontweight='600')
    ax.text(i+wd/2,b_-0.045,f'{b_:.2f}',ha='center',va='top',fontsize=7.6,color=BLUE,fontweight='600')
    ax.text(i,0.055,f"TP {g[cells[i]]['share']:.0f}%",ha='center',fontsize=7.6,color=INK,fontweight='600')
ax.axhline(0,color='#b9b8b0',lw=0.9,zorder=1)
ax.set_xticks(x); ax.set_xticklabels(lab,fontsize=7.4,color=INK2)
ax.set_ylim(-0.95,0.24); ax.set_ylabel('bp per event, day $t-1$',fontsize=8.2,color=INK2)
ax.set_title('Different event list, opposite answer',fontsize=8.4,color=INK,loc='left',pad=5)
ax.legend(loc='lower right',frameon=False,fontsize=7.8,labelcolor=INK2,handlelength=1.4)

ax=axes[1]
ax.bar([0,1],[-0.07,-2.47],0.5,color=[MUTED,RED],zorder=3)
ax.text(0,-0.14,'−0.07',ha='center',va='top',fontsize=8.2,color=INK2,fontweight='600')
ax.text(1,-2.56,'−2.47',ha='center',va='top',fontsize=8.2,color=RED,fontweight='600')
ax.axhline(0,color='#b9b8b0',lw=0.9,zorder=1)
ax.set_xticks([0,1]); ax.set_xticklabels(['300 scheduled\nmeetings','73 unscheduled\ncalls & actions'],fontsize=7.6,color=INK2)
ax.set_ylim(-3.2,0.5); ax.set_ylabel('expectations, bp per event',fontsize=8.2,color=INK2)
ax.set_title('Where the expectations move lives',fontsize=8.4,color=INK,loc='left',pad=5)
ax.text(1,0.22,'35$\\times$ larger',ha='center',fontsize=8.0,color=RED,fontweight='600')
fig.subplots_adjust(left=0.093,right=0.975,top=0.875,bottom=0.20,wspace=0.42)
save(fig,'s_eventlist.png')

# ---------------- 3. the ACM filter --------------------------------------
a=pd.read_excel('/mnt/user-data/uploads/clean_reactionFunction/ACMTermPremium.xls',sheet_name='ACM Daily')
a['DATE']=pd.to_datetime(a['DATE'])
mats=[1,2,3,5,7,10]
cols=['ACMY%02d'%m for m in mats]
a=a[['DATE']+cols+['ACMRNY10']].dropna().sort_values('DATE')
a=a[a.DATE>='1989-06-01'].reset_index(drop=True)
X=a[cols].diff().iloc[1:].values*100; yv=a['ACMRNY10'].diff().iloc[1:].values*100
m=sm.OLS(yv,sm.add_constant(X)).fit()
c=m.params[1:]; r2=m.rsquared; s1=c.sum()
fit=m.fittedvalues
fig,axes=frame(2,w=W,h=2.7)
ax=axes[0]
ax.scatter(fit,yv,s=2.2,color=BLUE,alpha=0.35,zorder=3,edgecolors='none')
lo,hi=-32,32
ax.plot([lo,hi],[lo,hi],color=INK2,lw=0.9,ls=(0,(4,3)),zorder=4)
ax.set_xlim(lo,hi); ax.set_ylim(lo,hi)
ax.set_xlabel('fitted from six yield changes (bp)',fontsize=8.2,color=INK2)
ax.set_ylabel('actual $\\Delta$ ACM expectations (bp)',fontsize=8.2,color=INK2)
ax.set_title('A perfect linear filter of the curve',fontsize=8.4,color=INK,loc='left',pad=5)
ax.text(0.04,0.93,f'$R^2$ = {r2:.5f}\n{len(yv):,} daily observations',transform=ax.transAxes,
        fontsize=8.2,color=INK,va='top',fontweight='600',linespacing=1.5)
ax.grid(color='#eae9e4',lw=0.7,zorder=0)

ax=axes[1]
ax.bar([0,1],[100,s1*100],0.82,color=[AQUA,BLUE],zorder=3)
ax.bar([0,1],[0,100-s1*100],0.82,bottom=[100,s1*100],color=['#dcdbd4',ORANGE],zorder=3)
ax.text(0,50,'expectations\n100%',ha='center',va='center',fontsize=7.6,color='white',fontweight='600',linespacing=1.4)
ax.text(1,s1*50,f'expectations\n{s1*100:.0f}%',ha='center',va='center',fontsize=7.6,color='white',fontweight='600',linespacing=1.4)
ax.text(1,s1*100+(100-s1*100)/2,f'“term premium”\n{100-s1*100:.0f}%',ha='center',va='center',fontsize=7.6,color='white',fontweight='600',linespacing=1.4)
ax.set_xticks([0,1]); ax.set_xticklabels(['the truth','what ACM reports'],fontsize=8.0,color=INK2)
ax.set_ylim(0,118); ax.set_yticks([0,50,100]); ax.set_ylabel('share of a 100 bp move',fontsize=8.4,color=INK2)
ax.set_title('A permanent, credible 100 bp shift',fontsize=8.4,color=INK,loc='left',pad=5)
ax.text(0.5,110,"$c'\\mathbf{1}=%.3f$"%s1,ha='center',fontsize=8.6,color=INK,fontweight='600')
fig.subplots_adjust(left=0.10,right=0.985,top=0.87,bottom=0.165,wspace=0.30)
save(fig,'s_acmfilter.png')
print('c1=',s1,'r2=',r2)

# ---------------- 4. r*: treatment and market leg -------------------------
f=pd.read_csv('fig9_data.csv',parse_dates=['date']); f['rf']=f.lr_mean-2.0
acm=pd.read_csv('rstar_acm_daily.csv',parse_dates=['date'])
hlw=pd.read_csv('rstar_hlw.csv',parse_dates=['date'])
fig,axes=frame(2,w=W,h=2.7)
ax=axes[0]
ax.plot(f.date,f.rf,'-o',color=AQUA,ms=2.6,lw=1.8,zorder=3)
ax.axhline(0,color='#b9b8b0',lw=0.9,zorder=1)
lo=f.loc[f.rf.idxmin()]
ax.annotate(f'trough {lo.rf:.2f}%, {lo.date:%b %Y}',xy=(lo.date,lo.rf),xytext=(pd.Timestamp('2012-10-01'),0.05),
            fontsize=7.8,color=INK2,arrowprops=dict(arrowstyle='-',color='#a9a89f',lw=0.8))
ax.annotate(f'{f.rf.iloc[-1]:.2f}%',xy=(f.date.iloc[-1],f.rf.iloc[-1]),xytext=(-4,9),textcoords='offset points',
            fontsize=8.2,color=AQUA,fontweight='600',ha='right')
ax.set_title('The treatment: the FOMC’s own $r^{*}$',fontsize=8.6,color=INK,loc='left',pad=18)
ax.text(0,1.012,'SEP longer-run projection $-$ 2.0',transform=ax.transAxes,
        fontsize=7.8,color=INK2,va='bottom')
ax.set_ylabel('Percent',fontsize=8.4,color=INK2); ax.set_ylim(-0.35,2.6)
ax.set_xlim(pd.Timestamp('2011-06-01'),pd.Timestamp('2026-12-31'))
ax.xaxis.set_major_locator(mdates.YearLocator(4)); ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

ax=axes[1]
mm=acm[acm.date>='1990-01-01']; hh=hlw[hlw.date>='1990-01-01']
ax.plot(mm.date,mm.ACMY01,color=MUTED,lw=1.0,zorder=2,label='1-year yield (policy cycle)')
ax.plot(mm.date,mm.rstar_acm,color=BLUE,lw=1.1,zorder=3,label='ACM-implied “market $r^{*}$”')
ax.plot(hh.date,hh.rstar_hlw,color=ORANGE,lw=1.7,zorder=4,label='HLW $r^{*}$')
ax.axhline(0,color='#b9b8b0',lw=0.9,zorder=1)
ax.set_title('The control we do not have',fontsize=8.6,color=INK,loc='left',pad=18)
ax.text(0,1.012,'ACM 9y1y on $\\Delta$1y: $\\beta$ = 0.287, $R^2$ = 0.83',
        transform=ax.transAxes,fontsize=7.8,color=INK2,va='bottom')
ax.set_ylabel('Percent',fontsize=8.4,color=INK2); ax.set_ylim(-1.2,9.6)
ax.set_xlim(pd.Timestamp('1990-01-01'),pd.Timestamp('2026-12-31'))
ax.xaxis.set_major_locator(mdates.YearLocator(7)); ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax.legend(loc='upper right',frameon=False,fontsize=7.6,labelcolor=INK2,handlelength=1.5)
fig.subplots_adjust(left=0.082,right=0.985,top=0.815,bottom=0.115,wspace=0.235)
save(fig,'s_rstar.png')

# ---------------- 5. timing: effect vs measurement ------------------------
fig,axes=frame(2,w=W,h=2.7)
ax=axes[0]
ax.axvspan(pd.Timestamp('2012-01-01'),pd.Timestamp('2027-01-01'),color='#eef6f2',zorder=0)
ax.plot(y.date,y.cin,color=DARK,lw=1.8,zorder=3)
ax.axhline(0,color='#b9b8b0',lw=0.9,zorder=1)
ax.axvline(pd.Timestamp('2012-01-01'),color=AQUA,lw=1.1,ls=(0,(4,3)),zorder=2)
ax.set_title('The decline predates the measure',fontsize=8.6,color=INK,loc='left',pad=18)
ax.text(0,1.012,'Cumulative 10-year change, in-window only',transform=ax.transAxes,
        fontsize=7.8,color=INK2,va='bottom')
ax.set_ylabel('Cumulative change (pp)',fontsize=8.4,color=INK2)
ax.set_xlim(pd.Timestamp('1989-06-01'),pd.Timestamp('2027-01-01')); ax.set_ylim(-8.6,1.0)
ax.xaxis.set_major_locator(mdates.YearLocator(7)); ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax.text(pd.Timestamp('1991-01-01'),-6.6,'before the SEP\n−5.85 pp (81%)',fontsize=8.0,color=INK,fontweight='600',linespacing=1.45,va='top')
ax.text(pd.Timestamp('2012-06-01'),-1.0,'SEP era\n−1.39 pp',fontsize=8.0,color=AQUA,fontweight='600',linespacing=1.45,va='top')

ax=axes[1]
per=['Jun 1989 –\nDec 2011','Jan 2012 –\nMar 2022','Mar 2022 –\nJul 2026']
bp=[-2.46,-0.40,-3.49]; tt=[-3.06,-0.41,-1.53]; nm=[245,85,35]
cols_=[DARK,'#c9c8c0',AQUA]
ax.bar(range(3),bp,0.5,color=cols_,zorder=3)
for i,(b_,t_,n_) in enumerate(zip(bp,tt,nm)):
    ax.text(i,b_-0.18,f'{b_:.2f}\n($t$ {t_:.2f})',ha='center',va='top',fontsize=7.6,color=INK2,linespacing=1.4)
    ax.text(i,0.16,f'{n_} mtgs',ha='center',fontsize=7.4,color=MUTED)
ax.axhline(0,color='#b9b8b0',lw=0.9,zorder=1)
ax.set_xticks(range(3)); ax.set_xticklabels(per,fontsize=7.6,color=INK2)
ax.set_ylim(-5.0,0.85); ax.set_ylabel('in-window drift, bp per meeting',fontsize=8.4,color=INK2)
ax.set_title('The dot-plot decade adds nothing',fontsize=8.6,color=INK,loc='left',pad=18)
ax.text(0,1.012,'Middle period: the Fed cut its own $r^{*}$ 1.78 pp',
        transform=ax.transAxes,fontsize=7.8,color=INK2,va='bottom')
fig.subplots_adjust(left=0.10,right=0.975,top=0.805,bottom=0.20,wspace=0.30)
save(fig,'s_timing.png')

# ---------------- 6. persistence puzzle ----------------------------------
yp=y[y.date<='2021-06-30']
inw=yp[yp.in_win].dy; out=yp[~yp.in_win].dy
fig,ax=frame(1,w=W*0.62,h=2.6)
x=np.arange(2)
ax.bar(x-0.19,[inw.std(),out.std()],0.36,color=MUTED,label='daily s.d. (bp)',zorder=3)
ax.bar(x+0.19,[abs(inw.mean()),abs(out.mean())],0.36,color=RED,label='|mean drift| (bp/day)',zorder=3)
for i,v in enumerate([inw.std(),out.std()]): ax.text(i-0.19,v+0.13,f'{v:.2f}',ha='center',fontsize=7.8,color=INK2)
for i,v in enumerate([abs(inw.mean()),abs(out.mean())]): ax.text(i+0.19,v+0.13,f'{v:.3f}',ha='center',fontsize=7.8,color=RED)
ax.set_xticks(x); ax.set_xticklabels(['FOMC-window days','all other days'],fontsize=8.2,color=INK2)
ax.set_ylim(0,9.2); ax.set_ylabel('basis points',fontsize=8.4,color=INK2)
ax.legend(loc='upper right',frameon=False,fontsize=7.8,labelcolor=INK2,handlelength=1.4)
ax.set_title('Same volatility, opposite persistence',fontsize=8.8,color=INK,loc='left',pad=16)
ax.text(0,1.012,'Paper sample: 972 window days vs 7,035 other days',
        transform=ax.transAxes,fontsize=7.8,color=INK2,va='bottom')
ax.text(0.5,2.9,'drift-to-noise\n45$\\times$ higher\ninside the window',ha='center',fontsize=8.2,
        color=INK,fontweight='600',linespacing=1.5)
fig.subplots_adjust(left=0.135,right=0.985,top=0.80,bottom=0.13)
save(fig,'s_persist.png')
print('in sd %.2f mean %.4f | out sd %.2f mean %.4f'%(inw.std(),inw.mean(),out.std(),out.mean()))
