import memcache
mc = memcache.Client(['221.206.125.7:12000'], debug=0)
#key = "959_STATUS"
#key="165_SUCCESSCOUNT"
#key="169_LEFTCOUNT"
#print(mc.set("1079_STATUS", 0))
#mc.incr("959_SUCCESSCOUNT", 30000)
#mc.set(key,0)
#print(ss)
#mc.incr("1040_LEFTCOUNT", delta=1500000)
#mc.decr(key,delta=2500000)
#print(mc.get("1079_WARN"))
#print(mc.set("1007_CALLEDCOUNT",0))
#print(mc.set("1007_SUCCESSCOUNT", 0))
#print(mc.set("840_SAVEDPIC", 1800))
#print(mc.set("1007_WARN", 0))
#print(mc.get("1054_USERNAME"))
print(mc.set("1190_LEFTCOUNT", 20000))
print(mc.set("1190_CALLEDCOUNT", 0))
print(mc.set("1190_SUCCESSCOUNT", 0))


