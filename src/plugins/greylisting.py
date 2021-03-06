'''
Created on 30.08.2012

@author: ehe
'''

import time

from sfsp import debug
from sfsp.plugin import *

def name():
    pass

#TODO: persist data
#TODO: configurable delays (general configurability)

@plugin()
class Greylisting():
    '''
    classdocs
    '''
    greytriplets = {}
    whitetriplets = {}

    def __init__(self):
        pass

    def passed(self):
        return filter.FilterResultOK

    def greylisted(self):
        return filter.FilterResult(filter.FilterResult.ERROR, filter.FilterResult.FAIL_DEFER, "Please try again later", 451)

    @event.listener(event.ValidateRecipient)
    def validateRecipient(self, evt, session, address):
        triplet = (session.client.address[0], session.transaction.mailfrom, address)
        if triplet in Greylisting.whitetriplets:
            print("found triplet", triplet, "in whitelist, accepting", file = debug.stream())
            return self.passed()
        elif not triplet in Greylisting.greytriplets:
            print("unknwon triplet", triplet, ", greylisting", file = debug.stream())
            Greylisting.greytriplets[triplet] = time.time()
            return self.greylisted()
        elif Greylisting.greytriplets[triplet] > time.time() - 15:
            print("triplet", triplet, "still greylisted, try again later", file = debug.stream())
            # TODO: restart waiting?
            # Greylisting.greytriplets[triplet] = time.time()
            return self.greylisted()
        elif Greylisting.greytriplets[triplet] < time.time() - 60 * 60 * 24 * 3: # older than 3 days
            print("triplet", triplet, "greylisted but not seen for very long, try again later", file = debug.stream())
            Greylisting.greytriplets[triplet] = time.time()
            return self.greylisted()
        else:
            print("triplet", triplet, "known, moving to whitelist, accepting")
            Greylisting.greytriplets.pop(triplet)
            Greylisting.whitetriplets[triplet] = time.time()
            return self.passed()
