from tabulate import tabulate
import datetime
import re
import time 
import numpy as np
import pandas as pd

from typing import Text
from typing import List

from trade_data import StockData
from indicator import Indicator



class Trade():
    stockdata = StockData()
    indi = Indicator()

    def __init__(self,short_selling:bool=True,additional_orders:bool=True):
        self.short_selling = short_selling
        self.additional_orders = additional_orders
        self.rm_order_executed = False
        self.buy_to_cover_stop_partial = False
        self.sell_stop_partial = False
        self.day_trade_stop_executed =False
        self.day_trade_stop_execution = False

#===================================================================================
# trading modules (place_buy_order & place_sell_order)
#===================================================================================  
    def day_trade(self,stop_time:str='13:30:00'):
        current_hsm = self.current_time.strftime("%Y-%m-%d %H:%M:%S")[-8:]
        if self.stream_data in ['stimulate','real']:
            freq = self.stream_time_gap
            terminate_time = datetime.datetime.strptime(stop_time, '%H:%M:%S') - datetime.timedelta(seconds = freq)
            if datetime.datetime.strptime(current_hsm, '%H:%M:%S') >= terminate_time :
                if self.num_units > 0: 
                    self.place_sell_order()
                    self.day_trade_stop_executed = True
                elif self.num_units < 0:
                    self.place_buy_order()
                    self.day_trade_stop_exeuted = True
                self.day_trade_stop_execution = True
        
        elif self.stream_data == 'hist':
            freq = self.freq
            hours = re.findall( r'(\d*)H',freq)
            minutes = re.findall( r'(\d*)[min,T]',freq)

            hours = int(hours[0]) if hours else 0
            minutes = int(minutes[0]) if minutes else 0                

            terminate_time = datetime.datetime.strptime(stop_time, '%H:%M:%S') - datetime.timedelta(hours=hours, minutes=minutes)
            if datetime.datetime.strptime(current_hsm, '%H:%M:%S') >= terminate_time :
                if self.num_units > 0:
                    self.place_sell_order()
                    self.day_trade_stop_executed = True
                elif self.num_units < 0:
                    self.place_buy_order()
                    self.day_trade_stop_executed = True
                self.day_trade_stop_execution = True

    def rm_order(self):
        rm_info_df = self.show_rm_info()
        rm_info_df_empty = rm_info_df.empty

        if self.num_units>0 and (rm_info_df_empty is not True):
            last_units = rm_info_df['units'].iloc[-1]
            last_sl = rm_info_df['sl'].iloc[-1]
            last_sp = rm_info_df['sp'].iloc[-1]
            if self.num_units > last_units:
                first_units = rm_info_df['units'].iloc[0]
                first_order_price = rm_info_df['order price'].iloc[0]
                first_sl = rm_info_df['sl'].iloc[0]
                first_sp = rm_info_df['sp'].iloc[0]
                if self.current_close>=last_sp or self.current_close<=last_sl:
                    self.place_sell_order(order_type='sell stop', units=self.num_units,sl=None,sp=None)
                    self.rm_order_executed = True

                elif self.current_close>=first_sp or self.current_close<=first_sl:      
                    self.rm_order_value = first_units * first_order_price
                    self.sell_stop_partial = True
                    self.place_sell_order(order_type='sell stop', units = first_units,sl=None,sp=None)
                    self.rm_order_executed = True

            elif self.num_units == last_units and (self.current_close>=last_sp or self.current_close<=last_sl):
                self.place_sell_order(order_type='sell stop', units=self.num_units,sl=None,sp=None)                
                self.rm_order_executed = True

        elif self.num_units<0 and (rm_info_df_empty is not True):  
            last_units = rm_info_df['units'].iloc[-1]
            last_sl = rm_info_df['sl'].iloc[-1]
            last_sp = rm_info_df['sp'].iloc[-1]
            last_units = abs(last_units) 
            num_units = abs(self.num_units) 

            if num_units > last_units:
                first_units = rm_info_df['units'].iloc[0]
                first_order_price = rm_info_df['order price'].iloc[0]
                first_sl = rm_info_df['sl'].iloc[0]
                first_sp = rm_info_df['sp'].iloc[0]

                if self.current_close<=last_sp or self.current_close>=last_sl:
                    self.place_buy_order(order_type='buy to cover stop', units=num_units,sl=None,sp=None)
                    self.rm_order_executed = True

                elif self.current_close<=first_sp or self.current_close>=first_sl:      
                    self.rm_order_value = first_units * first_order_price
                    self.buy_to_cover_stop_partial = True                    
                    self.place_buy_order(order_type='buy to cover stop', units = first_units,sl=None,sp=None)
                    
                    self.rm_order_executed = True

            elif num_units == last_units and (self.current_close<=last_sp or self.current_close>=last_sl):
                self.place_buy_order(order_type='buy to cover stop', units=num_units,sl=None,sp=None)                
                self.rm_order_executed = True 

    def place_buy_order(self,order_type:str='buy',amount:int=None,units:int=None,sl:int=None,sp:int=None): 
        if self.rm_order_executed is True:
            self.rm_order_executed = False
        elif self.day_trade_stop_executed is True:
            self.day_trade_stop_executed = False
        
        elif self.day_trade_stop_execution is True:
            self.day_trade_stop_execution = False

        else:
            if self.additional_orders:
                self._place_buy_order(order_type,amount,units,sl,sp)
            else:
                if self.num_units <= 0:
                    self._place_buy_order(order_type,amount,units,sl,sp)

    def place_sell_order(self,order_type:str='short sell',amount:int=None,units:int=None,sl:int=None,sp:int=None):
        if self.rm_order_executed is True:
            self.rm_order_executed = False

        elif self.day_trade_stop_executed is True:
            self.day_trade_stop_executed = False
        
        elif self.day_trade_stop_execution is True:
            self.day_trade_stop_execution = False

        else:
            if self.short_selling:
                if self.additional_orders:
                    self._place_sell_order(order_type,amount,units,sl,sp)
                else:
                    if self.num_units>= 0:
                        self._place_sell_order(order_type,amount,units,sl,sp)
            else:
                if self.num_units> 0:
                    self._place_sell_order(order_type,amount,units,sl,sp)

    def _place_buy_order(self,order_type:str='buy',amount:int=None,units:int=None,sl:int=None,sp:int=None):
        self.order_price = self.current_ask 
        self.profit = np.nan
        order_type = order_type
        #----------------------------------------
        if self.data_type == 'stock':
            commsion_ratio = 0.001425 

        elif self.data_type =='future':
            # not ready
            commsion_ratio = 0
        #----------------------------------------
        if order_type=='buy' and self.num_units < 0:
            self.sl = np.nan
            self.sp = np.nan
            order_type = 'buy to cover'  # sell to cover  
            units = abs(self.num_units)
        elif sl is not None or sp is not None:
            if sl is None:
                sl = 0
            if sp is None:
                sp = 0
            sl= (1-sl)*self.order_price
            sp= (1+sp)*self.order_price
            self.sl = round(sl,2)
            self.sp = round(sp,2)   
        elif sl is None and sp is None:
            # no special order detected
            self.sl = np.nan
            self.sp = np.nan
        #----------------------------------------
        if units is None:
            units = int(amount/self.order_price)
        units = units
        #----------------------------------------
        order_value = units * self.order_price 
        commsion = units * self.order_price * commsion_ratio
        self.order_value = np.round(order_value,2)
        commsion = np.round(commsion,2)
        if self.balance < order_value and order_type=='buy':
            if self.verbose:
                print(f"current close = {self.current_close}, balance is not enough, fail to execute {order_type} order.")
        else:
            if order_type in ['buy to cover','buy to cover stop']:
                
            
                if self.buy_to_cover_stop_partial:
                    self.balance += (self.order_value - commsion)
                    self.profit = (self.order_value - commsion) - (self.rm_order_value + self.rm_order_value * commsion_ratio)
                    self._profit.append(self.profit)
                    self.buy_to_cover_stop_partial = False
                    self._delete_rm_info()

                else:
                    self._balance -= (self.order_value + commsion)
                    self.balance = self._balance                   
                    total_profit = self.balance - self.init_balance
                    self.profit = total_profit - self._total_profit[-1] - sum(self._profit)
                    self._total_profit.append(total_profit)
                    self.profit = np.round(self.profit,2)
                    self._profit = []                 
                    self._reset_rm_info()
            elif order_type=='buy':
                self._update_rm_info(order_type,units)
                self.balance -= (self.order_value + commsion)
                self._balance -= (self.order_value + commsion)
            
            self.balance = np.round(self.balance,2)
            self._balance = np.round(self._balance,2)
            self.profit = np.round(self.profit,2)
            self.units = units
            self.num_units += self.units
            self.num_trades += 1 
            self.num_buy_orders += 1

            self._update_order_info(order_type)

            
            
            if self.verbose:
                print({'ts':self.current_time,'order type':order_type,
                                                    'order price (ask)': self.order_price,             
                                                    'total units':self.num_units,
                                                    'order units':self.units,                                                  
                                                    'order value': self.order_value,
                                                    'sl':self.sl,
                                                    'sp':self.sp,
                                                    'balance':self.balance,
                                                    'profit':self.profit,                                   
                                                    })
            else:
                print({'ts':self.current_time,'order type':order_type,
                                                    'order price (ask)': self.order_price,             
                                                    'balance':self.balance,
                                                    'profit':self.profit,                                                    
                                                    })
    
    def _place_sell_order(self,order_type:str='short sell',amount:int=None,units:int=None,sl:int=None,sp:int=None):
        self.order_price = self.current_bid
        self.profit = np.nan
        order_type = order_type
        #----------------------------------------
        if self.data_type == 'stock':
            commsion_ratio = 0.001425 

        elif self.data_type =='future':
            # not ready
            commsion_ratio = 0
        #----------------------------------------
        if order_type=='short sell' and self.num_units > 0:
            self.sl = np.nan
            self.sp = np.nan
            order_type = 'sell'  # sell to cover  
            units = self.num_units               
        elif sl is not None or sp is not None:
            if sl is None:
                sl = 0
            if sp is None:
                sp = 0
            sl= (1+sl)*self.order_price
            sp= (1-sp)*self.order_price
            self.sl = round(sl,2)
            self.sp = round(sp,2)            
        elif sl is None and sp is None:
            # no special order detected
            self.sl = np.nan
            self.sp = np.nan
        #----------------------------------------
        if units is None:
            units = int(amount/self.order_price)
        units = units
        #----------------------------------------        
        order_value = units * self.order_price 
        commsion = units * self.order_price * commsion_ratio
        self.order_value = np.round(order_value,2)
        commsion = np.round(commsion,2)
        if self.balance < order_value and order_type=='short sell':
            if self.verbose:
                print(f"current close = {self.current_close}, balance is not enough, fail to execute {order_type} order.")
        else:
            if order_type=='sell' or order_type=='sell stop' : 
                self.balance += self.order_value - commsion
                self._balance += self.order_value - commsion
                
                if self.sell_stop_partial:
                    self.profit = (self.order_value - commsion) - (self.rm_order_value + self.rm_order_value * commsion_ratio)            
                    self._profit.append(self.profit)
                    self.sell_stop_partial = False
                    self._delete_rm_info()
                
                else: 
                    total_profit = self.balance - self.init_balance
                    self.profit = total_profit - self._total_profit[-1] - sum(self._profit)
                    self._total_profit.append(total_profit)
                    self.profit = np.round(self.profit,2)
                    self._profit = [] 
                    self._reset_rm_info()

            elif order_type=='short sell':
                self._update_rm_info(order_type,units)
                self.balance -= (self.order_value + commsion)
                self._balance += self.order_value - commsion

            self.balance = np.round(self.balance,2)
            self._balance = np.round(self._balance,2)
            self.profit = np.round(self.profit,2)
            self.units = units
            self.num_units -= self.units
            self.num_trades += 1
            self.num_buy_orders += 1

            self._update_order_info(order_type) 
            
            
            if self.verbose:
                print({'ts':self.current_time,'order type':order_type,
                                                    'order price (bid)': self.order_price,             
                                                    'total units':self.num_units,
                                                    'order units':self.units,                                                  
                                                    'order value': self.order_value,
                                                    'sl':self.sl,
                                                    'sp':self.sp,
                                                    'balance':self.balance,
                                                    'profit':self.profit,                                                    
                                                    })
            else:
                print({'ts':self.current_time,'order type':order_type,
                                                    'order price (bid)': self.order_price,             
                                                    'balance':self.balance,
                                                    'profit':self.profit,                                                    
                                                    })
    def close_trade(self):
        pass

#===================================================================================
# updata info modules
#===================================================================================
    def _update_order_info(self,order_type:str):
        self.order_info.append({'ts':self.current_time,'order type':order_type,
                                                    'order price': self.order_price,             
                                                    'total units':self.num_units,
                                                    'order units':self.units,                                                  
                                                    'order value': self.order_value,
                                                    'sl':self.sl,
                                                    'sp':self.sp,
                                                    'balance':self.balance,
                                                    'profit':self.profit, 

                                                })
    def show_order_info(self):
        order_info_df = self.order_info.copy()
        order_info_df = pd.DataFrame(order_info_df)
        order_info_df.set_index('ts',inplace=True)
        print(tabulate(order_info_df,headers=order_info_df.columns, tablefmt='pretty'))
        return order_info_df

    def _update_rm_info(self,order_type:str,units:int):
        self.rm_info.append({'ts':self.current_time,'order type':order_type,'order price': self.order_price,'units':units,'sl':self.sl,'sp':self.sp})
        
    def _delete_rm_info(self):
        self.rm_info = self.rm_info[1:]

    def _reset_rm_info(self):
        self.rm_info = []
   
    def show_rm_info(self):
        if self.rm_info:
            rm_info_df = self.rm_info.copy()
            rm_info_df = pd.DataFrame(rm_info_df)
            rm_info_df.set_index('ts',inplace=True)
            print(tabulate(rm_info_df,headers=rm_info_df.columns, tablefmt='pretty'))
            return rm_info_df
        else:
            rm_info_df = pd.DataFrame(columns = ['ts','order type','order price','units','sl','sp'])
            print(tabulate(rm_info_df,headers=rm_info_df.columns, tablefmt='pretty'))            
            return rm_info_df
#===================================================================================
# set up modules (set up data, set up account, set up trade)
#===================================================================================
    def set_up_trade_info(self):
        #----------------------------------------
        # order related info  
        #----------------------------------------  
        self.order_info = []
        self.rm_info = []
        self.num_buy_orders = 0
        self.num_sell_orders = 0
        self.num_trades = 0
        #----------------------------------------
        # position related info 
        #----------------------------------------
        self._total_profit = [0] 
        self._profit = []
        self.num_units = 0 # total positions outstanding
        #----------------------------------------
        # price related info 
        #----------------------------------------
        self.min_price = 0
        self.mox_price = 0
        print(' |------------------------------------------------------------------------|')
        print(' | trade info initiated |                                                 |')
        print(' |------------------------------------------------------------------------|')
        print(f' - short selling = {self.short_selling}')
        print(f' - additional arders = {self.additional_orders}')
        print(f' - order information = {self.order_info}')
        print(f' - risk management information = {self.rm_info}')
        print(f' - number of buy orders = {self.num_buy_orders}')
        print(f' - number of sell orders = {self.num_sell_orders}')
        print(f' - total number of trades =  {self.num_trades}')
        print(f' - current position =  {self.num_units}')

    def set_up_data(self, data_type:str, symbol:str, hist_start:str, 
            hist_end:str=datetime.datetime.now().strftime('%Y-%m-%d'), stream_data:str='simulate',
            after_market_data:bool=False,freq:str=None,
            stream_time_gap:int=None, verbose:bool=False)->Text:
        
        if stream_data not in ['stimulate','hist','real']:
            raise TypeError("stream_data must be 'stimulate','hist','real'.")

        # get latest price from historical data 
        self.stockdata._get_hist_oneminute_kbar(data_type, symbol, hist_start, hist_end) 

        # get historical dataframe (|ts|Open|Volume|High|Close|Low|)
        self.hist_df = self.stockdata._clean_up_data(freq,after_market_data)
        # set up parameters
        self.data_type = data_type
        self.symbol = symbol
        self.hist_start = hist_start
        self.stream_data = stream_data
        self.greq = freq
        self.stream_time_gap = stream_time_gap # seconds
        self.verbose = verbose
        if stream_data == 'real':
            indicator_df = self.hist_df
            self.indicator_df = indicator_df.to_dict('records')
        elif stream_data == 'hist':
            self.indicator_df = []

        print(' |------------------------------------------------------------------------|')
        print(' | data setted |                                                          |')
        print(' |------------------------------------------------------------------------|')
        print(f' - data type = {data_type}, symble = {symbol}')
        print(f' - historical data started from {hist_start} to {self.stockdata.hist_end}')
        print(f' - streaming data mode = {stream_data}')
        print(f' - streaming time gap = {stream_time_gap} seconds')
        
    def set_up_account(self,init_balance:int,account_type:str='demo'):
        
        if account_type in ['real','demo']:
            self.account_type = account_type
            self.init_balance = init_balance # keep track of profit
            self._balance = init_balance # keep track of short sell balance
            self.balance = init_balance
        else: 
            print("you didn't specify account params properly, set up failed")


        print(' |------------------------------------------------------------------------|')        
        print(' | current account status |                                               |') 
        print(' |------------------------------------------------------------------------|')
        print(f' - account type = {self.account_type}')
        print(f' - account balance = {self.balance}')

    def get_simulated_market(self):
        if self.stream_data == 'simulate':
            current_time, simulated_close, simulated_bid, simulated_ask = self.stockdata.get_simulated_stream()
            
            self.current_time = current_time
            self.current_close = simulated_close
            self.current_bid = simulated_bid
            self.current_ask = simulated_ask

            return current_time, simulated_close
        else:
            raise TypeError("to use stimulated streaming data, set stream_data = 'stimulate'")
        


    def get_hist_market(self):
        if self.stream_data == 'hist':
            tem = self.stockdata.get_hist_stream(self.hist_df)
            
            for _, data in tem.T.iteritems():
                hist_time, hist_vol = data.iloc[:2]
                hist_open, hist_high, hist_low, hist_close, simulated_hist_bid, simulated_hist_ask = data.iloc[2:].astype('float').round(2)
                hist_close = np.round(hist_close,2)

                self.current_time = hist_time
                self.current_close = hist_close
                self.current_bid = simulated_hist_bid
                self.current_ask = simulated_hist_ask
                
                self.current_open = hist_open
                self.current_high = hist_high
                self.current_low = hist_low
                self.current_vol = hist_vol

                self.indicator_df.append({'Open':self.current_open, 'High':self.current_high,'Low':self.current_low,'Close':self.current_close,'Volume':self.current_vol})

                yield hist_time, hist_close
                

        else:
            raise TypeError("to use histrical streaming data, set stream_data = 'hist'") 
    
    def get_real_market(self):
        data_dict = self.stockdata.get_real_stream(data_type = self.data_type,symbol=self.symbol)

        self.current_time = pd.to_datetime(data_dict['ts'])
        self.current_close = data_dict['close']
        self.current_bid = data_dict['buy_price']
        self.current_ask = data_dict['sell_price']

        self.current_open = data_dict['open']
        self.current_high = data_dict['high']
        self.current_low = data_dict['low']
        self.current_vol = data_dict['volume']

        self.indicator_df.append({'Open':self.current_open, 'High':self.current_high,'Low':self.current_low,'Close':self.current_close,'Volume':self.current_vol})

        return self.current_time, self.current_close

    def add_indicator(self,indicator:str,*args,**kargs)->List:
        if self.stream_data in ['real','hist']:
            indicator_df = pd.DataFrame(self.indicator_df)
            current_indicator = getattr(self.indi,indicator)(indicator_df,*args,**kargs)
            current_indicator = [_.round(2) for _ in current_indicator]
            return current_indicator
        else:
            raise TypeError("add_indicator method is only available under stream_data = 'real' or 'hist'") 

    # def add_indicator(self,indicator:str,*args,**kargs):
    #     self.indicator_df.append({'Open':self.current_open, 'High':self.current_high,'Low':self.current_low,'Close':self.current_close,'Volume':self.current_vol})
    #     indicator_df = pd.DataFrame(self.indicator_df)
    #     current_indicator = getattr(self.indi,indicator)(indicator_df,*args,**kargs)
    #     if all([pd.isna(_.iloc[-1]) for _ in current_indicator]) is not True:
    #         return [round(_.iloc[-1],2) for _ in current_indicator]
    #     else:
    #         return current_indicator