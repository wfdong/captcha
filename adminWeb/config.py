import web, memcache, pylibmc
DB = web.database(host='221.206.125.7', dbn='mysql', user='captcha', pw='1234', db='test')
#cache = False
web.config.debug = False
memServer='221.206.125.7:12000'

#mc = memcache.Client([memServer], debug=0)
mc = pylibmc.Client(["221.206.125.7:12000"], binary=True)
mc.behaviors = {"tcp_nodelay": True, "ketama": True}

_LEFTCOUNT="_LEFTCOUNT"
_CALLEDCOUNT="_CALLEDCOUNT"
_SUCCESSCOUNT="_SUCCESSCOUNT"
'''import web
DB = web.database(host='221.206.125.7', dbn='mysql', user='captcha', pw='1234', db='test')
cache = False
web.config.debug = True
host='221.206.125.7'
user='captcha'
passwd='1234'
db='test'
port=3306'''
