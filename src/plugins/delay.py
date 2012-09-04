'''
Created on 04.09.2012

@author: ehe
'''

import time

from sfsp.plugin import *

@plugin()
class Delay():

    @event.listener(event.SendSMTPBanner, scope = event.Scope.SESSION)
    def SendSMPTBanner(self):
        pass
