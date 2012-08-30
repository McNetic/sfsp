from .filter import Filter

class PluginException(Exception):
    pass

class Plugin():
    loadedPlugins = set()
    knownHooks = frozenset()
    
    def __init__(self):
        Plugin.register(self);
        self.hooks = set()
    
    def registerHook(self, hook):
        if not hook in self.__class__.knownHooks:
            raise PluginException
        self.hooks.add(hook)
    
    @staticmethod
    def register(plugin):
        Plugin.loadedPlugins.add(plugin.__class__())
        