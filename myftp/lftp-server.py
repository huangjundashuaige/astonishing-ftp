#!/usr/bin/env python
# coding: utf-8

# In[6]:


import sys
import struct
import socket
import os
import threading
import json
from varyPackage.packages import *
import argparse
# In[12]:
## global variable
states = dict()
file_dict = dict()
require_dict = dict()
file_package_length = 1024
## send file fsm  require->ok->ok back->(send and ack)->fin
## recv file fsm  request->ok->(send and ack)->fin


def init_args():
    global args
    parser = argparse.ArgumentParser(description='aftp server')
    #parser.add_argument('--file', default="./sampleFile/123.txt", type=str, help='the file send or recv')
    #parser.add_argument('--recv', action="store_true",help="recv")
    #parser.add_argument('--send',action="stroe_true",help="send")
    #parser.add_argument('dest_ip',default="127.0.0.1",type=str,help="ip address target")
    #parser.add_argument('dest_port',default=8888,type=int,help="ip port target")
    parser.add_argument('--source_ip',default="127.0.0.1",type=str,help="ip address target")
    parser.add_argument('--source_port',default=8888,type=int,help="ip port target")
    parser.add_argument('--debug',action="store_true",help="debuging")
    args = parser.parse_args()


# In[ ]:





# In[9]:




# In[10]:


def log(message):
    if args.debug:
        print(message)


# In[14]:


def init():
    log("---init ftp server---")
    udpsock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    udpsock.bind((args.source_ip,args.source_port))
    if args.debug==False:
        udpsock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        udpsock.settimeout(1)
    log("server bind to {} : {}".format(args.source_ip,args.source_port))
    return udpsock

def whatKindaPackage(data):
    if data[:4] == bytes("0000",encoding="utf-8"):
        return "FileClass"
    else:
        return eval(data.decode())["kind"]


def send_file(addr):
    global file_dict
    global args
    filesocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    if file_dict[addr]["current_seq"] + 1024 > file_dict[addr]["length"]:
        log(file_dict[addr]["bytes_file"][file_dict[addr]["current_seq"]:])
        package = FileClass(file_dict[addr]["bytes_file"][file_dict[addr]["current_seq"]:],args.source_ip,args.source_port)
        file_dict[addr]["current_seq"] = file_dict[addr]["length"]
    else:
        package = FileClass(file_dict[addr]["bytes_file"][file_dict[addr]["current_seq"]:file_dict[addr]["current_seq"]+1024],args.source_ip,args.source_port)
        file_dict[addr]["current_seq"] += 1024
    package.seq(file_dict[addr]["current_seq"])
    filesocket.sendto(bytes(package),(require_dict[addr].package["source_ip"],require_dict[addr].package["source_port"]))
# self extended socket send method with timer to make sure
#def timer_send(socket,package,addr):
#    socket.sendto(package,addr)
#    
#    t = threading.Timer(rtt_dict[addr],)

def init_file_dict(addr,bytes_file):
    global file_dict
    file_dict[addr] = dict()
    file_dict[addr]["length"] = len(bytes_file)
    log("length {}".format(len(bytes_file)))
    file_dict[addr]["current_seq"] = 0
    file_dict[addr]["bytes_file"] = bytes_file

def init_require_dict(addr,package):
    global require_dict
    require_dict[addr] = package

def handle_file_package(data):
    global file_dict
    if whatKindaPackage(data) == "FileClass":
        package = FileClass(data)
        addr =(package.package["source_ip"],package.package["source_port"])
        if package.package["seq"] <= file_dict[addr]["current_ack"] + 1024:
            log(package.package["data"])
            file_dict[addr]["file"].write(package.data)
            file_dict[addr]["current_ack"] = package.package["seq"]
        udpsocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        ackpackage = AckClass(file_dict[addr]["current_ack"],args.source_ip,args.source_port)
        udpsocket.sendto(bytes(ackpackage),addr)

def multiplexing(udpsocket,data,addr):
    kind = whatKindaPackage(data)
    if kind!="FileClass":
        addr = (eval(data.decode())["source_ip"],eval(data.decode())["source_port"])
    log(kind)
    if kind == "RequireFileClass":
        #fsm
        states[addr] = "require"
        
        log("make sure require file package")
        package = RequireFileClass(data)
        f = open(package.package["data"],'rb')
        # test whole file
        init_file_dict(addr,f.read())
        init_require_dict(addr,package)
        f.close()
        send_file(addr)
    if kind == "RequestFileClass":
        #fsm
        states[addr] = "request"
        log("request to send file package")
        package = RequestFileClass(data)

        # create file handler
        f = open(package.package["data"],'ab')
        addr = (package.package["source_ip"],package.package["source_port"])
        file_dict[addr] = dict()
        file_dict[addr]["file"] = f
        file_dict[addr]["current_ack"] = 0


        sendBackUdpSocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        sendBackUdpSocket.sendto(bytes("ok",encoding="utf-8"),(package.package["source_ip"],int(package.package["source_port"])))
        log("send back ok package")
        sendBackUdpSocket.close()
    elif kind == "FileClass":
        # add flow control and congestion control
        # and timer and send back
        handle_file_package(data)
    elif kind == "ack":
        # need flow control and congestion control
        # need send back
        if file_dict[addr]["length"] <= AckClass(data).package["data"]:
            udpsocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
            udpsocket.sendto(bytes(AckClass(None,args.source_ip,args.source_port)),addr)
            log("send fin package")
            return
        send_file(addr)
        log("send file package")
    elif kind=="fin":
        log("finish sending file")
        log("---fin---")
        file_dict[addr]["file"].close()
        file_dict[addr] = None
        require_dict[addr]=None
def runServer(udpsocket):
    log("running server")
    while True:
        if args.debug==True:
            data, addr = udpsocket.recvfrom(2048)
        else:
            try:
                data , addr = udpsocket.recvfrom(2048)
            except Exception as e:
                print(e)
                log("recv time out")
                continue
        # addr should be ("127.0.0.1", 8000)
        #log(data)
        t = threading.Thread(target=multiplexing,args=(udpsocket,data,addr))
        t.start()
# In[15]:


if __name__ == "__main__":
    init_args()
    sock = init()
    runServer(sock)

# In[ ]:




