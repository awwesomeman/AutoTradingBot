# simple ma cross over strategy
new_trade = Trade(short_selling=False,additional_orders=False)
new_trade.set_up_trade_info()
new_trade.set_up_data('future','TXF202110','2021-09-27',stream_data='real',stream_time_gap=300)
new_trade.set_up_account(init_balance=1000000,account_type='demo')
streaming_freq = new_trade.stream_time_gap

while True:
   
    ts, close = new_trade.get_real_market()

    ma5 = new_trade.add_indicator('ma',5)[0]
    ma20 = new_trade.add_indicator('ma',20)[0]
    
    if len(ma5)>2 and len(ma20)>2:
        
        ma5_now = ma5.iloc[-2]
        ma5_last = ma5.iloc[-3]

        ma20_now = ma20.iloc[-2]
        ma20_last = ma20.iloc[-3]

        if ma5_now > ma20_now and ma5_last <= ma20_last:
            new_trade.place_buy_order(units=1000,sl=0.1,sp=0.1)
            
        
        if ma5_now < ma20_now and ma5_last >= ma20_last:
            new_trade.place_sell_order(units=1000,sl=0.1,sp=0.1)
            
        print(ts,close,'ma5now',ma5_now,'ma20now',ma20_now,'ma5last',ma5_last,'ma20last',ma20_last)





    time.sleep(streaming_freq)