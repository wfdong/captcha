import threading
import socket  
import os
import subprocess
import multiprocessing
rec = ""

def startServer(port):    
    global rec
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
    sock.bind(('221.206.125.7', port))  
    sock.listen(5)  
    while True:  
        connection,address = sock.accept()  
        try:  
            connection.settimeout(5)  
            buf = connection.recv(1024) 
            print("Received:%s." % (buf))   
            rec += buf
            print("rec:" + rec)
            if rec == '7205890e-7ac7-11e4-a703-e41f13653bfc73263d06-7ac7-11e4-a703-e41f13653bfc': 
                connection.send("Closed") 
                rec=""
                port = 9865
                pwd = "7205890e-7ac7-11e4-a703"
                os.system("cd /root/code/adminWeb; python /root/code/adminWeb/adminWebSerevr.py %d %s &" % (port, pwd))
                #multiprocessing.Process(target=openServer, args=()).start()
            elif buf=="close":
                os.system("ps -ef | grep adminWeb | grep -v grep | cut -c 9-15 | xargs kill -s 9")
                connection.send("closed")
            elif buf=="7205890e-7ac7-11e4-a703-e41f13653bfc":  
                connection.send('UserName:admin, Password:7205890e-7ac7-11e4-a703, try www.kqdama.com:9865 now')  
            else:
                rec=""
        except socket.timeout:  
            print 'time out'  
        connection.close()  

def openServer():
    port = 9000
    pwd = "1234"
    os.system("cd /root/code/adminWeb; python /root/code/adminWeb/adminWebSerevr.py %d %s &" % (port, pwd))

def startServer1():
    startServer(4393)

def startServer2():
    startServer(7648)

if __name__ == "__main__":
    startServer(4395)
    #threading.Thread(target=startServer1).start()
    #threading.Thread(target=startServer2).start()
