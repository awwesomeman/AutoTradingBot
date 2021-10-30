
import time
from trade import Trade

streaming_freq = 1 # 60 seconds
new_trade = Trade()
new_trade.set_up_trade_info()
new_trade.set_up_data('stock','2330','2021-01-01',
                        stream_data='hist',stream_time_gap=0)
new_trade.set_up_account(init_balance=1000000,account_type='demo')


for data in new_trade.get_hist_market('60min'):

    ts,close,*_= data

    if close <= 600:
        new_trade.place_buy_order(units=1000)
    if close > 600:
        new_trade.place_sell_order(units=1000)

print('finish')