'''
Created on 31.08.2012

@author: ehe
'''

import inspect
from pprint import pprint
import time
import traceback
import weakref

from sfsp import debug
from sfsp.util.bucketset import BucketSet
import sfsp.session

class Scope(object):
    GLOBAL = 0
    SESSION = 1

class EventResult(object):
    NONE = -1,
    OK = 0

    FAIL_NOT = 0
    FAIL_CHOOSE = 1
    FAIL_DEFER = 2
    FAIL_NOW = 3

    def __init__(self, errorlevel, faillevel, message):
        self.faillevel = faillevel
        self.errorlevel = errorlevel
        self.message = message

    def failNow(self):
        return EventResult.FAIL_NOW == self.faillevel

    def failChoose(self):
        return EventResult.FAIL_CHOOSE == self.faillevel

    def failDefer(self):
        return EventResult.FAIL_DEFER == self.faillevel

    def failNot(self):
        return EventResult.FAIL_NOT == self.faillevel

class EventResultList():

    def __init__(self):
        self.mainresult = None
        self.resultlist = set()

    def addResult(self, result):
        self.resultlist.add(result)

    def setMainResult(self, result):
        if self.mainresult:
            self.addResult(self.mainresult)
        self.mainresult = result

    def failNow(self):
        if self.mainresult:
            return self.mainresult.failNow()
        else:
            return False

    def failChoose(self):
        if self.mainresult:
            return self.mainresult.failChoose()
        else:
            return False

    def failDefer(self):
        if self.mainresult:
            return self.mainresult.failDefer()
        else:
            return False

    def failNot(self):
        if self.mainresult:
            return self.mainresult.failNot()
        else:
            return True


class Event():

    lastEventID = 1

    @classmethod
    def getNextEventID(cls):
        return + +cls.lastEventID

    def __init__(self):
        self.eventID = Event.getNextEventID()
        self.listeners = BucketSet()

    def notify(self, *args):
        for listener in self.listeners:
            try:
                listener(self, *args)
            except Exception:
                print("Error in event listener %s:")
                traceback.print_exc()

    def probe(self, defaultresult, *args):
        resultlist = EventResultList()
        for listener in self.listeners:
            result = listener(self, *args)
            if not resultlist.mainresult:
                resultlist.mainresult = result
            elif resultlist.mainresult.errorlevel < result.errorlevel:
                resultlist.setMainResult(result)
            else:
                resultlist.addResult(result)
        if not resultlist.mainresult:
            resultlist.setMainResult(defaultresult)
        return resultlist

    def register(self, plugin, method, priority, scope):
        self.listeners.add(EventListener(plugin, method, scope), priority)

class SessionWrapper(object):

    def __init__(self, session):
        self._session = weakref.proxy(session)

    def getIID(self):
        return self._session.getIID()

    def __getattr__(self, attr):
        return getattr(self._session, attr)

class EventListener():

    MIN_PRIORITY = 1
    MAX_PRIORITY = 9
    DEFAULT_PRIORITY = 5

    CLEANUP_INTERVAL = 10

    def __init__(self, module, method, scope):
        self.module = module
        self.method = method
        self.scope = scope
        self._lastCleanup = time.time()
        if Scope.SESSION == scope:
            self._sessionModules = {}

    def __repr__(self):
        return 'EventListener(%(module), %(method), %(scope))' % (self)

    def _cleanupSessionModules(self):
        timeClean = time.time() - EventListener.CLEANUP_INTERVAL
        if self._lastCleanup < timeClean:
            #print("_cleanupSessionModules()", file = debug.stream())
            #print("before: ", file = debug.stream())
            #pprint(self._sessionModules)
            #self._sessionModules = dict(filter(lambda (session, (module, createTime)): createTime < timeClean, self._sessionModules.items()))
            self._sessionModules = dict(filter(lambda x: None != x[1] and sfsp.session.SMTPSession.sessionActive(x[0]), self._sessionModules.items()))
            #print("after: ", file = debug.stream())
            #pprint(self._sessionModules)
            self._lastCleanup = time.time()

    def _getSessionObject(self):
        for frame in inspect.stack():
            if 'self' in frame[0].f_locals and sfsp.session.SMTPSession == frame[0].f_locals['self'].__class__:
                return SessionWrapper(frame[0].f_locals['self'])

    def _getSessionModule(self, session):
        if session.getIID() in self._sessionModules:
            #print("_getSessionModule() for (%s, %s): return from cache for %s" % (self.module, self.method, session.getIID()), file = debug.stream())
            module = self._sessionModules[session.getIID()]
        else:
            #print("_getSessionModule() for (%s, %s): create new for %s" % (self.module, self.method, session.getIID()), file = debug.stream())
            module = self.module()
            self._sessionModules[session.getIID()] = module
        self._cleanupSessionModules()
        return module

    def __call__(self, evt, *args):
        session = self._getSessionObject()
        if Scope.SESSION == self.scope:
            module = self._getSessionModule(session)
        else:
            module = self.module
        return getattr(module, self.method)(evt, session, * args)

class listener:
    '''decorator for event listening methods'''

    def __init__(self, event, priority = EventListener.DEFAULT_PRIORITY):
        if EventListener.MIN_PRIORITY > priority or EventListener.MAX_PRIORITY < priority:
            raise ValueError('EventListener priority must be within %d and %d' % (EventListener.MIN_PRIORITY, EventListener.MAX_PRIORITY))
        self.priority = priority
        self.event = event

    def __call__(self, func):
        if not hasattr(func, 'eventListener'):
            func.eventListener = set()
        func.eventListener.add((self.event, self.priority))

        return func

StartSession = Event()
ValidateClientAddress = Event()
SendSMTPBanner = Event()
ReceivedSMTPHelo = Event()
SendSMTPHeloResponse = Event()
ReceivedSMTPMail = Event()
SendSMTPMailResponse = Event()
ReceivedSMTPRcpt = Event()
SendSMTPRcptResponse = Event()
StartTransaction = Event()
AddRecipient = Event()
ValidateRecipient = Event()
ValidateData = Event()
