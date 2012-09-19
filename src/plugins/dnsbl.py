'''
Created on 19.09.2012

@author: ehe
'''
from sfsp.plugin import event, plugin

@plugin()
class DNSBL(object):

    @event.listener(event.ValidateClientAddress, priority = 3)
    def validateRecipient(self):
        pass
