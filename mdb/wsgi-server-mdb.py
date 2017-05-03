#!/usr/bin/python
# -*- coding: utf-8 -*- 

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

from cgi import parse_qs, escape
from DBUtils.PooledDB import PooledDB
import LOG
import memcache, time
import pylibmc
import cgi

pool = PooledDB(MySQLdb,mincached=2,maxcached=200,maxshared=200,maxconnections=200,host=config.host,user=config.user,passwd=config.passwd,db=config.db,port=config.port)
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
    ID = None
    for f in fs:
        if f == "username":
            userN=fs[f].value
        elif f == "password":
            oriPass=fs[f].value
            passW=hashlib.md5(oriPass).hexdigest()
        elif f == "token":
            token=fs[f].value
    print("%s, %s, %s" % (userN, passW, token))
    if userN == None or passW == None or token == None:
        LOG.log.error("Argument Error : %s, %s, %s, length=%d" % (userN, passW, token, length))
        print("Argument Error : %s, %s, %s" % (userN, passW, token))
        return ["1003"]
    
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
        status = mc.get(str(authorID)+ config._STATUS)
        if status != 0:
            print 'second'
            return '1001'
    print("step1 pass")
    #step2 check subsuer belong to this author
    SubUserID=mc.get(userN)
    if SubUserID==None:
        ret = config.checkSubUser(userN,passW, authorID)
        if ret != "0":
            return ret
    else:
        LeftCount = mc.get(str(SubUserID)+config._LEFTCOUNT)
        if LeftCount <= 0:
            return '1002'
        if mc.get(str(SubUserID) + config._PARENTID)==-1:
            return '1001'

        print("%s--%s" % (mc.get(str(SubUserID) + config._USERNAME), userN))
        if mc.get(str(SubUserID) + config._USERNAME)!=userN:
            return '1008'
        print("%s--%s" % (mc.get(str(SubUserID) + config._PASSWORD), passW))
        if mc.get(str(SubUserID) + config._PASSWORD)!=passW:
            return '1008'
    print("---step2 pass---")
    #check all pass, update
    mc.incr(str(SubUserID)+"_SUCCESSCOUNT",delta=1)
    mc.decr(str(SubUserID)+"_LEFTCOUNT",delta=1)
    return '0'


