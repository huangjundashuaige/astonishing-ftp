#!/usr/bin/env python
# coding: utf-8

# In[6]:


import sys
import struct
import socket
import os
import threading

# In[12]:


def args():
    if len(sys.argv) ==2:
        return dict({"ip":sys.argv[1].split(":")[0],"port":sys.argv[1].split(":")[1]})
    elif len(sys.argv) ==1:
        return dict({"ip":"127.0.0.1","port":8888})
    else:
        raise Exception("wrong uausage")


# In[ ]:





# In[9]:


# global variable
isDebug = True


# In[10]:


def log(message):
    if isDebug:
        print(message)


# In[14]:


def init():
    try:
        ipNport = args()
        log("---init ftp server---")
        udpsock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        udpsock.bind((ipNport["ip"],int(ipNport["port"])))
        log("server bind to {} : {}".format(ipNport["ip"],ipNport["port"]))
        return udpsock
    except Exception as e:
        print(e)

def toprouter():
    

def runServer(udpsocket):
    log("running server")
    while True:
        data , addr = udpsocket.recvfrom(1024)
        router(data,addr)
        # addr should be ("127.0.0.1", 8000)
        t = threading.Thread(target=toprouter,agrs=(udpsocket,data,addr))
        t.start()
# In[15]:


if __name__ == "__main__":
    init()


# In[ ]:




