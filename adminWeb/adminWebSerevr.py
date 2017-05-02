# -*- coding: utf-8 -*-
import web
import datetime, config
import hashlib
import model
import db
import threading, sys
import LOG
import random
from os import path
import time

'''
web服务器入口
'''

cookieName = "captcha-account-save"
cookieID = "captcha-USERID-save"
TIMEOUT= 3600

IP="221.206.124.137"
render = web.template.render('templates/')

urls = (
    '/','login',
    '/login', 'login',
    '/logout','logout',
    #'/index', 'accountdetail',
    '/charge','charge',
    '/accountdetail','accountdetail',
    #'/tradedetail','tradedetail',
    #'/changepwd','changepwd',
    #'/accuracy','accuracy',
    '/updateparentcount','updateparentcount'
)

PASSWORD=""

captchas = {}
app = web.application(urls, globals())
session = web.session.Session(app, web.session.DiskStore('sessions'), initializer={'log': 0})

def getCookieName():
    try: 
        return web.cookies().get(cookieName)
    except:
        # Do whatever handling you need to, etc. here.
        return None
    
def getCookieID():
    try: 
        return web.cookies().get(cookieID)
    except:
        # Do whatever handling you need to, etc. here.
        return None

class updateparentcount:
    def GET(self):
        #if web.ctx['ip'] != IP:
        #    return render.login()
        account = getCookieName()
        if account == None:
            return web.seeother('login')
        if session.count == 0:
            return web.seeother('login')
        i = web.input(parentid=None)
        if i.parentid == None:
            return "<script type=\"text/javascript\"> alert(\"\u53c2\u6570\u4f20\u9012\u9519\u8bef\uff01\"); \
            window.location.href=\"accountdetail\"; </script>"
        
        myvar = dict(ID=i.parentid)
        results = config.DB.select('userinfo', myvar, where="ID = $ID")
        if(len(results) == 0):
            return "<script type=\"text/javascript\" charset=”utf-8″> alert(\"\u53c2\u6570\u63d0\u4ea4\u9519\u8bef\uff01\u6ca1\u6709\u6743\u9650\uff01\"); \
            window.location.href=\"accountdetail\"; </script>"
        return render.updateparentcount(results[0])
        
    def POST(self):
        #if web.ctx['ip'] != IP:
        #    return render.login()
        account = getCookieName()
        if account == None:
            return web.seeother('login')
        if session.count == 0:
            return web.seeother('login')
        i = web.input()
        leftcount = None
        try:
            #检查数字是否输入正确
            leftcount = int(i.leftcount)
        except:
            return "<script type=\"text/javascript\" charset=”utf-8″> alert(\"\u8bf7\u8f93\u5165\u6b63\u786e\u683c\u5f0f\u7684\u6570\u5b57\uff01\"); \
            window.location.href=\"accountdetail\"; </script>"
        
        
        myvar = dict(ID=i.parentid)
        results = config.DB.select('userinfo', myvar, where="ID = $ID")
        if(len(results) == 0):
            return "<script type=\"text/javascript\" charset=”utf-8″> alert(\"\u53c2\u6570\u63d0\u4ea4\u9519\u8bef\uff01\u6ca1\u6709\u6743\u9650\uff01\"); \
            window.location.href=\"subuserlist\"; </script>"
        #subuser = results[0]
        parentID = i.parentid
        myvar = dict(parentID=i.parentid)
        results2 = config.DB.select('userinfo', myvar, where="ID = $parentID")
        author = results2[0]
        if i.ope == "sub":
            leftcount = -1 * leftcount

        '''if author.LEFTCOUNT - leftcount < 0:
            return "<script type=\"text/javascript\" charset=”utf-8″> alert(\"\u60a8\u7684\u5269\u4f59\u8c03\u7528\u6b21\u6570\u4e0d\u8db3\uff01\"); \
            window.location.href=\"accountdetail\"; </script>"'''
        
        # add for memcached
        key = str(parentID) + config._LEFTCOUNT
        print(key + "-" + str(leftcount))
        print("In mem %s" % config.mc.get(key))
        LOG.info("======WEB update begin=====")
        LOG.info("Before update, KEY %s, LEFT %s, delta %s" % (key, config.mc.get(key), leftcount))
        if leftcount >= 0:
            config.mc.incr(key, leftcount)
        else:
            config.mc.decr(key, -1 * leftcount)
        LOG.info("After update, KEY %s, LEFT %s, delta %s" % (key, config.mc.get(key), leftcount))
        LOG.info("Add %s for ID=%s, username=%s, time=%s" % (str(leftcount), str(parentID), author.ACCOUNT, time.strftime( '%Y-%m-%d %X', time.localtime() )))
        return "<script type=\"text/javascript\"> alert(\"\u4fee\u6539\u6210\u529f\"); \
            window.location.href=\"accountdetail\"; </script>"

class login:
    def GET(self):
        #if web.ctx['ip'] != IP:
        #    return render.login()
        return render.login()
    def POST(self):
        #if web.ctx['ip'] != IP:
        #    return render.login()
        global PASSWORD
        i = web.input()
        if i.username == "admin" and i.password == PASSWORD:
            web.setcookie(cookieName, "admin", TIMEOUT)
            session.count = 1
            return web.seeother('accountdetail')
        else:
            return "<script type=\"text/javascript\"> alert(\"\u7528\u6237\u540d\u6216\u5bc6\u7801\u9519\u8bef\"); \
            window.location.href=\"login\"; </script>"
        #pwdhash = hashlib.md5(i.password).hexdigest()
        #myvar = dict(account=i.username, password = pwdhash)
        #results = config.DB.select('userinfo', myvar, where="ACCOUNT = $account and PASSWORD = $password")
        #if(len(results) != 0):
            

class accountdetail:
    def GET(self):
        #if web.ctx['ip'] != IP:
        #    return render.login()
        account = getCookieName()
        if account == None:
            return web.seeother('login')
        if session.count == 0:
            return web.seeother('login')
        myvar = dict(account=account)
        results = config.DB.select('userinfo')
        views = []
        for t in results:
            #bit value in db, need convert
            if t.STATUS == 1:
                t.STATUS = "被冻结"
            elif t.STATUS == 0:
                t.STATUS = "正常"
            else:
                t.STATUS = "未知状态！"
            if t.CALLEDCOUNT == 0:
                t.COLUMN1 = 100.00
            else:
                t.COLUMN1 = "%10.2f" % (100.0 * t.SUCCESSCOUNT / t.CALLEDCOUNT)
            #if t.PARENTID == -1:
            t.COLUMN2 = "updateparentcount?parentid=" + str(t.ID)
            #else:
            #    t.COLUMN2 = "#"
            if t.PARENTID == -1:
                t.COLUMN3 = "作者账户"
            else:
                t.COLUMN3 = "子账户"
            views.append(t)
        return render.accountdetail(views)
    def POST(self):
        #if web.ctx['ip'] != IP:
        #    return render.login()
        account = getCookieName()
        if account == None:
            return web.seeother('login')
        if session.count == 0:
            return web.seeother('login')
        i = web.input()
        condition = ""
        #账户类型
        accountType = i.type
        if accountType == "1":
            condition += "PARENTID = -1"
        elif accountType == "2":
            condition += "PARENTID != -1"
        #账户状态
        status=i.status
        if len(condition) > 0:
            condition += " and "
        if status == "1":
            condition += "STATUS = 0"
        elif status == "2":
            condition += "STATUS = 1"
        else:
            condition += "1=1"
        #从属于作者
        author = i.author
        if author != None and len(author) > 0:
            myvar = dict(account=author)
            results = config.DB.select('userinfo', myvar, where="ACCOUNT=$account and PARENTID = -1")
            authorID = results[0].ID
            if len(condition) > 0:
                condition += " and PARENTID = " + str(authorID)
            else:
                condition += " PARENTID = " + str(authorID)
        print(condition)
        myvar = dict(account=account)
        results = config.DB.select('userinfo', myvar, where=condition)
        views = []
        for t in results:
            #bit value in db, need convert
            if t.STATUS == 1:
                t.STATUS = "被冻结"
            elif t.STATUS == 0:
                t.STATUS = "正常"
            else:
                t.STATUS = "未知状态！"
            if t.CALLEDCOUNT == 0:
                t.COLUMN1 = 100.00
            else:
                t.COLUMN1 = "%10.2f" % (100.0 * t.SUCCESSCOUNT / t.CALLEDCOUNT)
            t.COLUMN2 = "updateparentcount?parentid=" + str(t.ID)
            if t.PARENTID == -1:
                t.COLUMN3 = "作者账户"
            else:
                t.COLUMN3 = "子账户"
            views.append(t)
        return render.accountdetail(views)

class logout:
    def GET(self):
        #if web.ctx['ip'] != IP:
        #    return render.login()
        web.setcookie(cookieName, '', expires=-1)
        web.setcookie(cookieID, '', expires=-1)
        session.count=0
        return web.seeother('login')

if __name__ == "__main__":
    LOG.info("Admin Web Server Start")
    #app = web.application(urls, globals())
    print(sys.argv)
    PASSWORD=sys.argv[2]
    app.run()
