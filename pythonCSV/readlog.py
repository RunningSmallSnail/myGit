#encoding:utf8
__author__ = 'RZRK'

import os
import logging
import time
import datetime

import traceback
import ConfigParser
from dbfpy import dbf
import codecs

import smtplib
from email.mime.text import MIMEText
from email.header import Header

def getGBK(raw):
    if type(raw) == str:
        return raw.decode('utf-8').encode('gbk')
    elif type(raw) == unicode:
        return raw.encode("gbk")
    return raw

logger = logging.getLogger(__name__)
logger.setLevel(level = logging.INFO)
handler = logging.FileHandler("log/readlog.log")
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

config = ConfigParser.ConfigParser()
try:
    config.readfp(codecs.open('.\\config.ini', "r", "utf-8-sig"))
except Exception, e:
    logger.info(str(traceback.format_exc()))
    exit()

LOG_FILE_PATH = getGBK(config.get("filePath","LOG_FILE_PATH"))
logger.info(LOG_FILE_PATH)
CSV_OUTPUT_PATH = getGBK(config.get("filePath","CSV_OUTPUT_PATH"))
logger.info(CSV_OUTPUT_PATH)
TEST_MODE = config.get("filePath","TEST_MODE") == "1"
logger.info(TEST_MODE)
STARTED_TIME = config.get("filePath","STARTED_TIME")
STOP_TIME = config.get("filePath","STOP_TIME")

#处理输出目录 不存在就创建，存在就加上 \
if (not os.path.exists(CSV_OUTPUT_PATH)):
    os.makedirs(CSV_OUTPUT_PATH)
CSV_OUTPUT_PATH = CSV_OUTPUT_PATH + "\\"
#print(CSV_OUTPUT_PATH)

#邮件相关
sender = getGBK(config.get("mail","SENDER"))
receivers = getGBK(config.get("mail","RECEIVER"))
username = config.get("mail","USERNAME")
password = config.get("mail","PASSWORD")
reliableTime = config.get("mail","RELIABLE_TIME")
logger.info(receivers)
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

DATESTR = time.strftime('%Y-%m-%d',time.localtime(time.time()))
DATESTR_WITHOUT_LINE = time.strftime('%Y%m%d',time.localtime(time.time()))

if TEST_MODE:
    DATESTR = "2018-04-13"
    DATESTR_WITHOUT_LINE = "20180413"

ORDER_FILE = "Tentrusts_" + DATESTR_WITHOUT_LINE + ".log"
DEAL_FILE = "Trealdeal_" + DATESTR_WITHOUT_LINE + ".log"
POS_FILE = "CC_HHCSK5VTNSFMLA3P5J4Q_" + DATESTR_WITHOUT_LINE + ".log"
FUND_FILE = "ZJ_HHCSK5VTNSFMLA3P5J4Q_" + DATESTR_WITHOUT_LINE + ".log"

#由于计算港股市值的原因，改了此处的匹配关系 原来 n 是 沪港通 o 是深港通

MARKETMAP = {"1":"上证所",
             "2":"深交所",
             "n":"上证所",
             "o":"深交所",}

OPTMAP = {"1":"买入",
          "2":"卖出",
          "6":"卖出",
          "0B":"买入",
          "B":"买入",
          "C":"买入",
          "S":"卖出",
          "q":"卖出",
          "0S":"卖出",}

STATUSMAP = {"1":"已报",
          "2":"已报",
          "3":"已报",
          "4":"已报",
          "5":"废单",
          "6":"部成",
          "7":"已成",
          "8":"部撤",
          "9":"已撤",
          "a":"已报",
          "b":"已报",
          "c":"已报",}


stockholder2acc = {}

def getStatusByMap(status):
    if status == "5" or status == "8" or status == "9":
    #if STATUSMAP.has_key(status):
        return STATUSMAP[status]
    else:
        return STATUSMAP["1"]

def readData(oriStr, retDict, keyStr, lastCursor, cursor):
    retDict[keyStr] = oriStr[lastCursor - 1 : cursor - 1].strip()
    if keyStr == "stockholder" and len(retDict[keyStr]) > 0:
        retDict[keyStr] = retDict[keyStr].zfill(10)
    return cursor

def isAvailableTime(filePath):
    #判断文件是否在规定时间内发生变化
    nowTime = time.localtime(time.time())
    lastExchangeTime= time.localtime(os.stat(filePath).st_mtime)
    nowTime =time.strftime("%Y%m%d%H%M%S",nowTime)
    lastExchangeTime =time.strftime("%Y%m%d%H%M%S",lastExchangeTime)
    #最后修改时间大于 设定的可信赖时间
    if((int(nowTime) - int(lastExchangeTime))> int(reliableTime)):
        return False
    else:
        return True

def readOrder(filePath):
    orders = {}
    cancels = {}
    if(not os.path.exists(filePath + ORDER_FILE)):
        emailMag("order log not found")
        logger.info("order log not found " + filePath + ORDER_FILE)
        return None
    else:
        if(not isAvailableTime(filePath + ORDER_FILE)):
            emailMag("order log not changed in set time ")
            logger.info("order log not changed in set time ")
    try:
        db = dbf.Dbf(filePath + ORDER_FILE, True)
        fields = []
        for field in db.fieldNames:
            fields.append(field)
        for record in db:
            dataDict = {}
            dataDict["date"] = record["JLSJC"].split(" ")[0]
            dataDict["timeLog"] = record["JLSJC"].split(" ")[1]
            dataDict["type"] = record["SJLX"]
            dataDict["weituoxuhao"] = record["WTXH"]
            dataDict["entrustBS"] = str(record["WTFX"])
            dataDict["price"] = record["WTJG"]
            dataDict["vol"] = str(record["WTSL"])
            dataDict["code"] = record["ZQDM"]
            dataDict["stockholder"] = record["GDDM"]
            dataDict["amount"] = record["WTJE"]
            dataDict["market"] = str(record["MAKT"])
            #因为港股的代码是5位，所以补位 分开处理
            if(dataDict["market"] == 'o' or dataDict["market"] == 'n'):
                dataDict["code"] = dataDict["code"].zfill(5)
            else:
                dataDict["code"] = dataDict["code"].zfill(6)
            dataDict["account"] = record["ZJZH"]
            dataDict["time"] = record["WTSJ"]
            dataDict["productid"] = record["ZCDY"]
            dataDict["SBFX"] = record["SBFX"]
            dataDict["orderstatus"] = str(record["WTZT"])
            if dataDict["type"].find("dbquery") >= 0:
                dataDict["orderstatus"] = getStatusByMap(dataDict["orderstatus"])
            else:
                dataDict["orderstatus"] = getStatusByMap("1")
            dataDict["weituopihao"] = record["WTPH"]
            if not dataDict["type"].find("wthdrw") >= 0:
                orders[dataDict["weituopihao"]] = dataDict
            else:
                cancels[dataDict["weituopihao"]] = dataDict
                #print dataDict["weituoxuhao"], dataDict["weituopihao"], dataDict
                #此处觉得应该都给上 账号
            if len(dataDict["account"]) > 0:
                stockholder2acc[dataDict["stockholder"]] = dataDict["account"]
            else:
                if stockholder2acc.has_key(dataDict["stockholder"]):
                    dataDict["account"] = stockholder2acc[dataDict["stockholder"]]

        #print len(orders)
        entrusts = []
        kk = 1
        for i in orders:
            entrusts.append(orders[i]["weituopihao"])
            #print orders[i]
            #break
        entrusts.sort()
        #print len(cancels)
        cans = []
        for i in cancels:
            cans.append(cancels[i]["weituopihao"])
        cans.sort()
        # for val in orders.items():
        #     print(val)
        # for val in cancels.items():
        #     print(val)
    except Exception, e:
        strWarn = "order warn, "
        logger.info(strWarn)
        emailMag(strWarn)
        logger.info(str(e.message) + " " + str(traceback.format_exc()))
    return orders, cancels

def readDeal(filePath):
    deals = {}
    if(not os.path.exists(filePath + DEAL_FILE)):
        emailMag("deal log not found")
        logger.info("deal log not found " + filePath + DEAL_FILE )
        return None
    else:
        if(not isAvailableTime(filePath + DEAL_FILE)):
            emailMag("deal log not changed in set time ")
            logger.info("deal log not changed in set time ")
    try:
        db = dbf.Dbf(filePath + DEAL_FILE, True)
        fields = []
        for field in db.fieldNames:
            fields.append(field)
        for record in db:
            #print i
            dataDict = {}
            dataDict["date"] = record["JLSJC"].split(" ")[0]
            dataDict["timeLog"] = record["JLSJC"].split(" ")[1]
            dataDict["type"] = record["SJLX"]
            dataDict["dateStr"] = record["FSRQ"]
            dataDict["chengjiaoxuhao"] = str(record["CJXH"])
            dataDict["chengjiaobianhao"] = record["CJBH"]
            dataDict["weituopihao"] = str(record["WTXH"])
            dataDict["code"] = record["ZQDM"]
            dataDict["market"] = record["JYSC"]
            #因为港股的代码是5位，所以补位 分开处理
            if(dataDict["market"] == 'o' or dataDict["market"] == 'n'):
                dataDict["code"] = dataDict["code"].zfill(5)
            else:
                dataDict["code"] = dataDict["code"].zfill(6)
            dataDict["stockholder"] = record["GDDM"]
            dataDict["time"] = record["CJSJ"]
            dataDict["vol"] = str(record["CJSL"])
            dataDict["price"] = record["CJJG"]
            dataDict["amount"] = record["CJJE"]
            dataDict["fee"] = record["TOTALFEE"]#佣金+税
            dataDict["ordervol"] = record["WTSL"]
            dataDict["price2"] = record["PRICE"]
            dataDict["volinorder"] = record["DRSL"]
            dataDict["amountinorder"] = record["DRJE"]
            dataDict["weituopihao2"] = record["WTPH"]
            dataDict["entrustBS"] = record["SBFX"]
            if stockholder2acc.has_key(dataDict["stockholder"]):
                dataDict["account"] = stockholder2acc[dataDict["stockholder"]]
            deals[dataDict["weituopihao"] + "_" + dataDict["chengjiaoxuhao"]] = dataDict
            #print dataDict
            #break
    except Exception, e:
        strWarn = "deal warn, "
        logger.info(strWarn)
        emailMag(strWarn)
        logger.info(str(e.message) + " " + str(traceback.format_exc()))
    #print stockholder2acc
    return deals

def readFund(filePath):
    fundes = {}
    if(not os.path.exists(filePath + FUND_FILE)):
        emailMag("fund log not found")
        logger.info("fund log not found " + filePath + FUND_FILE)
        return None
    else:
        if(not isAvailableTime(filePath + FUND_FILE)):
            emailMag("fund log not changed in set time ")
            logger.info("fund log not changed in set time " )
    try:
        db = dbf.Dbf(filePath + FUND_FILE, True)
        fields = []
        for field in db.fieldNames:
            fields.append(field)
        for record in db:
            dataDict = {}
            # for field in db.fieldNames:
            #     print field, record[field]
            dataDict["account"] = record["ZJZH"]
            # dataDict["dangqianxianjinyue"] = record["DQYE"]
            # dataDict["dAvailable_t+0"] = record["KYZJ"]
            dataDict["dangqianxianjinyue"] = record["KYZJ"]
            dataDict["dAvailable_t+0"] = record["DQYE"]
            fundes[dataDict["account"]] = dataDict
    except Exception, e:
        strWarn = "Pos warn, "
        logger.info(strWarn)
        emailMag(strWarn)
        logger.info(str(e.message) + " " + str(traceback.format_exc()))
    return fundes

# def readFund():
#     with open(LOG_FILE_PATH + FUND_FILE, 'r') as file:
#         lines = file.read()
#     strList = []
#     lenN = len(lines)
#     last = 162
#     while last < lenN:
#         strList.append(lines[last : last + 61])
#         last += 61
#     fundes = {}
#     for i in strList:
#         dataDict = {}
#         datas = i.split(" ")
#         datas = [j.strip() for j in datas if len(j) > 0]
#         dataDict["k1"] = datas[0]
#         dataDict["account"] = datas[1]
#         dataDict["dangqianxianjinyue"] = datas[3]
#         dataDict["dAvailable_t+0"] = datas[2]
#         fundes[dataDict["account"]] = dataDict
#     # for i in fundes:
#     #     print fundes[i]
#     # print len(fundes)
#     return fundes

def readPos(filePath):
    poses = {}
    if(not os.path.exists(filePath + POS_FILE)):
        emailMag("position log not found")
        logger.info("position log not found " + filePath + POS_FILE)
        return None
    else:
        if(not isAvailableTime(filePath + POS_FILE)):
            emailMag("position log not changed in set time")
            logger.info("position log not changed in set time")
    try:
        db = dbf.Dbf(filePath + POS_FILE, True)
        fields = []
        for field in db.fieldNames:
            fields.append(field)
        for record in db:
            dataDict = {}
            #for field in db.fieldNames:
                #print field, record[field]
            dataDict["account"] = record["ZJZH"]
            dataDict["stockholder"] = record["GDZH"]
            dataDict["market"] = record["SCBH"]
            dataDict["code"] = record["ZQDM"]
            #因为港股的代码是5位，所以补位 分开处理
            if(dataDict["market"] == 'o' or dataDict["market"] == 'n'):
                dataDict["code"] = dataDict["code"].zfill(5)
            else:
                dataDict["code"] = dataDict["code"].zfill(6)
            dataDict["chsname"] = record["ZQMC"]
            dataDict["allvol"] = record["DQSL"]
            dataDict["canuse"] = record["KYSL"]
            dataDict["cost"] = record["DQCB"]
            dataDict["income"] = record["FDYK"]
            poses[dataDict["account"] + "_" + dataDict["market"] + "_" + dataDict["code"]] = dataDict
    except Exception, e:
        strWarn = "Pos warn, "
        logger.info(strWarn)
        emailMag(strWarn)
        logger.info(str(e.message) + " " + str(traceback.format_exc()))
    return poses

# def readPos():
#     with open(LOG_FILE_PATH + POS_FILE, 'r') as file:
#         lines = file.read()
#     strList = []
#     lenN = len(lines)
#     last = 418
#     while last < lenN:
#         strList.append(lines[last : last + 269])
#         last += 269
#     poses = {}
#     for i in strList:
#         #print i
#         dataDict = {}
#         datas = i.split(" ")
#         datas = [j.strip() for j in datas if len(j) > 0]
#         #print datas
#         dataDict["k1"] = datas[0]
#         dataDict["account"] = datas[1]
#         dataDict["k2"] = datas[2][0:1]
#         dataDict["stockholder"] = datas[2][1:]
#         dataDict["market"] = datas[3][0:1]
#         dataDict["code"] = datas[3][1:]
#         dataDict["chsname"] = datas[4]
#         dataDict["allvol"] = datas[5]
#         dataDict["canuse"] = datas[6]
#         dataDict["cost"] = datas[7]
#         dataDict["income"] = datas[8]
#         poses[dataDict["account"] + "_" + dataDict["market"] + "_" + dataDict["code"]] = dataDict
#
#     # for i in poses:
#     #     print poses[i]
#     # print len(poses)
#     return poses

def writeFund(datas,num):
    filename = CSV_OUTPUT_PATH + "_"+ str(num) + "_fund.csv"
    with open(filename,'w') as fileAcc:
        fileAcc.write("证券公司,资金账号,账号名称,账号类型,产品名称,冻结金额,总资产,可用金额,手续费,盈亏,总市值,上次质押金额,质押金额,可取金额,交易日,股票总市值,债券总市值,基金总市值,回购总市值,净资产,总负债,申购费,币种".decode("utf-8").encode("gbk"))
        fileAcc.write("\n")
        for i in datas:
            try:
                strTmp = ",%s,,主账号,,,,%s,,,,,,%s,%s,,,,,,,,"%(datas[i]["account"],datas[i]["dAvailable_t+0"],datas[i]["dAvailable_t+0"],DATESTR)
                fileAcc.write(strTmp.decode("utf-8").encode("gbk"))
                fileAcc.write("\n")
            except Exception, e:
                strWarn = "fund warn, " + str(i)
                logger.info(strWarn)
                emailMag(strWarn)
                logger.info(str(e.message) + " " + str(traceback.format_exc()))

def writePos(datas,num):
    filename = CSV_OUTPUT_PATH +  "_"+ str(num) + "_position.csv"
    with open(filename,'w') as fileAcc:
        fileAcc.write("证券公司,资金账号,账号名称,账号类型,产品名称,市场名称,证券代码,证券名称,当前拥股,成本价,当前成本,市值,盈亏,股东账号,冻结数量,可用余额,在途股份,昨夜拥股,最新价,盈亏比例,成交类型,到期日,组合成交号,组合序号,累计成本,单股成本,分级基金可用,分级基金可赎回量,ETF申赎可用量,成本跌幅止损,当日跌幅止损".decode("utf-8").encode("gbk"))
        fileAcc.write("\n")
        for i in datas.values():
            try:
                allvol = int(float(i["allvol"]) + 1e-3)
                singleCost = 0
                marketValue = 0
                if not allvol == 0:
                    singleCost = float(i["cost"]) / allvol
                    marketValue = (float(i["cost"])+float(i["income"]))/allvol
                strTmp = ",%s,,主账号,,%s,%s,%s,%s,%s,%s,%s,%s,,,%s,,,%s,,普通成交,,,2147483647,,,0,0,0,,"\
                         %(i["account"],MARKETMAP[i["market"]],i["code"],i["chsname"].decode("gbk").encode("utf-8"),i["allvol"],str(singleCost), i["cost"], str(float(i["cost"])+float(i["income"])),i["income"],\
                           i["canuse"],str(marketValue))
                fileAcc.write(strTmp.decode("utf-8").encode("gbk"))
                fileAcc.write("\n")
            except Exception, e:
                strWarn = "pos warn, " + str(i)
                logger.info(strWarn)
                emailMag(strWarn)
                logger.info(str(e.message) + " " + str(traceback.format_exc()))

def writeDeals(datas,num):
    filename = CSV_OUTPUT_PATH +  "_"+ str(num) + "_dealdetail.csv"
    with open(filename,'w') as fileAcc:
        fileAcc.write("证券公司,资金账号,账号名称,账号类型,产品名称,指令编号,报单来源,交易市场,证券代码,证券名称,成交编号,合同编号,操作,成交价格,成交数量,成交日期,成交时间,手续费,成交金额,买卖标记,委托类别,投资备注".decode("utf-8").encode("gbk"))
        fileAcc.write("\n")
        for i in datas.values():
            try:
                strTmp = ",%s,,主账号,,,,%s,%s,,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,买卖,"\
                         %(i["account"],MARKETMAP[i["market"]],i["code"],i["chengjiaoxuhao"],i["weituopihao2"], OPTMAP[i["entrustBS"]], i["price"], i["vol"],i["date"].replace("-", ""),i["time"],i["fee"],i["amount"],\
                           OPTMAP[i["entrustBS"]])
                fileAcc.write(strTmp.decode("utf-8").encode("gbk"))
                fileAcc.write("\n")
            except Exception, e:
                strWarn = "deal warn, " + str(i)
                logger.info(strWarn)
                emailMag(strWarn)
                logger.info(str(e.message) + " " + str(traceback.format_exc()))

def writeCancleDeals(datas,num):
    filename = CSV_OUTPUT_PATH +  "_"+ str(num) + "_dealdetail.csv"
    with open(filename,'a') as fileAcc:
        #fileAcc.write("证券公司,资金账号,账号名称,账号类型,产品名称,指令编号,报单来源,交易市场,证券代码,证券名称,成交编号,合同编号,操作,成交价格,成交数量,成交日期,成交时间,手续费,成交金额,买卖标记,委托类别,投资备注".decode("utf-8").encode("gbk"))
        #fileAcc.write("\n")
        for i in datas.values():
            try:
                strTmp = ",%s,,主账号,,,,%s,%s,,,%s,,,%s,%s,,,,,,"\
                         %(i["account"],MARKETMAP[i["market"]],i["code"],i["weituopihao"],'-'+i["vol"],i["date"].replace("-", "")  )
                #print (type(strTmp))
                #print (strTmp)
                fileAcc.write(strTmp.decode("utf-8").encode("gbk"))
                fileAcc.write("\n")
            except Exception, e:
                strWarn = "writeCancleDeals warn, " + str(i)
                logger.info(strWarn)
                emailMag(strWarn)
                logger.info(str(e.message) + " " + str(traceback.format_exc()))

def writeOrders(datas,num):
    filename = CSV_OUTPUT_PATH + "_" + str(num) + "_order.csv"
    with open(filename,'w') as fileAcc:
        fileAcc.write("证券公司,资金账号,账号名称,账号类型,产品名称,指令编号,报单来源,交易市场,证券代码,证券名称,委托价格,委托量,合同编号,委托状态,成交数量,委托剩余量,冻结金额,冻结手续费,委托日期,委托时间,成交均价,已撤数量,买卖标记,委托类别,废单原因".decode("utf-8").encode("gbk"))
        fileAcc.write("\n")
        for i in datas.values():
            try:
                strTmp = ",%s,,主账号,,,,%s,%s,,%s,%s,%s,%s,,,,,%s,%s,,,%s,买卖,"\
                         %(i["account"],MARKETMAP[i["market"]],i["code"],i["price"],i["vol"],i["weituopihao"], i["orderstatus"], i["date"].replace("-", ""),i["time"],OPTMAP[i["entrustBS"]])
                fileAcc.write(strTmp.decode("utf-8").encode("gbk"))
                fileAcc.write("\n")
            except Exception, e:
                strWarn = "order warn, " + str(i)
                logger.info(strWarn)
                emailMag(strWarn)
                logger.info(str(e.message) + " " + str(traceback.format_exc()))

def readInfo(filePath,i):
    logger.info("start")
    orders, cancels = readOrder(filePath)
    deals = readDeal(filePath)
    funds = readFund(filePath)
    poses = readPos(filePath)
    writeOrders(orders,i)
    logger.info("order done, len is " + str(len(orders)))
    writeDeals(deals,i)
    logger.info("deal done, len is " + str(len(deals)))
    writeCancleDeals(cancels,i)
    print "cancelDeal done"
    writeFund(funds,i)
    logger.info("funds done, len is " + str(len(funds)))
    writePos(poses,i)
    logger.info("pos done, len is " + str(len(poses)))
    logger.info("all done, wait next")
    print "all done, wait next"

def fixFileName(filePath):
    global POS_FILE, FUND_FILE
    try:
        files = os.listdir(filePath)
        for i in files:
            if i.startswith("CC") and i.endswith(DATESTR_WITHOUT_LINE + ".log"):
                POS_FILE = i
            if i.startswith("ZJ") and i.endswith(DATESTR_WITHOUT_LINE + ".log"):
                FUND_FILE = i
    except Exception, e:
            logger.info(str(traceback.format_exc()))
            exit()
    logger.info(POS_FILE + ", " + FUND_FILE)

def delCsvFiles(filePath):
    fileList = os.listdir(filePath)
    for i in range(0, len(fileList)):
        fileFullName = fileList[i]
        if fileFullName.endswith('.csv'):
            os.remove(filePath + fileFullName)

if __name__ == "__main__":
    logger.info("main started")
    STARTED_TIME = time.strptime(STARTED_TIME, "%H:%M:%S")
    STOP_TIME = time.strptime(STOP_TIME, "%H:%M:%S")
    STARTED_TIME = time.strftime("%H%M%S", STARTED_TIME)
    STOP_TIME = time.strftime("%H%M%S", STOP_TIME)
    logger.info(str(STARTED_TIME))
    logger.info(str(STOP_TIME))
    logger.info(str(LOG_FILE_PATH))
    logFilePath = LOG_FILE_PATH.split(';')
    j = 0
    for i in range(1440):
        #是转化时间，为比较时间做准备
        timeLocal = time.localtime(time.time())
        timeLocal = time.strftime("%H%M%S",timeLocal)
        logger.info(timeLocal)
        startTime = int(STARTED_TIME) - int(timeLocal)
        stopTime = int(timeLocal) - int(STOP_TIME)
        if(startTime <= 0 and stopTime <= 0):
            #delete old file
            logger.info(str("del file " + CSV_OUTPUT_PATH))
            delCsvFiles(CSV_OUTPUT_PATH)
            for filePath in logFilePath:
                j += 1
                filePath = filePath + "\\"
                fixFileName(filePath)
                try:
                    print(filePath)
                    readInfo(filePath,j)
                except Exception, e:
                    logger.info(str(traceback.format_exc()))
                    emailMag("转换出错，请及时查看日志转换")
                finally:
                    pass
            time.sleep(60)#单位秒

