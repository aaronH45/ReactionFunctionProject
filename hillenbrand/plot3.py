import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.dates as mdates
import pandas as pd, numpy as np
SURF='#fcfcfb'; INK='#0b0b0b'; INK2='#52514e'; DARK='#6f6e66'; BLUE='#2a78d6'; ORANGE='#eb6834'
plt.rcParams['font.family']='DejaVu Sans'
a=pd.read_csv('/home/claude/hb/acm_panel.csv',parse_dates=['date'])
f=pd.read_csv('/home/claude/hb/acm_fwd_panel.csv',parse_dates=['date'])

def cum(df,col):
    w=df.in_win.values; d=df[col].values
    return np.where(w,d,0).cumsum()/100, np.where(w,0,d).cumsum()/100, d.cumsum()/100

PANELS=[(a,'d_total','A.  10-year yield (ACM total)'),
        (a,'d_rn',   'B.  10-year risk-neutral (expected average short rate)'),
        (a,'d_tp',   'C.  10-year term premium'),
        (f,'d_fwd_rn','D.  9y1y risk-neutral forward — the r* endpoint')]

fig,axes=plt.subplots(2,2,figsize=(13.2,8.8)); fig.patch.set_facecolor(SURF)
for ax,(df,col,ttl) in zip(axes.ravel(),PANELS):
    ax.set_facecolor(SURF)
    ci,co,ct=cum(df,col)
    ax.plot(df.date,ct,color=DARK,lw=1.2,zorder=1,label='Actual (total)')
    ax.plot(df.date,co,color=ORANGE,lw=1.9,zorder=2,label='Outside FOMC windows')
    ax.plot(df.date,ci,color=BLUE,lw=1.9,zorder=3,label='In 3-day FOMC windows')
    ax.axvline(pd.Timestamp('2021-06-30'),color='#c9c8c0',lw=1.0,ls=(0,(4,3)),zorder=0)
    ax.set_title(ttl,fontsize=10.5,color=INK,loc='left',pad=7)
    ax.grid(axis='y',color='#eae9e4',lw=0.8,zorder=0); ax.axhline(0,color='#b9b8b0',lw=1.1,zorder=1)
    for s in ('top','right'): ax.spines[s].set_visible(False)
    for s in ('left','bottom'): ax.spines[s].set_color('#d5d4cd')
    ax.tick_params(colors=INK2,labelsize=9.5,length=3)
    ax.set_ylabel('Cumulative change (pp)',fontsize=9.5,color=INK2)
    ax.set_xlim(df.date.iloc[0],df.date.iloc[-1])
    ax.xaxis.set_major_locator(mdates.YearLocator(5)); ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    xe=mdates.date2num(df.date.iloc[-1])
    vals=sorted([(ci[-1],BLUE),(co[-1],ORANGE),(ct[-1],DARK)],key=lambda t:-t[0])
    span=max(v for v,_ in vals)-min(v for v,_ in vals)
    ymin,ymax=min(v for v,_ in vals)-0.12*max(span,1)-0.9, max(v for v,_ in vals)+0.9
    ypos=[vals[0][0]]
    for v,_ in vals[1:]: ypos.append(min(v,ypos[-1]-0.055*(ax.get_ylim()[1]-ax.get_ylim()[0])))
    for (v,c),yp in zip(vals,ypos):
        ax.plot([xe],[v],'o',ms=4.5,color=c,mec=SURF,mew=1.2,zorder=5,clip_on=False)
        if abs(yp-v)>0.03: ax.plot([xe,xe+130],[v,yp],color=c,lw=0.8,alpha=0.5,zorder=4,clip_on=False)
        ax.text(xe+190,yp,f'{v:+.2f}',va='center',ha='left',fontsize=8.8,color=c,fontweight='600',
                clip_on=False,zorder=6)
    ax.text(mdates.date2num(pd.Timestamp('2021-08-01')),ax.get_ylim()[1],' Jul 2021',fontsize=8,
            color='#a9a89f',va='top',ha='left')

h,l=axes[0,0].get_legend_handles_labels()
fig.legend(h,l,loc='lower left',bbox_to_anchor=(0.045,0.036),frameon=False,fontsize=9.5,
           labelcolor=INK2,handlelength=1.9,ncol=3,columnspacing=2.4)
fig.suptitle('The FOMC-window decline is predominantly the expectations component, not the risk premium',
             fontsize=13.5,color=INK,x=0.045,ha='left',y=0.977,fontweight='600')
fig.text(0.045,0.938,'Cumulative change since Jun 1989, split by whether the day falls in a 3-day FOMC window '
         '(t–1, t, t+1). Adrian–Crump–Moench decomposition, daily.\nAll 373 FOMC meetings incl. conference calls '
         'and unscheduled actions — 11.8% of trading days. Dashed line: end of the paper sample.',
         fontsize=9.5,color=INK2,ha='left',va='top')
fig.text(0.045,0.008,'Per-meeting window effect, Jun 1989–Jun 2021: 10y risk-neutral −1.90 bp (t −4.06); 10y term premium −0.25 bp (t −0.40); 9y1y risk-neutral −1.10 bp (t −3.98).\n'
         'Post-Jul 2021 the 9y1y risk-neutral window effect is unchanged at −1.10 bp per meeting. Cumulative totals shown at the right edge; ACM daily runs to 6 Aug 2026.',
         fontsize=8.3,color='#9a998f',ha='left',va='bottom',linespacing=1.5)
fig.subplots_adjust(left=0.058,right=0.945,top=0.872,bottom=0.135,hspace=0.30,wspace=0.20)
fig.savefig('/home/claude/hb/acm_decomposition.png',dpi=200,facecolor=SURF)
print('ok')
