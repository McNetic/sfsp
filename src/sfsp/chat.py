import asynchat
import socket

from sfsp import debug

__all__ = ['SMTPChat']

class SMTPChat(asynchat.async_chat):
    COMMAND = 0
    DATA = 1

    data_size_limit = 33554432
    command_size_limit = 512

    def __init__(self, server, conn, addr):
        asynchat.async_chat.__init__(self, conn)
        self.smtp_server = server
        self.conn = conn
        self.addr = addr
        self.received_lines = []
        self.smtp_state = self.COMMAND
        self.seen_greeting = ''
        self.mailfrom = None
        self.rcpttos = []
        self.received_data = ''
        self.fqdn = socket.getfqdn()
        self.num_bytes = 0
        try:
            self.peer = conn.getpeername()
        except socket.error as err:
            # a race condition  may occur if the other end is closing
            # before we can get the peername
            self.close()
            if err.args[0] != errno.ENOTCONN:
                raise
            return
        print('Peer:', repr(self.peer), file=debug.stream)
        self.push('220 %s %s' % (self.fqdn, __version__))
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
        self.received_lines.append(str(data, "utf8"))

    # Implementation of base class abstract method
    def found_terminator(self):
        line = EMPTYSTRING.join(self.received_lines)
        print('Data:', repr(line), file=debug.stream)
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
                                                      self.mailfrom,
                                                      self.rcpttos,
                                                      self.received_data)
            self.rcpttos = []
            self.mailfrom = None
            self.smtp_state = self.COMMAND
            self.num_bytes = 0
            self.set_terminator(b'\r\n')
            if not status:
                self.push('250 Ok')
            else:
                self.push(status)

    # SMTP and ESMTP commands
    def smtp_HELO(self, arg):
        if not arg:
            self.push('501 Syntax: HELO hostname')
            return
        if self.seen_greeting:
            self.push('503 Duplicate HELO/EHLO')
        else:
            self.seen_greeting = arg
            self.push('250 %s' % self.fqdn)

    def smtp_NOOP(self, arg):
        if arg:
            self.push('501 Syntax: NOOP')
        else:
            self.push('250 Ok')

    def smtp_QUIT(self, arg):
        # args is ignored
        self.push('221 Bye')
        self.close_when_done()

    # factored
    def __getaddr(self, keyword, arg):
        address = None
        keylen = len(keyword)
        if arg[:keylen].upper() == keyword:
            address = arg[keylen:].strip()
            if not address:
                pass
            elif address[0] == '<' and address[-1] == '>' and address != '<>':
                # Addresses can be in the form <person@dom.com> but watch out
                # for null address, e.g. <>
                address = address[1:-1]
        return address

    def smtp_MAIL(self, arg):
        print('===> MAIL', arg, file=debug.stream)
        address = self.__getaddr('FROM:', arg) if arg else None
        if not address:
            self.push('501 Syntax: MAIL FROM:<address>')
            return
        if self.mailfrom:
            self.push('503 Error: nested MAIL command')
            return
        self.mailfrom = address
        print('sender:', self.mailfrom, file=debug.stream)
        self.push('250 Ok')

    def smtp_RCPT(self, arg):
        print('===> RCPT', arg, file=debug.stream)
        if not self.mailfrom:
            self.push('503 Error: need MAIL command')
            return
        address = self.__getaddr('TO:', arg) if arg else None
        if not address:
            self.push('501 Syntax: RCPT TO: <address>')
            return
        self.rcpttos.append(address)
        print('recips:', self.rcpttos, file=debug.stream)
        self.push('250 Ok')

    def smtp_RSET(self, arg):
        if arg:
            self.push('501 Syntax: RSET')
            return
        # Resets the sender, recipients, and data, but not the greeting
        self.mailfrom = None
        self.rcpttos = []
        self.received_data = ''
        self.smtp_state = self.COMMAND
        self.push('250 Ok')

    def smtp_DATA(self, arg):
        if not self.rcpttos:
            self.push('503 Error: need RCPT command')
            return
        if arg:
            self.push('501 Syntax: DATA')
            return
        self.smtp_state = self.DATA
        self.set_terminator(b'\r\n.\r\n')
        self.push('354 End data with <CR><LF>.<CR><LF>')

