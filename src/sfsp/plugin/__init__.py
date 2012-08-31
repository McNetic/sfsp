from sfsp import debug
from sfsp.plugin import event

class PluginException(Exception):
    pass

class Plugin():
    loadedModules = set()
    loadedPlugins = set()
    knownHooks = frozenset()
    
    def __init__(self):
        pass
            
    
    @staticmethod
    def registerModule(module):
        Plugin.loadedModules.add(module)
    
    @staticmethod
    def registerPlugin(pluginClass):
        print('loading plugin', pluginClass.__name__, 'from', pluginClass.__module__, file=debug.stream())
        plugin = pluginClass()
        for key, func in pluginClass.__dict__.items():
            if hasattr(func, 'eventListener'):
                for evt in getattr(func, 'eventListener'):
                    evt.register(event.EventListener(plugin, key))
        Plugin.loadedPlugins.add(plugin)

def plugin(cls):
    """
        Decorator for all plugins
    """
    
    Plugin.registerPlugin(cls)
    
    return cls
