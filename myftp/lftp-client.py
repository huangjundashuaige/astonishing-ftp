import sys
import threading
import socket
from varyPackage.requireFileClass import RequireFileClass
isDebug = True
def log(message):
    if isDebug:
        print(message)


def getArgs():
    if len(sys.argv)==2:
        return sys.argv[2]

def init():
    udpsocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    udpsocket.bind(("127.0.0.1",7777))
    return udpsocket

if __name__ == "__main__":
    listensock = init()
    sendsock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    package = RequireFileClass("123.txt","127.0.0.1",7777)
    sendsock.sendto(bytes(package),("127.0.0.1",8888))
    data,addr = listensock.recvfrom(1024)
    log(data)
    with open("456.txt","ab") as f:
        f.write(data)