import sys
import threading
import socket
from varyPackage.packages import *
import argparse
from functools import reduce
import time
# global variable
file_dict = dict()
cache_file = dict()
args = None
start_time = time.time()
def log(message):
    if args.debug:
        print(message)



def init_args():
    global args
    parser = argparse.ArgumentParser(description='aftp client')
    parser.add_argument('--file', default="sampleFile/123.txt", type=str, help='the file send or recv')
    parser.add_argument('--store_file',default='recvFile/456.txt',type=str,help="rec file")
    parser.add_argument('--recv', action="store_true",help="recv")
    parser.add_argument('--send',action="store_true",help="send")
    parser.add_argument('--dest_ip',default="127.0.0.1",type=str,help="ip address target")
    parser.add_argument('--dest_port',default=8888,type=int,help="ip port target")
    parser.add_argument('--source_ip',default="127.0.0.1",type=str,help="ip address target")
    parser.add_argument('--source_port',default=7777,type=int,help="ip port target")
    parser.add_argument('--debug',action="store_true",help="debuging")
    args = parser.parse_args()
def init_socket():
    global args
    udpsocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    udpsocket.bind((args.source_ip,args.source_port))
    if args.debug==False:
        udpsocket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        udpsocket.settimeout(1)
    return udpsocket

def send_file_fragment(addr):
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
    filesocket.sendto(bytes(package),(args.dest_ip,args.dest_port))
def init_file_dict(addr,bytes_file):
    global file_dict
    file_dict[addr] = dict()
    file_dict[addr]["length"] = len(bytes_file)
    log("length {}".format(len(bytes_file)))
    file_dict[addr]["current_seq"] = 0
    file_dict[addr]["bytes_file"] = bytes_file


def send_file(sendsocket,listensock):
    package = RequestFileClass(args.store_file,args.source_ip,args.source_port)
    f = open(args.file,"rb")
    init_file_dict((args.dest_ip,args.dest_port),f.read())
    sendsocket.sendto(bytes(package),(args.dest_ip,args.dest_port))
    data,addr = listensock.recvfrom(2048)
    addr = (args.dest_ip,args.dest_port)
    if data == bytes("ok",encoding="utf-8"):
        log("ok recv")
        send_file_fragment((args.dest_ip,args.dest_port))
        while True:
            if args.debug == False:
                try:
                    data, addr = listensock.recvfrom(2048)
                except Exception as e:
                    log("interrupt")
                    continue
            else:
                data, addr = listensock.recvfrom(2048)
            kind = eval(data.decode())["kind"]
            addr = (args.dest_ip,args.dest_port)
            if kind == "ack":
            # need flow control and congestion control
            # need send back
                log(AckClass(data).package["data"])
                if file_dict[addr]["length"] <= AckClass(data).package["data"]:
                    log("send fin package")
                    udpsocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
                    udpsocket.sendto(bytes(FinClass(None,args.source_ip,args.source_port)),addr)
                    sys.exit(0)
                send_file_fragment((args.dest_ip,args.dest_port))
                log("send file package")



def whatKindaPackage(data):
    if data[:4] == bytes("0000",encoding="utf-8"):
        return "FileClass"
    else:
        return eval(data.decode())["kind"]

def check_continous():
    global cache_file
    global start_time
    key_list = cache_file.keys()
    key_list = sorted(key_list)
    for x in range(len(key_list)-1):
        if key_list[x+1] > key_list[x]+1024:
            return key_list[x]
    if time.time()-start_time >= 2:
        start_time = time.time()
        cache2dist((args.dest_ip,args.dest_port))
    return key_list[-1]

def cache2dist(addr):
    global cache_file
    key_list = sorted(cache_file.keys())
    bytes_file_list = list(map(lambda x:cache_file[x],key_list))
    bytes_file = reduce(lambda x,y:x+y,bytes_file_list)
    file_dict[addr]["file"].write(bytes_file)
    cache_file = dict()
def handle_file_package(data,addr):
    global file_dict
    kind = whatKindaPackage(data)
    log(kind)
    if kind == "FileClass":
        package = FileClass(data)
        if package.package["seq"] <= file_dict[addr]["current_ack"] + 1024:
            log("current seq={}".format(package.package["seq"]))
            #log(package.package["data"])
            #file_dict[addr]["file"].write(package.data)

            #from zero cache to infinate cache
            cache_file[package.package["seq"]] = package.data
            current_ack = check_continous()
            file_dict[addr]["current_ack"] = package.package["seq"]
        udpsocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        ackpackage = AckClass(file_dict[addr]["current_ack"],args.source_ip,args.source_port)
        udpsocket.sendto(bytes(ackpackage),(args.dest_ip,args.dest_port))
    elif kind == "fin":
        cache2dist(addr)
        file_dict[addr]["file"].close()
        sys.exit(0)

def recv_file(sendsocket,listensock):
    package = RequireFileClass(args.file,args.source_ip,args.source_port)
    sendsock.sendto(bytes(package),(args.dest_ip,args.dest_port))
    f = open(args.store_file,'ab')
    file_dict[(args.dest_ip,args.dest_port)] = dict()
    file_dict[(args.dest_ip,args.dest_port)]["file"] = f
    file_dict[(args.dest_ip,args.dest_port)]["current_ack"] = 0
    while True:
        if args.debug == False:
            try:
                data, addr = listensock.recvfrom(2048)
            except Exception as e:
                log("interupt")
                continue
        else:
            data,addr = listensock.recvfrom(2048)
        log(data)
        handle_file_package(data,(args.dest_ip,args.dest_port))
        

if __name__ == "__main__":
    init_args()
    listensock = init_socket()
    sendsock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    if args.recv==True:
        recv_file(sendsock,listensock)
    elif args.send==True:
        send_file(sendsock,listensock)