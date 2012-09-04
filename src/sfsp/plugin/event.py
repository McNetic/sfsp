'''
Created on 31.08.2012

@author: ehe
'''

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

    @staticmethod
    def getNextEventID():
        return + +Event.lastEventID

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

    def register(self, plugin, method, scope):
        # todo: check valid event
        self.listeners.add(EventListener(plugin, method, scope))

class EventListener():

    def __init__(self, module, method, scope):
        self.module = module
        self.method = method
        self.scope = scope

    def __call__(self, evt, *args):
        return getattr(self.module, self.method)(evt, *args)

class listener:
    '''decorator for event listening methods'''

    def __init__(self, event, scope = Scope.GLOBAL):
        self.event = event
        self.scope = scope

    def __call__(self, func):

        if not hasattr(func, 'eventListener'):
            func.eventListener = set()
        func.eventListener.add((self.event, self.scope))

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
