'''
Created on 14.09.2012

@author: ehe
'''

class SMTPErrorMessage(object):

    def __init__(self, bsc, esc, message):
        self.bsc = bsc
        self.esc = esc
        self.message = message

class SMTPError(object):

    def __init__(self):
        self.errors = []

    def add(self, error):
        self.errors.append(error)

