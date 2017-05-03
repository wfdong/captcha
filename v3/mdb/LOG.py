# -*- coding: UTF-8 -*-
import logging
from logging.handlers import RotatingFileHandler
import sys, os

LOGFILE = "restServer.log"
MAXLOGSIZE = 10*1024*1024 #Bytes
BACKUPCOUNT = 4
FORMAT = \
"%(asctime)s %(levelname)-8s[%(filename)s:%(lineno)d(%(funcName)s)] %(message)s"
LOGLVL = logging.DEBUG

handler = RotatingFileHandler(LOGFILE,
                              mode='a',
                              maxBytes=MAXLOGSIZE,
                              backupCount=BACKUPCOUNT)
formatter = logging.Formatter(FORMAT)
handler.setFormatter(formatter)
#handler.setLevel(LOGLVL) #####刚开始用handler设置日志级别，一直打不出来低于warning级别的日志，问题就在这里

log = logging.getLogger()
log.setLevel(LOGLVL) #####用LOG类设置级别是OK的
log.addHandler(handler)

def info(msg):
    log.info(msg)

def error(msg):
    log.error(msg)

def debug(msg):
    log.debug(msg)

def warning(msg):
    log.warning(msg)

def usage():
    print("Argument error!")
    print("Usage: pythono fcgi-server-cuda.py 8082")

def readPort(argv):
    if(len(argv) != 2):
        usage()
        os._exit(1)
    try:
        port = int(argv[1])
        return port
    except:
        print("port format error!\n" + str(sys.exc_info()))
        os._exit(1)
    return None
if __name__  == '__main__':
    print(sys.argv)
    port = readPort(sys.argv)
    print(port)
