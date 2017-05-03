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

pool = PooledDB(MySQLdb,mincached=2,maxcached=200,maxshared=200,maxconnections=200,host=host,user=user,passwd=passwd,db=db,port=port)
mc = memcache.Client([memServer], debug=0)

_USERNAME="_USERNAME"
_PASSWORD="_PASSWORD"
_LEFTCOUNT="_LEFTCOUNT"
_CALLEDCOUNT="_CALLEDCOUNT"
_SUCCESSCOUNT="_SUCCESSCOUNT"
_TOKEN="_TOKEN"
_STATUS="_STATUS"
_PARENTID="_PARENTID"

def MYSQL_PREPARE(connect,statement_Name,query)
def MYSQL_EXECUTE_PREPARE_RESULT(connect,statement_Name,*arg)


account= 'wfdsub'
conn = pool.connection()
        #conn=MySQLdb.connect(host=host,user=user,passwd=passwd,db=db,port=port)
        #cur=conn.cursor()
sql_statment="select * from userinfo where account=? and status=0"
MYSQL_PREPARE(dbcon,"prepare_name",sql_statment)
dataAll = MYSQL_EXECUTE_PREPARE_RESULT(conn,"prepare_name",token)
print dataAll
        #cur.execute("select * from userinfo where token='%s' and status=0" % (token))
        #rows = cur.fetchall()
