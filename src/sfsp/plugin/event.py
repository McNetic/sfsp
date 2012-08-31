'''
Created on 31.08.2012

@author: ehe
'''

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
        return ++Event.lastEventID
    
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
                
    def register(self, listener):
        # todo: check valid event
        self.listeners.add(listener)

class EventListener():
    
    def __init__(self, module, method):
        self.module = module
        self.method = method
    
    def __call__(self, evt, *args):
        return getattr(self.module, self.method)(evt, *args)

class listener:
    
    def __init__(self, event):
        self.event = event
        
    def __call__(self, func):
        
        if not hasattr(func, 'eventListener'):
            func.eventListener = set()
        func.eventListener.add(self.event)
        
        return func

StartTransaction = Event()
AddRecipient = Event()
ValidateRecipient = Event()