#! /usr/bin/env python3
'''
Created on 28.08.2012

@author: Nicolai Ehemann
'''
"""An RFC 2821 smtp proxy.

Usage: %(program)s [options]

Options:

    --nosetuid
    -n
        This program generally tries to setuid `nobody', unless this flag is
        set.  The setuid call will fail if this program is not run as root (in
        which case, use this flag).

    --version
    -V
        Print the version number and exit.

    --class classname
    -c classname
        Use `classname' as the concrete SMTP proxy class.  Uses `PureProxy' by
        default.

    --debug
    -d
        Turn on debugging prints.

    --help
    -h
        Print this message and exit.

Version: %(__version__)s

If localhost is not given then `localhost' is used, and if localport is not
given then 8025 is used.  If remotehost is not given then `localhost' is used,
and if remoteport is not given, then 25 is used.
"""


# Overview:
#   PureProxy - Proxies all messages to a real smtpd which does final
#   delivery.  One known problem with this class is that it doesn't handle
#   SMTP errors from the backend server at all.  This should be fixed
#   (contributions are welcome!).
#

# Author: Barry Warsaw <barry@python.org>
#
# TODO:
#
# - support mailbox delivery
# - alias files
# - ESMTP
# - handle error codes from the backend smtpd

import sys
import os
import errno
import getopt
import pkgutil
import traceback

import sfsp
from sfsp import debug

__all__ = ["SMTPServer", "PureProxy"]

program = sys.argv[0]
__version__ = 'Python SMTP proxy version 0.2'

COMMASPACE = ', '

def usage(code, msg = ''):
    print(__doc__ % globals(), file = sys.stderr)
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
            sys.argv[1:], 'c:dhnp:P:s:S:V',
            ['class=', 'debug', 'help', 'nosetuid', 'localport=', 'remoteport=', 'localhost=', 'remotehost=', 'version'])
    except getopt.error as e:
        usage(1, e)

    options = Options()
    for opt, arg in opts:
        if opt in ('-c', '--class'):
            options.classname = arg
        elif opt in ('-d', '--debug'):
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
            print(__version__, file = sys.stderr)
            sys.exit(0)

    # parse the rest of the arguments
    if 0 < len(args):
        usage(1, 'Invalid arguments: %s' % COMMASPACE.join(args))

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
