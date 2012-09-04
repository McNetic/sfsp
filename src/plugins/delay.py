'''
Created on 04.09.2012

@author: ehe
'''

import time

from sfsp.plugin import *

@plugin()
class Delay():

    @event.listener(event.StartSession)
    def StartSession(self, event, session):
        print(session.data_size_limit)

    @event.listener(event.SendSMTPBanner)
    def SendSMPTBanner(self, event, session):
        pass
