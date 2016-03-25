'''
Created on 03.09.2012

@author: ehe
'''
import unittest
import smtplib

class Test(unittest.TestCase):

    def setUp(self):
        self.smtp = smtplib.SMTP(host = 'localhost', port = 25)

    def tearDown(self):
        self.smtp.quit()

    def testRecipientNoFQDN(self):
        """recipient without fqdn should be rejected"""
        self.assertRaises(smtplib.SMTPRecipientsRefused, self.smtp.sendmail, "me", "you", "Headers\nHeaders\n\nBody\nBody\nBody")

#    def testEverythingOK(self):
#        self.smtp.sendmail("me@me.com", "en@enlightened.de", "Headers\nHeaders\n\nBody\nBody\nBody")

#    def testSample2(self):
#        self.smtp.sendmail("me", "you", "")
