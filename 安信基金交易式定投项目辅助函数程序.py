# -*- coding: utf-8 -*-
"""
Pycharm Editor: Mr.seven
This is a temporary script file.
"""
import datetime
import copy


# 资金列表
def make_capital_list(this_time_all_capital, constant_n_part_temp, denominator_temp=2):
    all_capital_list = []
    for capital_i in range(1, constant_n_part_temp + 1):
        #
        if capital_i == constant_n_part_temp:
            all_capital_list.append(this_time_all_capital / (constant_n_part_temp + denominator_temp) * 2)
        else:
            all_capital_list.append(this_time_all_capital / (constant_n_part_temp + denominator_temp))
    return all_capital_list
# print(make_capital_list(all_capital, 8))
# # exit()


# 计算每个价位的列表
def make_price_list(now_price, constant_n_part_temp, smallest_index_num_temp):
    all_price_list = []
    all_price_lowest_list = []
    temp_2 = now_price
    for price_i in range(1, constant_n_part_temp - 1):
        # 计算当前价格与最低价的平均价
        temp_1 = (temp_2 + smallest_index_num_temp) / 2.0
        all_price_list.append(temp_1)
        all_price_lowest_list.append(temp_1)
        # 将上一期计算出来的平均数放记录
        temp_2 = copy.deepcopy(temp_1)
    # 将投资者的最低心理价位也放进去
    all_price_lowest_list.append(smallest_index_num_temp)
    return all_price_list, all_price_lowest_list
# print(make_price_list(4749.886))
# exit()


# 判断本月的交易日中是否有常规的定投日期，若有则跳过，若无，则将定投日期向后推x日，直至存在交易日期list中
def judge_fix_invest_date_in_trading(this_year, this_month, default_fix_date, trading_list):
    # 构成本月初始设定的定投日期
    construct_fix_date = datetime.datetime(this_year, this_month, day=default_fix_date)
    # print(construct_fix_date)
    # 判断重新设定的定投日期是否在交易日期的list中
    if construct_fix_date in trading_list:
        # every_month_invest_date_return = default_fix_date
        return default_fix_date
    # 如果不在交易日列表中，并且初始的default 定投日期在28号及以后，则向前推x日
    # elif default_fix_date >= 28:
    #     for k in range(1, 15):
    #         default_fix_date = default_fix_date - k
    #         # 再次判断新的日期是否在里面
    #         construct_fix_date = datetime.datetime(this_year, this_month, day=default_fix_date)
    #         if construct_fix_date in trading_list:
    #             return default_fix_date
    # 如果不在的话，向后推n日，直至找到一个在的
    else:
        for k in range(1, 15):
            default_fix_date__ = default_fix_date + k
            # 再次判断新的日期是否在里面
            construct_fix_date__ = datetime.datetime(this_year, this_month, day=default_fix_date__)
            if construct_fix_date__ in trading_list:
                # print('新的日期构建成功：', construct_fix_date)
                # every_month_invest_date_return = construct_fix_date
                return default_fix_date__


# 定义每个中位数不同的区间差
def interval_point_func(now_index_price, median_location_temp):
    # 判断当前价格所处的区间2500、3000、3000以上即在第三个中位数及以后，进而确定 大于和小于中位数区间的距离
    if now_index_price >= 4000:
        # 若在第四个中位数及以后则使用 上下20个点的区间。对于在
        if median_location_temp <= 2:
            interval_point_temp = 50
        elif median_location_temp == 3:
            interval_point_temp = 20
        else:
            # 在第三个中位数之前的话，上下50个点
            interval_point_temp = 5
    elif (now_index_price >= 2500) & (now_index_price < 4000):
        # 若在第2个中位数以前则使用 上下50个点的区间
        if median_location_temp <= 1:
            interval_point_temp = 50
        elif median_location_temp == 2:
            interval_point_temp = 20
        # 若在第 3个中位数以后则使用上下5个点
        else:
            interval_point_temp = 5
    # 若当前指数在 2500至2000之间
    elif (now_index_price < 2500) & (now_index_price >= 2000):
        # 若在第2个中位数以前则使用 上下50个点的区间
        if median_location_temp == 0:
            interval_point_temp = 50
        elif median_location_temp <= 1:
            interval_point_temp = 20
        elif (median_location_temp > 1) & (median_location_temp <= 3):
            interval_point_temp = 5
        else:
            interval_point_temp = 0
    else:
        interval_point_temp = 0
    return interval_point_temp


