import asynchat
import errno
import socket

from sfsp import debug
from sfsp.transaction import *
from sfsp.client import *

__all__ = ['SMTPSession']

EMPTYSTRING = ''
NEWLINE = '\n'

class SMTPSession(asynchat.async_chat):
    COMMAND = 0
    DATA = 1

    data_size_limit = 33554432
    command_size_limit = 512

    def __init__(self, server, sock, address):
        asynchat.async_chat.__init__(self, sock)
        self.smtp_server = server
        self.sock = sock
        self.client = SMTPClient(address)
        self.received_lines = []
        self.smtp_state = self.COMMAND
        self.seen_greeting = False
        self.transaction = None
        self.received_data = ''
        self.fqdn = socket.getfqdn()
        self.num_bytes = 0
        try:
            self.peer = sock.getpeername()
        except socket.error as err:
            # a race condition  may occur if the other end is closing
            # before we can get the peername
            self.close()
            if err.args[0] != errno.ENOTCONN:
                raise
            return
        print('Peer:', repr(self.peer), file=debug.stream())
        self.push('220 %s %s' % (self.fqdn, self.smtp_server.version))
        self.set_terminator(b'\r\n')

    # Overrides base class for convenience
    def push(self, msg):
        asynchat.async_chat.push(self, bytes(msg + '\r\n', 'ascii'))

    # Implementation of base class abstract method
    def collect_incoming_data(self, data):
        limit = None
        if self.smtp_state == self.COMMAND:
            limit = self.command_size_limit
        elif self.smtp_state == self.DATA:
            limit = self.data_size_limit
        if limit and self.num_bytes > limit:
            return
        elif limit:
            self.num_bytes += len(data)
        self.received_lines.append(str(data, "ascii"))

    # Implementation of base class abstract method
    def found_terminator(self):
        line = EMPTYSTRING.join(self.received_lines)
        print('Data:', repr(line), file=debug.stream())
        self.received_lines = []
        if self.smtp_state == self.COMMAND:
            if self.num_bytes > self.command_size_limit:
                self.push('500 Error: line too long')
                self.num_bytes = 0
                return
            self.num_bytes = 0
            if not line:
                self.push('500 Error: bad syntax')
                return
            method = None
            i = line.find(' ')
            if i < 0:
                command = line.upper()
                arg = None
            else:
                command = line[:i].upper()
                arg = line[i+1:].strip()
            method = getattr(self, 'smtp_' + command, None)
            if not method:
                self.push('502 Error: command "%s" not implemented' % command)
                return
            method(arg)
            return
        else:
            if self.smtp_state != self.DATA:
                self.push('451 Internal confusion')
                self.num_bytes = 0
                return
            if self.num_bytes > self.data_size_limit:
                self.push('552 Error: Too much mail data')
                self.num_bytes = 0
                return
            # Remove extraneous carriage returns and de-transparency according
            # to RFC 821, Section 4.5.2.
            data = []
            for text in line.split('\r\n'):
                if text and text[0] == '.':
                    data.append(text[1:])
                else:
                    data.append(text)
            self.received_data = NEWLINE.join(data)
            status = self.smtp_server.process_message(self.peer,
                                                      self.transaction.mailfrom,
                                                      self.transaction.recipients,
                                                      self.received_data)
            self.transaction = None
            self.smtp_state = self.COMMAND
            self.num_bytes = 0
            self.set_terminator(b'\r\n')
            if not status:
                self.push('250 Ok')
            else:
                self.push(status)

    def reset(self):
        self.transaction = None
        self.received_data = ''
        self.smtp_state = self.COMMAND
    
    # SMTP and ESMTP commands
    def smtp_HELO(self, arg):
        # protocol validation (rfc8321)
        if not arg:
            self.push('501 Syntax: HELO hostname')
            return
        # end validation
        
        self.reset()
        self.client.pretense = arg
        self.seen_greeting = True
        self.push('250 %s' % self.fqdn)

    def smtp_NOOP(self, arg):
        # protocol validation (rfc8321)
        if arg:
            self.push('501 Syntax: NOOP')
            return
        # end validation
        
        self.push('250 Ok')

    def smtp_QUIT(self, arg):
        # protocol validation (rfc8321)
        if arg:
            self.push('501 Syntax: QUIT')
            return
        # end validation
        
        self.push('221 Bye')
        self.close_when_done()

    # factored
    def __getaddr(self, keyword, arg):
        address = None
        keylen = len(keyword)
        if arg[:keylen].upper() != keyword:
            address = arg[keylen:].strip()
            if not address:
                pass
            # TODO: Advanced address parsing?
            elif address[0] == '<' and address[-1] == '>' and address != '<>':
                # Addresses can be in the form <person@dom.com> but watch out
                # for null address, e.g. <>
                address = address[1:-1]
        return address

    def smtp_MAIL(self, arg):
        print('===> MAIL', arg, file=debug.stream())
        # protocol validation (rfc8321)
        if not self.seen_greeting:
            self.push('503 Error: MAIL before (EH|HE)LO')
            return
        address = self.__getaddr('FROM:', arg) if arg else None
        if not address:
            self.push('501 Syntax: MAIL FROM:<address>')
            return
        if self.transaction:
            self.push('503 Error: nested MAIL command')
            return
        # end validation
        
        self.transaction = SMTPTransaction(address)
        print('sender:', self.transaction.mailfrom, file=debug.stream())
        self.push('250 Ok')

    def smtp_RCPT(self, arg):
        print('===> RCPT', arg, file=debug.stream())
        # protocol validation (rfc8321)
        if not self.transaction:
            self.push('503 Error: need MAIL command')
            return
        address = self.__getaddr('TO:', arg) if arg else None
        if not address:
            self.push('501 Syntax: RCPT TO: <address>')
            return
        # end validation
        
        self.transaction.addRecipient(address)
        print('recips:', self.transaction.recipients, file=debug.stream())
        self.push('250 Ok')

    def smtp_RSET(self, arg):
        # protocol validation (rfc8321)
        if arg:
            self.push('501 Syntax: RSET')
            return
        # end validation
        
        # Resets the sender, recipients, and data, but not the greeting
        self.reset()
        self.push('250 Ok')

    def smtp_DATA(self, arg):
        # protocol validation (rfc8321)
        if not self.transaction.recipients:
            self.push('503 Error: need RCPT command')
            return
        if arg:
            self.push('501 Syntax: DATA')
            return
        # end validation
        
        self.smtp_state = self.DATA
        self.set_terminator(b'\r\n.\r\n')
        self.push('354 End data with <CR><LF>.<CR><LF>')

