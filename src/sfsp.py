#! /usr/bin/env python3
'''
Created on 28.08.2012

@author: Nicolai Ehemann
'''
"""An RFC 2821 smtp proxy.

Usage: %(program)s [options] [localhost:localport [remotehost:remoteport]]

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

import sfsp
from sfsp import debug

__all__ = ["SMTPServer","PureProxy"]

program = sys.argv[0]
__version__ = 'Python SMTP proxy version 0.2'


COMMASPACE = ', '



def usage(code, msg=''):
    print(__doc__ % globals(), file=sys.stderr)
    if msg:
        print(msg, file=sys.stderr)
    sys.exit(code)





class Options:
    setuid = 1


def parseargs():
    try:
        opts, args = getopt.getopt(
            sys.argv[1:], 'nVhc:d',
            ['class=', 'nosetuid', 'version', 'help', 'debug'])
    except getopt.error as e:
        usage(1, e)

    options = Options()
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage(0)
        elif opt in ('-V', '--version'):
            print(__version__, file=sys.stderr)
            sys.exit(0)
        elif opt in ('-n', '--nosetuid'):
            options.setuid = 0
        elif opt in ('-c', '--class'):
            options.classname = arg
        elif opt in ('-d', '--debug'):
            debug.enable()

    # parse the rest of the arguments
    if len(args) < 1:
        localspec = 'localhost:8025'
        remotespec = 'localhost:25'
    elif len(args) < 2:
        localspec = args[0]
        remotespec = 'localhost:25'
    elif len(args) < 3:
        localspec = args[0]
        remotespec = args[1]
    else:
        usage(1, 'Invalid arguments: %s' % COMMASPACE.join(args))

    # split into host/port pairs
    i = localspec.find(':')
    if i < 0:
        usage(1, 'Bad local spec: %s' % localspec)
    options.localhost = localspec[:i]
    try:
        options.localport = int(localspec[i+1:])
    except ValueError:
        usage(1, 'Bad local port: %s' % localspec)
    i = remotespec.find(':')
    if i < 0:
        usage(1, 'Bad remote spec: %s' % remotespec)
    options.remotehost = remotespec[:i]
    try:
        options.remoteport = int(remotespec[i+1:])
    except ValueError:
        usage(1, 'Bad remote port: %s' % remotespec)
    return options


if __name__ == '__main__':
    options = parseargs()
    proxy = sfsp.Proxy((options.localhost, options.localport),
                   (options.remotehost, options.remoteport), __version__)
    # Become nobody
    if options.setuid:
        try:
            import pwd
        except ImportError:
            print('Cannot import module "pwd"; try running with -n option.', file=sys.stderr)
            sys.exit(1)
        nobody = pwd.getpwnam('nobody')[2]
        try:
            os.setuid(nobody)
        except OSError as e:
            if e.errno != errno.EPERM: raise
            print('Cannot setuid "nobody"; try running with -n option.', file=sys.stderr)
            sys.exit(1)
    try:
        print('Starting...', file=debug.stream())
        proxy.run()
    except KeyboardInterrupt:
        pass
