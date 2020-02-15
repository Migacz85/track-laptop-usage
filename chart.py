# coding: utf-8
import pandas as pd
import numpy as np
import datetime
import matplotlib.pyplot as plt
import os

#Path to csv from main dir
dirname, filename = os.path.split(os.path.abspath(__file__))
active_log=dirname+"/log/active.csv"

plt.close('all')

# data = pd.read_csv('~/stats/log/away-time.csv', sep=" ", infer_datetime_format=True)
adata = pd.read_csv(active_log, sep=" ", infer_datetime_format=True)

# If you want to filter data
# data_filtered=data[data.time_suspend > 5000]
# data_filtered['time_suspend'] = data_filtered.time_suspend/60/60
# data_filtered.time = pd.to_datetime(data_filtered['date_end'],  format='%Y-%m-%d')
# data_filtered.set_index(['date_end'],inplace=True)

# data['time'] = pd.to_datetime(data['date_end'],  format='%Y-%m-%d')
# data.set_index(['date_end'],inplace=True)
# data = data.sum(level="date_end")
# data['Estimated away time'] = data['time_suspend']/60/60
# # data['Estimated usage time'] = 24 - data['Estimated away time']
# del data['time_suspend']


adata['time'] = pd.to_datetime(adata['date'],  format='%Y-%m-%d')
adata.set_index(['date'],inplace=True)
adata = adata.sum(level="date")
adata['Laptop usage time [h]'] = adata['usage']/60/60
# adata['Away time'] = 24 - adata['Laptop usage time [h]']
del adata['usage']

adata.plot(kind="bar")

# total_time_suspend=data.sum(level="date_end")
# total_time_suspend.plot(subplots=True, kind="bar")

# data.plot(kind="bar");
# data2.plot(kind="bar");
# plt.plot(data)
# pd.DataFrame(data[['date_end', 'time_suspend_h']]).plot(kind="bar")
# data.date_start = pd.to_datetime(data['date_end'], format='%Y-%m-%d')

plt.show()
