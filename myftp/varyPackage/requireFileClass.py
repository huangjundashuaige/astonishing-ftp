#!/usr/bin/env python
# coding: utf-8

# In[2]:


from packageClass import PackageClass    
import json

# In[3]:


class RequireFileClass(PackageClass):
    def __init__(self,data,ip=-1,port=-1):
        if ip == -1:
            self.package = eval(data.decode())
            return
        PackageClass.__init__(self,data)
    def _type(self):
        return "RequireFileClass"

