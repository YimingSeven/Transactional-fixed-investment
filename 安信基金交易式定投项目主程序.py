# -*- coding: utf-8 -*-
"""
Pycharm Editor: Mr.seven
This is a temporary script file.

此脚本，将交易式定投只分成3份，每个月第一个交易日进行投资


"""
import copy

import pandas as pd
import datetime
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import os
from tftip_function import make_capital_list, make_price_list, judge_fix_invest_date_in_trading, interval_point_func

# 当列太多时不换行
pd.set_option('expand_frame_repr', False)
# 设定显示最大的行数
pd.set_option("display.max_rows", 3000)

sns.set(color_codes=True)
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 寻找当前文件所在的文件路径, 并将所在文件路径字符反转 避免麻烦
file_path = os.path.abspath('.')
file_path_inver_sys = file_path.replace('\\', '/')

# 导入指数的数据
fund_npv = pd.read_excel(file_path_inver_sys + '/input_data/交易式定投-价值精选.xlsx', index_col=0, parse_dates=True, encoding='gbk')
hs_300 = pd.read_excel(file_path_inver_sys + '/input_data/hs300_use_fund.xlsx', index_col=0, parse_dates=True, encoding='gbk')
zz_stock_index = pd.read_excel(file_path_inver_sys + '/input_data/中证全指_pe.xlsx', index_col=0, parse_dates=True, encoding='gbk')

# 为中证全指计算PE TTM 在过去10年中的百分位值
zz_stock_index_percent = \
    zz_stock_index.rolling(window=2520, min_periods=1).apply(
        lambda x: pd.Series(x).rank(pct=True, ascending=True).iloc[-1])

# 设置投资者的初始风险厌恶，最低的指数点数
smallest_index_num = 2500

# 总资金数量
all_capital = 100000

# 赚取百分之几时，离场 10%
earning_n_percent = 0.10

# 分成了几份 3份，分成2.5万，2.5万，5万
constant_n_part_ = 8

# pe的上下分位点
down_point = 0.25
up_point = 0.75

# 每月定投的日期
every_month_invest_date = 1

# 所有的交易日期
all_trading_date = fund_npv.index.tolist()


# 初始化一个frame存放，仓位和资金情况
portfolio_resume = pd.DataFrame(np.zeros((len(all_trading_date), 4)), index=all_trading_date,
                                columns=['持仓数量', '已投资产', '未投资产', '建仓资产价格'])

# 初始化一个小指针变量，用于判断这新的开仓的回合，有几次昨日的收盘价大于了前一日的收盘价
tin_ = 777
# 初始化一个新的指针变量，用于记录上一次价格所位于的区间
last_time_price_zone = 777

# 定义一个list 存放每次开仓和平仓的日期
open_close_position_date = []
# 遍历
for i in range(1, len(all_trading_date)):
    # 当前的日期
    now_date = all_trading_date[i]
    # print(now_date)
    # 昨天的日期
    yesterday = all_trading_date[i - 1]
    # 判断本月的交易日中是否有常规的定投日期，若有则跳过，若无，则将定投日期向后推x日，直至存在交易日期list中
    every_month_invest_date_use = \
        judge_fix_invest_date_in_trading(this_year=now_date.year, this_month=now_date.month,
                                         default_fix_date=every_month_invest_date, trading_list=all_trading_date)
    # 取出当前交易日对应的PE(TTM)
    this_month_pe = zz_stock_index_percent.loc[yesterday, 'PE(TTM)']
    # 判断当前交易日的 估值分位是否大于75%，若大于75%则平仓
    if (this_month_pe > up_point) & (now_date.day == every_month_invest_date_use):
        # 计算当前组合中资产价值的情况，所处时点为 本日初，上日末的时点
        now_portfolio_fund = fund_npv.loc[yesterday, '收盘价'] * portfolio_resume.loc[yesterday, '持仓数量']
        # 若昨天组合资产价值超过已投资产的10%，则以今天的收盘价平仓，并开设新仓位，用第一部分资金去买入
        all_capital = now_portfolio_fund + portfolio_resume.loc[yesterday, '未投资产']
        # 判断上一日如果有仓位则平仓
        if portfolio_resume.loc[yesterday, '持仓数量'] != 0:
            portfolio_resume.loc[now_date, '持仓数量'] = 0
            portfolio_resume.loc[now_date, '已投资产'] = 0
            portfolio_resume.loc[now_date, '未投资产'] = all_capital
            portfolio_resume.loc[now_date, '建仓资产价格'] = fund_npv.loc[yesterday, '收盘价']
            # 记录买入的时点日期
            buy_in_date = now_date
            open_close_position_date.append(buy_in_date)
            print(buy_in_date)
            print('*************************')
            # 初始化一个新的指针变量，用于记录上一次价格所位于的区间
            last_time_price_zone = 777
        # 如果上一日没有仓位则，保持空仓 和 未投资产不变
        else:
            portfolio_resume.loc[now_date, '持仓数量'] = portfolio_resume.loc[yesterday, '持仓数量']
            portfolio_resume.loc[now_date, '已投资产'] = portfolio_resume.loc[yesterday, '已投资产']
            portfolio_resume.loc[now_date, '未投资产'] = portfolio_resume.loc[yesterday, '未投资产']
            portfolio_resume.loc[now_date, '建仓资产价格'] = fund_npv.loc[yesterday, '收盘价']
    # 若低于75%，则判断是否大于or小于25%, 若小于25%且有仓位则加满仓，若无仓位则立即满仓
    elif (this_month_pe < down_point) & (now_date.day == every_month_invest_date_use):
        # 判断当前（昨天）是否有仓位
        if portfolio_resume.loc[yesterday, '持仓数量'] != 0:
            # 计算 使用的资金，为余下的所有资金
            use_money = portfolio_resume.loc[yesterday, '未投资产']
            #
            portfolio_resume.loc[now_date, '持仓数量'] = \
                (use_money / fund_npv.loc[yesterday, '收盘价']) + portfolio_resume.loc[yesterday, '持仓数量']
            portfolio_resume.loc[now_date, '已投资产'] = portfolio_resume.loc[yesterday, '已投资产'] + use_money
            portfolio_resume.loc[now_date, '未投资产'] = all_capital - portfolio_resume.loc[now_date, '已投资产']
            portfolio_resume.loc[now_date, '建仓资产价格'] = fund_npv.loc[yesterday, '收盘价']
            # 将本次使用完的资金对应位置赋值成0
            for ii in range(this_use_money_nmu + 1, len(use_money_list)):
                use_money_list[ii] = 0
            # 记录买入的时点日期
            buy_in_date = now_date
            # 记录使用的资金是第几份
            this_use_money_nmu = len(use_money_list)
            # 将本次的价格所在区间的位置信息记录
            last_time_price_zone = 777
        # 如果当前无仓位，从 0 开始建仓，则直接满仓
        else:
            # 计算期初的 资本划分的list
            use_money_list = make_capital_list(this_time_all_capital=all_capital, constant_n_part_temp=constant_n_part_)
            # 计算期初 中间价位的list
            median_price_list, lowest_median_price = make_price_list(now_price=hs_300.loc[yesterday, '收盘价'],
                                                                     constant_n_part_temp=constant_n_part_,
                                                                     smallest_index_num_temp=smallest_index_num)

            # 计算 使用的资金
            portfolio_resume.loc[now_date, '持仓数量'] = all_capital / fund_npv.loc[yesterday, '收盘价']
            portfolio_resume.loc[now_date, '已投资产'] = all_capital
            portfolio_resume.loc[now_date, '未投资产'] = 0
            portfolio_resume.loc[now_date, '建仓资产价格'] = fund_npv.loc[yesterday, '收盘价']
            # 记录买入的时点日期
            buy_in_date = now_date
            open_close_position_date.append(buy_in_date)
            print(buy_in_date)
            print('.........................')
            # 记录使用的资金是第几份
            this_use_money_nmu = len(use_money_list)
            # 将本次使用完的资金对应位置赋值成0
            for ii in range(len(use_money_list)):
                use_money_list[ii] = 0
            # 将本次的价格所在区间的位置信息记录
            last_time_price_zone = 777

    # 若估值在25%至75%之间，则使用交易式定投进行运作
    else:
        # 判断当前资产组合中是否有仓位
        if (portfolio_resume.loc[yesterday, '已投资产'] == 0) & (now_date.day == every_month_invest_date_use):
            # 计算期初的 资本划分的list
            use_money_list = make_capital_list(this_time_all_capital=all_capital, constant_n_part_temp=constant_n_part_)
            # 若是每月的18号，则用 应该使用的额度计算买入的持仓数量
            portfolio_resume.loc[now_date, '持仓数量'] = use_money_list[0] / fund_npv.loc[yesterday, '收盘价']
            portfolio_resume.loc[now_date, '已投资产'] = use_money_list[0]
            portfolio_resume.loc[now_date, '未投资产'] = all_capital - use_money_list[0]
            portfolio_resume.loc[now_date, '建仓资产价格'] = fund_npv.loc[yesterday, '收盘价']
            # 计算期初 中间价位的list
            median_price_list, lowest_median_price = make_price_list(now_price=hs_300.loc[yesterday, '收盘价'],
                                                                     constant_n_part_temp=constant_n_part_,
                                                                     smallest_index_num_temp=smallest_index_num)
            #
            # 记录买入的时点日期
            buy_in_date = now_date
            open_close_position_date.append(buy_in_date)
            print(buy_in_date)
            print('.........................')
            # 对资金的标记减一
            # n_part_ = constant_n_part_ - 1
            # 记录使用的资金是第几份
            this_use_money_nmu = 0
            # 将本次使用完的资金对应位置赋值成0
            use_money_list[this_use_money_nmu] = 0

        # 如果资产组合中已经存在了仓位
        else:
            # 判断当前时点是否为 1号
            if now_date.day == every_month_invest_date_use:
                # 计算当前组合中资产价值的情况，所处时点为 本日初，上日末的时点
                now_portfolio_fund = fund_npv.loc[yesterday, '收盘价'] * portfolio_resume.loc[yesterday, '持仓数量']
                # 判断今日初始时点，组合中的资产价值是否大于已投入资产的 10%
                if now_portfolio_fund >= portfolio_resume.loc[yesterday, '已投资产'] * (1 + earning_n_percent):
                    # 若昨天组合资产价值超过已投资产的10%，则以今天的收盘价平仓，并开设新仓位，用第一部分资金去买入
                    all_capital = now_portfolio_fund + portfolio_resume.loc[yesterday, '未投资产']
                    # 并重置资金的标记
                    # n_part_ = constant_n_part_
                    # 平仓后重新设置资金份额列表
                    use_money_list = make_capital_list(this_time_all_capital=all_capital,
                                                       constant_n_part_temp=constant_n_part_)

                    # 储存当日的持仓数量、以投资和为投资的资产值
                    portfolio_resume.loc[now_date, '持仓数量'] = use_money_list[0] / fund_npv.loc[yesterday, '收盘价']
                    portfolio_resume.loc[now_date, '已投资产'] = use_money_list[0]
                    portfolio_resume.loc[now_date, '未投资产'] = all_capital - use_money_list[0]
                    portfolio_resume.loc[now_date, '建仓资产价格'] = fund_npv.loc[yesterday, '收盘价']

                    # 计算平仓后，重新开仓 中间价位的list
                    median_price_list, lowest_median_price = make_price_list(now_price=hs_300.loc[yesterday, '收盘价'],
                                                                             constant_n_part_temp=constant_n_part_,
                                                                             smallest_index_num_temp=smallest_index_num)

                    # 对资金的标记减一
                    # n_part_ -= 1
                    # 记录买入的时点日期
                    buy_in_date = now_date
                    open_close_position_date.append(buy_in_date)
                    print(buy_in_date)
                    print('*************************')
                    # 初始化一个新的指针变量，用于记录上一次价格所位于的区间
                    last_time_price_zone = 777
                    # 记录使用的资金是第几份
                    this_use_money_nmu = 0
                    # 将本次使用完的资金对应位置赋值成0
                    use_money_list[this_use_money_nmu] = 0
                # 若前一日收盘后，组合的资产价值 未能大于 已投入资产的10%
                else:
                    # 判断当前（昨日的收盘价）的价格在哪个价位区间中，并标记前一个 中位数的位置
                    for median_i in range(1, len(median_price_list)):
                        # 判断 当前价格是否大于前一个中位数价 并 小于后一个中位数价，
                        if (hs_300.loc[yesterday, '收盘价'] <= median_price_list[median_i - 1]) \
                                & (hs_300.loc[yesterday, '收盘价'] > median_price_list[median_i]):
                            median_location = median_i - 1
                            break
                        else:
                            median_location = 0
                    # 判断中位价格list中是否只有1个值 即仅分成3份
                    if len(median_price_list) == 1:
                        median_location = 0
                        interval_point = 50
                    # 判断当前（昨日的收盘）价是否大于第一个中位数 + 50点的价位，若大于则保持上个月持仓情况不变
                    if hs_300.loc[yesterday, '收盘价'] > (median_price_list[0] + 50):
                        #
                        median_location = 0
                    # 判断当前价格 是否小于 最后一个中位数 ， 若小于则将最后一个中位数的位置指针赋给位置指针变量
                    if hs_300.loc[yesterday, '收盘价'] <= median_price_list[-1]:
                        median_location = len(median_price_list) - 1

                    # 返回当前中位点对应的上下区间点数
                    interval_point = interval_point_func(now_index_price=hs_300.loc[yesterday, '收盘价'],
                                                         median_location_temp=median_location)
                    # 当前（昨日的收盘）价是否大于第一个中位数 + 50点的价位, 保持之前仓位
                    if hs_300.loc[yesterday, '收盘价'] > (median_price_list[0] + 50):
                        portfolio_resume.loc[now_date, '持仓数量'] = portfolio_resume.loc[yesterday, '持仓数量']
                        portfolio_resume.loc[now_date, '已投资产'] = portfolio_resume.loc[yesterday, '已投资产']
                        portfolio_resume.loc[now_date, '未投资产'] = portfolio_resume.loc[yesterday, '未投资产']
                        portfolio_resume.loc[now_date, '建仓资产价格'] = fund_npv.loc[yesterday, '收盘价']

                    # 如果当前价格小于等于 最后一个中位数  or  仅分成3份也用此部分
                    elif (hs_300.loc[yesterday, '收盘价'] <= median_price_list[-1]) \
                            or ((median_location == 0) & (constant_n_part_ == 3)):

                        # 判断当前价格是否处于上边界中位数的 +-区间差内
                        if (hs_300.loc[yesterday, '收盘价'] > (median_price_list[median_location] - interval_point)) \
                                & (hs_300.loc[yesterday, '收盘价'] < (median_price_list[median_location] + interval_point)) \
                                & (last_time_price_zone != median_location) & (
                                hs_300.loc[yesterday, '收盘价'] < hs_300.loc[buy_in_date, '收盘价']):

                            # 选出使用买入的资金量
                            use_money = sum(use_money_list[this_use_money_nmu + 1:median_location + 2])
                            #
                            # 则将下一段的未使用资金使用进来
                            portfolio_resume.loc[now_date, '持仓数量'] = \
                                (use_money / fund_npv.loc[yesterday, '收盘价']) + portfolio_resume.loc[yesterday, '持仓数量']
                            portfolio_resume.loc[now_date, '已投资产'] = portfolio_resume.loc[yesterday, '已投资产'] + use_money
                            portfolio_resume.loc[now_date, '未投资产'] = all_capital - portfolio_resume.loc[now_date, '已投资产']
                            portfolio_resume.loc[now_date, '建仓资产价格'] = fund_npv.loc[yesterday, '收盘价']
                            # 需要对资金的标记减一,防止震荡情况
                            # n_part_ -= 1
                            # 记录买入的时点日期
                            buy_in_date = now_date
                            # 将本次使用完的资金对应位置赋值成0
                            for ii in range(this_use_money_nmu + 1, median_location + 2):
                                use_money_list[ii] = 0
                            # 记录使用的资金是第几份
                            this_use_money_nmu = median_location + 1
                            # 将本次的价格所在区间的位置信息记录
                            last_time_price_zone = median_location
                            # 初始化一个变量，防止 相同的区间，下跌到中间区域后，无法触发条件
                            tin_ = 0

                        # 判断当前价格是否处于上下中位数之间，需要计算系数，提前使用下面区间对应的资金份额， 跌倒该区间内
                        elif (hs_300.loc[yesterday, '收盘价'] <= (median_price_list[median_location] - interval_point)) \
                             & (hs_300.loc[yesterday, '收盘价'] >= (smallest_index_num + interval_point)) \
                             & ((last_time_price_zone != median_location) or (tin_ == 0)) & (
                                         hs_300.loc[yesterday, '收盘价'] < hs_300.loc[buy_in_date, '收盘价']):

                            # 计算需要对使用的第三阶段资金乘以的系数：（P中位 - P当前） / （P中位 - P最低）
                            coef_temp = \
                                (median_price_list[median_location] - hs_300.loc[yesterday, '收盘价']) \
                                / (median_price_list[median_location] - smallest_index_num)
                            # 选出使用买入的资金量
                            use_money = \
                                sum(use_money_list[this_use_money_nmu + 1:-1]) + use_money_list[-1] * coef_temp
                            #
                            portfolio_resume.loc[now_date, '持仓数量'] = \
                                (use_money / fund_npv.loc[yesterday, '收盘价']) + portfolio_resume.loc[yesterday, '持仓数量']
                            portfolio_resume.loc[now_date, '已投资产'] = portfolio_resume.loc[yesterday, '已投资产'] + use_money
                            portfolio_resume.loc[now_date, '未投资产'] = all_capital - portfolio_resume.loc[now_date, '已投资产']
                            portfolio_resume.loc[now_date, '建仓资产价格'] = fund_npv.loc[yesterday, '收盘价']
                            # 将本次使用完的资金对应位置赋值成0
                            for ii in range(this_use_money_nmu + 1, len(use_money_list)):
                                # 对于使用的下一份的资金赋成, 减去系数部分后剩余的资金
                                if ii == (len(use_money_list) - 1):
                                    use_money_list[ii] = use_money_list[-1] * (1 - coef_temp)
                                else:
                                    use_money_list[ii] = 0
                            # 需要对资金的标记减一,防止震荡情况
                            # n_part_ -= 1
                            # 记录买入的时点日期
                            buy_in_date = now_date
                            # 记录使用的资金是第几份
                            this_use_money_nmu = median_location + 1
                            # 将本次的价格所在区间的位置信息记录
                            last_time_price_zone = median_location
                            # 将tin变量变化，防止 相同的区间，下跌到中间区域后，无法触发条件
                            tin_ += 1
                        # 若小于 投资者对应的最小价格则，全盘投入
                        elif (hs_300.loc[yesterday, '收盘价'] <= (smallest_index_num + interval_point)) \
                                & (hs_300.loc[yesterday, '收盘价'] < hs_300.loc[buy_in_date, '收盘价']) & \
                                (last_time_price_zone != median_location):
                            # 计算 使用的资金
                            use_money = portfolio_resume.loc[yesterday, '未投资产']
                            #
                            portfolio_resume.loc[now_date, '持仓数量'] = \
                                (use_money / fund_npv.loc[yesterday, '收盘价']) + portfolio_resume.loc[yesterday, '持仓数量']
                            portfolio_resume.loc[now_date, '已投资产'] = portfolio_resume.loc[yesterday, '已投资产'] + use_money
                            portfolio_resume.loc[now_date, '未投资产'] = all_capital - portfolio_resume.loc[now_date, '已投资产']
                            portfolio_resume.loc[now_date, '建仓资产价格'] = fund_npv.loc[yesterday, '收盘价']
                            # 将本次使用完的资金对应位置赋值成0
                            for ii in range(this_use_money_nmu + 1, len(use_money_list)):
                                use_money_list[ii] = 0
                            # 记录买入的时点日期
                            buy_in_date = now_date
                            # 记录使用的资金是第几份
                            this_use_money_nmu = median_location + 1
                            # 将本次的价格所在区间的位置信息记录
                            last_time_price_zone = median_location
                        # 如果对于不满足以上情况的 定投日期的数据，保持仓位不变
                        else:
                            portfolio_resume.loc[now_date, '持仓数量'] = portfolio_resume.loc[yesterday, '持仓数量']
                            portfolio_resume.loc[now_date, '已投资产'] = portfolio_resume.loc[yesterday, '已投资产']
                            portfolio_resume.loc[now_date, '未投资产'] = portfolio_resume.loc[yesterday, '未投资产']
                            portfolio_resume.loc[now_date, '建仓资产价格'] = fund_npv.loc[yesterday, '收盘价']

                    else:
                        # 判断当前价格是否处于上边界中位数的 +-区间差内
                        if (hs_300.loc[yesterday, '收盘价'] > (median_price_list[median_location] - interval_point)) \
                                & (hs_300.loc[yesterday, '收盘价'] < (median_price_list[median_location] + interval_point)) \
                                & (last_time_price_zone != median_location) & (hs_300.loc[yesterday, '收盘价'] < hs_300.loc[buy_in_date, '收盘价']):
                            # 选出使用买入的资金量
                            use_money = sum(use_money_list[this_use_money_nmu + 1:median_location + 2])
                            #
                            # 则将下一段的未使用资金使用进来
                            portfolio_resume.loc[now_date, '持仓数量'] = \
                                (use_money / fund_npv.loc[yesterday, '收盘价']) + portfolio_resume.loc[yesterday, '持仓数量']
                            portfolio_resume.loc[now_date, '已投资产'] = portfolio_resume.loc[yesterday, '已投资产'] + use_money
                            portfolio_resume.loc[now_date, '未投资产'] = all_capital - portfolio_resume.loc[now_date, '已投资产']
                            portfolio_resume.loc[now_date, '建仓资产价格'] = fund_npv.loc[yesterday, '收盘价']
                            # 需要对资金的标记减一,防止震荡情况
                            # n_part_ -= 1
                            # 记录买入的时点日期
                            buy_in_date = now_date
                            # 将本次使用完的资金对应位置赋值成0
                            for ii in range(this_use_money_nmu + 1, median_location + 2):
                                use_money_list[ii] = 0
                            # 记录使用的资金是第几份
                            this_use_money_nmu = median_location + 1
                            # 将本次的价格所在区间的位置信息记录
                            last_time_price_zone = median_location
                            # 初始化一个变量，防止 相同的区间，下跌到中间区域后，无法触发条件
                            tin_ = 0

                        # 判断当前价格是否处于下边界中位数的 +- 区间差内，并且是一次性下跌到该区间内的
                        elif (hs_300.loc[yesterday, '收盘价'] > (median_price_list[median_location + 1] - interval_point)) \
                                & (hs_300.loc[yesterday, '收盘价'] < (median_price_list[median_location + 1] + interval_point)) \
                                & (last_time_price_zone != median_location) & (hs_300.loc[yesterday, '收盘价'] < hs_300.loc[buy_in_date, '收盘价']):
                            # 选出使用买入的资金量
                            use_money = sum(use_money_list[this_use_money_nmu + 1:median_location + 3])
                            # 则将下一段的未使用资金使用进来
                            portfolio_resume.loc[now_date, '持仓数量'] = \
                                (use_money / fund_npv.loc[yesterday, '收盘价']) + portfolio_resume.loc[yesterday, '持仓数量']
                            portfolio_resume.loc[now_date, '已投资产'] = portfolio_resume.loc[yesterday, '已投资产'] + use_money
                            portfolio_resume.loc[now_date, '未投资产'] = all_capital - portfolio_resume.loc[now_date, '已投资产']
                            portfolio_resume.loc[now_date, '建仓资产价格'] = fund_npv.loc[yesterday, '收盘价']
                            # 需要对资金的标记减一,防止震荡情况
                            # n_part_ -= 1
                            # 记录买入的时点日期
                            buy_in_date = now_date
                            # 将本次使用完的资金对应位置赋值成0
                            for ii in range(this_use_money_nmu + 1, median_location +3):
                                use_money_list[ii] = 0
                            # 记录使用的资金是第几份
                            this_use_money_nmu = median_location + 2
                            # 将本次的价格所在区间的位置信息记录
                            last_time_price_zone = median_location
                            # 初始化一个变量，防止 相同的区间，下跌到中间区域后，无法触发条件
                            tin_ = 0

                        # 判断当前价格是否处于上下中位数之间，需要计算系数，提前使用下面区间对应的资金份额， 跌倒该区间内
                        elif (hs_300.loc[yesterday, '收盘价'] <= (median_price_list[median_location] - interval_point)) \
                                & (hs_300.loc[yesterday, '收盘价'] >= (median_price_list[median_location + 1] + interval_point)) \
                                & ((last_time_price_zone != median_location) or (tin_ == 0)) & (hs_300.loc[yesterday, '收盘价'] < hs_300.loc[buy_in_date, '收盘价']):
                            # 计算需要对使用的第三阶段资金乘以的系数：（P中位 - P当前） / （P中位 - P最低）
                            coef_temp = \
                                (median_price_list[median_location] - hs_300.loc[yesterday, '收盘价']) \
                                / (median_price_list[median_location] - median_price_list[median_location + 1])
                            # 选出使用买入的资金量
                            use_money = \
                                sum(use_money_list[this_use_money_nmu + 1:median_location + 2]) \
                                + use_money_list[median_location + 2] * coef_temp
                            #
                            portfolio_resume.loc[now_date, '持仓数量'] = \
                                (use_money / fund_npv.loc[yesterday, '收盘价']) + portfolio_resume.loc[yesterday, '持仓数量']
                            portfolio_resume.loc[now_date, '已投资产'] = portfolio_resume.loc[yesterday, '已投资产'] + use_money
                            portfolio_resume.loc[now_date, '未投资产'] = all_capital - portfolio_resume.loc[now_date, '已投资产']
                            portfolio_resume.loc[now_date, '建仓资产价格'] = fund_npv.loc[yesterday, '收盘价']
                            # 将本次使用完的资金对应位置赋值成0
                            for ii in range(this_use_money_nmu + 1, median_location + 3):
                                # 对于使用的下一份的资金赋成, 减去系数部分后剩余的资金
                                if ii == (median_location + 2):
                                    use_money_list[ii] = use_money_list[median_location + 2] * (1 - coef_temp)
                                else:
                                    use_money_list[ii] = 0
                            # 需要对资金的标记减一,防止震荡情况
                            # n_part_ -= 1
                            # 记录买入的时点日期
                            buy_in_date = now_date
                            # 记录使用的资金是第几份
                            this_use_money_nmu = median_location + 1
                            # 将本次的价格所在区间的位置信息记录
                            last_time_price_zone = median_location
                            # 将tin变量变化，防止 相同的区间，下跌到中间区域后，无法触发条件
                            tin_ += 1
                        # 若小于 投资者对应的最小价格则，全盘投入
                        elif (hs_300.loc[yesterday, '收盘价'] <= (smallest_index_num + interval_point)) \
                             & (hs_300.loc[yesterday, '收盘价'] < hs_300.loc[buy_in_date, '收盘价']) & \
                                (last_time_price_zone != median_location):
                            # 计算 使用的资金
                            use_money = portfolio_resume.loc[yesterday, '未投资产']
                            #
                            portfolio_resume.loc[now_date, '持仓数量'] = \
                                (use_money / fund_npv.loc[yesterday, '收盘价']) + portfolio_resume.loc[yesterday, '持仓数量']
                            portfolio_resume.loc[now_date, '已投资产'] = portfolio_resume.loc[yesterday, '已投资产'] + use_money
                            portfolio_resume.loc[now_date, '未投资产'] = all_capital - portfolio_resume.loc[now_date, '已投资产']
                            portfolio_resume.loc[now_date, '建仓资产价格'] = fund_npv.loc[yesterday, '收盘价']
                            # 将本次使用完的资金对应位置赋值成0
                            for ii in range(this_use_money_nmu + 1, len(use_money_list)):
                                use_money_list[ii] = 0
                            # 记录买入的时点日期
                            buy_in_date = now_date
                            # 记录使用的资金是第几份
                            this_use_money_nmu = median_location + 1
                            # 将本次的价格所在区间的位置信息记录
                            last_time_price_zone = median_location
                        # 如果对于不满足以上情况的 定投日期的数据，保持仓位不变
                        else:
                            portfolio_resume.loc[now_date, '持仓数量'] = portfolio_resume.loc[yesterday, '持仓数量']
                            portfolio_resume.loc[now_date, '已投资产'] = portfolio_resume.loc[yesterday, '已投资产']
                            portfolio_resume.loc[now_date, '未投资产'] = portfolio_resume.loc[yesterday, '未投资产']
                            portfolio_resume.loc[now_date, '建仓资产价格'] = fund_npv.loc[yesterday, '收盘价']

            else:
                portfolio_resume.loc[now_date, '持仓数量'] = portfolio_resume.loc[yesterday, '持仓数量']
                portfolio_resume.loc[now_date, '已投资产'] = portfolio_resume.loc[yesterday, '已投资产']
                portfolio_resume.loc[now_date, '未投资产'] = portfolio_resume.loc[yesterday, '未投资产']
                portfolio_resume.loc[now_date, '建仓资产价格'] = fund_npv.loc[yesterday, '收盘价']

print(portfolio_resume)
# exit()
portfolio_resume['投资净值'] = (portfolio_resume['建仓资产价格'] * portfolio_resume['持仓数量'] + portfolio_resume['未投资产']) / 100000
# 输出
# portfolio_resume.to_excel(file_path_inver_sys + '/output_data/交易式定投-价值精选回测结果-结合PE分8份.xlsx', encoding='gbk')

# 初始化存放绩效分析的dataframe
temp_frame = pd.DataFrame()
# 绩效分析
for k in range(1, len(open_close_position_date)):
    open_date = open_close_position_date[k - 1]
    close_date = open_close_position_date[k]
    # 找到close_date 在所有交易日中的index, 再找到该index向上一个位置
    last_one_index = all_trading_date.index(close_date) - 1
    last_date = all_trading_date[last_one_index]

    # 计算这段时间的累计收益率及年化收益率
    temp_frame.loc[k, '开始时间'] = datetime.datetime.strftime(open_date, '%Y-%m-%d')
    temp_frame.loc[k, '结束时间'] = datetime.datetime.strftime(close_date, '%Y-%m-%d')

    temp_frame.loc[k, '累计收益率'] = \
        portfolio_resume.loc[close_date, '建仓资产价格'] * portfolio_resume.loc[last_date, '持仓数量'] / portfolio_resume.loc[last_date, '已投资产']
    temp_frame.loc[k, '时间'] = len(portfolio_resume.loc[open_date:close_date])
    temp_frame.loc[k, '年化收益率'] = (temp_frame.loc[k, '累计收益率'] ** (254 / temp_frame.loc[k, '时间']) - 1) * 100

print(temp_frame)

len_ = len(portfolio_resume.loc['2014-05-05':])
aa_temp = \
    portfolio_resume.iloc[-1]['建仓资产价格'] * portfolio_resume.iloc[-1]['持仓数量'] + portfolio_resume.iloc[-1]['未投资产']
print('最低价格：', smallest_index_num)
print('每次赚x%平仓：', earning_n_percent)
print('分成了x份：', constant_n_part_)
print('PE下百分位：', down_point)
print('PE上百分位：', up_point)
print('累计收益率：', ((aa_temp / 100000) - 1.0) * 100)
print('年化收益率：', (((aa_temp / 100000) ** (254 / len_)) - 1.0) * 100)





