from sfsp.plugin import event
from sfsp.delivery import *

__all__ = ['SMTPTransaction']

class SMTPTransaction():
    '''
    classdocs
    '''

    def __init__(self, mailfrom):
        '''
        Constructor
        '''
        self.mailfrom = mailfrom
        self.recipients = []
        self.data  = ''
        self.delivery = SMTPDelivery()
        event.StartTransaction.notify(self)
    
    def addRecipient(self, address):
        self.recipients.append(address)
        event.AddRecipient.notify(self)
    
