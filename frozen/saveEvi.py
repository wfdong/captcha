'''
save evidence, and copy wrong pic to /root/code/web/static/index/frozen
'''
import os,shutil
import memcache
import time
mc = memcache.Client(['221.206.125.7:12000'], debug=0)

errorID = {}

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

def run():
    ID=1247
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

if __name__ == "__main__":
    run()
