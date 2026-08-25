import pandas as pd, numpy as np
U='/mnt/user-data/uploads/clean_reactionFunction/'

# --- ACM-implied r*: 9y1y risk-neutral forward minus 2.0, daily
a=pd.read_excel(U+'ACMTermPremium.xls',sheet_name='ACM Daily')
a['date']=pd.to_datetime(a['DATE'])
a['fwd_rn_9y1y']=10*a.ACMRNY10-9*a.ACMRNY09
a['fwd_tot_9y1y']=10*a.ACMY10-9*a.ACMY09
a['rstar_acm']=a.fwd_rn_9y1y-2.0
a['rstar_acm_5y5y']=(10*a.ACMRNY10-5*a.ACMRNY05)/5-2.0
acm=a[['date','rstar_acm','rstar_acm_5y5y','fwd_rn_9y1y','fwd_tot_9y1y','ACMY01','ACMY10','ACMRNY01']].dropna()

# --- Fed SEP r*
f=pd.read_csv(U+'wedge/fed_rstar.csv',parse_dates=['date'])
f['rstar_fed_mean_lvl']=f.rstar_fed_mean

# --- HLW
h=pd.read_excel(U+'HLW/Laubach_Williams_current_estimates.xlsx',sheet_name='data',skiprows=5)
h=h[['Date','rstar']].dropna().rename(columns={'Date':'date','rstar':'rstar_hlw'})

# --- SPD
s=pd.read_csv(U+'wedge/spd_rstar.csv',parse_dates=['date'])[['date','rstar_spd']]

for n,df in [('acm',acm),('fed',f),('hlw',h),('spd',s)]:
    print(f"{n}: {len(df)} obs  {df.date.min():%Y-%m}  -> {df.date.max():%Y-%m}")
acm.to_csv('rstar_acm_daily.csv',index=False)
f.to_csv('rstar_fed.csv',index=False); h.to_csv('rstar_hlw.csv',index=False); s.to_csv('rstar_spd.csv',index=False)

# ---------- diagnostics: is the 9y1y forward washed out? ----------
print("\n"+"="*78)
print("IS THE 9y1y RISK-NEUTRAL FORWARD FREE OF THE CYCLE?")
print("="*78)
m=acm.set_index('date').resample('QE').last().dropna()
m['short']=m.ACMY01
print("\n1. Co-movement with the CURRENT short rate (1y yield), quarterly:")
for lo,hi,lab in [('1990','2026','1990-2026'),('1990','2007','1990-2007'),('2008','2026','2008-2026')]:
    s_=m.loc[lo:hi]
    print(f"   {lab}:  corr(level) {s_.rstar_acm.corr(s_.short):+.3f}   "
          f"corr(4q changes) {s_.rstar_acm.diff(4).corr(s_.short.diff(4)):+.3f}")
hl=h.set_index('date').resample('QE').last()
j=m.join(hl,how='inner').dropna()
print(f"\n   HLW r* for comparison, 1990-2026: corr(level w/ 1y) "
      f"{j.rstar_hlw.corr(j.short):+.3f}   corr(4q chg) {j.rstar_hlw.diff(4).corr(j.short.diff(4)):+.3f}")

print("\n2. Beta of the 9y1y RN forward on the 1-year yield (quarterly changes):")
import statsmodels.api as sm
for col,lab in [('rstar_acm','9y1y RN fwd'),('rstar_acm_5y5y','5y5y RN fwd'),('rstar_hlw','HLW r*')]:
    d=j if col=='rstar_hlw' else m
    y=d[col].diff(); x=d.ACMY01.diff()
    ok=y.notna()&x.notna()
    r=sm.OLS(y[ok],sm.add_constant(x[ok])).fit(cov_type='HAC',cov_kwds={'maxlags':4})
    print(f"   {lab:12s} beta {r.params.iloc[1]:+.3f} (t {r.tvalues.iloc[1]:+5.2f})  R2 {r.rsquared:.2f}")

print("\n3. Persistence — an endpoint should be ~a martingale (rho ~ 1):")
for col,lab,df in [('rstar_acm','9y1y RN fwd (ACM)',m),('rstar_hlw','HLW r*',j)]:
    y=df[col].dropna(); x=y.shift(1)
    ok=y.notna()&x.notna()
    r=sm.OLS(y[ok],sm.add_constant(x[ok])).fit()
    rho=r.params.iloc[1]
    hl_=np.log(0.5)/np.log(rho) if 0<rho<1 else np.inf
    print(f"   {lab:20s} quarterly rho {rho:.4f}  half-life {hl_:5.1f} q = {hl_/4:4.1f} yr")

print("\n4. How much of a current shock survives 9 years ahead under a stationary VAR?")
print("   share = rho_monthly^108")
for rho in [0.98,0.99,0.995,0.997]:
    print(f"     rho={rho:.3f} (half-life {np.log(.5)/np.log(rho)/12:4.1f} yr)  ->  {rho**108:5.1%} of the shock still in the 9y-ahead expectation")
