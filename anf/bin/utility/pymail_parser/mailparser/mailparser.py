#!/usr/bin/env python
"""Describe file"""
from importlib import import_module
from re import search
from argparse import ArgumentParser
import logging
import logging.config
import sys
from antelope.stock import pfread, auto_convert

from .imap import ImapHelper
from .util import logouting

log = logging.getLogger(__name__)

DESCRIPTION = """"python mail parser

Copyright 2016 by the Regents of the University of California San Diego. All rights reserved.
"""


def recursive_auto_convert(container):
    if type(container) is dict:
        newcontainer = {}
        for k, v in container.items():
            newcontainer[k] = recursive_auto_convert(v)
        return newcontainer
    if type(container) is list:
        newcontainer = []
        for v in container:
            newcontainer.append(recursive_auto_convert(v))
        return newcontainer
    else:
        # TODO add exception for dotted quads; antelope thinks they're unix times
        return auto_convert(container)


def parse_mail(pffile):
    _modules = {}
    pf = pfread(pffile)
    logging.config.dictConfig(recursive_auto_convert(pf['logging']))
    try:
        # dotted quads get converted to unix times due to a bug in C is_epoch_str()
        # so turn on auto_convert after we read it
        pf.auto_convert = False
        host = pf['imap'].get('host', 'localhost')
        pf.auto_convert = True
        handlers = pf['Handlers']
        username = pf['imap']['username']
        password = pf['imap']['password']
        port = pf['imap'].get('port', None)
        mailbox = pf['imap'].get('mailbox', None)
        ssl = pf['imap'].get('ssl', False)
    except KeyError as e:
        raise Exception("Invalid pf file %r" % pffile)
    if not handlers:
        raise Exception("No handlers configured")
    for handler in handlers:
        _modules[handler['handler']] = import_module('mailparser_' + handler['handler'])
    h = ImapHelper(username, password, host, port, mailbox, ssl).login()
    with logouting(h):
        for num, flags, msg in h.getnew():
            for handler in handlers:
                if not search(handler['sender'], msg['From']):
                    continue
                if not search(handler['subject'], msg['Subject']):
                    continue
                _modules[handler['handler']].handle(msg, handler)
                if not handler.get('continue', False):
                    break


def parse_args(argv):
    argp = ArgumentParser(description=DESCRIPTION)
    argp.add_argument('-p', '--pffile', help='Parameter file', default=argv[0])
    argp.add_argument('-v', '--verbose', action='store_true', help='Increase verbosity')
    # TODO is this talking about mime-multipart? do we just want to ALWAYS do this?
    # argp.add_argument('-m', '--multiple', action='store_true', help='Try to parse into multiple messages')
    # TODO Can we keep logging config in the pffile?
    # argp.add_argument('-f', '--logfile', help='Log file')
    # TODO do we really need this or can we just install the handlers like normal python packages?
    # typically they would go in the root namespace but share a common prefix eg 'mailparser_anf_construction'
    # the PF file would list that package name and then we just import a standard API that all the handlers will share.
    # This is how I usually do python plugins.
    # argp.add_argument('-l', '--library', help='Path to directory containing parser handler python modules')
    # TODO make it possible to specify imap params on cmd line?
    return argp.parse_args(argv[1:])


def main(argv=None):
    if argv is None:
        argv = sys.argv
    args = parse_args(argv)
    if args.verbose:
        log.setLevel(logging.DEBUG)
    try:
        parse_mail(args.pffile)
    except Exception:
        log.critical('Terminating due to exception', exc_info=True)
        return -1
    return 0


if __name__ == '__main__':
    logging.basicConfig(level=logging.WARN)
    sys.exit(main())
