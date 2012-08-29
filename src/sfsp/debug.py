import sys

__all__ = ['stream', 'enable', 'disable']

class Devnull:
    def write(self, msg): pass
    def flush(self): pass

stream = Devnull()

def enable(debugstream = sys.stderr):
    stream = debugstream
    
def disable():
    stream = Devnull()
