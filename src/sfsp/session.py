import asynchat
import errno
import smtplib
import socket

from sfsp import debug
from sfsp.client import *
import sfsp.plugin.event as event
from sfsp.remoteserver import *
from sfsp.transaction import *
from sfsp.error import *
import sfsp.plugin.filter

__all__ = ['SMTPSession']

EMPTYSTRING = ''
CRLF = '\r\n'
BCRLF = b'\r\n'

class ErrorState:

    OK = 0
    DEFERED = 1
    FATAL = 2

    def __init__(self):
        self.state = 0


class SMTPSession(asynchat.async_chat):
    SMTP_COMMAND = 0
    SMTP_DATA = 1

    DATA_NONE = 0
    DATA_HEADER = 1
    DATA_BODY = 2

    data_size_limit = 33554432
    command_size_limit = 512

    def __init__(self, sfsp, sock, address):
        super().__init__(sock)
        self.sfsp = sfsp
        self.sock = sock
        self.client = SMTPClient(address)
        self.received_lines = []
        self.smtp_state = self.SMTP_COMMAND
        self.data_state = self.DATA_NONE
        self.error_state = ErrorState.OK
        self.seen_greeting = False
        self.transaction = None
        self.server = SMTPServer()
        self.num_bytes = 0
        self.set_terminator(BCRLF)
        self.last_line = None

    def initSMTP(self):
        event.StartSession.notify()
        self.fqdn = socket.getfqdn()
        """ TODO: kann peer wirklich unterschiedlich sein zu address?
        try:
            self.peer = self.sock.getpeername()
        except socket.error as err:
            # a race condition  may occur if the other end is closing
            # before we can get the peername
            self.close()
            if err.args[0] != errno.ENOTCONN:
                raise
            return
        print('Peer:', repr(self.peer), file = debug.stream())
        """
        print('Address:', repr(self.client.address), file = debug.stream())

        result = sfsp.plugin.filter.Filter.validateClientAddress(self.client)
        if result.failNow() or (not self.sfsp.options.defer_errors and result.failDefer()):
            self.sendReply(result)
        elif result.failChoose():
            # TODO: choose something?
            pass

        self.sendReply((220, '%s %s' % (self.fqdn, self.sfsp.version)), event.SendSMTPBanner)

    # Overrides base class for convenience
    def push(self, msg):
        super().push(bytes(msg + CRLF, 'ascii'))

    def pushReply(self, reply):
        if isinstance(reply[1], str):
            resp = reply[1]
        else:
            resp = str(reply[1], 'ascii')
        resp = resp.split(CRLF)
        msg = str(reply[0])
        if 1 < len(resp):
            msg += '-' + (CRLF + reply[0] + '-').join(resp[:-1]) + reply[0]
        msg += ' ' + resp[-1]
        self.push(msg)

    def sendReply(self, reply, evt = None):
        if evt:
            evt.notify()
        if isinstance(reply, str):
            self.push(reply)
        else:
            self.pushReply(reply)

    def sendOK(self, evt = None):
        return self.sendReply((250, 'Ok'), evt)

    # Implementation of base class abstract method
    def collect_incoming_data(self, data):
        limit = None
        if self.smtp_state == self.SMTP_COMMAND:
            limit = self.command_size_limit
        elif self.smtp_state == self.SMTP_DATA:
            limit = self.data_size_limit
        if limit and self.num_bytes > limit:
            return
        elif limit:
            self.num_bytes += len(data)
        self.received_lines.append(str(data, "ascii"))

    def command_terminated(self, line):
        if self.num_bytes > self.command_size_limit:
            self.sendReply((500, 'Error: line too long'))
            self.num_bytes = 0
            return
        self.num_bytes = 0
        if not line:
            self.sendReply((500, 'Error: bad syntax'))
            return
        i = line.find(' ')
        if i < 0:
            command = line.upper()
            arg = None
        else:
            command = line[:i].upper()
            arg = line[i + 1:].strip()
        method = getattr(self, 'smtp_' + command, None)
        if not method:
            self.sendReply((502, 'Error: command "%s" not implemented' % command))
            return
        method(arg)
        return

    def data_terminated(self, line):
        if self.smtp_state != self.SMTP_DATA or (self.data_state != self.DATA_HEADER and self.data_state != self.DATA_BODY):
            self.sendReply((451, 'Internal confusion'))
            self.num_bytes = 0
            return
        if self.num_bytes > self.data_size_limit:
            self.sendReply((552, 'Error: Too much mail data'))
            self.num_bytes = 0
            return

        if '.' == line:
            # end of transaction
            self.process_message()
            self.data_state = self.DATA_NONE
        else:
            # Remove extraneous carriage returns and de-transparency according
            # to RFC 821, Section 4.5.2.
            if line and '.' == line[0]:
                line = line[1:]
            if self.DATA_HEADER == self.data_state:
                if '' == line:
                    print("end of headers", file = debug.stream())
                    self.data_state = self.DATA_BODY
                else:
                    self.transaction.appendHeaderLine(line)
            else:
                self.transaction.appendBodyLine(line)

    def process_message(self):
        # filter, decide to deliver or reject
        #print("### Processing message ###", file = debug.stream())
        #print(self.transaction.completeMessage(), file = debug.stream())
        #print("### EOM ###", file = debug.stream())

        # TODO: content filtering here.

        # finally, delivery
        try:
            (code, reply) = self.server.data_data(self.transaction.completeMessage())
            # DO NOT DO ANYTHING OR SEND ANYTHING OTHER THAN 250 AFTER SUCCESSFUL DELIVERY!
            if 250 != code:
                self.sendReply((code, reply))
            else:
                self.sendOK()
        except Exception:
            self.sendReply((451, 'Error in processing'))
            raise

        self.transaction = None
        self.smtp_state = self.SMTP_COMMAND
        self.num_bytes = 0

    # Implementation of base class abstract method
    def found_terminator(self):
        line = EMPTYSTRING.join(self.received_lines)
        print('Data:', repr(line), file = debug.stream())
        self.received_lines = []
        if self.smtp_state == self.SMTP_COMMAND:
            self.command_terminated(line)
        else:
            self.data_terminated(line)

    def reset(self):
        self.transaction = None
        self.server.reset_if_needed()
        self.smtp_state = self.SMTP_COMMAND

    # SMTP and ESMTP commands
    def smtp_HELO(self, arg):
        event.ReceivedSMTPHelo.notify()
        # protocol validation (rfc8321)
        if not arg:
            self.sendReply('501 Syntax: HELO hostname', event.SendSMTPHeloResponse)
            return
        # end validation

        self.reset()
        self.client.pretense = arg
        self.seen_greeting = True
        self.sendReply((250, self.fqdn), event.SendSMTPHeloResponse)

    def smtp_NOOP(self, arg):
        # protocol validation (rfc8321)
        if arg:
            self.sendReply((501, 'Syntax: NOOP'))
            return
        # end validation

        self.sendOK()

    def smtp_QUIT(self, arg):
        # protocol validation (rfc8321)
        if arg:
            self.sendReply((501, 'Syntax: QUIT'))
            return
        # end validation

        self.server.quit_if_needed()
        self.sendReply((221, 'Bye'))
        self.close_when_done()

    # factored
    def __getaddr(self, keyword, arg):
        address = None
        keylen = len(keyword)
        print(arg[:keylen].upper(), keyword, file = debug.stream())
        if arg[:keylen].upper() == keyword:
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
        event.ReceivedSMTPMail.notify()
        print('===> MAIL', arg, file = debug.stream())
        # protocol validation (rfc8321)
        if not self.seen_greeting:
            self.sendReply('503 Error: MAIL before (EH|HE)LO', event.SendSMTPMailResponse)
            return
        if self.transaction:
            self.sendReply('503 Error: nested MAIL command', event.SendSMTPMailResponse)
            return
        address = self.__getaddr('FROM:', arg) if arg else None
        if not address:
            self.sendReply('501 Syntax: MAIL FROM:<address>', event.SendSMTPMailResponse)
            return
        # target smtp validation
        try:
            (code, reply) = self.server.connect_if_needed(self.sfsp.options.remoteaddress, self.sfsp.options.remoteport)
            if 220 != code:
                # TODO: maybe only forward 421?
                self.sendReply((code, reply), event.SendSMTPMailResponse)
                return
        except Exception:
            self.sendReply('451 Error in processing (connection to remote smtp server failed)', event.SendSMTPMailResponse)
            return
        try:
            self.server.ehlo_or_helo_if_needed()
        except smtplib.SMTPHeloError as excpt:
            self.sendReply('451 Error in processing (' + excpt.resp + ')', event.SendSMTPMailResponse)
            return
        try:
            (code, reply) = self.server.mail(address)
            # TODO: process reply code
            if 250 != code:
                self.sendReply((code, reply), event.SendSMTPMailResponse)
                return
        except Exception:
            self.sendReply('451 Error in processing (connection to remote smtp server failed)', event.SendSMTPMailResponse)
            return
        # end validation

        self.transaction = SMTPTransaction(address)

        print('sender:', self.transaction.mailfrom, file = debug.stream())
        self.sendOK(event.SendSMTPMailResponse)

    def smtp_RCPT(self, arg):
        event.ReceivedSMTPRcpt.notify()
        print('===> RCPT', arg, file = debug.stream())
        # protocol validation (rfc8321)
        if not self.transaction:
            self.sendReply('503 Error: need MAIL command', event.ReceivedSMTPRcpt)
            return
        address = self.__getaddr('TO:', arg) if arg else None
        if not address:
            self.sendReply('501 Syntax: RCPT TO: <address>', event.ReceivedSMTPRcpt)
            return
        # target smtp validation
        try:
            (code, reply) = self.server.rcpt(address)
            if 250 != code:
                # TODO: maybe examine reply?
                self.sendReply((code, reply), event.ReceivedSMTPRcpt)
                return
        except Exception:
            self.sendReply('451 Error in processing', event.ReceivedSMTPRcpt)
            return
        # end validation

        result = sfsp.plugin.filter.Filter.validateRecipient(address)
        if 250 != result.mainresult.smtp_error:
            self.sendReply((result.mainresult.smtp_error, result.mainresult.message), event.ReceivedSMTPRcpt)
            return


        # end filtering

        self.transaction.addRecipient(address)
        print('recips:', self.transaction.recipients, file = debug.stream())
        self.sendOK(event.ReceivedSMTPRcpt)

    def smtp_RSET(self, arg):
        # protocol validation (rfc8321)
        if arg:
            self.sendReply((501, 'Syntax: RSET'))
            return
        # end validation

        # Resets the sender, recipients, and data, but not the greeting
        self.reset()
        self.sendOK()

    def smtp_DATA(self, arg):
        # protocol validation (rfc8321)
        if not self.transaction.recipients:
            self.sendReply((503, 'Error: need RCPT command'))
            return
        if arg:
            self.sendReply((501, 'Syntax: DATA'))
            return
        # TODO: have recipients?
        # target smtp validation
        try:
            (code, reply) = self.server.data_cmd()
            if 354 != code:
                #TODO: maybe react to different codes 
                self.sendReply((451, 'Error in processing'))
                return
        except Exception:
            self.sendReply((451, 'Error in processing'))
            return
        # end validation

        self.smtp_state = self.SMTP_DATA
        self.data_state = self.DATA_HEADER
        self.sendReply((354, 'End data with <CR><LF>.<CR><LF>'))

