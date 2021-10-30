import numpy as np
import pandas as pd

from pandas import DataFrame
from typing import List

class Indicator():
    
    def __init__(self):
        pass
    
    @staticmethod
    def ma(df:DataFrame, n:int=5)->List:
        ma = df['Close'].rolling(n).mean()
        return [ma]

    @staticmethod
    def kdj(df:DataFrame, overbuy:int = 80, oversell:int = 20, time_period:int=10)->List:
        data = df.copy()
        ini_k = 50
        ini_d = 50
        k=[]
        d=[]
        rsv = (data['Close'].rolling(time_period).agg(lambda rows: rows.iloc[-1]) - data["Low"].rolling(time_period).min() ) / ( data["High"].rolling(time_period).max() - data["Low"].rolling(time_period).min() ) *100
        
        for _ in rsv:
            if pd.isna(_) is not True :
                ini_k =  2/3 * ini_k + 1/3 * _
                k.append(ini_k)
            else:  
                k.append(_)

        for _ in k:
            if pd.isna(_) is not True:
                ini_d =  2/3 * ini_d + 1/3 * _
                d.append(ini_d)  

            else:
                d.append(_)  
        k = pd.Series(k,index = rsv.index)
        d = pd.Series(d,index = rsv.index)
        j = 3 * k - 2 * d
        return [k,d,j]

    @staticmethod
    def rsi(self):
        pass


                if freq in ['B','W']:
                    proxy = pd.DatetimeIndex(tem.ts + pd.DateOffset(hours=9))
                    tem.index = proxy
                    tem = tem.resample('B',closed=closed,label=label).agg({'Volume': 'sum', 'Open': 'first','High':'max','Low':'min','Close':'last'}).dropna().reset_index()
                    if freq == 'W':
                        tem = tem.set_index('ts')
                        tem = tem.resample('W',closed=closed,label='left').agg({'Volume': 'sum', 'Open': 'first','High':'max','Low':'min','Close':'last'}).dropna().reset_index()

               
               
                else:
                    proxy = pd.DatetimeIndex(tem.ts + pd.DateOffset(hours=9))
                    tem.index = proxy
                    # there is something wrong with frequency lower than daily frequency 
                    # current support only the business day frequency for above symbols
                    tem = tem.resample('B',closed=closed,label=label).agg({'Volume': 'sum', 'Open': 'first','High':'max','Low':'min','Close':'last'}).dropna().reset_index()

        


