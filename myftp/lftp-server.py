#!/usr/bin/env python
# coding: utf-8

# In[6]:


import sys
import struct
import socket
import os
import threading
import json
import time
from varyPackage.packages import *
import argparse
# In[12]:
## global variable
states = dict()
file_dict = dict()
require_dict = dict()
file_package_length = 1024
global_dict = dict()

## send file fsm  require->ok->ok back->(send and ack)->fin
## recv file fsm  request->ok->(send and ack)->fin
rtt = 1
swnd_size = 10
time_out_limit = 3
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
        global_dict[addr]["sent_all"] = True
    else:
        package = FileClass(file_dict[addr]["bytes_file"][file_dict[addr]["current_seq"]:file_dict[addr]["current_seq"]+1024],args.source_ip,args.source_port)
        file_dict[addr]["current_seq"] += 1024
        # set the timer
        global_dict[addr]["timers"][file_dict[addr]["current_seq"]] = time.time()
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


def prepare_send_file(addr):
    global_dict[addr] = dict()
    global_dict[addr]["RTT"] = rtt
    global_dict[addr]["swnd_size"] = swnd_size
    global_dict[addr]["rtt_count"]=0
    global_dict[addr]["stop"] = False
    global_dict[addr]["sent_fin"] = False
    global_dict[addr]["sent_all"] = False
    # time out time,each ack makes it to check the timer if lost then resend n bags
    global_dict[addr]["time_out_limit"] = time_out_limit
    global_dict[addr]["timers"] = dict()
    global_dict[addr]["same_ack_count"] = 0
    global_dict[addr]["same_ack_value"] = 0
    global_dict[addr]["slow_start_flag"] = False
    global_dict[addr]["threshold"] = 0 

def update_con_wnd(addr):
    if global_dict[addr]["slow_start_flag"] ==False:
        global_dict[addr]["swnd_size"] += 1
    else:
        global_dict[addr]["swnd_size"] = global_dict[addr]["swnd_size"] *2
        if global_dict[addr]["swnd_size"] >= global_dict[addr]["threshold"]:
            global_dict[addr]["slow_start_flag"] = True


# flow control and pipeline functionality
def start_send_file(addr):
    log("start send file")
    update_con_wnd(addr)
    while True:
        if global_dict[addr]["stop"] ==True:
            return
        global_dict[addr]["rtt_count"]+=1
        log("the {} RTT".format(global_dict[addr]["rtt_count"]))
        start_time = time.time()
        swnd_count = 0
        while True:
            if time.time() - start_time > 1:
                break
            elif swnd_count > global_dict[addr]["swnd_size"]:
                log(time.time()-start_time)
                t= threading.Timer(global_dict[addr]["RTT"]-(time.time()-start_time),start_send_file,[addr])
                t.start()
                log("early stop")
                return
            else:
                swnd_count+=1
                if global_dict[addr]["sent_fin"] == True or global_dict[addr]["sent_all"]==True:
                    return
                else:
                    send_file(addr)

def lost_package_happen(addr):
    global_dict[addr]["threshold"] = global_dict[addr]["swnd_size"] //2
    global_dict[addr]["swnd_size"] = 1
    global_dict[addr]["slow_start_flag"] = True

def check_timer(addr):
    log("check the timer")
    for x in global_dict[addr]["timers"].keys():
        if time.time() - global_dict[addr]["timers"][x] > global_dict[addr]["time_out_limit"]:
            log("lost package")
            global_dict[addr]["current_seq"] = x
            lost_package_happen(addr)
            #global_dict[addr]["current_ack"] = x
            break
    t = threading.Timer(global_dict[addr]["RTT"],check_timer,[addr])
    t.start()
    
def fast_resend(addr,ack):
    global file_dict
    global args
    filesocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    if ack + 1024 > file_dict[addr]["length"]:
        #log(file_dict[addr]["bytes_file"][file_dict[addr]["current_seq"]:])
        log("send seq={}".format(ack))
        package = FileClass(file_dict[addr]["bytes_file"][ack:],args.source_ip,args.source_port)
        #file_dict[addr]["current_seq"] = file_dict[addr]["length"]
        global_dict[addr]["sent_all"] = True
    else:
        log("send seq={}".format(ack))
        package = FileClass(file_dict[addr]["bytes_file"][ack:ack+1024],args.source_ip,args.source_port)
        #file_dict[addr]["current_seq"] += 1024
        # set the timer
        global_dict[addr]["timer"][ack] = time.time()
    package.seq(ack)
    filesocket.sendto(bytes(package),(require_dict[addr].package["source_ip"],require_dict[addr].package["source_port"]))


def handle_timers(addr,data):
    package = AckClass(data)
    current_ack = package.package["data"]
    if current_ack not in global_dict[addr]["timers"].keys():
        if current_ack == global_dict[addr]["same_ack_value"]:
            global_dict[addr]["same_ack_count"] += 1
            if global_dict[addr]["same_ack_count"] >=3 :
                fast_resend(addr,global_dict[addr]["same_ack_value"])
                global_dict[addr]["swnd_size"] = global_dict[addr]["swnd_size"] //2
                global_dict[addr]["slow_start_flag"] = False
        else:
            global_dict[addr]["same_ack_value"] = current_ack
            global_dict[addr]["same_ack_count"] = 0
    else:
        if current_ack % 1000 == 0:
            global rtt
            rtt = time.time()-global_dict[addr]["timers"][current_ack]
            log("update rtt = {}".format(rtt))
        global_dict[addr]["timers"].pop(current_ack)
    

def multiplexing(udpsocket,data,addr):
    kind = whatKindaPackage(data)
    if kind!="FileClass":
        addr = (eval(data.decode())["source_ip"],eval(data.decode())["source_port"])
    else:
        addr = (FileClass(data).package["source_ip"],FileClass(data).package["source_port"])
    log(kind)

    if kind == "RequireFileClass":
        #fsm
        prepare_send_file(addr)
        states[addr] = "require"
        log("make sure require file package")
        package = RequireFileClass(data)
        f = open(package.package["data"],'rb')
        # test whole file
        init_file_dict(addr,f.read())
        init_require_dict(addr,package)
        f.close()
        start_send_file(addr)
        check_timer(addr)
    if kind == "RequestFileClass":
        #fsm
        global_dict[addr] = dict()
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
            udpsocket.sendto(bytes(FinClass(None,args.source_ip,args.source_port)),addr)
            log("send fin package")
            global_dict[addr]["sent_fin"]=True
            return
        #send_file(addr)
        handle_timers(addr,data)
        #check_timer(addr)
        log("recv ack")
    elif kind=="fin":
        log("finish sending file")
        log("---fin---")
        file_dict[addr]["file"].close()
        global_dict[addr]["stop"] =True
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




