#!/usr/bin/python
# -*- coding: utf-8 -*- 

from flup.server.fcgi import WSGIServer
import os
import datetime
import config
import hashlib
import base64
import uuid
import random
import binascii
import MySQLdb
import threading, sys
from Queue import Queue

from threading import Condition
from cStringIO import StringIO
from cgi import parse_qs, escape
from DBUtils.PooledDB import PooledDB

pool = PooledDB(MySQLdb,30,host=config.host,user=config.user,passwd=config.passwd,db=config.db,port=config.port)

putCon = Condition()
getCon = Condition()
allQueue = Queue()
doneDict = {}


def mdbapp(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    length=int(environ.get('CONTENT_LENGTH','0'))
    x=environ['wsgi.input'].read(length)
    strlist=x.split("&")
    if len(strlist)<2:
        return '1003'
    for i in range(len(strlist)):
        if str(strlist[i]).find("username")==0:
            userN=str(strlist[i]).split("=")[1]
            #print userN
        elif str(strlist[i]).find("password")==0:
            passW=hashlib.md5(str(strlist[i]).split("=")[1]).hexdigest()
            #print passW

    try:
        #查看该用户的剩余次数
#         conn=MySQLdb.connect(host=config.host,user=config.user,passwd=config.passwd,db=config.db,port=config.port)
        conn = pool.connection()
        cur=conn.cursor()
        cur.execute('select * from userinfo where account=%s and password=%s and status=0', (userN,passW))
        if int(cur.rowcount) <= 0:
            result="1001"
        cur.execute('update userinfo set leftCount=leftCount-1,successCount=successCount+1 where account=%s and password=%s and leftCount>0 and status=0', (userN,passW))
        if int(cur.rowcount) == 0:
#           print '1002'
            result="1002"
        else:
#           print 'ok'
            result="0"
        cur.close()
        conn.commit()
        conn.close()
    except MySQLdb.Error,e:
        print "Mysql Error %d: %s" % (e.args[0], e.args[1])
        result="1003"
#     print result
    return result

if __name__  == '__main__':
    WSGIServer(mdbapp,bindAddress=('127.0.0.1',8008)).run()
