import web, memcache
DB = web.database(host='221.206.125.7', dbn='mysql', user='captcha', pw='1234', db='test')
#cache = False
#web.config.debug = True
memServer='221.206.125.7:12000'

mc = memcache.Client([memServer], debug=0)

_LEFTCOUNT="_LEFTCOUNT"
_CALLEDCOUNT="_CALLEDCOUNT"
_SUCCESSCOUNT="_SUCCESSCOUNT"
