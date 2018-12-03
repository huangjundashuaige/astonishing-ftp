#!/usr/bin/env python
# coding: utf-8

# In[2]:


import json

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
            self.package = eval(data.decode())
            return
        PackageClass.__init__(self,data,source_ip,source_port)
        self.package["kind"] = "FileClass"
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
