import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import pandas as pd, numpy as np, statsmodels.api as sm
SURF='#fcfcfb'; INK='#0b0b0b'; INK2='#52514e'; MUTED='#9a998f'
BLUE='#2a78d6'; ORANGE='#eb6834'; DARK='#6f6e66'
plt.rcParams['font.family']='DejaVu Sans'
U='/mnt/user-data/uploads/clean_reactionFunction/'

f=pd.read_csv('fig9_data.csv',parse_dates=['date']).sort_values('date').reset_index(drop=True)
f['rev']=f.lr_mean.diff()
a=pd.read_excel(U+'ACMTermPremium.xls',sheet_name='ACM Daily'); a['date']=pd.to_datetime(a['DATE'])
a=a.sort_values('date').reset_index(drop=True)
a['fwd_rn']=10*a.ACMRNY10-9*a.ACMRNY09
idx={d:i for i,d in enumerate(a.date)}
def pos(dt):
    if dt in idx: return idx[dt]
    nx=a.date[a.date>=dt]; return idx[nx.iloc[0]] if len(nx) else None

K0,K1=-60,6
COLS={'fwd_rn':'9y1y risk-neutral forward  (the endpoint)','ACMTP10':'10y term premium  (risk price)'}
ev=[]
for i in range(1,len(f)):
    p=pos(f.date[i])
    if p is None or np.isnan(f.rev[i]) or p+K1>=len(a) or p+K0<0: continue
    row={'rev':f.rev[i]}
    for c in COLS:
        base=a[c].iloc[p+K0]
        for k in range(K0,K1): row[f'{c}_{k}']=(a[c].iloc[p+k]-base)*100
    row['win_rn']=(a.ACMRNY10.iloc[p+1]-a.ACMRNY10.iloc[p-1])*100
    row['win_tp']=(a.ACMTP10.iloc[p+1]-a.ACMTP10.iloc[p-1])*100
    row['inter']=(a.fwd_rn.iloc[p-2]-a.fwd_rn.iloc[p+K0])*100
    ev.append(row)
E=pd.DataFrame(ev); print('meetings used:',len(E))

def path(c):
    b=[];lo=[];hi=[]
    for k in range(K0,K1):
        m=sm.OLS(E[f'{c}_{k}'].values,sm.add_constant(E.rev.values)).fit(cov_type='HAC',cov_kwds={'maxlags':4})
        b.append(m.params[1]); se=m.bse[1]; lo.append(m.params[1]-1.645*se); hi.append(m.params[1]+1.645*se)
    return np.array(b),np.array(lo),np.array(hi)

fig=plt.figure(figsize=(13.2,9.2)); fig.patch.set_facecolor(SURF)
gs=fig.add_gridspec(2,2,height_ratios=[0.46,1],hspace=0.42,wspace=0.22,
                    left=0.062,right=0.975,top=0.855,bottom=0.105)
axT=fig.add_subplot(gs[0,:]); axP=fig.add_subplot(gs[1,0]); axB=fig.add_subplot(gs[1,1])
for ax in (axT,axP,axB): ax.set_facecolor(SURF)

# ---------- STEP 1: the timeline ----------
axT.set_xlim(-70,14); axT.set_ylim(-1.05,1.45); axT.axis('off')
axT.plot([-64,9],[0,0],color='#c9c8c2',lw=2,zorder=1,solid_capstyle='round')
axT.add_patch(FancyBboxPatch((-63,-0.22),58,0.44,boxstyle='round,pad=0.02,rounding_size=0.12',
    facecolor='#eef3fa',edgecolor=BLUE,lw=1.2,zorder=2))
axT.add_patch(FancyBboxPatch((-1.6,-0.30),3.2,0.60,boxstyle='round,pad=0.02,rounding_size=0.12',
    facecolor='#fdeee7',edgecolor=ORANGE,lw=1.4,zorder=3))
for x,lab in [(-63,'Previous SEP\n(t−60)'),(0,'This SEP\n(t)')]:
    axT.plot([x],[0],'o',ms=8,color=DARK,mec=SURF,mew=1.6,zorder=5)
    axT.text(x,-0.46,lab,ha='center',va='top',fontsize=9.2,color=INK2,linespacing=1.4)
axT.text(-34,0.34,'INTERMEETING  ~3 months',ha='center',fontsize=9.6,color=BLUE,fontweight='600')
axT.text(-34,0.62,'Data arrives. The market reprices continuously.',ha='center',fontsize=9.2,color=INK2)
axT.text(0,0.44,'WINDOW\n[t−1, t+1]',ha='center',va='bottom',fontsize=9.6,color=ORANGE,fontweight='600',linespacing=1.35)
axT.text(0,0.95,'The Fed publishes\nits revised longer-run dot',ha='center',va='bottom',fontsize=9.2,
         color=INK2,linespacing=1.4)
axT.text(-70,1.40,'Step 1.',fontsize=10.6,color=INK,fontweight='600',ha='left',va='top')
axT.text(-62.5,1.40,'Both the market and the Fed watch the same three months of data. Only the Fed’s view is published — quarterly, at t.',
         fontsize=10,color=INK2,ha='left',va='top')

# ---------- STEP 2: the event-time path ----------
ks=np.arange(K0,K1)
for c,col,lab in [('fwd_rn',BLUE,'9y1y risk-neutral forward'),('ACMTP10',ORANGE,'10y term premium')]:
    b,lo,hi=path(c)
    axP.fill_between(ks,lo,hi,color=col,alpha=0.11,zorder=1)
    axP.plot(ks,b,color=col,lw=2.1,zorder=3,label=lab)
    axP.plot([ks[-1]],[b[-1]],'o',ms=5,color=col,mec=SURF,mew=1.2,zorder=4,clip_on=False)
axP.axvspan(-1,1,color='#fdeee7',zorder=0)
axP.axvline(0,color=ORANGE,lw=1.0,ls=(0,(3,2)),zorder=2)
axP.axhline(0,color='#b9b8b0',lw=1.1,zorder=2)
axP.set_xlim(K0,K1-1); axP.set_xlabel('Trading days relative to the SEP meeting',fontsize=9.8,color=INK2)
axP.set_ylabel('Cumulative bp per 1 pp of the revision\nannounced at day 0',fontsize=9.6,color=INK2,linespacing=1.5)
axP.legend(loc='upper left',frameon=False,fontsize=9.2,labelcolor=INK2)
axP.set_title('Step 2.  The market has already moved before the Fed speaks',
              fontsize=10.6,color=INK,loc='left',pad=8)
axP.text(0.985,0.045,'shaded band = 90% CI\norange strip = the announcement window',transform=axP.transAxes,
         ha='right',va='bottom',fontsize=8.4,color=MUTED,linespacing=1.5)

# ---------- STEP 3/4: the window, raw and conditional ----------
def wcoef(lhs,ctrl):
    X=E[['rev']+ (['inter'] if ctrl else [])].values
    m=sm.OLS(E[lhs].values,sm.add_constant(X)).fit(cov_type='HAC',cov_kwds={'maxlags':4})
    return m.params[1],1.96*m.bse[1],m.tvalues[1]
labels=['Risk-neutral\n(expectations)','Term premium\n(risk price)']
x=np.arange(2); w=0.36
for j,(ctrl,alpha,tag) in enumerate([(False,1.0,'raw'),(True,0.42,'controlling for the\nintermeeting drift')]):
    vals=[wcoef('win_rn',ctrl),wcoef('win_tp',ctrl)]
    for i,(b,e,t) in enumerate(vals):
        c=[BLUE,ORANGE][i]
        axB.bar(x[i]+(j-0.5)*w,b,w*0.9,yerr=e,color=c,alpha=alpha,edgecolor=SURF,lw=1.5,zorder=3,
                error_kw=dict(ecolor='#8f8f8a',lw=1.1,capsize=3))
        axB.text(x[i]+(j-0.5)*w,b+e+2.2,f'{b:+.0f}\n(t {t:+.2f})',ha='center',va='bottom',
                 fontsize=8.6,color=c,fontweight='600',linespacing=1.3)
axB.axhline(0,color='#b9b8b0',lw=1.1,zorder=2)
axB.set_xticks(x); axB.set_xticklabels(labels,fontsize=9.8,color=INK2)
axB.set_ylabel('bp response in the window, per 1 pp revision',fontsize=9.6,color=INK2)
axB.set_ylim(-22,66)
axB.set_title('Steps 3 & 4.  In the window only the risk price moves',
              fontsize=10.6,color=INK,loc='left',pad=8)
axB.text(0.03,0.955,'solid = raw    faded = controlling for the intermeeting drift',transform=axB.transAxes,
         fontsize=8.8,color=MUTED,va='top')

for ax in (axP,axB):
    ax.grid(axis='y',color='#eae9e4',lw=0.8,zorder=0)
    for s in ('top','right'): ax.spines[s].set_visible(False)
    for s in ('left','bottom'): ax.spines[s].set_color('#d5d4cd')
    ax.tick_params(colors=INK2,labelsize=9.5,length=3)

fig.suptitle('The market learns r* from the data; the Fed’s announcement moves the price of risk',
             fontsize=13.5,color=INK,x=0.062,ha='left',y=0.972,fontweight='600')
fig.text(0.062,0.918,'Response to a 1 percentage-point revision in the FOMC longer-run projection. 56 SEP meetings, January 2012 – March 2026. '
         'ACM decomposition, HAC(4) standard errors.',fontsize=9.4,color=INK2,ha='left',va='top')
fig.text(0.062,0.010,'The intermeeting drift is measured from day t−60 to day t−2, so it never overlaps either announcement window.\n'
         'Over that stretch the 10-year yield moves +182 bp per pp of the eventual revision (t = 4.26), against +32 bp inside the window.',
         fontsize=8.3,color=MUTED,ha='left',va='bottom',linespacing=1.5)
fig.savefig('steps.png',dpi=200,facecolor=SURF)
print('ok')
