import sys, numpy as np, pandas as pd
sys.path.insert(0,'/home/claude/hb'); from fomc_dates import FOMC; from calls import CALLS
p='/mnt/user-data/uploads/clean_reactionFunction/ACMTermPremium.xls'
a=pd.read_excel(p,sheet_name='ACM Daily'); a['DATE']=pd.to_datetime(a['DATE'])
a=a.rename(columns={'DATE':'date'}).sort_values('date').reset_index(drop=True)
# 9y1y forwards: f = 10*Y10 - 9*Y09
a['fwd_rn']=10*a.ACMRNY10-9*a.ACMRNY09
a['fwd_tp']=10*a.ACMTP10 -9*a.ACMTP09
a['fwd_tot']=10*a.ACMY10 -9*a.ACMY09
COLS={'9y1y total':'fwd_tot','9y1y risk-neutral (r* proxy)':'fwd_rn','9y1y term premium':'fwd_tp'}
a=a[['date']+list(COLS.values())].dropna()
a=a[a.date>='1989-06-01'].reset_index(drop=True)
for k,c in COLS.items(): a['d_'+c]=a[c].diff()*100
a=a.iloc[1:].reset_index(drop=True)
idx={d:i for i,d in enumerate(a.date)}
win=np.zeros(len(a),bool); meet=[]
for d in pd.to_datetime(sorted(set(FOMC)|set(CALLS))):
    if d not in idx:
        nx=a.date[a.date>=d]
        if len(nx)==0: continue
        d=nx.iloc[0]
    i=idx[d]; meet.append(i)
    for k in (-1,0,1):
        if 0<=i+k<len(a): win[i+k]=True
a['in_win']=win
a.to_csv('acm_fwd_panel.csv',index=False)
def st(s):
    se=s.std(ddof=1)/np.sqrt(len(s)); return s.mean(),se,s.mean()/se,s.sum()/100
M=pd.DataFrame([[a.date.iloc[i]]+[a['d_'+c].iloc[max(0,i-1):i+2].sum() for c in COLS.values()]
                for i in meet],columns=['date']+list(COLS))
print("9y1y FORWARD — per-meeting 3-day window change (bp)")
for lab,lo,hi in [('Jun1989-Jun2021','1989-06-01','2021-06-30'),('Jul2021-Jul2026','2021-07-01','2026-07-31')]:
    s=M[(M.date>=lo)&(M.date<=hi)]; print(f"  {lab} (n={len(s)})")
    for k in COLS:
        m,se,t,c=st(s[k]); print(f"    {k:30s} {m:+7.2f} bp  t {t:+6.2f}   cumul {c:+6.2f} pp")
print("\n9y1y FORWARD — per-day drift on NON-window days (bp/day)")
for lab,lo,hi in [('Jun1989-Jun2021','1989-06-01','2021-06-30'),('Jul2021-Jul2026','2021-07-01','2026-07-31')]:
    s=a[(~a.in_win)&(a.date>=lo)&(a.date<=hi)]; print(f"  {lab} (n={len(s)})")
    for k,c in COLS.items():
        m,se,t,cu=st(s['d_'+c]); print(f"    {k:30s} {m:+7.3f}    t {t:+6.2f}   cumul {cu:+6.2f} pp")
print("\nDaily sd check (bp/day, non-window, pre-2021) — is the TP null a low-variance artefact?")
s=a[(~a.in_win)&(a.date<='2021-06-30')]
for k,c in COLS.items(): print(f"    {k:30s} sd {s['d_'+c].std():.2f}")
