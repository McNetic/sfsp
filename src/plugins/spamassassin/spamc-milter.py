# Simple milter deamon that handles email messages off to spamd for
# classification.  Messages classified as spam are rejected.  Other
# are augmented with Spamassassin additional headers.

import email.parser
from cStringIO import StringIO

import Milter as milter
import spamc


# headers to add to scanned messages
HEADERS = ('X-Spam-Checker-Version', 'X-Spam-Level', 'X-Spam-Status',)


class Milter(milter.Base):

    def __init__(self):
        # integer incremented with each call
        self.id = milter.uniqueID()
        self.fd = StringIO()

    @milter.noreply
    def connect(self, hostname, family, hostaddr):
        self.hostname = hostname
        self.hostaddr = hostaddr
        return milter.CONTINUE

    def hello(self, heloname):
        self.helo = heloname
        return milter.CONTINUE

    def envfrom(self, mailfrom, *str):
        self.mailfrom = mailfrom
        return milter.CONTINUE

    @milter.noreply
    def envrcpt(self, recipient, *str):
        self.recipient = recipient
        return milter.CONTINUE

    @milter.noreply
    def header(self, name, val):
        # add header to buffer
        self.fd.write('%s: %s\n' % (name, val))
        return milter.CONTINUE

    @milter.noreply
    def eoh(self):
        # terminate headers
        self.fd.write('\n')
        return milter.CONTINUE

    @milter.noreply
    def body(self, chunk):
        # add body to buffer
        self.fd.write(chunk)
        return milter.CONTINUE

    def eom(self):
        # ask spamd about the received message
        self.conn = spamc.Client('localhost')
        resp = self.conn.request('HEADERS', self.fd.getvalue())
        # reject spam messages
        if resp.result:
            return milter.REJECT
        # parse returned message headers
        data = resp.read()
        print(data)
        headers = email.parser.Parser().parsestr(data)
        # add headers
        for name in HEADERS:
            # transform multiple line headers to single line ones
            value = ' '.join(headers.get(name, '').split())
            self.addheader(name, value)
        # accept message
        return milter.ACCEPT

    def close(self):
        # clean up
        self.fd.close()
        self.conn.close()
        return milter.CONTINUE

    def abort(self):
        # client disconnected prematurely
        return milter.CONTINUE


def main():
    socketname = "/var/spool/postfix/private/spamc"
    timeout = 600

    # register the milter factory
    milter.factory = Milter
    # ask milter features we use
    milter.set_flags(milter.CHGHDRS + milter.ADDHDRS)
    # run
    milter.runmilter("spamc-milter", socketname, timeout)


if __name__ == "__main__":
    main()
