'''
Created on 04.09.2012

@author: ehe
'''

import time

from sfsp.plugin import *
from sfsp import debug

@plugin()
class Delay():
    delay = 20

    def __init__(self):
        self.start_time = 0

    @event.listener(event.StartSession)
    @event.listener(event.ReceivedSMTPHelo)
    @event.listener(event.ReceivedSMTPMail)
    @event.listener(event.ReceivedSMTPRcpt)
    def StartSession(self, event, session):
        self.start_time = time.time()

    @event.listener(event.SendSMTPBanner)
    @event.listener(event.SendSMTPHeloResponse)
    @event.listener(event.SendSMTPMailResponse)
    @event.listener(event.SendSMTPRcptResponse)
    def SendSMPTBanner(self, event, session):
        print("Delaying for %d seconds" % (Delay.delay - (time.time() - self.start_time)), file = debug.stream())
        time.sleep(Delay.delay - (time.time() - self.start_time))
