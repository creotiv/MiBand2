import numpy as np
import pandas as pd
import sys
from stockstats import StockDataFrame
import matplotlib.pyplot as plt

df = pd.DataFrame.from_csv(sys.argv[1], index_col=None)
print df.head
df['time'] = pd.to_datetime(df['time'], unit='s')
df = df.set_index('time')
print df.describe()
# plt.subplot('111')
# df.plot(kind='line')
# plt.subplot('122')
# df.plot(kind='histogram')
df.rolling('120s').mean().plot()
plt.show()
