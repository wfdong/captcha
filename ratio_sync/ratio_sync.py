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

errorID = {}

pool = PooledDB(MySQLdb,mincached=1,maxcached=10,maxshared=10,maxconnections=10,host=config.host,user=config.user,passwd=config.passwd,db=config.db,port=config.port)
#mc = pylibmc.Client([config.memServer], binary=True,behaviors={"tcp_nodelay": True,"ketama": True})
mc = memcache.Client([config.memServer], debug=0)

'''
Following code are used for save evidence
'''
def saveEvidence(ID):
    mc.set(str(ID) + "_SAVEDPIC", 1)
    mc.set(str(ID) + "_WARN", 1)
    count = 30
    i = 0
    while(True):
        time.sleep(0.5)
        if mc.get(str(ID) + "_SAVEDPIC") > 100:
            mc.set(str(ID) + "_SAVEDPIC", 2000)
            break
        i = i + 1
        if i > count:
            break
    mc.set(str(ID) + "_WARN", 0)
    print("Saved %d pics" % (mc.get(str(ID) + "_SAVEDPIC")))
    return mc.get(str(ID) + "_SAVEDPIC")

def startMove(dir_path, account):
    outFile = open("/root/code/web/static/index/frozen/%s/index.html" % (account), 'w')
    outFile.write("<html><table>\n")
    for lists in os.listdir(dir_path):
        path = os.path.join(dir_path, lists)
        if not os.path.isdir(path):
            end = path.find(".jpg")
            begin=path.rindex('/')
            #print(path)
            if end != -1:
                ID = path[begin+1:end-5]
                #print(ID)
                if ID in errorID:
                    #print("in")
                    #should move to /root/code/web/static/index/frozen
                    shutil.copy(path, "/root/code/web/static/index/frozen/%s/" % (account))
                    outFile.write("<tr><td>%s</td><td><img src=\"%s\" /></td></tr>\n" % (path[begin + 1:], path[begin + 1:]))
    outFile.write("</table><html>")

def readErrorFile(fileName):
    file = open(fileName)
    while 1:
        line = file.readline()
        if not line:
            break
        if len(line) < 5:
            continue
        begin = line.find("__") + 2
        ID = line[begin:len(line) - 1]
        #print(ID)
        errorID[ID] = 1

def beginSaveEvi(ID):
    #ID=210
    account = mc.get(str(ID) + "_USERNAME")
    if account == None:
        print("ERROR:can not find user with ID:" + str(ID))
        return
    print("account Name:" + account)
    try:
        os.system("rm -f /home/newevidence/wanghu/%s.txt" % str(ID))
        os.system("rm -f /home/newevidence/%s/*" % (account))
        os.system("rm -f /root/code/web/static/index/frozen/%s/*" % (account))
        os.makedirs("/root/code/web/static/index/frozen/%s/" % (account))
    except:
        print("/root/code/web/static/index/frozen/%s/ already exsits." % (account))
    count = saveEvidence(ID)
    print("saveEvidence done...")
    if count <= 5:
        print("Too few pic saved, exit")
        return
    readErrorFile("/home/newevidence/wanghu/%s.txt" % str(ID))
    print(errorID)
    startMove("/home/newevidence/%s/" % (account), account)


'''
sync method between memcached and mysql
Attention:we only update leftcount, calledcount, successcount now, web changed data will be implemented later
'''
def sync():
    try:
        ratioconn=MySQLdb.connect(host=config.host,user=config.user,passwd=config.passwd,db=config.db,port=config.port)
        ratiocur=ratioconn.cursor()
        ratiocur.execute("select ratio from dynamicratio where userid=1007 and date=(SELECT  now() - interval (TIME_TO_SEC(now()) mod 3600) second from dual)")
        standardrows = ratiocur.fetchall()
        print standardrows
        LOG.log.error("ratio error:%s" % (str(standardrows[0][0])))
        standard=standardrows[0][0]
        print 'standard:'
        print standard
        ratiocur.execute("select * from dynamicratio")
        ratiorows = ratiocur.fetchall()
        for ratiorow in ratiorows:
            print 'ratiorow:'
            print ratiorow[0]
            print ratiorow[1]
            print ratiorow[2]
            if str(ratiorow[2])!='NULL' and str(ratiorow[2])!='None':
                if (float(ratiorow[2])!=float(0)) and (float(ratiorow[2])<float(standard)*0.01):
                    #mc.set(str(ratiorow[1])+'_WARN',1)
                    #save evidence
                    #beginSaveEvi(ratiorow[1])
                    #time.sleep(900)
                    mc.set(str(ratiorow[1])+"_STATUS",1)
        ratiocur.execute("select * from dynamicratio where ratio is not NULL and date=(SELECT  now() - interval (TIME_TO_SEC(now()) mod 3600) second from dual)")
        ratiorows2 = ratiocur.fetchall()
        strs=""
        output = open("/root/code/web/static/index/ratio.html", 'wa')
        output.write("<html>" + strs + "</html>")
        for ratiorow2 in ratiorows2:
            strs="UserId:%s, ratio:%s, date:%s;\n" % (str(ratiorow2[1]),str(ratiorow2[2]),str(ratiorow2[3]))
            output = open("/root/code/web/static/index/ratio.html", 'a')
            output.write("<html>" + strs + "<br />" + "</html>")
            output.close()
        ratiocur.close()
        ratioconn.close()
    except MySQLdb.Error,e:
        print "Mysql Error %d: %s" % (e.args[0], e.args[1])
        LOG.log.error("Mysql Error %d: %s" % (e.args[0], e.args[1]))
        if ratiocur != None:
            ratiocur.close()
        if ratioconn != None:
            ratioconn.close()
   

if __name__ == "__main__":
    while(True):
        sync()
        time.sleep(3600)

