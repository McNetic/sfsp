'''
Created on 31.08.2012

@author: ehe
'''

import inspect
import sfsp.session

class Scope():
    GLOBAL = 0
    SESSION = 1

class EventResult():
    NONE = -1,
    OK = 0

    def __init__(self, errorlevel, message):
        self.errorlevel = errorlevel
        self.message = message

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

class Event():

    lastEventID = 1

    @classmethod
    def getNextEventID(cls):
        return + +cls.lastEventID

    def __init__(self):
        self.eventID = Event.getNextEventID()
        self.listeners = set()

    def notify(self, *args):
        for listener in self.listeners:
            listener(self, *args)

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

    def register(self, plugin, method):
        # todo: check valid event
        self.listeners.add(EventListener(plugin, method))

class SessionWrapper(object):

    def __init__(self, session):
        self._session = session

    def __getattr__(self, attr):
        return getattr(self._session, attr)

class EventListener():

    def __init__(self, module, method):
        self.module = module
        self.method = method

    def getSessionObject(self):
        for frame in inspect.stack():
            if 'self' in frame[0].f_locals and sfsp.session.SMTPSession == frame[0].f_locals['self'].__class__:
                return SessionWrapper(frame[0].f_locals['self'])

    def __call__(self, evt, *args):
        return getattr(self.module, self.method)(evt, self.getSessionObject(), * args)

class listener:
    '''decorator for event listening methods'''

    def __init__(self, event):
        self.event = event

    def __call__(self, func):
        if not hasattr(func, 'eventListener'):
            func.eventListener = set()
        func.eventListener.add(self.event)

        return func

StartSession = Event()
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
