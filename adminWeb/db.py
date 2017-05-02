import config, model

def test():
    try:
        conn=MySQLdb.connect(host='localhost',user='root',passwd='',db='captcha',port=3306)
        cur=conn.cursor()
        count = cur.execute('select * from userinfo')
        print(count)
        result = cur.fetchone()
        print(result)
        cur.close()
        conn.close()
    except MySQLdb.Error,e:
        print "Mysql Error %d: %s" % (e.args[0], e.args[1])

def addUser(user):
    n = config.DB.insert('userinfo', \
                  account=user.account, \
                  password=user.password, \
                  leftCount = user.leftCount, \
                  calledCount = user.calledCount, \
                  successCount = user.successCount, \
                  regTime=user.regTime)
    print("n=" + str(n))
    if n != 5:
        print("insert error")

def addRecord(record):
    n = config.DB.insert('record', \
                         userid = record.userid, \
                         tradeNumber = record.tradeNumber, \
                         money = record.money, \
                         count = record.count, \
                         addTime = record.tradeTime, \
                         result = record.result, \
                         comment = record.comment)
    print("n=" + str(n))
        
def testInsertUser():
    user = model.userinfo()
    user.account = "test2"
    user.password = "password"
    user.leftCount = 1000
    user.calledCount = 2
    addUser(user)

def testInsertRecord():
    record = model.record(2, "101100122108329219302183989", 10, 20000)
    addRecord(record)

def testSelect():
    myvar = dict(account="zhangda")
    results = config.DB.select('userinfo', myvar, where="account = $account")
    #print(results[0].account)
    print(len(results))

if __name__ == "__main__":
    #testInsertUser()
    #testInsertRecord()
    testSelect()
