from sfsp import debug
from sfsp.plugin import event

__all__ = ['plugin', 'event', 'filter']

class PluginException(Exception):
    pass

class Plugin():
    loadedModules = set()
    loadedPlugins = set()

    def __init__(self):
        pass


    @classmethod
    def registerModule(cls, module, *args):
        cls.loadedModules.add(module)

    @classmethod
    def registerPlugin(cls, pluginClass, pluginScope):
        print('loading plugin', pluginClass.__name__, 'from', pluginClass.__module__, file = debug.stream())
        if event.Scope.GLOBAL == pluginScope:
            plugin = pluginClass()
        else:
            plugin = pluginClass
        for key, func in pluginClass.__dict__.items():
            if hasattr(func, 'eventListener'):
                for (evt, priority) in getattr(func, 'eventListener'):
                    evt.register(plugin, key, priority, pluginScope)
        cls.loadedPlugins.add(pluginClass)

class plugin:
    """
        Decorator for all plugins
    """
    def __init__(self, scope = event.Scope.GLOBAL):
        self.scope = scope

    def __call__(self, cls):

        Plugin.registerPlugin(cls, self.scope)

        return cls
