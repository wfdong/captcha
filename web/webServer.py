# -*- coding: utf-8 -*-
import web
import datetime, config
import hashlib
import model
import alipay, db
import threading, sys
import LOG
import random
from cStringIO import StringIO
from PIL import Image
from wheezy.captcha.image import captcha

from wheezy.captcha.image import background
from wheezy.captcha.image import curve
from wheezy.captcha.image import noise
from wheezy.captcha.image import smooth
from wheezy.captcha.image import text

from wheezy.captcha.image import offset
from wheezy.captcha.image import rotate
from wheezy.captcha.image import warp
from os import path
import uuid

'''
web服务器入口
'''

cookieName = "captcha-account-save"
cookieID = "captcha-USERID-save"
TIMEOUT= 3600

render = web.template.render('templates/')



urls = (
    '/login', 'login',
    '/reg','reg',
    '/regbyadmin','regbyadmin',
    '/reg?','reg',
    '/logout','logout',
    '/index', 'accountdetail',
    '/charge','charge',
    '/accountdetail','accountdetail',
    '/tradedetail','tradedetail',
    '/changepwd','changepwd',
    '/captcha', 'Captcha',
    '/','login',
    '/help', 'help',
    '/apihelp', 'apihelp',
    '/subuserlist','subuserlist',
    '/addsubuserpage','addsubuserpage',
    '/deletesubuser', 'deletesubuser',
    '/updatesubuserpwd','updatesubuserpwd',
    '/updatesubusercount','updatesubusercount',
    '/addsubuser', 'addsubuser',
    '/delsubuser', 'delsubuser',
    '/modsubuser', 'modsubuser',
    '/queryallsubuser', 'queryallsubuser',
    '/querysubuser', 'querysubuser',
    '/queryuserinfo', 'queryuserinfo',
    '/loginsubuser', 'loginsubuser'
)

captchas = {}


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

def querySubUser(username):
    user = model.userinfo(0,username, '', 0, 0, 0,-1)
    users = db.querySubUser(user)
    return users
def addSubUser(username,passwd,count,parentid):
	pwdhash = hashlib.md5(passwd).hexdigest()
	user = model.userinfo(username, pwdhash, count, 0, 0,parentid)
	db.addSubUser(user)
	
def delSubUser(id):
    config.DB.delete('userinfo', where='id=$id',vars={'id':id})
    #config.mc.delete()
    
def modSubUser(id,username,passwd,count,leftcount,succount):
    pwdhash = hashlib.md5(passwd).hexdigest()
    user = model.userinfo(id, username, pwdhash, leftcount, succount, 0)
    db.modSubUser(user)
    
####增加子用户
####传参：父用户的token，子用户username，password
class addsubuser:
    def POST(self):
        x = web.input()
        token=x.token
        subname=x.subname
        subpasswd=x.subpasswd
        parentid=-2
        leftCount=0
        if ' ' in x.subname or '/' in x.subname or '\\' in x.subname:
            return "1007"
        myvar = dict(account=x.subname)
        results = config.DB.select('userinfo', myvar, where="account = $account")
        if(len(results) != 0):
            return "1006"
        res1=config.DB.query('select * from userinfo where token=$token and parentid=-1', vars={'token':token})
        if (len(res1)==0):
            #print 'user error'
            return "1001"
        else:
            res=res1[0]
            parentid=res.ID
        results = config.DB.query('select * from userinfo where account=$account and parentid=$parentid', vars={'account':subname,'parentid':parentid})
        if (len(results)!=0):
            #print 'user already exist'
            return "1006"
        addSubUser(subname,subpasswd,0,parentid)
        return '0'
        
####删除子用户
####传参：父用户的username，password，子用户的username
class delsubuser:
    def POST(self):
        x = web.input()
        username=x.username
        passwd=x.password
        pwdhash = hashlib.md5(passwd).hexdigest()
        subname=x.subname
        parentid=-2
        parentLeftCount=0
        res1=config.DB.query('select * from userinfo where account=$account and password=$password and parentid=-1', vars={'account':username,'password':pwdhash})
        if (len(res1)==0):
            #print 'user error'
            return "1001"
        else:
            re=res1[0]
            parentid=re.ID
            parentLeftCount=re.LEFTCOUNT
        res2=config.DB.query('select * from userinfo where account=$account and parentid=$parentid', vars={'account':subname,'parentid':parentid})
        if (len(res2)==0):
            #print 'user not exist'
            return "1007"
        else:
            res=res2[0]
            if res.STATUS != 0:
                return "1013"
            delSubUser(res.ID)
            '''config.DB.update('userinfo',\
                         where='id=$id',vars={'id':parentid}, \
                         leftCount = parentLeftCount+res.LEFTCOUNT)'''
            #just mark status = 2 and leftcount = 0 for delete
            config.mc.set(str(res.ID) + "_STATUS", 2)
            config.mc.set(str(res.ID) + "_LEFTCOUNT", 0)
            # add for memcached
            LOG.info("======DLL delete begin=====\n")
            LOG.info("Before delete, SUBID %s, LEFT %s, parent leftcount %s" % (str(res.ID), str(res.LEFTCOUNT), config.mc.get(str(parentid) + config._LEFTCOUNT)))
            config.mc.incr(str(parentid) + config._LEFTCOUNT, delta=res.LEFTCOUNT)
            LOG.info("After delete,  parent leftcount %s" % (config.mc.get(str(parentid) + config._LEFTCOUNT)))
            return '0'
       
####修改子用户信息（只能修改子用户的密码和leftCount）
####传参：父用户的username，password，子用户的username，password，要增加的leftCount（delt值）
class modsubuser:
    def POST(self):
        x = web.input()
        username=x.username
        passwd=x.password
        pwdhash = hashlib.md5(passwd).hexdigest()
        subname=x.subname
        subpasswd=x.subpassword
        subpwdhash = hashlib.md5(subpasswd).hexdigest()
        subleftcount_delt=x.subleftcount_delt
        
        USERID=config.mc.get(username.encode("utf-8"))
        if USERID==None:
            print 'user not exist'
            return "1007"
        elif pwdhash!=config.mc.get(str(USERID)+"_PASSWORD"):
            return "1001"
        
        parentLeftCount=config.mc.get(str(USERID)+config._LEFTCOUNT)
        
        SUBID=config.mc.get(subname.encode("utf-8"))
        if SUBID==None:
            return "1007"
        elif USERID!=config.mc.get(str(SUBID)+"_PARENTID"):
            return "1007"
        SUBLEFTCOUNT=config.mc.get(str(SUBID)+config._LEFTCOUNT)
        SUBSTATUS = config.mc.get(str(SUBID)+ "_STATUS")
        if SUBSTATUS != 0:
            return "1013"
        if (parentLeftCount-int(subleftcount_delt)<0):
            #print 'leftcount not enough'
            return "1002"
        else:
            if ((SUBLEFTCOUNT+int(subleftcount_delt))<0):
                return "1009"
            # add for memcached
            LOG.info("======DLL update begin=====\n")
            LOG.info("Before update, SUBID %s, DELTA %s, subuser leftconut %s, parent leftcount %s" % (str(SUBID), int(subleftcount_delt.encode("utf-8")), config.mc.get(str(SUBID) + config._LEFTCOUNT), config.mc.get(str(USERID) + config._LEFTCOUNT)))
            if int(subleftcount_delt.encode("utf-8")) > 0:
                config.mc.incr(str(SUBID) + config._LEFTCOUNT, abs(int(subleftcount_delt.encode("utf-8"))))
                config.mc.decr(str(USERID) + config._LEFTCOUNT, abs(int(subleftcount_delt.encode("utf-8"))))
                LOG.info("After update, subuser leftconut %s, parent leftcount %s" % (config.mc.get(str(SUBID) + config._LEFTCOUNT), config.mc.get(str(USERID) + config._LEFTCOUNT)))
                return '0'
            else:
                config.mc.decr(str(SUBID) + config._LEFTCOUNT, abs(int(subleftcount_delt.encode("utf-8"))))
                config.mc.incr(str(USERID) + config._LEFTCOUNT, abs(int(subleftcount_delt.encode("utf-8"))))
                LOG.info("After update, subuser leftconut %s, parent leftcount %s" % (config.mc.get(str(SUBID) + config._LEFTCOUNT), config.mc.get(str(USERID) + config._LEFTCOUNT)))
                return '0'
    
####查询所有的subuser
####传参：父用户的username，password        
class queryallsubuser:
    def POST(self):
        x = web.input()
        username=x.username
        passwd=x.password
        pwdhash = hashlib.md5(passwd).hexdigest()
        res1=config.DB.query('select * from userinfo where account=$account and password=$password and parentid=-1', vars={'account':username,'password':pwdhash})
        if (len(res1)==0):
            #print 'user error'
            return 1001
        else:
            id=res1[0].ID
        res2=config.DB.query('select * from userinfo where parentid=$id', vars={'id':id})
        userlist=[]
        for user in res2:
            userlist.append(["USERNAME:"+user.ACCOUNT, "PASSWORD:"+str(user.PASSWORD), "LEFTCOUNT:"+str(user.LEFTCOUNT), "CALLEDCOUNT:"+str(user.CALLEDCOUNT), "SUCCESSCOUNT:"+str(user.SUCCESSCOUNT)])
        return userlist
        
####查询特定的subuser
####传参：父用户的username，password，要查询的子用户的username
class querysubuser:
    def POST(self):
        x = web.input()
        token=x.token
        subname=x.subname
        res1=config.DB.query('select * from userinfo where token=$token and parentid=-1', vars={'token':token})
        if (len(res1)==0):
            #print 'user error'
            return "1001"
        else:
            res2=config.DB.query('select * from userinfo where account=$account and parentid=$id', vars={'account':subname,'id':res1[0].ID})
            if (len(res2)==0):
                return "1007"
            else:
                user=res2[0]
                return ["USERNAME:"+user.ACCOUNT, "LEFTCOUNT:"+str(user.LEFTCOUNT), "CALLEDCOUNT:"+str(user.CALLEDCOUNT), "SUCCESSCOUNT:"+str(user.SUCCESSCOUNT)]

####登陆子账户
####传参：父用户的username，password，要查询的子用户的username
class loginsubuser:
    def POST(self):
        x = web.input()
        token=x.token
        subname=x.subname
        subpasswd = x.subpasswd
        pwdhash = hashlib.md5(subpasswd).hexdigest()
        res1=config.DB.query('select * from userinfo where token=$token and parentid=-1', vars={'token':token})
        if (len(res1)==0):
            #print 'user error'
            return "1001"
        else:
            ID = res1[0].ID
            res2=config.DB.query('select * from userinfo where account=$account and parentid=$id', vars={'account':subname,'id':ID})
            if (len(res2)==0):
                return "1007"
            res3=config.DB.query('select * from userinfo where account=$account and password=$password and parentid=$id', vars={'account':subname,'id':ID, 'password':pwdhash})
            if (len(res3)==0):
                return "1008"
        return ["0"]                
class queryuserinfo:
    def POST(self):
        x=web.input()
        username=x.username
        passwd=x.password
        pwdhash = hashlib.md5(passwd).hexdigest()
        print pwdhash
        hashlib.md5(pwdhash)
        res1=config.DB.query('select * from userinfo where account=$account and password=$password and parentid=-1', vars={'account':username,'password':pwdhash})
        if (len(res1)==0):
            #print 'user error'
            return "1001"
        else:
            user=res1[0]
            return ["USERNAME:"+user.ACCOUNT, "TOKEN:"+str(user.TOKEN), "LEFTCOUNT:"+str(user.LEFTCOUNT), "CALLEDCOUNT:"+str(user.CALLEDCOUNT), "SUCCESSCOUNT:"+str(user.SUCCESSCOUNT)]
         
    
		
class index:
    def GET(self): 
        return render.accountdetail()
    
class help:
    def GET(self): 
        return render.help()

class apihelp:
    def GET(self): 
        return render.apihelp()
    
_controllersDir = path.abspath(path.dirname(__file__))
_webDir = path.dirname(_controllersDir)
#for local
#_fontsDir = path.join(path.dirname(_webDir),'python')
#for centos
_fontsDir = path.join(path.dirname(_webDir),'code')
_fontsDir = path.join(_fontsDir,'web')
_fontsDir = path.join(_fontsDir,'fonts') 
_chars = 'ABCDEFJHJKMNPQRSTUVWXY'
SESSION_KEY_CAPTCHA = 'captcha'

class Captcha:
    def GET(self):
        print(_fontsDir)
        captcha_image = captcha(drawings=[
            background(),
            text(fonts=[
                path.join(_fontsDir,'Candara.ttf')],
                drawings=[
                    warp(),
                    rotate(),
                    offset()
                ]),
            curve(),
            noise(),
            smooth()
        ])
        chars = random.sample(_chars, 4)
        web.config.session_parameters['capctha'] = ''.join(chars)
        #session[SESSION_KEY_CAPTCHA] = ''.join(chars)
        image = captcha_image(chars)
        out = StringIO()
        image.save(out,"jpeg",quality=75)
        web.header('Content-Type','image/jpeg')
        return out.getvalue()

def isInteger(num):
    try:
        t = int(num)
        return True
    except ValueError:
        return False

class charge:
    def GET(self):
        account = getCookieName()
        if account == None:
            return web.seeother('login')
        return render.charge(account)
    def POST(self):
        userid = getCookieID()
        if userid == None:
            return web.seeother('login')
        #cap = web.config.session_parameters['capctha']
        i = web.input()
        if not isInteger(i.money):
            return "<script type=\"text/javascript\" charset=”utf-8″> alert(\"\u5145\u503c\u91d1\u989d\u53ea\u80fd\u4e3a\u6574\u6570\uff01\"); \
            window.location.href=\"charge\"; </script>"
        '''if cap.lower() != i.captcha.lower():
            return "<script type=\"text/javascript\" charset=”utf-8″> alert(\"\u9a8c\u8bc1\u7801\u8f93\u5165\u9519\u8bef\uff0c\u8bf7\u91cd\u65b0\u8f93\u5165\uff01\"); \
            window.location.href=\"charge\"; </script>"'''
        #检查数据库中（成功的记录里）有没有该订单号
        myvar = dict(tradeNumber=i.tradeNumber, result=True)
        results = config.DB.select('record', myvar, where="tradeNumber = $tradeNumber and result = $result")
        if(len(results) > 0):
            print("select did not pass.")
            return "<script type=\"text/javascript\" charset=”utf-8″> alert(\"\u8bf7\u4e0d\u8981\u63d0\u4ea4\u91cd\u590d\u7684\u8ba2\u5355\u53f7\"); \
            window.location.href=\"charge\"; </script>"
        trade = model.record(userid, i.tradeNumber, i.money, 0, False, None)
        alipay.queue.put(trade, 1)
        return "<script type=\"text/javascript\" charset=”utf-8″> alert(\"\u4fe1\u606f\u5df2\u63d0\u4ea4\uff0c\u8bf7\u4e00\u5206\u949f\u540e\u67e5\u770b\"); \
            window.location.href=\"charge\"; </script>"
    
class reg:
    def GET(self):
        #print(web.config.session_parameters['capctha'])
        return render.reg()

class regbyadmin:
    def GET(self):
        #print(web.config.session_parameters['capctha'])
        return render.regbyadmin()
    def POST(self):
        i = web.input()
        if ' ' in i.username or '/' in i.username or '\\' in i.username:
            return "<script type=\"text/javascript\" charset=”utf-8″> alert(\"\u7528\u6237\u540d\u4e0d\u80fd\u6709\u7a7a\u683c\u6216\u7279\u6b8a\u5b57\u7b26\"); \
            window.location.href=\"regbyadmin\"; </script>"
        #cap = web.config.session_parameters['capctha']
        #print(cap)
        '''if cap.lower() != i.captcha.lower():
            return "<script type=\"text/javascript\" charset=”utf-8″> alert(\"\u9a8c\u8bc1\u7801\u8f93\u5165\u9519\u8bef\uff0c\u8bf7\u91cd\u65b0\u8f93\u5165\uff01\"); \
            window.location.href=\"regbyadmin\"; </script>"'''
        if i.password != i.confirmPassword:
            return "<script type=\"text/javascript\" charset=”utf-8″> alert(\"\u4e24\u6b21\u8f93\u5165\u7684\u5bc6\u7801\u4e0d\u4e00\u81f4\uff0c\u8bf7\u91cd\u65b0\u8f93\u5165\"); \
            window.location.href=\"regbyadmin\"; </script>"
        #if ' ' in i.username:
        #    
        myvar = dict(account=i.username)
        results = config.DB.select('userinfo', myvar, where="account = $account")
        if(len(results) != 0):
            return "<script type=\"text/javascript\" charset=”utf-8″> alert(\"\u8be5\u7528\u6237\u540d\u5df2\u5b58\u5728\uff0c\u8bf7\u91cd\u65b0\u8f93\u5165\"); \
            window.location.href=\"regbyadmin\"; </script>"
        pwdhash = hashlib.md5(i.password).hexdigest()
        user = model.userinfo(i.username, pwdhash, 0, 0, 0, -1, token=uuid.uuid1())
        db.addUser(user)
        #n = config.DB.insert('userinfo', account=i.username, password=pwdhash, leftCount = 0, calledCount = 0, regTime=datetime.datetime.utcnow())
        return "<script type=\"text/javascript\"> alert(\"\u6ce8\u518c\u6210\u529f\"); \
            window.location.href=\"login\"; </script>"

class login:
    def GET(self):
        return render.login()
    def POST(self):
        i = web.input()
        pwdhash = hashlib.md5(i.password).hexdigest()
        myvar = dict(account=i.username, password = pwdhash)
        results = config.DB.select('userinfo', myvar, where="ACCOUNT = $account and PASSWORD = $password and STATUS=0 and PARENTID = -1")
        if(len(results) != 0):
            user = results[0]
            web.setcookie(cookieName, user.ACCOUNT, TIMEOUT)
            web.setcookie(cookieID, user.ID, TIMEOUT)
            return web.seeother('charge')
        else:
            return "<script type=\"text/javascript\"> alert(\"\u7528\u6237\u540d\u6216\u5bc6\u7801\u9519\u8bef\uff0c\u6216\u8d26\u53f7\u5df2\u88ab\u51bb\u7ed3\"); \
            window.location.href=\"login\"; </script>"

class accountdetail:
    def GET(self):
        account = getCookieName()
        if account == None:
            return web.seeother('login')
        myvar = dict(account=account)
        results = config.DB.select('userinfo', myvar, where="account = $account")
        account = results[0]
        return render.accountdetail(account)
    def POST(self):
        ID = getCookieID()
        if ID == None:
            return web.seeother('login')
        myvar = dict(ID=ID)
        newtoken=uuid.uuid1()
        n = config.DB.update('userinfo', where="ID = '" + ID + "'", token=newtoken)
        config.mc.delete(config.mc.get(str(ID)+'_TOKEN'),0)
        config.mc.set(str(newtoken),str(ID)) 
        config.mc.set(str(ID)+'_TOKEN',newtoken)
        return "<script type=\"text/javascript\"> alert(\"\u4ee4\u724c\u66f4\u65b0\u6210\u529f\"); \
            window.location.href=\"accountdetail\"; </script>"

class tradedetail:
    def GET(self):
        account = getCookieName()
        if account == None:
            return web.seeother('login')
        myvar = dict(account=account)
        results = config.DB.select('userinfo', myvar, where="account = $account")
        myvar = dict(userid=results[0].ID)
        trades = config.DB.select('record', myvar, where="userid = $userid", order="ADDTIME DESC")
        views = []
        for t in trades:
            #bit value in db, need convert
            if ord(t.RESULT) == 1:
                t.RESULT = "成功"
            else:
                t.RESULT = "失败"
            views.append(t)
        return render.tradedetail(views, account)
    

class subuserlist:
    def GET(self):
        account = getCookieName()
        if account == None:
            return web.seeother('login')
        ID = getCookieID()
        if ID == None:
            return web.seeother('login')
        myvar = dict(ID=ID)
        results = config.DB.select('userinfo', myvar, where="PARENTID = $ID")
        views = []
        for t in results:
            t.COLUMN1 = ""
            if t.STATUS == 0:
                t.COLUMN2 = "正常"
            elif t.STATUS == 1:
                t.COLUMN2 = "被冻结"
            else:
                t.COLUMN2 = "账户异常"
            views.append(t)
        return render.subuserlist(views, account)

class addsubuserpage:
    def GET(self):
        account = getCookieName()
        if account == None:
            return web.seeother('login')
        ID = getCookieID()
        if ID == None:
            return web.seeother('login')
        return render.addsubuser(account)
        
    def POST(self):
        ID = getCookieID()
        if ID == None:
            return web.seeother('login')
        '''
        cap = web.config.session_parameters['capctha']
        if cap.lower() != i.captcha.lower():
            return "<script type=\"text/javascript\" charset=”utf-8″> alert(\"\u9a8c\u8bc1\u7801\u8f93\u5165\u9519\u8bef\uff0c\u8bf7\u91cd\u65b0\u8f93\u5165\uff01\"); \
            window.location.href=\"addsubuserpage\"; </script>"
        print(cap)
        '''
      #  res=config.DB.select('userinfo', myvar, where="ID = $ID and STATUS=0")
      # if(len(res)==0):
      #      return "<script type=\"text/javascript\" charset=?.tf-8?? alert(\"\u8d26\u53f7\u5df2\u88ab\u5c01\"); \
      #      window.location.href=\"addsubuserpage\"; </script>"
        i = web.input()
        if len(i.account) == 0:
            return "<script type=\"text/javascript\" charset=”utf-8″> alert(\"\u7528\u6237\u540d\u957f\u5ea6\u4e0d\u80fd\u4e3a0\uff01\"); \
                window.location.href=\"addsubuserpage\"; </script>"
        if ' ' in i.account or '/' in i.account or '\\' in i.account:
            return "<script type=\"text/javascript\" charset=”utf-8″> alert(\"\u7528\u6237\u540d\u4e0d\u80fd\u6709\u7a7a\u683c\u6216\u7279\u6b8a\u5b57\u7b26\"); \
                window.location.href=\"addsubuserpage\"; </script>"
        if i.password != i.confirmPassword:
            return "<script type=\"text/javascript\" charset=”utf-8″> alert(\"\u4e24\u6b21\u8f93\u5165\u7684\u5bc6\u7801\u4e0d\u4e00\u81f4\uff0c\u8bf7\u91cd\u65b0\u8f93\u5165\"); \
            window.location.href=\"addsubuserpage\"; </script>"
        myvar = dict(account=i.account)
        results = config.DB.select('userinfo', myvar, where="account = $account")
        if(len(results) != 0):
            return "<script type=\"text/javascript\" charset=”utf-8″> alert(\"\u8be5\u7528\u6237\u540d\u5df2\u5b58\u5728\uff0c\u8bf7\u91cd\u65b0\u8f93\u5165\"); \
            window.location.href=\"addsubuserpage\"; </script>"
        myvar = dict(account=i.account, ID=ID)
        results = config.DB.select('userinfo', myvar, where="account = $account and PARENTID=$ID")
        if(len(results) != 0):
            return "<script type=\"text/javascript\" charset=”utf-8″> alert(\"\u8be5\u7528\u6237\u540d\u5df2\u5b58\u5728\uff0c\u8bf7\u91cd\u65b0\u8f93\u5165\"); \
            window.location.href=\"addsubuserpage\"; </script>"
        #addSubUser(i.account, )
        pwdhash = hashlib.md5(i.password).hexdigest()
        user = model.userinfo(i.account, pwdhash, 0, 0, 0, ID)
        db.addSubUser(user)
        return "<script type=\"text/javascript\"> alert(\"\u6ce8\u518c\u6210\u529f\"); \
            window.location.href=\"subuserlist\"; </script>"
        #return render.addsubuser(account)

class deletesubuser:
    def GET(self):
        account = getCookieName()
        if account == None:
            return web.seeother('login')
        ID = getCookieID()
        if ID == None:
            return web.seeother('login')
        i = web.input(subuserid=None)
        if i.subuserid == None:
            return "<script type=\"text/javascript\"> alert(\"\u53c2\u6570\u4f20\u9012\u9519\u8bef\uff01\"); \
            window.location.href=\"subuserlist\"; </script>"
        #确保这个id是该作者下面的才行
        myvar = dict(ID=i.subuserid, PARENTID=ID)
        parentLeftCount=0
        results = config.DB.select('userinfo', myvar, where="ID = $ID and PARENTID=$PARENTID")
        if(len(results) == 0):
            return "<script type=\"text/javascript\" charset=”utf-8″> alert(\"\u53c2\u6570\u63d0\u4ea4\u9519\u8bef\uff01\u6ca1\u6709\u6743\u9650\uff01\"); \
            window.location.href=\"subuserlist\"; </script>"
        #获取作者leftcount
        res1=config.DB.query('select * from userinfo where ID = $ID', vars={'ID':ID})
        if (len(res1)==0):
            return web.seeother('login')
        res = results[0]
        subStatus = res.STATUS
        if subStatus != 0:
            return "<script type=\"text/javascript\" charset=”utf-8″> alert(\"\u5b50\u7528\u6237\u88ab\u51bb\u7ed3\uff0c\u4e0d\u80fd\u5220\u9664\uff01\"); \
            window.location.href=\"subuserlist\"; </script>"
        parentLeftCount = res1[0].LEFTCOUNT
        delSubUser(i.subuserid)
        '''config.DB.update('userinfo',\
                         where='id=$id',vars={'id':ID}, \
                         leftCount = parentLeftCount + res.LEFTCOUNT)'''
        config.mc.set(str(i.subuserid) + "_STATUS", 2)
        config.mc.set(str(i.subuserid) + "_LEFTCOUNT", 0)
        LOG.info("======WEB delete begin=====\n")
        LOG.info("Before delete, SUBID %s, SUBCOUNT = %s, parent leftcount %s" % (str(i.subuserid), str(res.LEFTCOUNT), config.mc.get(str(ID) + config._LEFTCOUNT)))
        # add for memcached
        config.mc.incr(str(ID) + config._LEFTCOUNT, delta=res.LEFTCOUNT)
        LOG.info("After delete,  parent leftcount %s" % (config.mc.get(str(ID) + config._LEFTCOUNT)))
        return "<script type=\"text/javascript\"> alert(\"\u5220\u9664\u6210\u529f\uff01\"); \
            window.location.href=\"subuserlist\"; </script>"

class updatesubuserpwd:
    def GET(self):
        account = getCookieName()
        if account == None:
            return web.seeother('login')
        ID = getCookieID()
        if ID == None:
            return web.seeother('login')
        i = web.input(subuserid=None)
        if i.subuserid == None:
            return "<script type=\"text/javascript\"> alert(\"\u53c2\u6570\u4f20\u9012\u9519\u8bef\uff01\"); \
            window.location.href=\"subuserlist\"; </script>"
        #确保这个id是该作者下面的才行
        myvar = dict(ID=i.subuserid, PARENTID=ID)
        results = config.DB.select('userinfo', myvar, where="ID = $ID and PARENTID=$PARENTID")
        if(len(results) == 0):
            return "<script type=\"text/javascript\" charset=”utf-8″> alert(\"\u53c2\u6570\u63d0\u4ea4\u9519\u8bef\uff01\u6ca1\u6709\u6743\u9650\uff01\"); \
            window.location.href=\"subuserlist\"; </script>"
        return render.updatesubuserpwd(results[0], account)
        
    def POST(self):
        ID = getCookieID()
        if ID == None:
            return web.seeother('login')
        i = web.input()
        if i.password != i.confirmPassword:
            return "<script type=\"text/javascript\" charset=”utf-8″> alert(\"\u4e24\u6b21\u8f93\u5165\u7684\u5bc6\u7801\u4e0d\u4e00\u81f4\uff0c\u8bf7\u91cd\u65b0\u8f93\u5165\"); \
            window.location.href=\"subuserlist\"; </script>"
        pwdhash = hashlib.md5(i.password).hexdigest()
        #确保这个id是该作者下面的才行
        myvar = dict(ID=i.subuserid, PARENTID=ID)
        results = config.DB.select('userinfo', myvar, where="ID = $ID and PARENTID=$PARENTID")
        if(len(results) == 0):
            return "<script type=\"text/javascript\" charset=”utf-8″> alert(\"\u53c2\u6570\u63d0\u4ea4\u9519\u8bef\uff01\u6ca1\u6709\u6743\u9650\uff01\"); \
            window.location.href=\"subuserlist\"; </script>"
        if i.password != None:
            config.DB.update('userinfo', where='id=$id',vars={'id':i.subuserid}, password=pwdhash)
        return "<script type=\"text/javascript\"> alert(\"\u4fee\u6539\u6210\u529f\"); \
            window.location.href=\"subuserlist\"; </script>"

class updatesubusercount:
    def GET(self):
        account = getCookieName()
        if account == None:
            return web.seeother('login')
        ID = getCookieID()
        if ID == None:
            return web.seeother('login')
        i = web.input(subuserid=None)
        if i.subuserid == None:
            return "<script type=\"text/javascript\"> alert(\"\u53c2\u6570\u4f20\u9012\u9519\u8bef\uff01\"); \
            window.location.href=\"subuserlist\"; </script>"
        #确保这个id是该作者下面的才行
        myvar = dict(ID=i.subuserid, PARENTID=ID)
        results = config.DB.select('userinfo', myvar, where="ID = $ID and PARENTID=$PARENTID")
        if(len(results) == 0):
            return "<script type=\"text/javascript\" charset=”utf-8″> alert(\"\u53c2\u6570\u63d0\u4ea4\u9519\u8bef\uff01\u6ca1\u6709\u6743\u9650\uff01\"); \
            window.location.href=\"subuserlist\"; </script>"
        subUser = results[0]
        subStatus = subUser.STATUS
        if subStatus != 0:
            return "<script type=\"text/javascript\" charset=”utf-8″> alert(\"\u5b50\u7528\u6237\u88ab\u51bb\u7ed3\uff0c\u4e0d\u80fd\u4fee\u6539\u7801\u6570\uff01\"); \
            window.location.href=\"subuserlist\"; </script>"
        return render.updatesubusercount(subUser, account)
        
    def POST(self):
        ID = getCookieID()
        if ID == None:
            return web.seeother('login')
        i = web.input()
        leftcount = None
        try:
            #检查数字是否输入正确
            leftcount = int(i.leftcount)
        except:
            return "<script type=\"text/javascript\" charset=”utf-8″> alert(\"\u8bf7\u8f93\u5165\u6b63\u786e\u683c\u5f0f\u7684\u6570\u5b57\uff01\"); \
            window.location.href=\"subuserlist\"; </script>"
        
        #确保这个id是该作者下面的才行
        myvar = dict(ID=i.subuserid, PARENTID=ID)
        results = config.DB.select('userinfo', myvar, where="ID = $ID and PARENTID=$PARENTID")
        if(len(results) == 0):
            return "<script type=\"text/javascript\" charset=”utf-8″> alert(\"\u53c2\u6570\u63d0\u4ea4\u9519\u8bef\uff01\u6ca1\u6709\u6743\u9650\uff01\"); \
            window.location.href=\"subuserlist\"; </script>"
        subuser = results[0]
        #检测子账户的状态是否被冻结
        subStatus = subuser.STATUS
        if subStatus != 0:
            return "<script type=\"text/javascript\" charset=”utf-8″> alert(\"\u5b50\u7528\u6237\u88ab\u51bb\u7ed3\uff0c\u4e0d\u80fd\u4fee\u6539\u7801\u6570\uff01\"); \
            window.location.href=\"subuserlist\"; </script>"
        myvar = dict(ID=ID)
        results2 = config.DB.select('userinfo', myvar, where="ID = $ID and PARENTID=-1")
        author = results2[0]
        if i.ope == "sub":
            leftcount = -1 * leftcount

        if author.LEFTCOUNT - leftcount <= 0:
            return "<script type=\"text/javascript\" charset=”utf-8″> alert(\"\u60a8\u7684\u5269\u4f59\u8c03\u7528\u6b21\u6570\u4e0d\u8db3\uff01\"); \
            window.location.href=\"subuserlist\"; </script>"
        
        if subuser.LEFTCOUNT + leftcount < 0:
            return "<script type=\"text/javascript\" charset=”utf-8″> alert(\"\u5b50\u7528\u6237\u5269\u4f59\u8c03\u7528\u6b21\u6570\u4e0d\u80fd\u4e3a\u8d1f\u503c\uff01\"); \
            window.location.href=\"subuserlist\"; </script>"
        '''config.DB.update('userinfo',\
                         where='id=$id',vars={'id':i.subuserid}, \
                         leftCount = subuser.LEFTCOUNT+int(i.leftcount))
        config.DB.update('userinfo',\
                         where='id=$id',vars={'id':ID}, \
                         leftCount = author.LEFTCOUNT-int(i.leftcount))'''
        # add for memcached
        LOG.info("======Web update begin=====\n")
        LOG.info("Before update, SUBID %s, DELTA %s, subuser leftconut %s, parent leftcount %s" % (str(i.subuserid), str(leftcount), config.mc.get(str(i.subuserid) + config._LEFTCOUNT), config.mc.get(str(ID) + config._LEFTCOUNT)))
        print("In mem %s" % config.mc.get((str(i.subuserid) + config._LEFTCOUNT)))
        print("In mem %s" % config.mc.get((str(ID) + config._LEFTCOUNT)))
        if leftcount >= 0:
            config.mc.incr(str(i.subuserid) + config._LEFTCOUNT, delta=leftcount)
            config.mc.decr(str(ID) + config._LEFTCOUNT, delta=leftcount)
        else:
            config.mc.decr(str(i.subuserid) + config._LEFTCOUNT, delta = -1 * leftcount)
            config.mc.incr(str(ID) + config._LEFTCOUNT, delta= -1 * leftcount)
        LOG.info("After update, subuser leftconut %s, parent leftcount %s" % (config.mc.get(str(i.subuserid) + config._LEFTCOUNT), config.mc.get(str(ID) + config._LEFTCOUNT)))
        return "<script type=\"text/javascript\"> alert(\"\u4fee\u6539\u6210\u529f\"); \
            window.location.href=\"subuserlist\"; </script>"

class changepwd:
    def GET(self):
        account = getCookieName()
        if account == None:
            return web.seeother('login')
        return render.changepwd(account)
    def POST(self):
        account = getCookieName()
        if account == None:
            return web.seeother('login')
        i = web.input()
        if i.password != i.confirmPassword:
            return unicode("<script type=\"text/javascript\" charset=”utf-8″> alert(\"\u4e24\u6b21\u8f93\u5165\u7684\u5bc6\u7801\u4e0d\u4e00\u81f4\uff0c\u8bf7\u91cd\u65b0\u8f93\u5165\"); \
            window.location.href=\"changepwd\"; </script>", "utf-8")
        oldpwdhash = hashlib.md5(i.oldPassword).hexdigest()
        myvar = dict(account=account, password = oldpwdhash)
        results = config.DB.select('userinfo', myvar, where="ACCOUNT = $account and PASSWORD = $password")
        if(len(results) == 0):
            return "<script type=\"text/javascript\" charset=”utf-8″> alert(\"\u539f\u59cb\u5bc6\u7801\u9519\u8bef\uff0c\u8bf7\u91cd\u65b0\u8f93\u5165\"); \
            window.location.href=\"changepwd\"; </script>"
        pwdhash = hashlib.md5(i.password).hexdigest()
        n = config.DB.update('userinfo', where="account = '" + account + "'", password=pwdhash)
        return "<script type=\"text/javascript\"> alert(\"\u5bc6\u7801\u4fee\u6539\u6210\u529f\"); \
            window.location.href=\"changepwd\"; </script>"

class logout:
    def GET(self):
        web.setcookie(cookieName, '', expires=-1)
        web.setcookie(cookieID, '', expires=-1)
        return web.seeother('login')

if __name__ == "__main__":
    #threading.Thread(target = demaonThread, args = (), name = 'demonthread').start()
    LOG.info("Web server start")
    print(config.mc)
    print(str(146) + config._LEFTCOUNT)
    print(config.mc.get("146_LEFTCOUNT"))
    print(config.mc.get("144_LEFTCOUNT"))
    print(config.mc.get("145_LEFTCOUNT"))
    config.mc.set("test", "1")
    print(config.mc.get("test"))
    #print("In mem %s" % config.mc.get(str(144) + config._LEFTCOUNT))
    #alipay.alipayDeamon().start()
    app = web.application(urls, globals())
    app.run()
    app.run()

