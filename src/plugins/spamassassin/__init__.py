'''
Created on 20.09.2012

@author: ehe
'''

import email

from .spamc import Client as SPAMC

from sfsp.plugin import plugin, event

@plugin(scope = event.Scope.SESSION)
class SpamAssassin(object):

    @event.listener(event.ValidateData)
    def validateData(self, evt, session, transaction):
         # ask spamd about the received message
        self.conn = SPAMC('localhost')
        resp = self.conn.request('HEADERS', transaction.completeMessage(), 'nobody')

        # reject spam messages
        #if resp.result:
        #    return milter.REJECT

        # parse returned message headers
        data = resp.read()
        print(data)
        headers = email.parser.Parser().parsestr(data)
        # add headers
        for name in headers:
            # transform multiple line headers to single line ones
            value = ' '.join(headers.get(name, '').split())
            print('#%s#%s#' % (name, value))
        # accept message
        #return milter.ACCEPT

