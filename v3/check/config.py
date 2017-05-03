import threading
import MySQLdb
from DBUtils.PooledDB import PooledDB
import memcache, time

host='221.206.125.7'
user='captcha'
passwd='1234'
db='test'
port=3306
memServer='221.206.125.7:12000'

tokenLock = threading.Lock()
subuserLock = threading.Lock()

pool = PooledDB(MySQLdb,mincached=2,maxcached=100,maxshared=100,maxconnections=100,host=host,user=user,passwd=passwd,db=db,port=port)
mc = memcache.Client([memServer], debug=0)

_USERNAME="_USERNAME"
_PASSWORD="_PASSWORD"
_LEFTCOUNT="_LEFTCOUNT"
_CALLEDCOUNT="_CALLEDCOUNT"
_SUCCESSCOUNT="_SUCCESSCOUNT"
_TOKEN="_TOKEN"
_STATUS="_STATUS"
_PARENTID="_PARENTID"

def checkToken(token):
    try:
        conn = pool.connection()
        #conn=MySQLdb.connect(host=host,user=user,passwd=passwd,db=db,port=port)
        cur=conn.cursor()
        #if token.find("=") != -1 or token.find("'") != -1 or token.find("\"")!= -1 or token.find("delete") != -1:
        #    return '1004'    
        #if token.find("union") != -1 or token.find(",") != -1 or token.find("?") != -1 or token .find(";") != -1:
        #    return '1004'
        if checkSpecial(token):
            return '1004'
        cur.execute("select * from userinfo where token='%s' and status=0" % (token))
        rows = cur.fetchall()
        if int(cur.rowcount) <= 0:
            cur.close()
            conn.close()
            return "1001"
        cur.close()
        conn.close()
        #should check mem here, after mysql select, to prevent wrong token lock
        tokenLock.acquire()
        if mc.get(token) != None:
            tokenLock.release()
            return "0"
        row = rows[0]
        #this id is author id
        authorID = row[0]
        #set username and token to ID
        mc.set(str(token),authorID)
        mc.set(str(row[1]),authorID)
        mc.set(str(authorID)+_USERNAME,row[1])
        mc.set(str(authorID)+_PASSWORD,row[2])
        mc.set(str(authorID)+_LEFTCOUNT,row[3])
        mc.set(str(authorID)+_CALLEDCOUNT,row[4])
        mc.set(str(authorID)+_SUCCESSCOUNT,row[5])
        mc.set(str(authorID)+_TOKEN,row[7])
        mc.set(str(authorID)+_STATUS,row[10])
        mc.set(str(authorID)+_PARENTID,row[11])
        tokenLock.release()
        return "0"
    except MySQLdb.Error,e:
        print "Mysql Error %d: %s" % (e.args[0], e.args[1])
        LOG.log.error("Mysql Error %d: %s, %s" % (e.args[0], e.args[1], "select ID from userinfo where token"))
        flag='error'
        if cur != None:
            cur.close()
        if conn != None:
            conn.close()
        tokenLock.release()
        return "1004"

def checkSpecial(token):
    if token == None:
        return True
    token = str(token)
    if token.find("=") != -1 or token.find("'") != -1 or token.find("\"")!= -1 or token.find("delete") != -1:
        return True
    if token.find("union") != -1 or token.find(",") != -1 or token.find("?") != -1 or token .find(";") != -1:
        return True
    if token.find("--") != -1 or token.find("version") != -1 or token.find("select") != -1 or token.find("top") != -1 or token.find("name") != -1:
        return True
    return False

def checkSubUser(userN,passW,authorID):
    try:
        if checkSpecial(userN) or checkSpecial(passW) or checkSpecial(authorID):
            return '1004'
        conn = pool.connection()
        #conn=MySQLdb.connect(host=host,user=user,passwd=passwd,db=db,port=port)
        cur=conn.cursor()
        sql = ("select * from userinfo where account='%s' and password='%s' and parentid = '%s' and status=0" % (userN,passW,authorID))
        cur.execute(sql)
        rows = cur.fetchall()
        if int(cur.rowcount) <= 0:
            cur.close()
            conn.close()
            return '1001'
        elif rows[0][3] <= 0:
            #left count not enough
            cur.close()
            conn.close()
            return '1002'
        cur.close()
        conn.close()
        #should check mem here, after mysql select, to prevent wrong token lock
        subuserLock.acquire()
        if mc.get(userN) != None:
            subuserLock.release()
            return "0"
        row = rows[0]
        #this id is author id
        SubUserID = row[0]
        #set username and token to ID
        #mc.set(token,SubUserID)
        mc.set(str(row[1]),SubUserID)
        mc.set(str(SubUserID)+_USERNAME,row[1])
        mc.set(str(SubUserID)+_PASSWORD,row[2])
        mc.set(str(SubUserID)+_LEFTCOUNT,row[3])
        mc.set(str(SubUserID)+_CALLEDCOUNT,row[4])
        mc.set(str(SubUserID)+_SUCCESSCOUNT,row[5])
        mc.set(str(SubUserID)+_TOKEN,row[7])
        mc.set(str(SubUserID)+_STATUS,row[10])
        mc.set(str(SubUserID)+_PARENTID,row[11])
        subuserLock.release()
        return "0"
    except MySQLdb.Error,e:
        print "Mysql Error %d: %s" % (e.args[0], e.args[1])
        LOG.log.error("Mysql Error %d: %s, %s" % (e.args[0], e.args[1], "select * from userinfo where account"))
        if cur != None:
            cur.close()
        if conn != None:
            conn.close()
        subuserLock.release()
        return '1004'
