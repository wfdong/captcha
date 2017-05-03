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
import traceback

#pool = PooledDB(MySQLdb,mincached=2,maxcached=200,maxshared=200,maxconnections=200,host=config.host,user=config.user,passwd=config.passwd,db=config.db,port=config.port)
mc = memcache.Client([config.memServer], debug=0)
#mc = pylibmc.Client([config.memServer], binary=True,behaviors={"tcp_nodelay": True,"ketama": True})

def application(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    if environ['REQUEST_METHOD'].upper() != 'POST':
        return ["1003"]
    myFile=''
    length = 0
    try:
        length=int(environ.get('CONTENT_LENGTH','0'))
    except:
        return ["1003"]
    inputForm = environ['wsgi.input']
    post_form = environ.get('wsgi.post_form')
    if (post_form is not None
        and post_form[0] is inputForm):
        return post_form[2]
    environ.setdefault('QUERY_STRING', '')
    fs = cgi.FieldStorage(fp=inputForm,
                          environ=environ,
                          keep_blank_values=1)
    userN = None
    passW = None
    oriPass = None
    token = None
    myFile = None
    ID = None
    for f in fs:
        if f == "username":
            userN=fs[f].value
        elif f == "password":
            oriPass=fs[f].value
            passW=hashlib.md5(oriPass).hexdigest()
        elif f == "token":
            token=fs[f].value
        elif f == "myfile":
            myFile=fs[f].value
    print("%s, %s, %s, length=%d" % (userN, passW, token, length))
    if userN == None or passW == None or token == None or myFile == None:
        LOG.log.error("Argument Error : %s, %s, %s, length=%d" % (userN, passW, token, length))
        print("Argument Error : %s, %s, %s" % (userN, passW, token))
        return "1003"
    
    authorID = -1
    parentID = -1
    authorID = mc.get(token)
    #step1 check author token, status
    if authorID==None:
        #this token has not been set in memcached
        #checktoken will check token if exsit and save token to memcached
        ret = config.checkToken(token)
        authorID = mc.get(token)
        if ret != "0":
            return ret
    else:
        status = mc.get("%s%s" % (str(authorID), config._STATUS))
        if status != 0:
            print 'second'
            return '1001'
    #print("step1 pass")
    #step2 check subsuer belong to this author
    try:
        if userN.find(" ") != -1:
            return '1003'
        SubUserID=mc.get(userN)
    except:
        return '1012'
    if SubUserID==None:
        ret = config.checkSubUser(userN,passW, authorID)
        if ret != "0":
            return ret
    else:
        LeftCount = mc.get("%s%s" % (str(SubUserID), config._LEFTCOUNT))
        if LeftCount <= 0:
            return '1002'
        if mc.get("%s%s" % (str(SubUserID), config._PARENTID))==-1:
            return '1001'
        if mc.get("%s%s" % (str(SubUserID), config._STATUS)) != 0:
            return '1001'

        #print("%s--%s" % (mc.get(str(SubUserID) + config._USERNAME), userN))
        if mc.get("%s%s" % (str(SubUserID), config._USERNAME))!=userN:
            return ['1008']
        #print("%s--%s" % (mc.get(str(SubUserID) + config._PASSWORD), passW))
        if mc.get("%s%s" % (str(SubUserID), config._PASSWORD))!=passW:
            return ['1008']
    #print("---step2 pass---")
    #mc.incr(str(SubUserID) + config._CALLEDCOUNT)
    #call distribute
    try:
        #needEvidence = "False"
        #opener = urllib2.build_opener(MultipartPostHandler.MultipartPostHandler)
        #params = { "username" : userN, "myfile" : myFile}
        #data = opener.open("http://127.0.0.1:8009/distribute", params, timeout=70)
        #content = data.read()
        content = "ABCD"
        #print("%s" % (content))
        if content.find("10") == -1:
            #success one result, then we check whether this user need save evidence
            #In memcached, I add 2 fields, "F_WARN" and "FROZEN", default they are 0, "FROZEN" is equal to STATUS 
            #These 2 fileds will be changed in another sync process
            #We compare F_WARN here, and if is 1, save pic
            #nextNum = None
            nextNum = mc.incr(str(SubUserID) + "_NUM")
            if nextNum == None:
                #if can not be none
                return '1013'
                #nextNum = mc.set(str(SubUserID) + "_NUM", 0)
            #if nextNum > 20000:
                # if > 20000, just roll back to 0
            #    nextNum = mc.set(str(SubUserID) + "_NUM", 0)
            #code key is like subuserid_CODE_nextNUm, 731_CODE_1
            #!!!MUST set code value to 0
            mc.set("%d%s%d" % (SubUserID, "_CODE_", nextNum), 0)    
            #All 3 counts need changed
            #result = mc.incr(str(SubUserID) + config._CALLEDCOUNT)
            #mc.incr(str(SubUserID)+"_SUCCESSCOUNT",delta=1)
            #mc.decr(str(SubUserID)+"_LEFTCOUNT",delta=1)
            #if result == None:
            #    LOG.log.error(str(SubUserID) + "RESULT NONE")
                
            warn = mc.get("%s%s" % (str(SubUserID), "_WARN"))
            #print("warn:" + str(warn))
            if warn == None:
                #it can not be none
                return '1014'
                #mc.set("%s%s" % (str(SubUserID), "_WARN"), 0)
                #make sure every user has his pic directory
                #os.makedirs("%s%s" % ("/home/newevidence/", userN))
                #os.makedirs("%s%s%s" % ("/home/newevidence/", userN, "/wrong"))
            #print("eual:" + str(warn == 1))
            if warn == 1:
                #begin save image
                #print("------------")
                savedPicNum = mc.get("%s%s" % (str(SubUserID), "_SAVEDPIC"))
                if savedPicNum == None:
                    #it can not be none
                    return '1015'
                    #savedPicNum = mc.set("%s%s" % (str(SubUserID), "_SAVEDPIC"), 1)
                print("picnum:" + str(savedPicNum))
                if savedPicNum <= 2000:   
                    mc.incr("%s%s" % (str(SubUserID), "_SAVEDPIC"))
                    #only save pic less then 2000
                    #print("++++++++")
                    path="%s%s%s%s%s%s%s" % ('/home/newevidence/', userN, '/', str(nextNum), '_', content, '.jpg')
                    #path='/home/newevidence/' + userN + '/' + str(time.strftime('%Y-%m-%d-%H-%M-%S',time.localtime(time.time()))) + '_' + ret + '.jpg'
                    #path2="/home/newevidence/wanghu/" + content + ".jpg"
                    print("+++++++++path:" + path)
                    PicData = open(path,'wb')
                    PicData.write(myFile)
                    PicData.close()
            #All 3 counts need changed
            result = mc.incr(str(SubUserID) + config._CALLEDCOUNT)
            mc.incr(str(SubUserID)+"_SUCCESSCOUNT",delta=1)
            mc.decr(str(SubUserID)+"_LEFTCOUNT",delta=1)
            return "%d_%s" % (nextNum, content)
        else:
            return content
    except:
        LOG.log.error("Unexpected error:" + str(traceback.format_exc()))
        return '1011'


