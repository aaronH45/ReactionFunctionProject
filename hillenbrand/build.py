import sys, numpy as np, pandas as pd
sys.path.insert(0,'/home/claude/hb')
from fomc_dates import FOMC

SRC = '/mnt/user-data/uploads/clean_reactionFunction/feds200628.csv'
with open(SRC) as f:
    for i, line in enumerate(f):
        if line.startswith('Date,'):
            hdr = i; break
gsw = pd.read_csv(SRC, skiprows=hdr, parse_dates=['Date'], na_values=['NA'])
y = (gsw[['Date','SVENY10']].dropna().sort_values('Date')
       .rename(columns={'Date':'date','SVENY10':'y10'}).reset_index(drop=True))
y = y[y.date >= '1989-01-01'].reset_index(drop=True)

base = float(y.y10.iloc[0]); base_date = y.date.iloc[0]
y['dy'] = y.y10.diff()*100                      # basis points
y = y.iloc[1:].reset_index(drop=True)           # first row has no change

idx = {d: i for i, d in enumerate(y.date)}
fomc = pd.to_datetime(sorted(FOMC))
fomc = fomc[(fomc >= y.date.iloc[0]) & (fomc <= y.date.iloc[-1])]

# w3: daily changes ON days t-1, t, t+1   (change from close t-2 to close t+1)
# w2: daily changes ON days t, t+1        (change from close t-1 to close t+1)
w3 = np.zeros(len(y), bool); w2 = np.zeros(len(y), bool)
miss = []
for d in fomc:
    if d not in idx:
        miss.append(d); continue
    i = idx[d]
    for k in (-1,0,1):
        if 0 <= i+k < len(y): w3[i+k] = True
    for k in (0,1):
        if 0 <= i+k < len(y): w2[i+k] = True

for tag, w in (('w3', w3), ('w2', w2)):
    y[f'in_{tag}']  = w
    y[f'cum_in_{tag}']  = base + np.where(w, y.dy, 0).cumsum()/100
    y[f'cum_out_{tag}'] = base + np.where(w, 0, y.dy).cumsum()/100
y['cum_all'] = base + y.dy.cumsum()/100
y.to_csv('/home/claude/hb/fomc_window_panel.csv', index=False)

print(f"GSW SVENY10 : {base_date:%Y-%m-%d} ({base:.2f}%) -> {y.date.iloc[-1]:%Y-%m-%d} ({y.y10.iloc[-1]:.2f}%)"
      f"   {len(y)+1} trading days")
print(f"FOMC meetings: {len(fomc)}   unmatched to a trading day: {len(miss)}")
print(f"reconstruction check: {y.cum_all.iloc[-1]-y.y10.iloc[-1]:+.2e} pp\n")

def tbl(lo, hi):
    m = (y.date.dt.year>=lo)&(y.date.dt.year<=hi); s = y[m]
    n = int(((fomc.year>=lo)&(fomc.year<=hi)).sum())
    lvl0 = base if lo==1989 else float(y.y10[m].iloc[0])
    print(f"--- {lo}-{hi}   {n} meetings   {s.y10.iloc[0]:.2f}% -> {s.y10.iloc[-1]:.2f}%   "
          f"total {s.dy.sum():+.0f} bp")
    for tag,lab in (('w3','3 daily chgs (t-1,t,t+1)'),('w2','2 daily chgs (t-1->t+1)')):
        i_ = s.dy[s[f'in_{tag}']].sum(); o = s.dy[~s[f'in_{tag}']].sum()
        d = s[f'in_{tag}'].sum()
        print(f"    {lab:26s} window days {d:5d} ({100*d/len(s):4.1f}%)  "
              f"in {i_:+7.0f} bp   out {o:+7.0f} bp   in/total {i_/s.dy.sum()*100:6.1f}%")
for a,b in [(1989,2019),(1989,2026),(1989,2008),(2009,2026)]:
    tbl(a,b)
