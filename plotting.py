
# real time plot reference
# keep only new values https://makersportal.com/blog/2018/8/14/real-time-graphing-in-python
# Corey Schafer https://www.youtube.com/watch?v=Ercd-Ip5PfQ&list=PL-osiE80TeTvipOqomVEeZ1HRrcEvtZB_&index=9&ab_channel=CoreySchafer
# https://www.youtube.com/watch?v=GIywmJbGH-8&t=406s&ab_channel=IndianPythonista
# https://www.youtube.com/watch?v=O1ApWe_KIMM&list=PLQVvvaa0QuDcR-u9O8LyLR7URiKuW-XZq&index=31&ab_channel=sentdex
# ax, fig https://vimsky.com/zh-tw/examples/usage/matplotlib-axes-axes-axhline-in-python.html
import matplotlib.pyplot as plt
from matplotlib.animation import  FuncAnimation
import pandas as pd
import time
from datetime import datetime

from trade_data import StockData


"""

fig = plt.figure()
ax1 = fig.add_subplot(1,1,1)

def animate(i):
    x = []
    y=[]
    start = 0
    for _ in range(15):
        x.append(start)
        y.append(get_stram_data('TXF202110')['buy_price'])
        start+=1
        time.sleep(2)
    
    ax1.clear()
    ax1.plot(x,y)


ani = animation.FuncAnimation(fig,animate,interval=3000)    
plt.show()

#print(get_stram_data('TXF202110'))
"""



'''def animation(i,symble):
    x.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    y.append(data._get_simulated_close('stock',symble,'2021-09-16'))
    
    plt.cla()
    plt.title(symble)
    plt.plot(x,y)
    time.sleep(1)
ani = FuncAnimation(plt.gcf(),animation, fargs=('2330',),interval=1000)
plt.tight_layout()
plt.show()'''
fig, ax = plt.subplots()
data= StockData()
symble='2330'
date=[]
close=[]
bid=[]
ask=[]
data._get_hist_close('stock',symble,'2021-09-16')
def animation(i,symble):

    t, c,b,a = data._get_simulated_close()

    date.append(t)
    close.append(c)
    bid.append(b)
    ask.append(a)
    
    plt.cla()
    plt.title(symble)
    ax.plot_date(date, close, marker='', linestyle='-',color='blue',label='close')
    ax.plot_date(date, bid, marker='', linestyle='--',color='green',label='bid')
    ax.plot_date(date, ask, marker='', linestyle='--',color='olive',label='ask')
    ax.legend(loc= 'upper left',ncol=3)
    # if y[-1] >= 605 and y[-2]<605:
    #     ax.axhline(605,linewidth=4, color='r')
    plt.xticks([date[0], date[-1]], rotation="horizontal")
    
    #fig.autofmt_xdate()

ani = FuncAnimation(plt.gcf(),animation, fargs=(symble,),interval=1000)
plt.tight_layout()
plt.show()