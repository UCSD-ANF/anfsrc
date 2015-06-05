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
    logging.basicConfig(format='update_rrd[%(levelname)s]: %(message)s')
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

try:
    from db2web.sta2json import Stations
except Exception, e:
    sys.exit("Problem loading Stations class. %s(%s)\n" % (Exception, e))

try:
    from db2web.event2json import Events
except Exception, e:
    sys.exit("Problem loading Events class. %s(%s)\n" % (Exception, e))



usage = "Usage: %prog [options]"

parser = OptionParser(usage=usage)
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
    refresh = pf['refresh']
    if not refresh:
        raise
except:
    refresh = 60

notify("refresh every [%s]secs" % refresh)

stations = Stations(options.pf)
events = Events(options.pf)

while(True):
    debug('stations.get_all_sta_cache()')
    stations.get_all_sta_cache()

    debug('stations.get_all_orb_cache()')
    stations.get_all_orb_cache()

    debug('stations.dump_cahce()')
    stations.dump_cache(to_mongo=True, to_json=True)

    debug('events.get_event_cache()')
    events._get_event_cache()
    debug('events.dump_cahce()')
    events.dump_cache(to_mongo=True, to_json=True)

    debug('sleep(%s)' % refresh)
    sleep(refresh)
