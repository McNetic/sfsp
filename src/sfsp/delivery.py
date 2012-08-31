'''
Created on 31.08.2012

@author: ehe
'''

from smtplib import SMTP

class SMTPDelivery(SMTP):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        SMTP.__init__(self)
    
    