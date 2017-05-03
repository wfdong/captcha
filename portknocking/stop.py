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
            if buf=="close":
                os.system("ps -ef | grep adminWeb | grep -v grep | cut -c 9-15 | xargs kill -s 9")
                connection.send("closed")
            else:  
                connection.send('one request.')  
        except socket.timeout:  
            print 'time out'  
        connection.close()  

if __name__ == "__main__":
    startServer(7689)
    #threading.Thread(target=startServer1).start()
    #threading.Thread(target=startServer2).start()
