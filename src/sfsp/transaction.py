from sfsp.plugin import event

__all__ = ['SMTPTransaction']

NEWLINE = '\n'

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
        self.headerLines = []
        self.bodyLines = []
        event.StartTransaction.notify(self)

    def addRecipient(self, address):
        self.recipients.append(address)
        event.AddRecipient.notify(self)

    def appendHeaderLine(self, line):
        self.headerLines.append(line)

    def appendBodyLine(self, line):
        self.bodyLines.append(line)

    def completeMessage(self):
        return NEWLINE.join(self.headerLines + [''] + self.bodyLines);

