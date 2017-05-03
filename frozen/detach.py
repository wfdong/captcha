import os,shutil

errorID = {}

def start(dir_path):
    print(errorID)
    for lists in os.listdir(dir_path): 
        path = os.path.join(dir_path, lists) 
        if not os.path.isdir(path):
            end = path.find("_")
            #print(path)
            if end != -1:
                ID = path[2:end]
                #print(ID)
                if ID in errorID:
                    #print("in")
                    shutil.move(path, "./wrong/")

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

if __name__ == "__main__":
    readErrorFile("1007.txt")
    print(errorID)
    start(".")


