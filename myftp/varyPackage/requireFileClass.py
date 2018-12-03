#!/usr/bin/env python
# coding: utf-8

# In[2]:


import json

# In[3]:
class PackageClass:
    def __init__(self,data,ip,port):
        self.package = dict()
        self.package["data"] = data
        self.package["ip"] = ip
        self.package["port"] = port
        self.package["kind"] = "PackageClass"
    def _type(self):
        return "PackageClass"
    def __str__(self):
        return str(self.package)
    def __bytes__(self):
        return bytes(str(self),encoding="utf-8")



class RequireFileClass(PackageClass):
    def __init__(self,data,ip=-1,port=-1):
        if ip == -1:
            self.package = eval(data.decode())
            return
        PackageClass.__init__(self,data,ip,port)
        self.package["kind"] = "RequireFileClass"
    def _type(self):
        return "RequireFileClass"

