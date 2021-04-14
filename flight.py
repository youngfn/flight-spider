#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author  : jia666
# @Time    : 2020/08/26 8:31
import requests

#   请求头
request_head = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36",
}

#   post传值
ploy_data = {
    "b": {"locationAirCity": "杭州", "locationCity": "杭州", "timeout": 5000, "holiday": "default", "simpleData": "yes",
          "t": "f_urInfo_superLow_data", "cat": "touch_flight_home", "tabName": ""}, "c": {}
}

#   目标url
url='https://m.flight.qunar.com/lowFlightInterface/api/getAirLine'

#   发送post请求，json解析返回数据
response=requests.post(url,json=ploy_data,headers=request_head).json()

#航班信息列表获取
domList = response.get('data').get('domList')
interList = response.get('data').get('interList')

#航班信息列表遍历及信息提取与整理及打印显示
def get_airplane(list):
    for i in list:
        price = i.get('price')  # 机票价格
        data = i.get('date')  # 出发时间
        backDate = i.get('backDate', '')  # 返回时间
        depcity = i.get('depCity')  # 出发城市
        arrciry = i.get('arrCity')  # 目的城市
        flightNo = i.get('flightNo')  # 飞行航班
        discount = i.get('discount')  # 折扣
        depDateWeek = i.get('depDateWeek')  # 出发周
        backDateWeek = i.get('backDateWeek', '')  # 返回周
        flightTypeDesc = i.get('flightTypeDesc')  # 飞行类型

        s = str(depcity) + '--' + str(arrciry) + '\t' + str(flightNo) + '\t' + str(flightTypeDesc) + '\t'*2 + str(
            discount) + '\n' + str(data) + '\t' + str(depDateWeek) + '\t' * 5 + str(price) \
            + '\n' + backDate + '\t' + backDateWeek

        print('-' * 50)
        print(str(s))
        print('-' * 50)

get_airplane(domList)
get_airplane(interList)
