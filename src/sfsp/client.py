'''
Created on 30.08.2012

@author: ehe
'''

__all__ = ['SMTPClient']

class SMTPClient():
    '''
    classdocs
    '''


    def __init__(self, address):
        self.address = address
        self._pretense = ''
        
    @property
    def pretense(self):
        return self._pretense
    
    @pretense.setter
    def pretense(self, value):
        self._pretense = value
        