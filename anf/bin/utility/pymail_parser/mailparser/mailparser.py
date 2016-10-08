#!/usr/bin/env python
"""Describe file"""


from argparse import ArgumentParser
import sys

DESCRIPTION = """"python mail parser

Copyright 2016 by the Regents of the University of California San Diego. All rights reserved.
"""


argp = ArgumentParser(description=DESCRIPTION)
argp.add_argument('-v', '--verbose', action='store_true', help='Increase verbosity')
argp.add_argument('-m', '--multiple', action='store_true', help='Try to parse into multiple messages')
argp.add_argument('-f', '--logfile', help='Log file')
# TODO do we really need this or can we just install the handlers like normal python packages?
# typically they would go in the root namespace but share a common prefix eg 'mailparser_anf_construction'
# the PF file would list that package name and then we just import a standard API that all the handlers will share.
# This is how I usually do python plugins.
# argp.add_argument('-l', '--library', help='Path to directory containing parser handler python modules')


def main(argv=None):
    if argv is None:
        argv = sys.argv

    args = argp.parse_args(argv)

    return -1


if __name__ == '__main__':
    sys.exit(main())
