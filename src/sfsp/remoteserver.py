'''
Created on 31.08.2012

@author: ehe
'''

from sys import stderr
from sfsp import debug

from smtplib import SMTP, _fix_eols, _quote_periods, bCRLF

__all__ = ['SMTPServer']

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
        print("connect_if_needed()", file = debug.stream())
        if not self.connected:
            print("  not connected, try connect", file = debug.stream())
            try:
                reply = SMTP.connect(self, host, port)
                print("  reply (%s, %s)" % reply, file = debug.stream())
                if 220 == reply[0]:
                    print("  connected = True", file = debug.stream())
                    self.connected = True
                return reply
            except Exception:
                raise
        else:
            return (250, 'Already connected')

    def reset_if_needed(self):
        print("reset_if_needed()", file = debug.stream())
        if self.connected:
            print("  connected, try reset", file = debug.stream())
            SMTP.rset(self)

    def quit_if_needed(self):
        if self.connected:
            self.quit()

    def ehlo_or_helo_if_needed(self):
        SMTP.ehlo_or_helo_if_needed(self)


    def data_cmd(self):
        self.putcmd("data")
        (code, repl) = self.getreply()
        if self.debuglevel > 0:
            print("data:", (code, repl), file = stderr)
        return (code, repl)

    def data_data(self, msg):
        if isinstance(msg, str):
            msg = _fix_eols(msg).encode('ascii')
        q = _quote_periods(msg)
        if q[-2:] != bCRLF:
            q = q + bCRLF
        q = q + b"." + bCRLF
        self.send(q)
        (code, msg) = self.getreply()
        if self.debuglevel > 0:
            print("data:", (code, msg), file = stderr)
        return (code, msg)

