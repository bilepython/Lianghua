# coding=utf-8

from __future__ import division

import os
import pandas as pd
import warnings

warnings.filterwarnings("ignore")


# 计算FQ格
def cal_right_price(input_stock_data, type='qfq'):
    """
    :param input_stock_data: 标准股票数据，需要'收盘价', '涨跌幅'
    :param type: 确定是qfq还是hfq，分别为'hfq'，'qfq'
    :return: 新增一列'hfq价'/'qfq价'的stock_data
    """
    # 计算收盘FQ
    stock_data = input_stock_data.copy()
    
    num = {'hfq': 0, 'qfq': -1}
    price1 = stock_data['close'].iloc[num[type]]
    stock_data['FQ_temp'] = (stock_data['change'] + 1.0).cumprod()
    price2 = stock_data['FQ_temp'].iloc[num[type]]
    stock_data['FQ'] = stock_data['FQ_temp'] * (price1 / price2)
    stock_data.pop('FQ_temp')

    # 计算openFQ
    stock_data['FQ_open'] = stock_data['FQ'] / (stock_data['close'] / stock_data['open'])
    stock_data['FQ_high'] = stock_data['FQ'] / (stock_data['close'] / stock_data['high'])
    stock_data['FQ_low'] = stock_data['FQ'] / (stock_data['close'] / stock_data['low'])

    return stock_data[['FQ_open', 'FQ', 'FQ_high', 'FQ_low']]


# 获取指定股票对应的数据并按日期升序排序
def get_stock_data(stock_code):
    """
    :param stock_code: code
    :return: 返回数据集（code，date，open，close，change）
    """
    # 此处为存放csv文件的本地路径，请自行改正地址
    stock_data = pd.read_csv('E:/LHClass/stock_data/' + str(stock_code) + '.csv', parse_dates=['date'], index_col='date')
    stock_data.dropna(inplace=True)
    stock_data = stock_data[['open', 'close', 'high', 'low', 'change']]
    stock_data['code'] = stock_code
    stock_data.sort_index(inplace=True)
    
    # 计算FQ
    stock_data[['open', 'close', 'high', 'low']] = cal_right_price(stock_data, type='hfq')

    stock_data = stock_data['2005-01-01':]

    return stock_data


# 计算+DI和-DI指标并得到信号和仓位
def adx(stock_data, n=14):

    df = stock_data.copy()

    # 计算HD和LD值
    df['hd'] = df['high'] - df['high'].shift(1)
    df['ld'] = df['low'].shift(1) - df['low']

    # 计算TR值
    df['t1'] = df['high'] - df['low']
    df['t2'] = abs(df['high'] - df['close'].shift(1))
    df.ix[df['t1'] >= df['t2'], 'temp1'] = df['t1']
    df.ix[df['t1'] < df['t2'], 'temp1'] = df['t2']

    df['temp2'] = abs(df['low'] - df['close'].shift(1))

    df.ix[df['temp1'] >= df['temp2'], 'temp'] = df['temp1']
    df.ix[df['temp1'] < df['temp2'], 'temp'] = df['temp2']

    df.dropna(inplace=True)

    df['tr'] = pd.rolling_sum(df['temp'], n)

    df.ix[(df['hd'] > 0) & (df['hd'] > df['ld']), 'hd1'] = df['hd']
    df['hd1'].fillna(0, inplace=True)

    df.ix[(df['ld'] > 0) & (df['ld'] > df['hd']), 'ld1'] = df['ld']
    df['ld1'].fillna(0, inplace=True)

    df['dmp'] = pd.rolling_sum(df['hd1'], n)
    df['dmm'] = pd.rolling_sum(df['ld1'], n)

    df['pdi'] = df['dmp'] / df['tr'] * 100
    df['mdi'] = df['dmm'] / df['tr'] * 100
    df.dropna(inplace=True)

    # 当+DI上穿-DI，买入，信号为1
    df.ix[df['pdi'] > df['mdi'], 'signal'] = 1
    # 当+DI下穿-DI，卖空，信号为-1
    df.ix[df['pdi'] < df['mdi'], 'signal'] = -1

    df['signal'].fillna(method='ffill', inplace=True)

    # =====计算每天的仓位
    df.ix[0, 'position'] = 0
    # 出现买入信号而且第二天open没有涨停
    df.ix[(df['signal'].shift(1) == 1) & (df['open'] < df['close'].shift(1) * 1.097), 'position'] = 1
    # 出现卖出信号而且第二天open没有跌停
    df.ix[(df['signal'].shift(1) == -1) & (df['open'] > df['close'].shift(1) * 0.903), 'position'] = 0

    df['position'].fillna(method='ffill', inplace=True)

    return df


# 根据每日仓位计算总资产的日收益率
def account(df, slippage=1.0 / 1000, commision_rate=1.0 / 1000):
    """
    :param df: 账户数据集
    :param slippage: 买卖滑点 默认为1.0 / 1000
    :param commision_rate: 手续费 默认为2.0 / 1000
    :return: 返回账户资产的日收益率和日累计收益率的数据集
    """
    df.ix[0, 'capital_rtn'] = 0
    # 当加仓时,计算当天资金曲线涨幅capital_rtn.capital_rtn = 昨天的position在今天涨幅 + 今天open新买入的position在今天的涨幅(扣除手续费)
    df.ix[df['position'] > df['position'].shift(1), 'capital_rtn'] = (df['close'] / df['open'] - 1) * (
        1 - slippage - commision_rate) * (df['position'] - df['position'].shift(1)) + df['change'] * df[
        'position'].shift(1)
    # 当减仓时,计算当天资金曲线涨幅capital_rtn.capital_rtn = 今天open卖出的positipn在今天的涨幅(扣除手续费) + 还剩的position在今天的涨幅
    df.ix[df['position'] < df['position'].shift(1), 'capital_rtn'] = (df['open'] / df['close'].shift(1) - 1) * (
        1 - slippage - commision_rate) * (df['position'].shift(1) - df['position']) + df['change'] * df['position']
    # 当仓位不变时,当天的capital_rtn是当天的change * position
    df.ix[df['position'] == df['position'].shift(1), 'capital_rtn'] = df['change'] * df['position']

    return df


# 计算年化收益率函数
def annual_return(date_line, capital_line):
    """
    :param date_line: 日期序列
    :param capital_line: 账户价值序列
    :return: 输出在回测期间的年化收益率
    """
    # 将数据序列合并成dataframe并按日期排序
    df = pd.DataFrame({'date': date_line, 'capital': capital_line})

    # 计算年化收益率
    annual = (df['capital'].iloc[-1] / df['capital'].iloc[0]) ** (250 / len(df)) - 1

    return annual


# 计算最大回撤函数
def max_drawdown(date_line, capital_line):
    """
    :param date_line: 日期序列
    :param capital_line: 账户价值序列
    :return: 输出最大回撤及开始日期和结束日期
    """
    # 将数据序列合并为一个dataframe并按日期排序
    df = pd.DataFrame({'date': date_line, 'capital': capital_line})

    df['max2here'] = pd.expanding_max(df['capital'])  # 计算当日之前的账户最大价值
    df['dd2here'] = df['capital'] / df['max2here'] - 1  # 计算当日的回撤
    #  计算最大回撤和结束时间
    temp = df.sort_values(by='dd2here').iloc[0][['date', 'dd2here']]
    max_dd = temp['dd2here']

    return max_dd


# 遍历数据文件夹中所有股票文件的文件名，得到股票代码列表
stock_code_list = ['601318','002594','000069','300309','000002','000860','601166']
# 此处为股票数据文件的本地路径，请自行修改
'''
for root, dirs, files in os.walk('E:/LHClass/stock_data'):
    if files:
        for f in files:
            if '.csv' in f:
                stock_code_list.append(f.split('.csv')[0])
'''

for code in stock_code_list:

    stock_data = get_stock_data(code)

    # 剔除上市不到1年半的股票
    if len(stock_data) < 360:
        continue

    re = pd.DataFrame(columns=['code', 'start', 'param', 'stock_rtn', 'stock_md', 'strategy_rtn',
                               'strategy_md', 'excessive_rtn'])
    i = 0

    for p in range(10, 31, 2):

        df = adx(stock_data, n=p)
        # 计算策略每天涨幅
        df = account(df)
        # 计算资金曲线
        df['capital'] = (df['capital_rtn'] + 1).cumprod()

        # =====根据资金曲线,计算相关评价指标
        df = df['2006-01-01':]
        date_line = list(df.index)
        capital_line = list(df['capital'])
        stock_line = list(df['close'])
        # 股票的年化收益
        stock_rtn = annual_return(date_line, stock_line)
        # 策略的年化收益
        strategy_rtn = annual_return(date_line, capital_line)
        # 股票最大回撤
        stock_md = max_drawdown(date_line, stock_line)
        # 策略最大回撤
        strategy_md = max_drawdown(date_line, capital_line)

        re.loc[i, 'code'] = df['code'].iloc[0]
        re.loc[i, 'start'] = df.index[0].strftime('%Y-%m-%d')
        re.loc[i, 'param'] = p
        re.loc[i, 'stock_rtn'] = stock_rtn
        re.loc[i, 'stock_md'] = stock_md
        re.loc[i, 'strategy_rtn'] = strategy_rtn
        re.loc[i, 'strategy_md'] = strategy_md
        re.loc[i, 'excessive_rtn'] = strategy_rtn - stock_rtn

        i += 1

    re.sort_values(by='excessive_rtn', ascending=False, inplace=True)

    re.iloc[0:1, :].to_csv('E:/LHClass/Result_Data/results5.csv', mode='a',header=None, index=False)
