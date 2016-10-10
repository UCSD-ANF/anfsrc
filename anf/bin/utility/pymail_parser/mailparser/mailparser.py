#!/usr/bin/env python
"""Describe file"""


from argparse import ArgumentParser
import logging
import sys


log = logging.getLogger(__name__)

DESCRIPTION = """"python mail parser

Copyright 2016 by the Regents of the University of California San Diego. All rights reserved.
"""


def parse_mail(pffile):
    # get imap config from pffile
    # connect to imap server
    # get new messages
    # for each new message
    # do universally useful stuff like decoding multipart etc
    # for each handler
    # if handler pattern matches
    # call handler w email
    # if not handler.continue break
    pass


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
    return argp.parse_args(argv)


def main(argv=None):
    if argv is None:
        argv = sys.argv
    args = parse_args(argv)
    if args.verbose:
        log.setLevel(logging.DEBUG)
    try:
        parse_mail(pffile)
    except Exception:
        log.critical('Terminating due to exception', exc_info=True)
        return -1
    return 0


if __name__ == '__main__':
    sys.exit(main())
