'''
Created on 18.04.2013

@author: Nicolai Ehemann
'''
import unittest
import smtplib
from test.mocksmtpd import MockSMTPServer

class TestMockSMTPD(unittest.TestCase):

    def setUp(self):
        self.smtpserver = MockSMTPServer(('localhost', 25), None, True)
        self.smtpserver.run()
        self.smtpclient = smtplib.SMTP('localhost')

    def tearDown(self):
        self.smtpclient.quit()
        self.smtpserver.quit()

    def testAcceptMail(self):
        self.smtpclient.sendmail("me@from.de", "valid@to.de", "Message")

    def testRejectRecipient(self):
        with self.assertRaises(smtplib.SMTPDataError):
            self.smtpclient.sendmail("me@from.de", "invalid@to.de", "Message")
