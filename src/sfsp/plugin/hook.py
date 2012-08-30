'''
Created on 30.08.2012

@author: ehe
'''
import inspect

def hook(fn):
#    obj = fn.im_self
#    for cls in inspect.getmro(obj.im_class):
#        fcls = None
#        if fn.__name__ in cls.__dict__:
#            fcls = cls
        
    print(fn.__name__, fn.__self__, fn.__dict__)