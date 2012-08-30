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
    
    def addRecipient(self, address):
        self.recipients.append(address)
    
