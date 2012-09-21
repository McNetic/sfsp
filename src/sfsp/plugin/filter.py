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

    def __init__(self, errorlevel, faillevel , message, smtp_error):
        super().__init__(errorlevel, faillevel, message)
        self.smtp_error = smtp_error

class Filter():
    '''
    classdocs
    '''

    @staticmethod
    def validateRecipient(address):
        return sfsp.plugin.event.ValidateRecipient.probe(FilterResultOK, address)

    @staticmethod
    def validateClientAddress(client):
        return sfsp.plugin.event.ValidateClientAddress.probe(FilterResultOK, client)

    @staticmethod
    def validateData(transaction):
        return sfsp.plugin.event.ValidateData.probe(FilterResultOK, transaction)

FilterResultOK = FilterResult(errorlevel = FilterResult.OK, faillevel = FilterResult.FAIL_NOT, message = 'Ok', smtp_error = 250);
