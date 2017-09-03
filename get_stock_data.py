# -*- coding: utf-8 -*-
"""
Created on Sat Aug 12 09:05:30 2017

@author: Bile.Xu
"""
import os
from pandas import Series
import pandas as pd
import tushare as ts
from datetime import datetime
from dateutil.parser import parse

end = datetime.today()
end = datetime.strftime(end,'%Y-%m-%d')

#获取沪深上市公司基本情况(已剔除掉退市的)
df = ts.get_stock_basics()
#已上市10年以上的
df = df[(df['timeToMarket']>0) & (df['timeToMarket']<20070731)]
df.to_csv('E:/LHClass/all.csv',encoding='gbk')
#获取所有股票代码列表
#df = pd.read_csv(r'C:\Users\xiaobiao_xu\Desktop\LHClass\all.csv')
temp = df.reset_index()
all_code=list(temp['code'])

'''alllist=[]
for code in allcode:
        code = str('0')*(6-len(str(code)))+str(code)
        alllist.append(code)
#alllist1=Series(alllist)
#alllist1.to_csv('C:/Users/xiaobiao_xu/Desktop/LHClass/stock_data/alllist.csv'.format(code),encoding='gbk')
#已经同步数据的股票

Root = r'C:\Users\xiaobiao_xu\Desktop\LHClass\stock_data'
stockcode=[]
for (root, dirs, files) in os.walk(Root):
     for f in files:
       stockcode.append(str(os.path.splitext(f)[0]))
#stocklist=Series(stockcode)
#stocklist.to_csv('C:/Users/xiaobiao_xu/Desktop/LHClass/stock_data/stocklist.csv'.format(code),encoding='gbk')
'''       
#同步股票日交易数据
for code in all_code:
       start = df.ix[code]['timeToMarket']
       start = parse(str(start))
       start = datetime.strftime(start,'%Y-%m-%d')
       stock_data = ts.get_k_data(code=code, start=start, end=end)
       stock_data['change'] = stock_data['close'].pct_change(-1)
       stock_data.dropna(inplace=True)
       stock_data.to_csv('E:/LHClass/stock_data/{}.csv'.format(code),encoding='gbk')
              
                             