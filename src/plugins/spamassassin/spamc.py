# implements http://svn.apache.org/repos/asf/spamassassin/trunk/spamd/PROTOCOL

import re
import socket
import email.parser


# default spamd port
HOST = 'localhost'
PORT = 783

# maximal line length when calling readline()
MAXLINE = 65536

# maximal amount of data to read at one time in
MAXAMOUNT = 1048576

# marker
UNKNOWN = 'UNKNOWN'


class ProtocolError(Exception):
    pass


class Response(object):
    def __init__(self, sock, method):
        self.fd = sock.makefile('rb', 0)
        self.method = method

        self.version = UNKNOWN
        self.status = UNKNOWN
        self.reason = UNKNOWN
        self.result = UNKNOWN
        self.score = UNKNOWN
        self.required = UNKNOWN

    def _read_status_line(self):
        line = self.fd.readline()
        if not line:
            raise ProtocolError('empty status line')

        try:
            version, status, reason = line.split()
        except ValueError:
            raise ProtocolError('bad status line: %s' % line)

        if not version.startswith('SPAMD/'):
            raise ProtocolError('bad status line: %s' % line)

        try:
            version = float(version[6:])
            status = int(status)
            reason = reason.strip()
        except ValueError:
            raise ProtocolError('bad status line: %s' % line)

        if not self.version > 1.0:
            raise ProtocolError('unknown protocol: %s' % self.version)

        return version, status, reason

    def _read_headers(self):
        headers = []
        while True:
            line = self.fd.readline(MAXLINE + 1)
            if len(line) > MAXLINE:
                raise ProtocolError('header line too long')
            headers.append(line)
            if line in ('\r\n', '\n', ''):
                break
        hstring = ''.join(headers)
        return email.parser.Parser().parsestr(hstring)

    def begin(self):
        # parse response status line
        self.version, self.status, self.reason = self._read_status_line()

        # parse headers
        self.headers = self._read_headers()

        # response length
        try:
            self.length = int(self.headers.get('content-length', ''))
        except ValueError:
            self.length = None

        # if the used methods returns a Spam header
        if self.method in ('CHECK', 'SYMBOLS', 'REPORT',
                           'REPORT_IFSPAM', 'PROCESS', 'HEADERS'):
            # parse Spam header
            value = self.headers.get("spam")
            try:
                m = re.match(r'^(\w+)\s;\s(-?\d+.?\d?)\s/\s(\d+.?\d?)$', value)
                result, score, required = m.groups()
                self.result = result == 'True'
                self.score = float(score)
                self.required = float(required)
            except (AttributeError, ValueError):
                raise ProtocolError('bad results header: %s' % value)

    def _read_data(self, size):
        s = []
        while size > 0:
            chunk = self.fd.read(min(size, MAXAMOUNT))
            if not chunk:
                raise ProtocolError('incomplete read')
            s.append(chunk)
            size = size - len(chunk)
        return ''.join(s)

    def read(self, size = None):
        if self.fd is None:
            return ''

        if self.length is not None:
            if size is None or size > self.length:
                # clip read to response size
                size = self.length
            s = self._read_data(size)
            self.length = self.length - size
            if not self.length:
                # we read everything
                self.close()
            return s

        s = self.fd.read(size)
        return s

    def close(self):
        if self.fd:
            self.fd.close()
            self.fd = None

    def __str__(self):
        return '%s %s' % (self.status, self.reason)


class Client(object):
    def __init__(self, host, port = PORT, timeout = socket._GLOBAL_DEFAULT_TIMEOUT, source = None):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.source = source
        self.sock = None
        self.method = None
        self.response = None

    def connect(self):
        self.sock = socket.create_connection((self.host, self.port),
                                             self.timeout, self.source)

    def close(self):
        if self.sock:
            self.sock.close()
            self.sock = None
        if self.response:
            self.response.close()
            self.response = None

    def request(self, method, body = None, user = None, headers = {}):
        # save the used method
        self.method = method

        # buffer output
        output = []

        # construct request
        request = '%s SPAMC/1.5' % method
        output.append(request)
        if body is not None:
            output.append('Content-length: %d' % len(body))
        if user is not None:
            output.append('User: %s' % user)
            # remove user from provided headers
            headers.pop('User', None)
        for header, value in headers.iteritems():
            output.append('%s: %s' % (header, value))
        output.append('')
        if body is not None:
            output.append(body)
        output.append('')

        # send
        data = '\r\n'.join(output)
        del output[:]
        self.connect()
        self.sock.sendall(data)

        # parse response
        self.response = Response(self.sock, self.method)
        self.response.begin()
        return self.response



MESSAGE = """\
Message-ID: <4E9D52C3.7060305@example.org>
Date: Tue, 18 Oct 2011 12:19:47 +0200
From: Example <example@example.org>
MIME-Version: 1.0
To: example@example.org
Subject: Test
Content-Type: text/plain; charset=ISO-8859-1
Content-Transfer-Encoding: 7bit

Hello

"""


def main():

    conn = Client(HOST, PORT)
    resp = conn.request('PING')
    print(resp)
    print(resp.read())

    for method in ('CHECK', 'SYMBOLS', 'REPORT', 'PROCESS', 'HEADERS',):
        print(method)
        conn = Client(HOST, PORT)
        resp = conn.request(method, MESSAGE, user = 'daniele')
        print(resp)
        print(resp.read(1024))

    method = 'HEADERS'
    conn = Client(HOST, PORT)
    resp = conn.request(method, MESSAGE, user = 'daniele')

    headers = email.parser.Parser().parsestr(resp.read())
    for name in ('X-Spam-Checker-Version', 'X-Spam-Level', 'X-Spam-Status',):
        print(name, headers.get(name, ''))


if __name__ == '__main__':
    main()
