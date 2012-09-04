'''
Created on 30.08.2012

@author: ehe
'''
import sfsp.plugin

class FilterResult(sfsp.plugin.event.EventResult):
    OK = 0
    WARNING = 1
    SUSPICIOUS = 2
    UNDESIRABLE = 3
    ERROR = 4
    PROTOCOL_FATAL = 5
    TRANSACTION_FATAL = 6
    SESSION_FATAL = 7

    def __init__(self, errorlevel, message, smtp_error):
        self.errorlevel = errorlevel
        self.message = message
        self.smtp_error = smtp_error

class Filter():
    '''
    classdocs
    '''

    @staticmethod
    def validateRecipient(address):
        return sfsp.plugin.event.ValidateRecipient.probe(FilterResultOK, address)


FilterResultOK = FilterResult(errorlevel = FilterResult.OK, message = 'Ok', smtp_error = 250);
