#!/usr/bin/env python
# -*- coding:utf-8 -*-  
'''
auth: qyf
notice: 输出文件采用的是GBK编码,此文件使用utf-8编码，输出和匹配使用不同的编码需要注意
'''

import xlrd
import os
import csv
import traceback
import time
import ConfigParser
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import codecs
import smtplib
from email.mime.text import MIMEText
from email.header import Header

config = ConfigParser.ConfigParser()
try:
    config.readfp(codecs.open('.\\O4CsvToCsvConfig.ini', "r", "utf-8-sig"))
except Exception, e:
    exit()

# utf-8 to gbk
def getGBK(raw):
    if type(raw) == str:
        return raw.decode('utf-8').encode('gbk')
    elif type(raw) == unicode:
        return raw.encode("gbk")
    return raw


#文件路径
LOG_FILE_PATH = getGBK(config.get("filePath","LOG_FILE_PATH"))
CSV_OUTPUT_PATH = getGBK(config.get("filePath","CSV_OUTPUT_PATH"))
LOG_FILE_PATH = LOG_FILE_PATH + "\\"
CSV_OUTPUT_PATH = CSV_OUTPUT_PATH + "\\"

#邮件相关
sender = getGBK(config.get("mail","SENDER"))
receivers = getGBK(config.get("mail","RECEIVER"))
username = config.get("mail","USERNAME")
password = config.get("mail","PASSWORD")
#处理多接收者邮箱
receiver = receivers.split(';')
subject = 'PB通文件警告'
smtpserver = 'smtp.163.com'

def emailMag(matter):
    msg = MIMEText(matter,'plain','utf-8')#中文需参数‘utf-8'，单字节字符不需要
    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = "<" + sender + ">"
    msg['To'] = "XXX@qq.com"
    smtp = smtplib.SMTP()
    smtp.connect('smtp.163.com')
    smtp.login(username, password)
    for recv in receiver:
        smtp.sendmail(sender, recv, msg.as_string())
    smtp.quit()

# 市场类别
EXCHANGE_TYPE_UNKNOWN        = '0' # 前台未知交易所
EXCHANGE_TYPE_SHANGHAI       = '1' # 上海A
EXCHANGE_TYPE_SHENZHEN       = '2' # 深圳A
EXCHANGE_TYPE_GEM            = '8' # 创业板
EXCHANGE_TYPE_TZ_A           = '9' # 特转A
EXCHANGE_TYPE_TZ_B           = 'A' # 特转B
EXCHANGE_TYPE_SHANGHAI_B     = 'D' # 上海B
EXCHANGE_TYPE_SHENZHEN_B     = 'H' # 深圳B
EXCHANGE_TYPE_HGT            = 'I' # 沪港通
EXCHANGE_TYPE_SGT            = 'J' # 深港通
EXCHANGE_TYPE_CZCE           = "CZCE"#郑商所
EXCHANGE_TYPE_DCE            = "DCE"#大商所
EXCHANGE_TYPE_SHFE           = "SHFE"#上期所
EXCHANGE_TYPE_CFFEX          = "CFFEX"#中金所

# 交易类别
ENTRUST_BS_BUY               = '1'# 买入
ENTRUST_BS_SELL              = '2'# 卖出
ENTRUST_BS_PLEDGE_RU         = 'R'# 质押入库
ENTRUST_BS_PLEDGE_CHU        = 'C'# 质押入库

# 委托类型
ENTRUST_TYPE_BS              = '0'# 委托买卖
ENTRUST_TYPE_QUERY           = '1'# 查询
ENTRUST_TYPE_CANCEL          = '2'# 撤单
ENTRUST_TYPE_APPEND          = '3'# 补单
ENTRUST_TYPE_RZWT            = '6'#融资委托
ENTRUST_TYPE_RQWT            = '7'#融券委托
ENTRUST_CREDIT_NORMAL        = '9'#信用普通委托

# 委托属性
ENTRUST_PROP_LIMIT_PRICE        = '0'# //限价
ENTRUST_PROP_ALLOTMENT          = '1'# //配股
ENTRUST_PROP_REFER              = '2'# //转托
ENTRUST_PROP_SUBSCRIBE          = '3'# //申购
ENTRUST_PROP_BUYBACK            = '4'# //回购
ENTRUST_PROP_PLACING            = '5'# //配售
ENTRUST_PROP_DECIDE             = '6'# //指定
ENTRUST_PROP_EQUITY             = '7'# //转股
ENTRUST_PROP_SELLBACK           = '8'# //回售
ENTRUST_PROP_DIVIDEND           = '9'# //股息
ENTRUST_PROP_SHENZHEN_PLACING   = 'A'# //深圳配售确认
ENTRUST_PROP_CANCEL_PLACING     = 'B'# //配售放弃
ENTRUST_PROP_WDZY               = 'C'# //无冻质押
ENTRUST_PROP_DJZY               = 'D'# //冻结质押
ENTRUST_PROP_WDJY               = 'E'# //无冻解押
ENTRUST_PROP_JDJY               = 'F'# //解冻解押
ENTRUST_PROP_ETF                = 'N'# //ETF申购
ENTRUST_PROP_VOTE               = 'H'# //投票
ENTRUST_PROP_YYSGYS             = 'Y'# //要约收购预售
ENTRUST_PROP_YSYYJC             = 'J'# //预售要约解除
ENTRUST_PROP_FUND_DEVIDEND      = 'K'# //基金分红
ENTRUST_PROP_FUND_ENTRUST       = 'L'# //基金申赎
ENTRUST_PROP_CROSS_MARKET       = 'M'# //跨市转托
ENTRUST_PROP_EXERCIS            = 'P'# //权证行权
ENTRUST_PROP_PEER_PRICE_FIRST   = 'Q'# //对手方最优价格
ENTRUST_PROP_L5_FIRST_LIMITPX   = 'R'# //最优五档即时成交剩余转限价
ENTRUST_PROP_MIME_PRICE_FIRST   = 'S'# //本方最优价格
ENTRUST_PROP_INSTBUSI_RESTCANCEL= 'T'# //即时成交剩余撤销
ENTRUST_PROP_L5_FIRST_CANCEL    = 'U'# //最优五档即时成交剩余撤销
ENTRUST_PROP_FULL_REAL_CANCEL   = 'V'# //全额成交并撤单
ENTRUST_PROP_FUND_CHAIHE        = 'W'# // 基金拆合
ENTRUST_PROP_DBQTJYFH           = 'a'# // 担保证券提交与返还
ENTRUST_PROP_XQHQ               = 'b'# // 现券还券划拨
ENTRUST_PROP_XJHK               = 'c'# // 现金还款
ENTRUST_PROP_QZPC               = 'd'# // 信用强平 bs 买入 融资 卖出 融券
ENTRUST_PROP_INCREASE_SHARE     = 'g'# // 股票增发
ENTRUST_PROP_DBPHZ              = 'h'# // 担保品转划
ENTRUST_PROP_BLOCK_INTENTION    = 'i'#  // 意向
ENTRUST_PROP_BLOCK_PRICE        = 'j'#  // 定价
ENTRUST_PROP_BLOCK_CONFIRM      = 'k'#  // 确认
ENTRUST_PROP_BLOCK_BLOCK_PRICE  = 'l'#  // 盘后定价
ENTRUST_PROP_FUND_REDEMPTION            = 'm'# // 货币基金的申赎
ENTRUST_PROP_NEEQ_PRICING               = 'w'# // 定价（挂牌公司交易-协议转让）
ENTRUST_PROP_NEEQ_MATCH_CONFIRM         = 'x'# // 成交确认（挂牌公司交易-协议转让）
ENTRUST_PROP_NEEQ_MUTUAL_MATCH_CONFIRM  = 'y'# // 互报成交确认（挂牌公司交易-协议转让）
ENTRUST_PROP_NEEQ_LIMIT                 = 'z'# // 限价（用于挂牌公司交易-做市转让-限价买卖和两网及退市交易-限价买卖）
ENTRUST_PROP_BID_LIMIT          = 'd'  #//港股通竞价限价
ENTRUST_PROP_ENHANCED_LIMIT     = 'e'  #//港股通增强限价
ENTRUST_PROP_RETAIL_LIMIT       = 'f'  #//港股通零股限价


# 委托状态
ORDER_STATUS_UNREPORTED                  = '0'#     // 未报（未成交）在lbm中委托成功写入未发标志 
ORDER_STATUS_REPORTING                   = '1'#     // 正报（未成交）在落地方式中,报盘扫描未发委托,并将委托置为正报状态 
ORDER_STATUS_REPORTED                    = '2'#     // 已报（未成交）报盘成功后,报盘机回写发送标志为已报 
ORDER_STATUS_REPORTED_PENDING_CANCEL     = '3'#     // 已报待撤（未成交）已报委托撤单
ORDER_STATUS_PART_FILLED_PENDING_CANCEL  = '4'#     // 部成待撤（未成交）部分成交后委托撤单
ORDER_STATUS_PART_FILLED_CANCELED        = '5'#     // 部撤（撤单成功）部分成交后撤单成交 
ORDER_STATUS_CANCELED                    = '6'#     // 已撤（撤单成功）全部撤单成交 
ORDER_STATUS_PART_FILLED                 = '7'#     // 部成 已报委托部分成交
ORDER_STATUS_FILLED                      = '8'#     // 已成 委托或撤单全部成交 
ORDER_STATUS_JUNK                        = '9'#     // 废单 委托确认为废单 
ORDER_STATUS_PENDING_REPORT              = 'A'#     // 待报（未成交）
ORDER_STATUS_UNKNOWN                     = 255#     // 未知


# 开平方向
ORDER_STATUS_DIRECTION_OPEN                  = '0'#     开
ORDER_STATUS_DIRECTION_EVENING_UP          = '1'#     平




# 删除目录下所有csv后缀文件
def delCsvFiles(filePath, suffix):
    if(not os.path.exists(filePath)):
        os.makedirs(filePath)
        return None
    fileList = os.listdir(filePath)
    for i in range(0, len(fileList)):
        fileFullName = fileList[i]
        if (not fileFullName.endswith( suffix + '.csv') and fileFullName.endswith( '.csv')):
            os.remove(filePath + fileFullName)

def getMarket(raw, default):
    if (raw == "深圳A股" or raw == "深交所A" or raw == "深A"):
        return "深交所"
    elif (raw == "上海A股" or raw == "上海证券交易所" or raw == "上交所A"):
        return "上证所"
    elif (raw == "港股通（沪）" ):
        return "沪港通"
    elif (raw == "港股通（深）" ):
        return "深港通"
    return default

def getEntrustBS(raw, default):
    if raw.find("买") >= 0:
        return ENTRUST_BS_BUY
    elif raw.find("卖") >= 0:
        return ENTRUST_BS_SELL
    elif raw.find("融资回购") >= 0:
        return ENTRUST_BS_BUY
    elif raw.find("融券回购") >= 0:
        return ENTRUST_BS_SELL
    elif raw.find("申购") >= 0:
        return ENTRUST_BS_BUY
    elif raw.find("赎回") >= 0:
        return ENTRUST_BS_SELL
    elif raw.find("分拆") >= 0:
        return ENTRUST_BS_SELL
    elif raw.find("合并") >= 0:
        return ENTRUST_BS_BUY
    return default

def getEntrustTime(raw, default):
    raw = raw.replace(":", "")
    return raw

def getEntrustDate(raw, default):
    raw = raw.replace("-", "")
    return raw

def getEntrusType(raw, default):
    if raw.find("融券") >= 0:
        return ENTRUST_TYPE_RQWT
    elif raw.find("融资") >= 0:
        return ENTRUST_TYPE_RZWT
    elif raw.find("信用") >= 0:
        return ENTRUST_CREDIT_NORMAL
    return default

def getEntrustProp(raw, default):
    if raw.find("回购") >= 0:
        return ENTRUST_PROP_BUYBACK
    elif raw.find("直接还款") >= 0:
        return ENTRUST_PROP_XJHK
    elif raw.find("直接还券") >= 0:
        return ENTRUST_PROP_XQHQ
    elif raw.find("增强限价盘") >= 0:
        return ENTRUST_PROP_BID_LIMIT
    elif raw.find("竞价限价盘") >= 0:
        return ENTRUST_PROP_ENHANCED_LIMIT
    elif raw.find("零股限价盘") >= 0:
        return ENTRUST_PROP_RETAIL_LIMIT
    elif raw.find("限价") >= 0:
        return ENTRUST_PROP_LIMIT_PRICE
    return default

def getEntrustStatus(raw, default):
    if raw.find("未报") >= 0:
        return ORDER_STATUS_UNREPORTED
    elif raw.find("正报") >= 0:
        return ORDER_STATUS_REPORTING
    elif raw.find("已报") >= 0:
        return ORDER_STATUS_REPORTED
    elif raw.find("已报待撤") >= 0:
        return ORDER_STATUS_REPORTED_PENDING_CANCEL
    elif raw.find("部成待撤") >= 0:
        return ORDER_STATUS_PART_FILLED_PENDING_CANCEL
    elif raw.find("部撤") >= 0:
        return ORDER_STATUS_PART_FILLED_CANCELED
    elif (raw.find("已撤") >= 0 or raw.find("撤单") >= 0):
        return ORDER_STATUS_CANCELED
    elif raw.find("部成") >= 0:
        return ORDER_STATUS_PART_FILLED
    elif (raw.find("已成") >= 0 or raw.find("全部成交") >= 0):
        return ORDER_STATUS_FILLED
    elif raw.find("废单") >= 0:
        return ORDER_STATUS_JUNK
    elif raw.find("待报") >= 0:
        return ORDER_STATUS_PENDING_REPORT
    return default

def getEntrustDirection(raw, default):
    if raw.find("开仓") >= 0:
        return ORDER_STATUS_DIRECTION_OPEN
    elif raw.find("平仓") >= 0:
        return ORDER_STATUS_DIRECTION_EVENING_UP
    return default

#基金产品名称对应关系
def getFundName(raw, key,default):
    for matcher in raw:
        if matcher[0] == key:
            return matcher[1]
    return default

# 产品名称和账号对应关系,这里是
productName = [
    ["四川信托锦绣成长1号四川信托锦绣成长1号缺省", "50818765"],
    ["宝鼎汇盈宝鼎汇盈集合资金信托计划", "61611666"],
    ["民信9号单一资金信托民信9号单一资金信托", "147852"],
    ["民信9号单一资金信托民信9号保管户缺省", "12345"],
    ["民信11号民信11号", "60800888"],
    ["民信11号民信11保管户缺省", "50818765"],
    ["天富6号天富6号", "63500064"],
    ["天富6号天富6号保管户缺省", "1234"],
    ["天富7号天富7号", "50818765"],
    ["天富7号天富7号场外缺省", "123456"],
    ["智盈8号智盈8号", "123"],
]
accountFund = [
    ["accountID", "产品名称",'',getFundName,productName],
    ["currentBalance", "当前现金余额" , 0],
    ["enableBalance", "当前现金余额", 0],
    ["fetchBalance", "当前现金余额", 0],
    ["marketValue", "股票+基金资产", 0],
    ["assetBalance", "现货总资产", 0],
]


# 持仓对应关系，第三参数是默认值，如果是中文的比例证券名称，第三参数不要填写
accountPosition = [
    ['accountID', "产品名称",'',getFundName,productName],
    ['exchangeName', "交易市场", EXCHANGE_TYPE_UNKNOWN, getMarket],
    ['stockCode', "证券代码"],
    ['stockName', "证券名称"],
    ['totalAmt', "持仓数量",0],
    ['enableAmount', "可用数量",0],
    ['lastPrice', "最新价",0],
    ['marketValue', "持仓市值(净价)",0],
    ['costBalance', "当前成本", 0],
    ['costPrice', "成本价",0],
    ['income', "柜台盈亏"],
]

accountOrder = [
    #["fundAccount", "资金账号"],
    ['accountID', "产品名称",'',getFundName,productName],
    ["entrustNo", "委托批号",''],
    ["exchangeName", "交易市场",EXCHANGE_TYPE_UNKNOWN, getMarket],
    ["stockCode", "证券代码"],
    ["stockName", "证券名称"],
    ["entrustDate", "业务日期",'', getEntrustDate],
    ["entrustTime", "委托时间", "", getEntrustTime],
    ["bsflage", "委托方向", "", getEntrustBS],
    ["entrustStatusName", "委托状态"],
    ["entrustPrice", "委托价格",'0'],
    ["entrustAmount", "委托数量",'0'],
    ["bizAmount", "成交数量",'0'],
    ["cancelAmount", "撤单数量",'0'],
    ["bizPrice", "成交均价",'0'],
    ["entrustTypeName", "价格类型",0],
    ["cancelInfo", "废单原因",''],

]

accountDeal = [
    #["fundAccount", "资金账号"],
    ['accountID', "产品名称",'',getFundName,productName],
    ["bizDate", "业务日期", '', getEntrustDate],
    ["bizTime", "成交时间", "", getEntrustTime],
    ["entrustNo", "委托批号"],
    ["exchangeName", "交易市场", EXCHANGE_TYPE_UNKNOWN, getMarket],
    ["stockCode", "证券代码"],
    ["stockName", "证券名称"],
    ["bizNo", "成交序号"],
    ["bsflage", "委托方向"],
    ["bizAmount", "成交数量",'0'],
    ["bizBalance", "成交金额",'0'],
    ["bizPrice", "成交均价", '0'],
]



def getWorkFiles(filePath, key):
    ret = []
    fileList = os.listdir(filePath)
    try:
        for i in range(0, len(fileList)):
            fileFullName = fileList[i]
            if fileFullName.endswith(key + ".csv") or fileFullName.endswith(key + ".xlsx") or fileFullName.endswith(key + ".XLS") or fileFullName.endswith(key + ".XLSX"):
                ret.append(fileFullName)
    except Exception, e:
        emailMag(filePath + key + "get work file error")
    if(len(ret) == 0):
        emailMag(filePath + key + ".csv not found")
    return ret

def translateXls2Csv(fileName, ifilename, translateTable, headpos):
    workbook = csv.reader(open(fileName))
    direAll = {}
    lineNum =0
    for row in workbook:
        direAll[lineNum] = row
        lineNum += 1
    #获取目标csv文件第一行描述
    sheets = direAll[0]
    #print len(direAll)

    #为了防止文件名和文件内容对应不上，加此判断
    if (fileName.find("dealdetail") > 0 and ("成交编号".decode('utf-8').encode('gbk') in sheets or "成交均价".decode('utf-8').encode('gbk') in sheets)):
        pass
    elif (fileName.find("order") > 0 and ("成交编号".decode('utf-8').encode('gbk') not in sheets) and (("委托编号".decode('utf-8').encode('gbk')  in sheets) or ("委托价格".decode('utf-8').encode('gbk')  in sheets))):
        pass
    elif (fileName.find("position") > 0 and ("可用数量".decode('utf-8').encode('gbk') in sheets or "持仓数量".decode('utf-8') in sheets)):
        pass
    elif (fileName.find("fund") > 0 and ("总资产".decode('utf-8').encode('gbk') in sheets or "回购资产".decode('utf-8').encode('gbk') in sheets)):
        pass
    else:
        return None

    outPutFile = CSV_OUTPUT_PATH + ifilename
    csv_file = file( '{xlsx}.csv'.format(xlsx=os.path.splitext(outPutFile.replace('_hs', ''))[0]), 'wb')
    csv_file_writer = csv.writer(csv_file)

    listHead = []
    for matcher in translateTable:
        listHead.append(matcher[0])

    #打印测试 修改编码格式
    shee = []
    for v in sheets:
        shee.append(v.decode('gbk').encode('utf-8'))
        #print v.decode('gbk').encode('utf-8')
    csv_file_writer.writerow(listHead)
    for pos in range(1,len(direAll)):
        listData = []
        for matcher in translateTable:
            val = ""
            if len(matcher) >= 4:
                if (matcher[1] in shee):
                    index = shee.index(matcher[1])
                    tmp = direAll[pos][index]
                    #处理账号问题
                    if (matcher[1] == "产品名称"):
                        #专门处理的accountId
                        index = shee.index("单元名称")
                        tm = direAll[pos][index]
                        tmp = tmp + tm
                        print(tmp.decode('gbk').encode('utf-8'))
                        val = matcher[3](matcher[4],tmp.decode('gbk').encode('utf-8'), matcher[2])
                    else:
                        val = matcher[3](tmp.decode('gbk').encode('utf-8'), matcher[2])

            elif len(matcher) >= 2:
                if (matcher[1] in shee):
                    index = shee.index(matcher[1])
                    val = direAll[pos][index]
                    val = val.decode('gbk').encode('utf-8')
            if len(matcher) == 3 and ( val == None or val == ""):
                val = matcher[2]
            listData.append(val)
        csv_file_writer.writerow(listData)
    csv_file.close()

def getFundData(filePath, suffix):
    lWorkFiles = []
    key = "fund" + suffix
    headpos = 1
    lWorkFiles = getWorkFiles(filePath, key)
    for ifile in lWorkFiles:
        print ifile
        translateXls2Csv(filePath + ifile, ifile, accountFund, headpos)

def getPositionData(filePath, suffix):
    lWorkFiles = []
    key = "position" + suffix
    headpos = 1
    lWorkFiles = getWorkFiles(filePath, key)
    print(lWorkFiles)
    for ifile in lWorkFiles:
        print(ifile)
        translateXls2Csv(filePath + ifile, ifile, accountPosition, headpos)

def getOrderData(filePath, suffix):
    lWorkFiles = []
    key = "order" + suffix
    headpos = 1
    lWorkFiles = getWorkFiles(filePath, key)
    for ifile in lWorkFiles:
        translateXls2Csv(filePath + ifile, ifile, accountOrder, headpos)

def getDealData(filePath, suffix):
    lWorkFiles = []
    key = "dealdetail" + suffix
    headpos = 1
    lWorkFiles = getWorkFiles(filePath, key)
    for ifile in lWorkFiles:
        translateXls2Csv(filePath + ifile, ifile, accountDeal, headpos)

def translateExlToCsv(filePath, suffix):
    getFundData(filePath, suffix)
    getPositionData(filePath, suffix)
    getOrderData(filePath, suffix)
    getDealData(filePath, suffix)

def startWork(filePath, suffix):
    try:
        delCsvFiles(CSV_OUTPUT_PATH, suffix)
        translateExlToCsv(filePath, suffix)
    except Exception, e:
        traceback.print_exc()

if __name__ == '__main__':
    startWork(getGBK(LOG_FILE_PATH), "_hs")
