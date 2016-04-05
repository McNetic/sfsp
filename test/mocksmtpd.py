#!/usr/bin/env python3
"""A noddy fake smtp server."""

import smtpd
import asyncore
import threading

class MockSMTPServer(smtpd.SMTPServer):
    """A Fake smtp server"""

    def __init__(self, localaddr, remoteaddr, silent=False):
        self.silent = silent
        self.debug("Running mock smtp server on port 25")
        smtpd.SMTPServer.__init__(self, localaddr, remoteaddr)

    def debug(self, message):
        if not self.silent:
            print(message)

    def process_message(self, peer, mailfrom, rcpttos, data, **kwargs):
        if "invalid@to.de" in rcpttos:
            return "550 no such user %s" % rcpttos[0]

    def run(self):
        self.thread = threading.Thread(target=asyncore.loop, kwargs={'timeout':1})
        self.thread.start()

    def quit(self):
        self.close()
        self.thread.join()

if __name__ == "__main__":
    smtp_server = MockSMTPServer(('localhost', 25), None)
    try:
        asyncore.loop()
    except KeyboardInterrupt:
        smtp_server.close()
