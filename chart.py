# coding: utf-8
import seaborn as sns
import pandas as pd
import numpy as np
import datetime
import matplotlib.pyplot as plt
import os

#Path to csv from main dir
dirname, filename = os.path.split(os.path.abspath(__file__))
active_log=dirname+"/log/active.csv"
away_log=dirname+"/log/away-time.csv"

plt.close('all')

adata = pd.read_csv(active_log, sep=" ", infer_datetime_format=True)
adata['time'] = pd.to_datetime(adata['date'],  format='%Y-%m-%d')
# adata=adata[adata['time_suspend'] > 5000]
adata.set_index(['date'],inplace=True)
adata = adata.sum(level="date")
adata['Laptop usage time [h]'] = adata['usage']/60/60
# adata['Away time'] = 24 - adata['Laptop usage time [h]']
del adata['usage']
adata.plot(kind="bar")
plt.show()

# create dataframe with datetime as index and aggregated (frequency) values
date = pd.date_range('2020-02-18', periods=10*12, freq='1h')
freq = np.random.poisson(lam=1, size=(len(date)))
type(freq)
freq = pd.read_csv('/home/migacz/stats/log/hourly-laptop.log', sep=" ")
freq['at2'] = freq['at']/60
freq['date']=pd.to_datetime(freq['date'],  format='%Y/%m/%d|%H')
freq['date_h']=freq['date'].dt.hour
freq['at2']

index = freq.date
df = pd.DataFrame(data=freq)
df.index=df.date
#add a column hours and da3s
df["hours"] = df.index.hour
df["days"] = df.index.map(lambda x: x.strftime('%b-%d'))
#df["at2"]=freq['at2']
# create pivot table, days will be columns, hours will be rows
piv = pd.pivot_table(df, values="at2",index=["hours"], columns=["days"], fill_value=0)
#plot pivot table as heatmap using seaborn
# ax = sns.heatmap(piv, square=True)
# plt.setp( ax.xaxis.get_majorticklabels(), rotation=90 )
# plt.tight_layout()
# plt.show()


df=df.resample('1H').asfreq().fillna(0)
df["hours"] = df.index.hour
df["days"] = df.index.map(lambda x: x.strftime('%b-%d'))
# create pivot table, days will be columns, hours will be rows
piv = pd.pivot_table(df, values="at2",index=["hours"], columns=["days"], fill_value=0)
#plot pivot table as heatmap using seaborn
ax = sns.heatmap(piv, square=True, cmap="YlGnBu", annot=True)
plt.setp( ax.xaxis.get_majorticklabels(), rotation=90 )
plt.tight_layout()
plt.show()

# If you want to filter data
# data_filtered=data[data.time_suspend > 5000]
# data_filtered['time_suspend'] = data_filtered.time_suspend/60/60
# data_filtered.time = pd.to_datetime(data_filtered['date_end'],  format='%Y-%m-%d')
# data_filtered.set_index(['date_end'],inplace=True)

# data = pd.read_csv(away_log, sep=" ", infer_datetime_format=True)
# data['time'] = pd.to_datetime(data['date_end'],  format='%Y-%m-%d')
# data.set_index(['date_end'],inplace=True)
# data = data.sum(level="date_end")
# data['Estimated away time'] = data['time_suspend']/60/60
# # data['Estimated usage time'] = 24 - data['Estimated away time']
# del data['time_suspend']
# data.plot(kind="bar")

# total_time_suspend=data.sum(level="date_end")
# total_time_suspend.plot(subplots=True, kind="bar")

# data.plot(kind="bar");
# data2.plot(kind="bar");

# plt.plot(data)
# pd.DataFrame(data[['date_end', 'time_suspend_h']]).plot(kind="bar")
# data.date_start = pd.to_datetime(data['date_end'], format='%Y-%m-%d')

plt.show()
