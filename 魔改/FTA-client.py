# -*- coding: UTF-8 -*-
import socket
import sys
import struct
import crpSocket2

DEBUG = True

def log(message):
    if DEBUG:
        print message

def connect():
    global sock
    global state

    
    print("Connecting...")
    # ftaServerIP  ftaServerPort 来自于命令行的输入
    sock.connect(ftaServerIP, ftaServerPort)
    state = 'CONNECTED'
    print("connected!")

def runClient():
    userInput = raw_input('\n\nEnter a command:\n')
    splitInput = userInput.split(' ', 1)

    if splitInput[0] == 'connect':
        connect()


clientPort = 7001
ftaServerIP = sys.argv[1] # 输入的127.0.0.1之类的
ftaServerPort = int(sys.argv[2]) # 端口号
debugFlag = True

sock = crpSocket2.CRPSocket2(clientPort, debugFlag)
state = 'DISCONNECTED'

try:
    sock.bind('127.0.0.1', clientPort)
except Exception as e:
    print "Error during binding " + str(e)
    sys.exit(1)

while True:
    runClient()