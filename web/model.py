import datetime

class userinfo():
    def __init__(self):
        self.__init__(self, None, None, None, None, None, None)
    def __init__(self, account, password, leftCount, calledCount, \
                 successCount,parentid, token=""):
        self.account = account
        self.password = password
        self.leftCount = leftCount
        self.calledCount = calledCount
        self.successCount = successCount
        self.parentid = parentid
        self.token = token
        self.regTime = datetime.datetime.utcnow()

class record():
    def __init__(self):
        self.__init__(self, None, None, None, None, False, None)
    def __init__(self, userid, tradeNumber, money, count):
        self.__init__(self, userid, tradeNumber, money, count, False, None)
    def __init__(self, userid, tradeNumber, money, count, result, comment):
        self.userid = userid
        self.tradeNumber = tradeNumber
        self.money = money
        self.count = count
        self.tradeTime = datetime.datetime.utcnow()
        self.result = result
        self.comment = comment
