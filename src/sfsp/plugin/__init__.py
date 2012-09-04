from sfsp import debug
from sfsp.plugin import event

__all__ = ['plugin', 'event']

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
        print('loading plugin', pluginClass.__name__, 'from', pluginClass.__module__, file = debug.stream())
        plugin = pluginClass()
        for key, func in pluginClass.__dict__.items():
            if hasattr(func, 'eventListener'):
                for (evt, scope) in getattr(func, 'eventListener'):
                    evt.register(plugin, key, scope)
        Plugin.loadedPlugins.add(plugin)

class plugin:
    """
        Decorator for all plugins
    """
    def __call__(self, cls):

        Plugin.registerPlugin(cls)

        return cls
