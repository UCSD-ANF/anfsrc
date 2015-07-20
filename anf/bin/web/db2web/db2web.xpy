try:
    import sys
    import json
    import socket
    import string
    import hashlib
    import tempfile
    import re
    import gzip
    from optparse import OptionParser
    from time import time, gmtime, strftime, sleep
    from datetime import datetime, timedelta
    from pprint import pprint
    from collections import defaultdict
except Exception, e:
    sys.exit("\n\tProblems importing libraries.%s %s\n" % (Exception, e))

try:
    from pymongo import MongoClient
except Exception,e:
    sys.exit("Problem loading Pymongo library. %s(%s)\n" % (Exception,e) )

try:
    import logging as logging
    logging.basicConfig(format='db2web[%(levelname)s]: %(message)s')
    logging.addLevelName(35, "NOTIFY")
    logger = logging.getLogger()

except Exception,e:
    sys.exit('Problems loading logging lib. %s' % e)

try:
    import antelope.datascope as datascope
    import antelope.orb as orb
    import antelope.Pkt as Pkt
    import antelope.stock as stock
except Exception, e:
    sys.exit("\n\tProblems loading ANTELOPE libraries. %s(%s)\n" % (Exception, e))

try:
    from db2web.db2web_libs import *
except Exception, e:
    sys.exit("Problem loading db2web_libs.py file. %s(%s)\n" % (Exception, e))

#try:
#    from db2web.sta2json import Stations
#except Exception, e:
#    sys.exit("Problem loading Stations class. %s(%s)\n" % (Exception, e))
#
#try:
#    from db2web.event2json import Events
#except Exception, e:
#    sys.exit("Problem loading Events class. %s(%s)\n" % (Exception, e))
#


usage = "Usage: %prog [options]"

parser = OptionParser(usage=usage)
parser.add_option("-c", action="store_true", dest="clean",
                    help="clean 'drop' collection on start", default=False)
parser.add_option("-v", action="store_true", dest="verbose",
                    help="verbose output", default=False)
parser.add_option("-d", action="store_true", dest="debug",
                    help="debug output", default=False)
parser.add_option("-p", "--pf", action="store", dest="pf", type="string",
                    help="parameter file path", default="db2web")

(options, args) = parser.parse_args()

if options.verbose:
    logger.setLevel(logging.INFO)
    log('Set log level to INFO')

if options.debug:
    logger.setLevel(logging.DEBUG)
    debug('Set log level to DEBUG')


notify('Read parameters from pf file %s' % options.pf)
pf = stock.pfread(options.pf)

try:
    modules = pf.get('modules')
    if not modules:
        raise
except:
    error('Cannot load any modules from PF file configuration.')

try:
    refresh = int(pf['refresh'])
    if not refresh:
        raise
except:
    refresh = 60

notify("refresh every [%s]secs" % refresh)

active = {}
for m in modules:

    try:
        notify( "from db2web.%s import %s" % (modules[m],m) )
        _temp = __import__("db2web.%s" % modules[m], globals(), locals(), [m], -1 )
        #notify(dir(_temp) )
    except Exception, e:
        error("Problem loading %s class from %s. [%s]\n" % (m,modules[m],e))

    try:
        notify( "temp = _temp.%s(options.pf,clean=%s)" % (m,options.clean) )
        exec( "temp = _temp.%s(options.pf,clean=%s)" % (m,options.clean) )
        active[m] = temp
        #notify(dir(temp) )
        #notify(dir(active[m]) )
    except Exception, e:
        error("Problem loading %s(%s) [%s]\n" % (m,options.pf,e))

while(True):

    for m in active:
        log( 'Call dump on %s' % m )
        active[m].dump()

    log('sleep(%s)' % refresh)
    sleep(refresh)
