import pandas as pd, numpy as np, statsmodels.api as sm
U='/mnt/user-data/uploads/clean_reactionFunction/'

# --- SEP longer-run and year+1 dots (mean and median), 57 meetings
f=pd.read_csv('fig9_data.csv',parse_dates=['date']).sort_values('date').reset_index(drop=True)
for c in ['lr_mean','lr_med','y1_mean','y1_med']:
    f['d_'+c]=f[c].diff()          # revision vs the PREVIOUS SEP = the news at this meeting

# --- ACM daily curve
a=pd.read_excel(U+'ACMTermPremium.xls',sheet_name='ACM Daily')
a['date']=pd.to_datetime(a['DATE']); a=a.sort_values('date').reset_index(drop=True)
idx={d:i for i,d in enumerate(a.date)}
MATS=[1,2,3,5,7,10]

def win(dt,col,k0=-1,k1=1):
    """change in col from close t+k0 to close t+k1, in bp"""
    if dt not in idx:
        nx=a.date[a.date>=dt]
        if len(nx)==0: return np.nan
        dt=nx.iloc[0]
    i=idx[dt]
    if i+k0<0 or i+k1>=len(a): return np.nan
    return (a[col].iloc[i+k1]-a[col].iloc[i+k0])*100

for n in MATS:
    f[f'dy{n}']  = f.date.map(lambda d: win(d,f'ACMY{n:02d}'))
    f[f'drn{n}'] = f.date.map(lambda d: win(d,f'ACMRNY{n:02d}'))
    f[f'dtp{n}'] = f.date.map(lambda d: win(d,f'ACMTP{n:02d}'))
d=f.dropna(subset=['d_lr_mean','dy10']).reset_index(drop=True)
d.to_csv('sep_reg_panel.csv',index=False)

def reg(y,X,names,lab):
    m=sm.OLS(y,sm.add_constant(X)).fit(cov_type='HAC',cov_kwds={'maxlags':4})
    out=[]
    for i,n in enumerate(names): out.append((n,m.params[i+1],m.tvalues[i+1]))
    return out,m.rsquared,int(m.nobs)

print("="*92)
print("HILLENBRAND TABLE 4, LEFT-HAND SIDE DECOMPOSED")
print("Window = [t-1, t+1] around the SEP meeting. LHS in bp, RHS in pp. HAC(4).")
print("RHS = revision in the FOMC longer-run r* since the PREVIOUS SEP.")
print("="*92)

for rhs,rlab in [('d_lr_mean','MEAN of dots (47 moves)'),('d_lr_med','MEDIAN of dots (19 moves)')]:
    s=d.dropna(subset=[rhs])
    print(f"\n--- RHS: {rlab}   n={len(s)}   sd(revision)={s[rhs].std():.3f} pp   "
          f"non-zero revisions={int((s[rhs].abs()>1e-9).sum())}")
    print(f"    {'LHS (10y)':16s} {'b (bp per pp)':>15s} {'t':>7s} {'R2':>7s}")
    for col,lab in [('dy10','total'),('drn10','risk-neutral'),('dtp10','term premium')]:
        o,r2,n=reg(s[col].values,s[[rhs]].values,['b'],lab)
        print(f"    {lab:16s} {o[0][1]:+15.2f} {o[0][2]:+7.2f} {r2:7.3f}")

print("\n" + "="*92)
print("CONTROLLING FOR THE NEAR-TERM POLICY SURPRISE (2y window change)")
print("="*92)
s=d.dropna(subset=['d_lr_mean','dy2'])
print(f"n={len(s)}")
print(f"    {'LHS (10y)':16s} {'b(LR revision)':>15s} {'t':>7s} {'b(2y move)':>12s} {'t':>7s} {'R2':>7s}")
for col,lab in [('dy10','total'),('drn10','risk-neutral'),('dtp10','term premium')]:
    o,r2,n=reg(s[col].values,s[['d_lr_mean','dy2']].values,['lr','d2'],lab)
    print(f"    {lab:16s} {o[0][1]:+15.2f} {o[0][2]:+7.2f} {o[1][1]:+12.3f} {o[1][2]:+7.2f} {r2:7.3f}")

print("\n" + "="*92)
print("MATURITY SIGNATURE — endpoint shock loads FLAT in n; cyclical shock decays as 1/n")
print("="*92)
s=d.dropna(subset=['d_lr_mean'])
print(f"    {'n':>3s} {'total':>16s} {'risk-neutral':>16s} {'term premium':>16s}")
for n in MATS:
    row=f"    {n:3d}"
    for pre in ['dy','drn','dtp']:
        o,_,_=reg(s[f'{pre}{n}'].values,s[['d_lr_mean']].values,['b'],'')
        row+=f"  {o[0][1]:+7.2f} (t{o[0][2]:+5.2f})"
    print(row)
