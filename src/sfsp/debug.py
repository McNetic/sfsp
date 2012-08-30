import sys

__all__ = ['stream', 'enable', 'disable']

class Devnull:
    def write(self, msg): pass
    def flush(self): pass

class Debug:
    stream = Devnull()    

def enable(debugstream = sys.stderr):
    Debug.stream = debugstream
    
def disable():
    Debug.stream = Devnull()

def stream():
    return Debug.stream 
