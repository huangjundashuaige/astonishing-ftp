import sys
import threading
import socket
from varyPackage.packages import *
import argparse
# global variable
file_dict = dict()
args = None
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

def recv_file(sendsocket,listensock):
    package = RequireFileClass(args.file,args.source_ip,args.source_port)
    sendsock.sendto(bytes(package),(args.dest_ip,args.dest_port))
    # one package need more expansion
    data,addr = listensock.recvfrom(2048)
    log(data)
    with open("456.txt","ab") as f:
        f.write(data)

def handle_file_package(data,addr):
    global file_dict
    if eval(data)["kind"] == "FileClass":
        package = FileClass(data)
        if package.package["seq"] <= file_dict[addr]["current_ack"] + 1024:
            log(package.package["data"])
            file_dict[addr]["file"].write(package.package["data"])
            file_dict[addr]["current_ack"] = package.package["seq"]
        udpsocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        ackpackage = AckClass(file_dict[addr]["current_ack"],args.source_ip,args.source_port)
        udpsocket.sendto(bytes(ackpackage),(args.dest_ip,args.dest_port))
    elif eval(data)["kind"] == "FinClass":
        file_dict[addr]["file"].close()
        sys.exit(0)

def send_file(sendsocket,listensock):
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