import asyncore
import socket
import time

from sfsp.chat import *
from sfsp import debug

class Proxy(asyncore.dispatcher):

    def __init__(self, localaddr, remoteaddr):
        self._localaddr = localaddr
        self._remoteaddr = remoteaddr
        asyncore.dispatcher.__init__(self)
        try:
            self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
            # try to re-use a server port if possible
            self.set_reuse_addr()
            self.bind(localaddr)
            self.listen(5)
        except:
            self.close()
            raise
        else:
            print('%s started at %s\n\tLocal addr: %s\n\tRemote addr:%s' % (
                self.__class__.__name__, time.ctime(time.time()),
                localaddr, remoteaddr), file=debug.stream)

    def run(self):
        asyncore.loop()

    def handle_accepted(self, conn, addr):
        print('Incoming connection from %s' % repr(addr), file=debug.stream)
        channel = SMTPChat(self, conn, addr)

    # API for "doing something useful with the message"
    def process_message(self, peer, mailfrom, rcpttos, data):
        """Override this abstract method to handle messages from the client.

        peer is a tuple containing (ipaddr, port) of the client that made the
        socket connection to our smtp port.

        mailfrom is the raw address the client claims the message is coming
        from.

        rcpttos is a list of raw addresses the client wishes to deliver the
        message to.

        data is a string containing the entire full text of the message,
        headers (if supplied) and all.  It has been `de-transparencied'
        according to RFC 821, Section 4.5.2.  In other words, a line
        containing a `.' followed by other text has had the leading dot
        removed.

        This function should return None, for a normal `250 Ok' response;
        otherwise it returns the desired response string in RFC 821 format.

        """
        raise NotImplementedError
