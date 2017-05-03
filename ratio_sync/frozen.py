#!/usr/bin/python
# -*- coding: utf-8 -*- 

import os
import datetime
import config
import hashlib
import uuid
import random
import MySQLdb
import threading, sys

from cgi import parse_qs, escape
from DBUtils.PooledDB import PooledDB
from urllib import urlencode
import urllib
import binascii
import cgi
import LOG
import MultipartPostHandler, urllib2
import memcache, time
#import pylibmc
import time

pool = PooledDB(MySQLdb,mincached=1,maxcached=10,maxshared=10,maxconnections=10,host=config.host,user=config.user,passwd=config.passwd,db=config.db,port=config.port)
#mc = pylibmc.Client([config.memServer], binary=True,behaviors={"tcp_nodelay": True,"ketama": True})
mc = memcache.Client([config.memServer], debug=0)
_USERNAME="_USERNAME"
_PASSWORD="_PASSWORD"
_LEFTCOUNT="_LEFTCOUNT"
_CALLEDCOUNT="_CALLEDCOUNT"
_SUCCESSCOUNT="_SUCCESSCOUNT"
_TOKEN="_TOKEN"
_STATUS="_STATUS"
_PARENTID="_PARENTID"
_NUM = "_NUM"
_WARN = "_WARN"
_SAVEDPIC = "_SAVEDPIC"

leftCounts = {}
calledCounts = {}
successCounts = {}
statusDict = {}
totalLeft = 0
totalcalled = 0
totalSuccess = 0
preTime = None
curTime = None

def getAllID():
    #conn = pool.connection()
    try:
        conn = None
        cur = None
        conn = pool.connection()
        #conn=MySQLdb.connect(host=config.host,user=config.user,passwd=config.passwd,db=config.db,port=config.port)
        cur=conn.cursor()
        cur.execute("select ID from userinfo")
        rows = cur.fetchall()
        print 'getAllID'
        ids = []
        for row in rows:
            ID=row[0]
            #print(ID)
            ids.append(str(ID))
        cur.close()
        conn.close()
        print("get ID done")
        return ids
    except MySQLdb.Error,e:
        print "Mysql Error %d: %s" % (e.args[0], e.args[1])
        LOG.log.error("Mysql Error %d: %s, %s" % (e.args[0], e.args[1], "update userinfo set calledCount"))
        flag='error'
        if cur != None:
            cur.close()
        if conn != None:
            conn.close()
        return []

'''sync method between memcached and mysql
Attention:we only update leftcount, calledcount, successcount now, web changed data will be implemented later
'''
def sync():
    try:
        #conn = pool.connection()
        conn = None
        cur = None
        global preTime, totalcalled, calledCounts, curTime, successCounts, totalLeft, totalSuccess
        conn = pool.connection()
        #conn=MySQLdb.connect(host=config.host,user=config.user,passwd=config.passwd,db=config.db,port=config.port)
        cur=conn.cursor()
        ids = getAllID()
        totalLeft = 0
        outFile = open('/home/record.txt', 'a')
        outFile.write("------\n------\n")
        for ID in ids:
            #test if exsit
            ACCOUNT = mc.get(ID + _USERNAME)
            LEFTCOUNT = mc.get(ID + _LEFTCOUNT)
            CALLEDCOUNT = mc.get(ID + _CALLEDCOUNT)
            SUCCESSCOUNT = mc.get(ID + _SUCCESSCOUNT)
            STATUS=mc.get(ID + _STATUS)
            NextNum = mc.get(ID+"_NUM")
            if NextNum > 20000:
                mc.set(ID+"_NUM", 0)
	    updateFlag = False
            #if CALLEDCOUNT > 5000:
                #if float( SUCCESSCOUNT ) / CALLEDCOUNT < 0.12:
                #    STATUS=0
                    #print 'account closed!! for not reporting!'
            output = "(%s, %s, %s, %s, %s, time=%s)" % (ID, ACCOUNT, LEFTCOUNT, CALLEDCOUNT, SUCCESSCOUNT, time.strftime('%Y-%m-%d %X', time.localtime()))
            outFile.write(output + "\n")
            #print(output)
            if LEFTCOUNT != None and CALLEDCOUNT != None and SUCCESSCOUNT != None:
                #cur.execute("update userinfo set leftcount=%s, calledcount=%s, successcount=%s,status=%s where ID=%s" % (LEFTCOUNT, CALLEDCOUNT, SUCCESSCOUNT, STATUS, ID))
                #calc speed
                if ID + _CALLEDCOUNT in calledCounts:
                    totalcalled += CALLEDCOUNT - calledCounts[ID + _CALLEDCOUNT]
                    if CALLEDCOUNT - calledCounts[ID + _CALLEDCOUNT] > 0:
                        print(str(ID) + "-" + str(CALLEDCOUNT - calledCounts[ID + _CALLEDCOUNT]))
			updateFlag  = True
                    calledCounts[ID + _CALLEDCOUNT] = CALLEDCOUNT
                else:
                    calledCounts[ID + _CALLEDCOUNT] = CALLEDCOUNT
                if ID + _SUCCESSCOUNT in successCounts:
                    totalSuccess += SUCCESSCOUNT - successCounts[ID + _SUCCESSCOUNT]
		    if SUCCESSCOUNT - successCounts[ID + _SUCCESSCOUNT] > 0:
		        updateFlag  = True
                    successCounts[ID + _SUCCESSCOUNT] = SUCCESSCOUNT
                else:
                    successCounts[ID + _SUCCESSCOUNT] = SUCCESSCOUNT
		if ID + _LEFTCOUNT in leftCounts:
		    if LEFTCOUNT != leftCounts[ID + _LEFTCOUNT]:
		        updateFlag  = True
                    leftCounts[ID + _LEFTCOUNT] = LEFTCOUNT
                else:
                    leftCounts[ID + _LEFTCOUNT] = LEFTCOUNT
		if ID + _STATUS in statusDict:
		    if STATUS != statusDict[ID + _STATUS]:
		        updateFlag  = True
                    statusDict[ID + _STATUS] = STATUS
                else:
                    statusDict[ID + _STATUS] = STATUS
                #print(str(ID) + "-" + str(CALLEDCOUNT - calledCounts[ID + _CALLEDCOUNT]) + "-" + str(SUCCESSCOUNT - successCounts[ID + _SUCCESSCOUNT]))
                totalLeft += LEFTCOUNT
                if updateFlag == True:
                    #print("update")
		    cur.execute("update userinfo set leftcount=%s, calledcount=%s, successcount=%s,status=%s where ID=%s" % (LEFTCOUNT, CALLEDCOUNT, SUCCESSCOUNT, STATUS, ID))
				
            else:
                initone(ID)
        cur.close()
        conn.commit()
        conn.close()
        outFile.close()
        if preTime == None:
            preTime = time.time()
        else:
            curTime = time.time()
            elp = curTime - preTime
            strs = "Total %s, time %s, speed %s, success %s" % (str(totalLeft), elp, str(float(totalcalled / elp)), str(float(totalSuccess / elp)))
            print(strs)
            output = open("/root/code/web/static/index/status.html", 'w')
            output.write("<html>" + strs + "</html>")
            output.close()
            preTime = curTime
            totalcalled = 0
            totalSuccess = 0
         
        
    except MySQLdb.Error,e:
        print "Mysql Error %d: %s" % (e.args[0], e.args[1])
        LOG.log.error("Mysql Error %d: %s, %s" % (e.args[0], e.args[1], "update userinfo set calledCount"))
        if cur != None:
            cur.close()
        if conn != None:
            conn.close()
        if outFile != None:
            outFile.close()
   

if __name__ == "__main__":
    #init()
    while(True):
        sync()
        updateAllFromMysql()
        time.sleep(1)

