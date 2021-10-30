#from main import AlgoTrade
import shioaji as sj
from shioaji.data import Kbars
import pandas as pd
import numpy as np
from datetime import datetime 
from typing import Tuple
from pandas import DataFrame
import re

def api_connection(ca_path:str='C:\\Users\\tsunglin\\Desktop\\SinoPac.pfx'):
    api = sj.Shioaji()
    accounts = api.login("id_number", "password")
    api.activate_ca(
        ca_path = ca_path,
        ca_passwd = 'id_number',
        person_id = 'id_number',
    )
    return api

class StockData():
    def __init__(self):
        self.api = api_connection()

    def get_available_id(self,data_type:str):
        return getattr(self.api.Contracts, {'future':'Futures','stock':'Stocks'}[data_type])

    def _get_hist_oneminute_kbar(self,data_type:str,symbol:str,hist_start:str,hist_end:str=datetime.now().strftime('%Y-%m-%d'))->DataFrame:
        """get historical  1min kbar dataframe

        Args:
            data_type (str): [description]
            symbol (str): [description]
            start (str): [description]
            end (str, optional): [description]. Defaults to datetime.now().strftime('%Y-%m-%d').

        Raises:
            TypeError: data_type must be 'stock' or 'future'.

        Returns:
            DataFrame: 
            ------------------------------
            |ts|Open|High|Low|Close|Volume|
            -------------------------------
            |xx|xxxx|xxxx|xxx|xxxxx|xxxxxx|
            |xx|xxxx|xxxx|xxx|xxxxx|xxxxxx|
            
        """
        
        if data_type == 'future':
            contracts = getattr(self.api.Contracts.Futures,symbol[:3])
            kbars = self.api.kbars(contracts[symbol],hist_start,hist_end)
            df = pd.DataFrame({**kbars})
            df.ts = pd.to_datetime(df.ts)
            df = df[['ts','Open', 'High', 'Low',  'Close', 'Volume']]
            self.hist_df =df
            self.symbol = symbol
            return df
        elif data_type =='stock':
            kbars = self.api.kbars(self.api.Contracts.Stocks[symbol], hist_start, hist_end)
            df = pd.DataFrame({**kbars})
            df.ts = pd.to_datetime(df.ts)
            df = df[['ts','Open', 'High', 'Low',  'Close', 'Volume']]
            self.hist_df = df
            self.symbol = symbol
            return df
        else:
            raise TypeError("data_type must be 'stock' or 'future'.")

    def _clean_up_kbar(self,freq:str=None,after_market_data:bool=False):
        """
        Args:
            self ([type]): [description]
            freq (str, optional): 
                specifies the data frequency. Defaults to None, Defaults to None (1min)
                'min': minute data
                'T': minute data
                'M': monthly data, end of the month, the data we be displayed one day earlier than other platform
                'W': weekly data, end of the week, the data we be displayed one day earlier than other platform
                'B' : business day
        Yields:
            
        """
        tem = self.hist_df.copy()
        label='right'
        closed = 'right'
        target_dict = {'Volume': 'sum', 'Open': 'first','High':'max','Low':'min','Close':'last'}
        
        if after_market_data == False:

            if self.symbol[:3] in ['GDF','TGH','RTF','RHF','XEF','XJF','XBF','XAF']:
                hours = tem['ts'].apply(lambda x: x.hour) 
                tem = tem[(hours > 7) & (hours < 17)]
    
            if self.symbol[:3] in ['BRF','TXF','MXF','EXF','ZEF','UDF','SPF','UNF','F1F']:
                hours = tem['ts'].apply(lambda x: x.hour) 
                tem = tem[(hours > 7) & (hours < 14)]
        
        if after_market_data == True and self.symbol[:3] in ['GDF','TGH','RTF','RHF','XEF','XJF','XBF','XAF','BRF','TXF','MXF','EXF','ZEF','UDF','SPF','UNF','F1F']:
            
            if freq is None:
                return tem    

            if 'min' in freq or 'T' in freq:
                tem = tem.set_index('ts')
                tem = tem.resample(freq,closed=closed,label=label).agg(target_dict).dropna().reset_index()
            
            if freq[-1] in ['B','W','M']:
                proxy = pd.DatetimeIndex(tem.ts + pd.DateOffset(hours=9))
                tem.index = proxy
                tem = tem.resample('B',closed=closed,label=label).agg(target_dict).dropna().reset_index()
                if freq in ['W','M']:
                    tem = tem.set_index('ts')
                    tem = tem.resample(freq,closed=closed,label='left').agg(target_dict).dropna().reset_index()
            return tem

        if freq:

            if freq in ['W','M']:
                tem = tem.set_index('ts')
                tem = tem.resample('B',closed=closed,label=label).agg(target_dict).resample(freq,closed=closed,label='left').agg(target_dict).dropna().reset_index()
            else:
                tem = tem.set_index('ts')
                tem = tem.resample(freq,closed=closed,label=label).agg(target_dict).dropna().reset_index()
        elif freq is None:
            tem = tem[['ts', 'Volume', 'Open', 'High', 'Low',  'Close']]

        return tem
            

    def _broadcast_kbar(self,df):
        tem = df
        self.hist_open = tem.Open
        self.hist_high = tem.High
        self.hist_low = tem.Low
        self.hist_close = tem.Close
        self.hist_vol = tem.Volume
        self.hist_ts = tem.ts

        self.hist_end = tem.iloc[-1].strftime('%Y-%m-%d %H:%M:%S')
        self.hist_close_mean = tem.mean() 
        self.hist_close_std = tem.std()

    def get_real_stream(self,data_type:str,symbol:str):
        if data_type == 'future':
            contracts = getattr(self.api.Contracts.Futures,symbol[:3])
            contracts = [contracts[symbol]]
            snapshots = self.api.snapshots(contracts)

            return snapshots[0]
        elif data_type =='stock':
            contracts = [self.api.Contracts.Stocks[symbol]]
            snapshots = self.api.snapshots(contracts)

            return snapshots[0]
        else:
            raise TypeError("data_type must be 'stock' or 'future'.")

    def get_simulated_stream(self)->Tuple:
        """ we use normoral distribution estimated from the past to simulate fake data for testing purpose. 
            first, we have to execute _get_hist_close() method to get our input variables.
        Returns:
            [type]: [description]
        """
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        simulated_close = np.random.normal(self.hist_close_mean, self.hist_close_std, 1)[0]
        spread = np.random.rand(1)[0]/1000
        simulated_bid = simulated_close - spread * simulated_close
        simulated_ask = simulated_close + spread * simulated_close

        simulated_bid = np.round(simulated_bid,2)
        simulated_ask = np.round(simulated_ask,2)
        simulated_close = np.round(simulated_close,2)

        return current_time, simulated_close, simulated_bid, simulated_ask

    def get_hist_stream(self,df:DataFrame): 
        """
        put in df after using _clean_up method

        Args:
            df (DataFrame): [description]

        Returns:
            [type]: [description]
        """

        tem = df.copy()
        spread = np.random.rand(len(tem))/1000 
        #stem = tem.loc[:,['ts','Close']]
        tem['simulated_hist_bid'] = (tem['Close'] - spread * tem['Close']).round(2)
        tem['simulated_hist_ask'] = (tem['Close'] + spread * tem['Close']).round(2)
        
        return tem
