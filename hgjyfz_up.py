# -*- coding: utf-8 -*-
"""
Created on Wed Aug 16 11:32:42 2017

@author: Bile.Xu
"""

import pandas as pd

import tushare as ts
from datetime import datetime
from dateutil.parser import parse

#获取第一天及最近的日

stock_basics = ts.get_stock_basics()

end = datetime.today()
end = datetime.strftime(end,'%Y-%m-%d')
stock_list = ['sh601318','sz002594','sz000069','sz300512','sz000002','sz000860','sz399006']
output = pd.DataFrame()
#stock_list = ['300512']
for stock in stock_list:
    stock1= stock.strip('shz')
    if stock1.startswith('39'):
        start = '2010-06-02'
        index = True
    else:
        start = stock_basics.ix[stock1]['timeToMarket']
        start = parse(str(start))
        start = datetime.strftime(start,'%Y-%m-%d')
        index = False
    df = ts.get_k_data(code=stock1, start=start, end=end,index=index)
    df['change'] = df['close'].pct_change() 
    df.to_csv('E:/LHClass/stock_data/{}.csv'.format(stock1),encoding='gbk')

    # ==========导入上证指数的原始数据
    # 注意：这里请填写数据文件在您电脑中的路径，并注意路径中斜杠的方向

    index_data = pd.read_csv(r'E:\LHClass\stock_data\{}.csv'.format(stock1), parse_dates=['date'])
    # 保留这几个需要的字段：'date', 'high', 'low', 'close', 'change'
    index_data = index_data[['date', 'high', 'low', 'close', 'change','volume']]
    # 对数据按照【date】日期从小到大排序
    index_data.sort_values('date', inplace=True)


    # ==========计算海龟法则的买卖
    # 设定海龟法则的两个参数，当收盘价大于最近N1天的最高价时买入，当收盘价低于最近N2天的最低价时卖出
    # 这两个参数可以自行调整大小，但是一般N1 > N2
    N1 = 20
    N2 = 10
    
    # 通过rolling_max方法计算high_N1价
    index_data['price_sum'] =  pd.rolling_sum(index_data['close']*index_data['volume'],N1)
    index_data['price_sum'].fillna(value=pd.expanding_sum(index_data['close']*index_data['volume']), inplace=True)
    index_data['volume_sum'] = pd.rolling_sum(index_data['volume'],N1)
    index_data['volume_sum'].fillna(value=pd.expanding_sum(index_data['volume']), inplace=True)
    index_data['price_w'] =  index_data['price_sum']/index_data['volume_sum']
    
    # 对于上市不足N1天的数据，取上市至今的最高价
    index_data['high_N1'] = pd.rolling_max(index_data['high'], N1)
    index_data['high_N1'].fillna(value=pd.expanding_max(index_data['high']), inplace=True)
    
    # 通过相似的方法计算low_N2价
    index_data['low_N2'] =  pd.rolling_min(index_data['low'], N2)
    index_data['low_N2'].fillna(value=pd.expanding_min(index_data['low']), inplace=True)
    
    # 当当天的【close】> 昨天的【high_N1】时，将【signal】设定为1
    buy_index = index_data[index_data['close'] > index_data['high_N1'].shift(1)].index
    index_data.loc[buy_index, 'signal'] = 1
    # 当当天的【close】< 昨天的【low_N2】时，将【signal】设定为0
    sell_index = index_data[index_data['close'] < index_data['low_N2'].shift(1)].index
    index_data.loc[sell_index, 'signal'] = 0
    
    # 当当天的【close】> 昨天的【high_N1】时，还有成交量，将【signal】设定为1
    buy_index = index_data[index_data['close'] > index_data['price_w'].shift(1)].index
    index_data.loc[buy_index, 'signal1'] = 1
    # 当当天的【close】< 昨天的【low_N2】时，还有成交量，将【signal】设定为0
    sell_index = index_data[index_data['close'] < index_data['price_w'].shift(1)].index
    index_data.loc[sell_index, 'signal1'] = 0
                  
    # 计算每天的cw，当天持有上证指数时，cw为1，当天不持有上证指数时，cw为0
    index_data['position'] = index_data['signal'].shift(1)
    index_data['position'].fillna(method='ffill', inplace=True)
    # 计算每天的cw，当天持有上证指数时，cw为1，当天不持有上证指数时，cw为0
    index_data['position1'] = index_data['signal1'].shift(1)
    index_data['position1'].fillna(method='ffill', inplace=True)

    # 取1992年之后的数据，排出较早的数据

    index_data = index_data[index_data['date'] > pd.to_datetime(start)]
    # 当cw为1时，买入上证指数，当cw为0时，空仓。计算从上市至今的zjindex
    index_data['zjindex'] = (index_data['change'] * index_data['position'] + 1.0).cumprod()
    initial_idx = index_data.iloc[0]['close'] / (1 + index_data.iloc[0]['change'])
    index_data['zjindex'] *= initial_idx
    # 当cw为1时，买入上证指数，当cw为0时，空仓。计算从19920101至今的zjindex
    index_data['zjindex1'] = (index_data['change'] * index_data['position1'] + 1.0).cumprod()
    initial_idx = index_data.iloc[0]['close'] / (1 + index_data.iloc[0]['change'])
    index_data['zjindex1'] *= initial_idx
    # 输出数据到指定文件
    index_data[['date', 'high', 'low', 'close', 'volume','change', 'high_N1',
            'low_N2','price_w','signal','signal1', 'position', 'position1','zjindex', 'zjindex1']].to_csv(r'E:\LHClass\Result_Data\turtle_{}.csv'.format(stock), index=False, encoding='gbk')
   
    max_index = len(index_data)
    l = len(output)
    output.loc[l, 'code'] = stock
    output.loc[l, 'signal'] =index_data.loc[max_index,'signal']
    output.loc[l, 'signal1'] =index_data.loc[max_index,'signal1']
    output.loc[l, 'zjindex'] =index_data.loc[max_index,'zjindex']
    output.loc[l, 'zjindex1'] =index_data.loc[max_index,'zjindex1']
    output.to_csv(r'E:\LHClass\Result_Data\Signal_Stream.csv', index=False, encoding='gbk')
    # ==========计算每年指数的收益以及海龟法则的收益
    index_data['hg_change'] = index_data['change'] * index_data['position']
    
    index_data['hg_change1'] = index_data['change'] * index_data['position1']
    year_rtn = index_data.set_index('date')[['change', 'hg_change','hg_change1']].\
               resample('A', how=lambda x: (x+1.0).prod() - 1.0) * 100

    year_rtn.to_csv(r'E:\LHClass\Result_Data\{}_yeatr.csv'.format(stock), encoding='gbk')
