import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.dates as mdates
import pandas as pd, numpy as np
f=pd.read_csv('fig9_data.csv',parse_dates=['date'])
DARK='#3d3d3d'; MID='#8c8c8c'; LIGHT='#a8a8a8'; INK='#111111'; INK2='#4a4a4a'
plt.rcParams['font.family']='DejaVu Sans'

fig,ax=plt.subplots(figsize=(11.0,6.4)); fig.patch.set_facecolor('white'); ax.set_facecolor('white')

ax.axvspan(pd.Timestamp('2021-12-31'),pd.Timestamp('2026-12-31'),color='#f4f4f2',zorder=0)
ax.plot(f.date,f.lr_mean,'-o',color=DARK,mfc=DARK,ms=5.2,lw=1.3,zorder=4,
        label='Fed forecast for long-run level of federal funds rate')
ax.plot(f.date,f.y1_mean,'--D',color=MID,mfc=LIGHT,mec=MID,ms=5.4,lw=1.1,zorder=3,
        label='Fed forecast for federal funds rate in 1 year')
ax.plot(f.date,f.pi_lr,linestyle=(0,(1,2.2)),marker='s',color=MID,mfc=LIGHT,mec=MID,
        ms=4.8,lw=1.1,zorder=2,label='Fed forecast for long-run inflation')

ax.set_ylabel('Fed Forecast (%)',fontsize=11,color=INK2)
ax.set_ylim(0,5.75); ax.set_yticks(np.arange(0,5.1,1))
ax.set_xlim(pd.Timestamp('2011-09-01'),pd.Timestamp('2026-12-31'))
ax.xaxis.set_major_locator(mdates.YearLocator(2)); ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax.tick_params(colors=INK2,labelsize=10.5,direction='out',length=4)
for s in ax.spines.values(): s.set_color('#555555'); s.set_linewidth(0.9)
ax.axvline(pd.Timestamp('2021-12-31'),color='#b8b8b4',lw=1.0,ls=(0,(4,3)),zorder=1)
ax.text(pd.Timestamp('2026-10-15'),5.52,'extension beyond the published figure',
        fontsize=9,color='#8f8f8a',va='top',ha='right',style='italic')

ax.annotate('long-run dot bottoms at 2.43 (Mar 2022),\nthen is revised UP +0.74 pp to 3.16 by Mar 2026',
            xy=(pd.Timestamp('2022-03-16'),2.425),xytext=(pd.Timestamp('2022-06-01'),1.15),
            fontsize=9.2,color=INK,ha='left',
            arrowprops=dict(arrowstyle='-',color='#9a9a96',lw=0.9,
                            connectionstyle='arc3,rad=0.15'))

ax.set_title('Figure 9 (replicated and extended): The Time Series of the Dot Plot Forecasts',
             fontsize=13,color=INK,pad=12)
ax.legend(loc='upper center',bbox_to_anchor=(0.5,-0.105),frameon=True,fontsize=10,
          edgecolor='#555555',fancybox=False,ncol=1,handlelength=3.0,labelcolor=INK2)
leg=ax.get_legend(); leg.get_frame().set_linewidth(0.9)

fig.text(0.055,0.012,
 'Note: Each point is the cross-participant MEAN of individual FOMC members’ projections at that SEP meeting, matching the published figure '
 '(the median does not).\n"In 1 year" is the projection for the end of the following calendar year, which is why the series steps up each March as the target year rolls '
 'forward. Long-run\ninflation is 2.0 in all 594 archived longer-run PCE submissions. 57 SEP meetings, Jan 2012 – Mar 2026. Source: FOMC SEP dot-plot archive.',
 fontsize=8.2,color='#8f8f8a',ha='left',va='bottom',linespacing=1.5)
fig.subplots_adjust(left=0.075,right=0.975,top=0.925,bottom=0.315)
fig.savefig('fig9_extended.png',dpi=200,facecolor='white')
print('ok')
