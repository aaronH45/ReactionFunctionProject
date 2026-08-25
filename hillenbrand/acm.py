import sys, numpy as np, pandas as pd
sys.path.insert(0,'/home/claude/hb'); from fomc_dates import FOMC; from calls import CALLS

p='/mnt/user-data/uploads/clean_reactionFunction/ACMTermPremium.xls'
a=pd.read_excel(p,sheet_name='ACM Daily')
a['DATE']=pd.to_datetime(a['DATE'])
COLS={'total':'ACMY10','rn':'ACMRNY10','tp':'ACMTP10'}
a=a[['DATE']+list(COLS.values())].dropna().sort_values('DATE').reset_index(drop=True)
a=a.rename(columns={'DATE':'date'})
a=a[a.date>='1989-06-01'].reset_index(drop=True)
print(f"ACM daily: {a.date.iloc[0]:%Y-%m-%d} -> {a.date.iloc[-1]:%Y-%m-%d}, {len(a)} obs")

for k,c in COLS.items(): a['d_'+k]=a[c].diff()*100
a=a.iloc[1:].reset_index(drop=True)
idx={d:i for i,d in enumerate(a.date)}

ALL=sorted(set(FOMC)|set(CALLS))
win=np.zeros(len(a),bool); pos=np.full(len(a),9,int)   # pos: 0=t-1,1=t,2=t+1
meet=[]
for d in pd.to_datetime(ALL):
    if d not in idx:
        nx=a.date[a.date>=d]
        if len(nx)==0: continue
        d=nx.iloc[0]
    i=idx[d]; meet.append(i)
    for j,k in enumerate((-1,0,1)):
        if 0<=i+k<len(a): win[i+k]=True; pos[i+k]=j
a['in_win']=win; a['wpos']=pos
a.to_csv('acm_panel.csv',index=False)
print(f"events {len(meet)}, window days {win.sum()} ({100*win.mean():.1f}%)\n")

def stats(s):
    se=s.std(ddof=1)/np.sqrt(len(s)); return s.mean(), se, s.mean()/se, s.sum()/100

ERAS=[('Jun1989-Jun2021','1989-06-01','2021-06-30'),
      ('Jul2021-Jul2026','2021-07-01','2026-07-31')]

print("="*84)
print("A. PER-MEETING 3-day window change (bp)      [mean, se, t, cumulated pp]")
print("="*84)
mrows=[]
for i in meet:
    d=a.date.iloc[i]
    mrows.append([d]+[a['d_'+k].iloc[max(0,i-1):i+2].sum() for k in COLS])
M=pd.DataFrame(mrows,columns=['date']+list(COLS))
for lab,lo,hi in ERAS:
    s=M[(M.date>=lo)&(M.date<=hi)]
    print(f"  {lab}  (n={len(s)})")
    for k in COLS:
        m,se,t,c=stats(s[k]); print(f"    {k:6s} {m:+7.2f} bp  se {se:5.2f}  t {t:+6.2f}   cumul {c:+6.2f} pp")

print("\n"+"="*84)
print("B. PER-DAY drift on NON-window days (bp/day)")
print("="*84)
for lab,lo,hi in ERAS:
    s=a[(~a.in_win)&(a.date>=lo)&(a.date<=hi)]
    print(f"  {lab}  (n={len(s)})")
    for k in COLS:
        m,se,t,c=stats(s['d_'+k]); print(f"    {k:6s} {m:+7.3f}    se {se:5.3f}  t {t:+6.2f}   cumul {c:+6.2f} pp")

print("\n"+"="*84)
print("C. WITHIN-WINDOW: which of the three days? (mean bp per meeting-day)")
print("="*84)
for lab,lo,hi in ERAS:
    s=a[a.in_win&(a.date>=lo)&(a.date<=hi)]
    print(f"  {lab}")
    for j,dn in enumerate(['t-1','t  ','t+1']):
        g=s[s.wpos==j]
        line=f"    day {dn}  n={len(g):4d}  "
        for k in COLS:
            m,se,t,_=stats(g['d_'+k]); line+=f"{k}: {m:+6.2f} (t{t:+5.2f})   "
        print(line)
