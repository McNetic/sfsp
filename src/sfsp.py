#! /usr/bin/env python3
"""
sfsp - Small/Simple filtering SMTP Proxy

(C) 2012,2016 Nicolai Ehemann (en@enlightened.de)


"""

import sys
import os
import errno
import getopt
import pkgutil
import traceback

import sfsp
from sfsp import debug

program = sys.argv[0]
__version__ = '0.1'
__years__ = '2012,2016'

def usage(code, msg = ''):
    print("""Usage: %(program)s [options]
Options:
  -d | --debug         enable debug output
  -h | --help          print this help and exit
  -n | --nosetuid      disable setuid 'nobody' (use when not running as root)
  -p | --remoteport    remote smtp server port, default: 25
  -P | --localport     (local) port sfsp listens on, default: 8025
  -s | --remotehost    remote smtp server hostname (or ip), default: localhost
  -S | --localhost     (local) hostname/ip sfsp listens on, default: localhostt
  -V | --version       print version information and exit
""" % globals(), file = sys.stderr)
    if msg:
        print(msg, file = sys.stderr)
    sys.exit(code)

class OptDict(dict):

    def __getattr__(self, name):
        return self.get(name)

    def __setattr__(self, name, value):
        if not name in self:
            self[name] = value
        super().__setattr__(name, value)

class Options(OptDict):
    setuid = 1
    localaddress = 'localhost'
    localport = 8025
    remoteaddress = 'localhost'
    remoteport = 25

    modules = OptDict()
    modules.delay = OptDict()
    modules.delay.enabled = False
    modules.dnsbl = OptDict()
    modules.dnsbl.enabled = False
    modules.greylisting = OptDict()
    modules.greylisting.enabled = False
    modules.spamassassin = OptDict()
    modules.spamassassin.enabled = True

    delay = 0
    defer_errors = True

def parseargs():
    try:
        opts, args = getopt.getopt(
            sys.argv[1:], 'dhnp:P:s:S:V',
            ['debug', 'help', 'nosetuid', 'localport=', 'remoteport=', 'localhost=', 'remotehost=', 'version'])
    except getopt.error as e:
        usage(1, e)

    options = Options()
    for opt, arg in opts:
        if opt in ('-d', '--debug'):
            debug.enable()
        elif opt in ('-h', '--help'):
            usage(0)
        elif opt in ('-n', '--nosetuid'):
            options.setuid = 0
        elif opt in ('-p', '--remoteport'):
            try:
                options.remoteport = int(arg)
            except ValueError:
                    usage(1, 'Bad remote port: %s' % arg)
        elif opt in ('-P', '--localport'):
            try:
                options.localport = int(arg)
            except ValueError:
                    usage(1, 'Bad local port: %s' % arg)
        elif opt in ('-s', '--remotehost'):
            options.remoteaddress = arg
        elif opt in ('-S', '--localhost'):
            options.localaddress = arg
        elif opt in ('-V', '--version'):
            print("%(program)s v%(__version__)s. (C) %(__years__)s Nicolai Ehemann (en@enlightened.de) " % globals(), file = sys.stderr)
            sys.exit(0)

    # parse the rest of the arguments
    if 0 < len(args):
        usage(1, 'Invalid arguments: %s' % ', '.join(args))

    return options

def load_plugin(plugin, *args):
    try:
        __import__(plugin)
        sfsp.plugin.Plugin.registerModule(plugin, *args)
    except ImportError as err:
        print('Cannot import module "{}"'.format(plugin), file = sys.stderr)
        traceback.print_exc()

def load_plugins(modopts):
    for _, plugin, _ in pkgutil.iter_modules(['plugins']):
        if not modopts[plugin] or modopts[plugin].enabled:
            load_plugin('plugins.%s' % plugin)
    pass

def require_version_3_2():
    if 3 > sys.version_info.major or 2 > sys.version_info.minor:
        print("%(program) requires at least python version >= 3.2" % globals())
        sys.exit(1)

if __name__ == '__main__':
    require_version_3_2()
    options = parseargs()
    load_plugins(options.modules)
    proxy = sfsp.Proxy(options, __version__)
    # Become nobody
    if options.setuid:
        try:
            import pwd
        except ImportError:
            print('Cannot import module "pwd"; try running with -n option.', file = sys.stderr)
            sys.exit(1)
        nobody = pwd.getpwnam('nobody')[2]
        try:
            os.setuid(nobody)
        except OSError as e:
            if e.errno != errno.EPERM: raise
            print('Cannot setuid "nobody"; try running with -n option.', file = sys.stderr)
            sys.exit(1)
    try:
        proxy.run()
    except KeyboardInterrupt:
        pass
