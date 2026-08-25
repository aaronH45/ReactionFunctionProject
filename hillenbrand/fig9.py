import pandas as pd, numpy as np
U='/mnt/user-data/uploads/clean_reactionFunction/'
d=pd.read_csv(U+'anonymized/dotplot_dots_long.csv',dtype={'horizon':str})
d['date']=pd.to_datetime(d.date); d['yr']=pd.to_numeric(d.horizon,errors='coerce')

lr = d[d.horizon=='LR'].groupby('date')['dot'].agg(lr_mean='mean',lr_med='median',n='size')
y1 = d[d.yr==d.date.dt.year+1].groupby('date')['dot'].agg(y1_mean='mean',y1_med='median',n1='size')
fig9 = lr.join(y1,how='outer')
fig9['pi_lr']=2.0                      # longer-run PCE: 2.0 in all 594 archived submissions
fig9['rstar']=fig9.lr_mean-fig9.pi_lr
fig9=fig9.reset_index()
fig9.to_csv('fig9_data.csv',index=False)

# validation against the published figure (2012-2021)
chk=fig9[fig9.date<='2021-12-31']
print(f"meetings {len(fig9)}  {fig9.date.min():%Y-%m}  ->  {fig9.date.max():%Y-%m}")
print(f"validation window {len(chk)} meetings 2012-2021\n")
print("published-figure readings vs computed MEAN (and MEDIAN, which does not match):")
for dt,pub in [('2012-01-25',4.20),('2014-06-18',3.75),('2016-09-21',2.93),
               ('2019-12-11',2.50),('2021-12-15',2.50)]:
    r=fig9[fig9.date==dt].iloc[0]
    print(f"  LR  {dt}  paper~{pub:.2f}   mean {r.lr_mean:.3f}   median {r.lr_med:.2f}")
for dt,pub in [('2014-06-18',1.20),('2015-03-18',2.03),('2016-03-16',2.07),('2020-06-10',0.13)]:
    r=fig9[fig9.date==dt].iloc[0]
    print(f"  1y  {dt}  paper~{pub:.2f}   mean {r.y1_mean:.3f}   median {r.y1_med:.2f}")
print("\nExtension, 2022 onward:")
print(fig9[fig9.date>='2022-01-01'][['date','lr_mean','y1_mean','rstar']].to_string(index=False))
