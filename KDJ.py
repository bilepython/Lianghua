# -*- coding: utf-8 -*-
'''
KDJ指标的中文名称又叫随机指标，最早起源于期货市场，由乔治·莱恩（George Lane）首创。随机指标KDJ最早是以KD指标的形式出现，而KD指标是在威廉指标的基础上发展起来的。
不过KD指标只判断股票的超买超卖的现象，在KDJ指标中则融合了移动平均线速度上的观念，形成比较准确的买卖信号依据。在实践中，K线与D线配合J线组成KDJ指标来使用。
KDJ指标在设计过程中主要是研究最高价、最低价和收盘价之间的关系，同时也融合了动量观念、强弱指标和移动平均线的一些优点。
因此，能够比较迅速、快捷、直观地研判行情，被广泛用于股市的中短期趋势分析，是期货和股票市场上最常用的技术分析工具。

随机指标KDJ是以最高价、最低价及收盘价为基本数据进行计算，得出的K值、D值和J值分别在指标的坐标上形成的一个点，连接无数个这样的点位，就形成一个完整的、能反映价格波动趋势的KDJ指标。
它主要是利用价格波动的真实波幅来反映价格走势的强弱和超买超卖现象，在价格尚未上升或下降之前发出买卖信号的一种技术工具。
它在设计过程中主要是研究最高价、最低价和收盘价之间的关系，同时也融合了动量观念、强弱指标和移动平均线的一些优点，因此，能够比较迅速、快捷、直观地研判行情。
由于KDJ线本质上是一个随机波动的观念，故其对于掌握中短期行情走势比较准确。
'''
import os
import pandas as pd

# ========== 遍历数据文件夹中所有股票文件的文件名，得到股票代码列表stock_code_list
stock_code_list = ['601318','002594','300309','000002','000860','601166']

'''
stock_code_list = []
for root, dirs, files in os.walk(r'E:\LHClass\stock_data'):# 注意：这里请填写数据文件在您电脑中的路径
    if files:
        for f in files:
            if '.csv' in f:
                stock_code_list.append(f.split('.csv')[0])
'''

# ========== 根据上一步得到的代码列表，遍历所有股票，将这些股票合并到一张表格all_stock中
all_stock = pd.DataFrame()

# 遍历每个创业板的股票
for code in stock_code_list:
    
    # 从csv文件中读取该股票数据
    stock_data = pd.read_csv('E:/LHClass/stock_data/' + code + '.csv',
                             parse_dates=[1])# 注意：这里请填写数据文件在您电脑中的路径
    stock_data.sort_values('date', inplace=True)# 对数据按照【date】交易日期从小到大排序

    # 计算KDJ指标
    low_list = pd.rolling_min(stock_data['low'], 9)
    low_list.fillna(value=pd.expanding_min(stock_data['low']), inplace=True)
    high_list = pd.rolling_max(stock_data['high'], 9)
    high_list.fillna(value=pd.expanding_max(stock_data['high']), inplace=True)
    rsv = (stock_data['close'] - low_list) / (high_list - low_list) * 100
    stock_data['KDJ_K'] = pd.ewma(rsv, com=2)
    stock_data['KDJ_D'] = pd.ewma(stock_data['KDJ_K'], com=2)
    stock_data['KDJ_J'] = 3 * stock_data['KDJ_K'] - 2 * stock_data['KDJ_D']
    # 计算KDJ指标金叉、死叉情况
    stock_data['KDJ_金叉死叉'] = ''
    kdj_position = stock_data['KDJ_K'] > stock_data['KDJ_D']
    stock_data.loc[kdj_position[(kdj_position == True) & (kdj_position.shift() == False)].index, 'KDJ_金叉死叉'] = '金叉'
    stock_data.loc[kdj_position[(kdj_position == False) & (kdj_position.shift() == True)].index, 'KDJ_金叉死叉'] = '死叉'
    stock_data.to_csv(r'E:\LHClass\Result_Data\{}_kdj.csv'.format(code), index=False, encoding='gbk')
    # 通过复权价格计算接下来几个交易日的收益率
    for n in [1, 2, 3, 5, 10, 20, 45]:
        stock_data['接下来'+str(n)+'个交易日涨跌幅'] = stock_data['close'].shift(-1*n) / stock_data['close'] - 1.0
    stock_data.dropna(how='any', inplace=True)# 删除所有有空值的数据行

    # 筛选出KDJ金叉的数据，并将这些数据合并到all_stock中
    stock_data = stock_data[(stock_data['KDJ_金叉死叉'] == '金叉')]
    if stock_data.empty:
        continue
    all_stock = all_stock.append(stock_data, ignore_index=True)

# ========== 根据上一步得到的所有股票KDJ金叉数据all_stock，统计这些股票在未来交易日中的收益情况
print
print '历史上所有股票出现KDJ金叉的次数为%d，这些股票在：' % all_stock.shape[0]
print

for n in [1, 2, 3, 5, 10, 20, 45]:
    print "金叉之后的%d个交易日内，" % n,
    print "平均涨幅为%.2f%%，" % (all_stock['接下来'+str(n)+'个交易日涨跌幅'].mean() * 100),
    print "其中上涨股票的比例是%.2f%%。" % \
          (all_stock[all_stock['接下来'+str(n)+'个交易日涨跌幅'] > 0].shape[0]/float(all_stock.shape[0]) * 100)
    print
