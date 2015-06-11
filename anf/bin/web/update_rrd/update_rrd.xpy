"""
Produce and maintain RRD archives base on some Antelope ORB.
"""

import re
import json
import subprocess
import multiprocessing
from optparse import OptionParser
from collections import defaultdict

try:
    import antelope.orb as orb
    import  antelope.Pkt as Pkt
    import antelope.stock as stock
    import antelope.datascope as datascope
except Exception,e:
    sys.exit( "\n\tProblems with Antelope libraries.%s %s\n" % (Exception,e) )

try:
    import logging as logging
    logging.basicConfig(format='update_rrd[%(levelname)s]: %(message)s')
    logging.addLevelName(35, "NOTIFY")
    logger = logging.getLogger()

except Exception,e:
    sys.exit('Problems loading logging lib. %s' % e)

try:
    from update_rrd_functions import *
except Exception,e:
    sys.exit( "\n\tProblems with required libraries.%s %s\n" % (Exception,e) )



##################
#MAIN
##################

usage = "usage: %prog [options]"
parser = OptionParser(usage=usage)

parser.add_option("-t", action="store_true", dest="test",
        help="Test processing delay", default=False)
parser.add_option("-S", action="store", dest="state",
        help="State file to track ORB pckt", default=False)
parser.add_option("-n", action="store", dest="net",
        help="Subset on vnet or snet regex", default=False)
parser.add_option("-s", action="store", dest="sta",
        help="Subset on stations regex", default=False)
parser.add_option("-p", action="store", dest="pf",
        help="Parameter file to use", default=sys.argv[0])
parser.add_option("-v", action="store_true", dest="verbose",
        help="verbose output", default=False)
parser.add_option("-d", action="store_true", dest="debug",
        help="Debugging mode.", default=False)

(options, args) = parser.parse_args()

if options.verbose:
    logger.setLevel(logging.INFO)
    log('Set log level to INFO')

if options.debug:
    logger.setLevel(logging.DEBUG)
    debug('Set log level to DEBUG')

if len(args) != 0:
    parser.print_help()
    parser.error("incorrect number of arguments")


notify('START SCRIPT: %s' % stock.strydtime(stock.now()) )

#
# Parse parameter file
#
log('Read PF "%s"' % options.pf)
try:
    pf = stock.pfread(options.pf)
except Exception,e:
    error('Problems with PF %s' % options.pf)

ORB = pf.get('ORB')
BUFFER = pf.get('BUFFER', 1200)
SELECT = pf.get('SELECT')
REJECT = pf.get('REJECT')
ARCHIVE = pf.get('ARCHIVE')
RRD_NPTS = pf.get('RRD_NPTS')
CHANNELS = pf.get('CHANNELS')
DEFAULT_ORB_START = pf.get('DEFAULT_ORB_START','oldest')

log('\tORB: %s' % ORB)
log('\tBUFFER: %s' % BUFFER)
log('\tSELECT: %s' % SELECT)
log('\tREJECT: %s' % REJECT)
log('\tARCHIVE: %s' % ARCHIVE)
log('\tRRD_NPTS: %s' % RRD_NPTS)
log('\tCHANNELS: %s' % CHANNELS)
log('\tDEFAULT_ORB_START: %s' % DEFAULT_ORB_START)


if not os.path.isdir(ARCHIVE):
    logger.critical('Cannot find specified directory: %s' % ARCHIVE )
    parser.print_help()
    sys.exit()

orbobj = Orbserver( ORB, options.state, time_buffer=BUFFER,
        start_default=DEFAULT_ORB_START, select=SELECT, reject=REJECT,
        test=options.test )

data_cache = Cache(ARCHIVE, options.net, options.sta, RRD_NPTS, CHANNELS, BUFFER)
data_cache.go_to_work( orbobj )
