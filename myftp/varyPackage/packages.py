#!/usr/bin/env python
# coding: utf-8

# In[2]:


import json
from functools import reduce
# In[3]:
class PackageClass:
    def __init__(self,data,ip,port):
        self.package = dict()
        self.package["data"] = data
        self.package["source_ip"] = ip
        self.package["source_port"] = port
        self.package["kind"] = "PackageClass"
    def __str__(self):
        return str(self.package)
    def __bytes__(self):
        return bytes(str(self),encoding="utf-8")



class RequireFileClass(PackageClass):
    def __init__(self,data,source_ip=-1,source_port=-1):
        if source_ip == -1:
            self.package = eval(data.decode())
            return
        PackageClass.__init__(self,data,source_ip,source_port)
        self.package["kind"] = "RequireFileClass"


class RequestFileClass(PackageClass):
    def __init__(self,data,source_ip=-1,source_port=-1):
        if source_ip == -1:
            self.package = eval(data.decode())
            return
        PackageClass.__init__(self,data,source_ip,source_port)
        self.package["kind"] = "RequestFileClass"


class FileClass(PackageClass):
    def __init__(self,data,source_ip=-1,source_port=-1):
        if source_ip == -1:
            self.data_length = int(data[4:8].decode())
            self.package = eval(data[8:len(data)-self.data_length].decode())
            self.data =data[len(data)-self.data_length:]
            return
        PackageClass.__init__(self,data,source_ip,source_port)
        self.package["data"]=None
        self.data = data
        self.data_length = len(data)
        #print(len(data))
        self.package["kind"] = "FileClass"
    def __bytes__(self):
        if len(str(self.data_length))!=4:
            data_length = reduce(lambda x,y:x+y,['0' for x in range(4-len(str(self.data_length)))])+str(self.data_length)
        else:
            data_length = str(self.data_length)
        #print("package length"+str(len(self.data)))
        return bytes('0000'+data_length+str(self),encoding="utf-8")+self.data
    def ack(self,start_byte):
        self.package["ack"]=start_byte
    def seq(self,start_byte):
        self.package["seq"]=start_byte

class AckClass(PackageClass):
    def __init__(self,data,source_ip=-1,source_port=-1):
        if source_ip == -1:
            self.package = eval(data.decode())
            return
        PackageClass.__init__(self,data,source_ip,source_port)
        self.package["kind"] = "ack"
    def ack(self,start_byte):
        self.package["ack"]=start_byte
    def seq(self,start_byte):
        self.package["seq"]=start_byte

class SeqClass(PackageClass):
    def __init__(self,data,source_ip=-1,source_port=-1):
        if source_ip == -1:
            self.package = eval(data.decode())
            return
        PackageClass.__init__(self,data,source_ip,source_port)
        self.package["kind"] = "seq"
    def ack(self,start_byte):
        self.package["ack"]=start_byte
    def seq(self,start_byte):
        self.package["seq"]=start_byte

class FinClass(PackageClass):
    def __init__(self,data,source_ip=-1,source_port=-1):
        if source_ip == -1:
            self.package = eval(data.decode())
            return
        PackageClass.__init__(self,data,source_ip,source_port)
        self.package["kind"] = "fin"
    def ack(self,start_byte):
        self.package["ack"]=start_byte
    def seq(self,start_byte):
        self.package["seq"]=start_byte
