'''
Created on 31.08.2012

@author: ehe
'''

from smtplib import SMTP

class SMTPServer(SMTP):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        SMTP.__init__(self)
        self.connected = False

    def connect_if_needed(self, host, port):
        if not self.connected:
            try:
                reply = SMTP.connect(self, host, port)
                if 220 == reply[0]:
                    self.connected = True
                return reply
            except Exception:
                raise
        else:
            return (250, 'Already connected')

    def quit_if_needed(self):
        if self.connected:
            self.quit()

    def ehlo_or_helo_if_needed(self):
        SMTP.ehlo_or_helo_if_needed(self)
