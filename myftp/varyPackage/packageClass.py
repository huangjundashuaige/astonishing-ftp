#!/usr/bin/env python
# coding: utf-8

# In[1]:


import json


# In[36]:


class PackageClass:
    def __init__(self,data,ip,port):
        self.package = dict()
        self.package["data"] = data
        self.package["ip"] = ip
        self.package["port"] = port
    def _type(self):
        return "PackageClass"
    def __str__(self):
        return str(self.package)
    def __bytes__(self):
        return bytes(str(self),encoding="utf-8")




