'''
Created on 30.08.2012

@author: ehe
'''
import sfsp.plugin
from .hook import hook

class FilterResult():
    OK = 0
    WARNING = 1
    SUSPICIOUS = 2
    UNDESIRABLE = 3
    ERROR = 4
    PROTOCOL_FATAL = 5
    TRANSACTION_FATAL = 6
    SESSION_FATAL = 7
    
    def __init__(self):
        self.errorlevel = FilterResult.OK
        self.message = None
        self.smtp_error = 250

class Filter(sfsp.plugin.Plugin):
    '''
    classdocs
    '''

    def __init__(self):
        sfsp.plugin.Plugin.__init__(self)
    
    @hook
    def validateRecipient(self, address):
        pass
    
    def notifyStartTransaction(self):
        pass
        
    def notifyAddRecipient(self):
        pass

