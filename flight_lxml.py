# -*- coding: utf-8 -*-
import xml.etree.ElementTree as etree
import requests
import time
from lxml import etree
from email.mime.text import MIMEText
import smtplib


def ShowDict(d):
    print('=================')
    for v in d:
        print(v, '->', d[v])
def TripDict(d):
    for v in d:
        d[v] = d[v].strip()



# 从网上抓取票价数据，去哪儿网已经整理好放到一个xml文件，直接解析就可以了
def GetPlaneTicketPrice(FromAddr, ToAddr):
    requrl = 'http://ws.qunar.com/holidayService.jcp?lane=%s-%s' % (FromAddr, ToAddr)
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36"
    headers = {"User-Agent": user_agent}
    request = requests.get(requrl, headers=headers)
    response = request.text.encode(encoding="utf-8")
    tree = etree.fromstring(response)

    # print(tree)
    # root = tree.getroot()
    root = tree.getiterator()
    print(type(root))



    all_info = []
    for node in root:
        cur_info = {}
        try:
            na = node.attrib
            cur_info = dict(na.items())
            #print na["date"],na['go_avc'],na['go_start'],na['go_expires']
            for child in node:
                ca = child.attrib
                item_1 = dict(cur_info.items() + ca.items())
                # print(item_1)
                item_1['from_addr'] = FromAddr
                item_1['to_addr'] = ToAddr
                item_2 = {}
                for i in item_1:
                    item_2[i.encode('utf-8')] = item_1[i] .encode('utf-8')
                all_info.append(item_2)
                #ShowDict(item_1)
        except:
            pass
    return all_info

#时间转换函数
def GetCurrentDate():
    return time.strftime("%Y-%m-%d", time.localtime())

def GetTimeSruFromDateStr(date_str) :
    return time.strptime(date_str, "%Y-%m-%d")

def GetDateStrFromTimeSru(ti):
    return "%04d-%02d-%02d" % (ti.tm_year, ti.tm_mon, ti.tm_mday)

def GetTimeSruFromDateTimeStr(date_str):
    return time.strptime(date_str, "%Y-%m-%d %H:%M:%S")

def GetDateTimeStrFromTimeSru (ti):
    return "%04d-%02d-%02d %02d:%02d:%02d" % (ti.tm_year, ti.tm_mon,ti.tm_mday , ti.tm_hour, ti.tm_min, ti.tm_sec )

#帅选需要的字段数据和航班类型，按折扣排序
def GetTripByPrice(tp_info, trip_type='go', date_beg=None, date_end=None) :
    if not date_beg:
        date_beg = GetCurrentDate()
    if not date_end:
        date_end = date_beg

    tp = trip_type

    #过滤出需要的类型和数据类型转换
    trip_info = []
    for v in tp_info:
        if v['type'] != trip_type:
            continue
        nv = {}
        nv['date'] = GetTimeSruFromDateStr(v['date'])
        nv['avc'] = v[tp + '_avc']
        nv['price'] = int(v['price'])
        nv['from_addr'] = v['from_addr']
        nv['to_addr'] = v['to_addr']
        #time.strptime(date_str, "%Y-%m-%d")
        ds = v['date'] + ' ' + v[tp + '_start'] + ":00"
        nv['start_time'] = GetTimeSruFromDateTimeStr(ds)
        de = v['date'] + ' ' + v[tp + '_expires'] + ":00"
        nv['expires_time'] = GetTimeSruFromDateTimeStr(de)
        dis = v['discount']
        fDis = None
        for i in dis:
            if i.isdigit():
                fDis = float(''.join([ s for s in dis if (s.isdigit() or s == '.')]))
                break
        if fDis== None:
            cc = {"全价": 10.0, "半价": 5.0, "免费": 0.0}
            fDis = cc[dis]
        nv['discount'] = fDis
        nv['name'] = v['name']
        trip_info.append(nv)

    #日期过滤
    date_beg_t = GetTimeSruFromDateStr(date_beg)
    date_end_t = GetTimeSruFromDateStr(date_end)
    trip_info = [v for v in trip_info if date_beg_t <= v['start_time'] <= date_end_t]

    #按价格排序
    sorted_tp = sorted(trip_info, key = lambda k: k['discount'])
    return sorted_tp

#根据航班列表生成网页源码
def MakeHtmlPage (TripList) :
    html_h = '''<html>
    <body>
    <center>
    <h4>【低价机票助手】#title#</h4>
    <table border="1" cellspacing="0" cellpadding="0" width="600" style="BORDER-COLLAPSE: collapse">
    <tr>
        <th>航班</th>
        <th>出发时间</th>
        <th>抵达时间</th>
        <th>折扣</th>
        <th>价格</th>
    </tr>'''

    html_t = '''    </table>
    </center>
    </body>
    </html>
    '''

    if not TripList:
        print('null trip found')
        return
    data_tr = ''
    from_addr = TripList[0]['from_addr' ]
    to_addr = TripList[0]['to_addr' ]
    title = '发现【%s->%s】低价机票，请注意哦!' % (from_addr, to_addr)
    html_h = html_h.replace('#title#', title)
    for v in TripList:
        cr = '    <tr>\r\n'
        ts = GetDateTimeStrFromTimeSru(v['start_time'])
        te = GetDateTimeStrFromTimeSru(v['expires_time'])
        dis = '%.1f折' % (v['discount'])
        price = '%d元' % (v['price'])
        cr = '    <tr>\r\n'
        cr += '        <th>%s</th>\r\n' % (v['avc'])
        cr += '        <th>%s</th>\r\n' % ts
        cr += '        <th>%s</th>\r\n' % te
        cr += '        <th>%s</th>\r\n' % dis
        cr += '        <th>%s</th>\r\n' % price
        cr += '    </tr>\r\n'
        data_tr += cr

    html = html_h + data_tr + html_t
    return html

#判断邮件内容是否可以发送，统一邮件内容30分内只允许发送一次
his_msg = []
def CanSend (msg) :
    tNow = time.time()
    MinTime = 30 * 60
    bSend = True
    for i, m in enumerate(his_msg):
        if (msg == m[0]) and (tNow - m[1] < MinTime):
            bSend = False

        if tNow - m[1] > MinTime:
            del his_msg[i]

    if bSend:
        his_msg.append([msg, tNow])
    return bSend

#根据航班列表生成文本信息
def MakeEmailMsg (TripList) :
    if not TripList:
        print('null trip found')
        return
    msg = ''
    from_addr = TripList[ 0]['from_addr' ]
    to_addr = TripList[ 0]['to_addr' ]
    msg += '发现【%s->%s】低价机票，请注意哦~~\r\n' % (from_addr, to_addr)
    msg += '=' * 60 + "\r\n"
    msg += '%s\t%s\t%s\t%s\t%s\r\n' % ('航班'.center(32), '出发日期'.center(32),'航班时间' .center(40),'折扣', '价格')
    for v in TripList:
        ts = GetDateTimeStrFromTimeSru(v['start_time'])
        te = GetDateTimeStrFromTimeSru(v['expires_time'])
        di = ts[:10]
        ti = '%s->%s' % (ts[- 8:], te[-8:])
        dis = '%.1f折' % (v['discount'])
        price = '%d元' % (v['price'])
        msg += '%s\t%s\t%s\t%s\t%s\r\n' % (v['avc'], di, ti, dis, price)
    msg += '='*60 + "\r\n\r\n"
    return msg

#发送邮件，支持HTML格式和普通文本格式
def send_mail (to_list, sub,content ,ishtml=False) :
    if not CanSend(content):
        return False
    mail_host = "smtp.qq.com"# https://mail.qq.com/
    mail_user = "xxxx"
    mail_pass = "xxxxx"
    mail_postfix = "qq.com"

    me=mail_user + "<" + mail_user + "@" + mail_postfix+">"
    msg = MIMEText(content)
    if ishtml:
        msg = MIMEText(content, _subtype='html', _charset='utf-8')
    msg ['Subject'] = sub
    msg ['From'] = me
    msg ['To'] = ";".join(to_list)
    try:
        s = smtplib.SMTP()
        s.connect(mail_host)
        s.login(mail_user, mail_pass)
        s.sendmail(me, to_list, msg.as_string ())
        s.close()
        print('send emial success')
        return True
    except Exception as e:
        print(str(e))
        print('send emial failed')
        return False

#监控低价航班列表，一旦发现有低折扣的机票就发送邮件
def MonitorLowTrip (FromAddr, ToAddr, DisCount=3, MaxNum=5 ):
    email_li = ['xxxxx@qq.com']
    while True:
        all_info = GetPlaneTicketPrice(FromAddr, ToAddr)
        #print all_info
        LowTrip = GetTripByPrice(all_info, date_beg='2018-10-01' ,date_end= '2018-10-08')[:MaxNum]

        if LowTrip:
            if LowTrip[ 0]['discount' ] <= DisCount:
                msg = MakeHtmlPage(LowTrip) .encode('utf-8' )
                send_mail(email_li, "[低价机票]", msg, True)
                print(msg)
        else:
            print('未发现符合要求的机票')
        time.sleep(10)

if __name__ == '__main__':

    #启动监控脚本，监控从深圳飞往宁波的机票，低于4折就把最低价的10条记录发往邮箱
	MonitorLowTrip('深圳', '西安', 5, 10)
