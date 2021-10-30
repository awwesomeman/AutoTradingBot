
import time
from trade import Trade

streaming_freq = 1 # 60 seconds
new_trade = Trade()
new_trade.set_up_trade_info()
new_trade.set_up_data('stock','2330','2021-09-16',simulated_data=True)
new_trade.set_up_account(init_balance=1000000,account_type='demo')


while True:
    
    current_time,simulated_close,*_=new_trade.get_market()

    if simulated_close <= 603:
        new_trade.place_buy_order(units=1000)
    if simulated_close >= 607:
        new_trade.place_sell_order(units=1000)

    if new_trade.num_trades == 2:
        break

    time.sleep(streaming_freq)