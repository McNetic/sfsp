'''
Created on 19.09.2012

@author: ehe
'''

import asyncdns

from sfsp.plugin import event, plugin

@plugin(scope = event.Scope.SESSION)
class DNSBL(object):

    blacklists = set()

    def __init__(self):
        self.results = []

    @classmethod
    def register(cls, blacklist):
        cls.blacklists.add(blacklist)

    @staticmethod
    def reverseIp(ip):
        ip = ip.split('.')
        ip.reverse()
        return '.'.join(ip)

    @event.listener(event.ValidateClientAddress, priority = 3)
    def validateClientAddress(self, event, session, client):
        wheel = asyncdns.TimeWheel()
        resolver = asyncdns.Resolver(wheel)

        def collect_result(nameserver, domain, results):
            #TODO: scoring
            print('Got one: ', domain, results)
            latch.countDown()

        reverseIp = self.reverseIp(client.address[0])
        latch = asyncdns.CountDownLatch(len(self.__class__.blacklists))
        try:
            for blacklist in self.__class__.blacklists:
                resolver.lookupAddress('%s.%s' % (reverseIp, blacklist.zone), callback = collect_result, expired = 10, nameservers = asyncdns.Resolver.system_nameservers())
            latch.await()
        except Exception as excpt:
            print('Error in lookup: ', excpt)

        #TODO: react to scores


class DNSBlacklist(object):

    def __init__(self, name, zone):
        self.name = name
        self.zone = zone
        DNSBL.register(self)

_ProxyBL = DNSBlacklist('ProxyBL', 'dnsbl.proxybl.org')
_UCEProtectLevel1 = DNSBlacklist('UCEPROTECT Level 1', 'dnsbl-1.uceprotect.net')
_NiXSpam = DNSBlacklist('NiX Spam', 'ix.dnsbl.manitu.net')
_Truncate = DNSBlacklist('Truncate', 'truncate.gbudb.net')
