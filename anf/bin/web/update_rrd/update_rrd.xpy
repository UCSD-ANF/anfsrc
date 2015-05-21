"""
Produce and maintain RRD archives base on some Antelope ORB.
The tools will look for the oldest data in the ORB and will
request the last point injected into the RRD. Then pass to
the RRD the missing data. Data before the last import will
be ignored.

Juan Reyes
reyes@ucsd.edu
"""

import re
import subprocess
from time import sleep
from collections import defaultdict
from optparse import OptionParser

try:
    import antelope.datascope as datascope
    import antelope.stock as stock
    import antelope.orb as orb
    import  antelope.Pkt as Pkt
except Exception,e:
    sys.exit( "\n\tProblems with Antelope libraries.%s %s\n" % (Exception,e) )

import json

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

PROCESSES = set()

usage = "usage: %prog [options]"
parser = OptionParser(usage=usage)

parser.add_option("-n", action="store", dest="net",
        help="Subset on vnet or snet regex", default=False)
parser.add_option("-s", action="store", dest="sta",
        help="Subset on stations regex", default=False)
parser.add_option("-p", action="store", dest="pf",
        help="Parameter file to use", default=sys.argv[0])
parser.add_option("-v", action="store_true", dest="verbose",
        help="verbose output", default=False)
#parser.add_option("-c", action="store", dest="channels",
#        help="Subset on channels", default='.*')
parser.add_option("-d", action="store_true", dest="debug",
    help="Debugging mode.", default=False)
#parser.add_option("-a", action="store_true", dest="active",
#    help="Active stations only", default=False)
#parser.add_option("-r", action="store_true", dest="rebuild",
#    help="force re-build of archives", default=False)

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


#
# Parse parameter file
#
log('Read PF "%s"' % options.pf)
try:
    pf = stock.pfread(options.pf)
except Exception,e:
    error('Problems with PF %s' % options.pf)

ORB = pf['ORB']
BUFFER = pf['BUFFER']
SELECT = pf['SELECT']
REJECT = pf['REJECT']
ARCHIVE = pf['ARCHIVE']
RRD_NPTS = pf['RRD_NPTS']
TIMEFORMAT = pf['TIMEFORMAT']
CHANNELS = pf['CHANNELS']

log('ORB: %s' % ORB)
log('BUFFER: %s' % BUFFER)
log('SELECT: %s' % SELECT)
log('REJECT: %s' % REJECT)
log('ARCHIVE: %s' % ARCHIVE)
log('RRD_NPTS: %s' % RRD_NPTS)
log('TIMEFORMAT: %s' % TIMEFORMAT)
log('CHANNELS: %s' % CHANNELS)


if not os.path.isdir(ARCHIVE):
    logger.critical('Cannot find specified directory: %s' % ARCHIVE )
    parser.print_help()
    sys.exit()


notify('START SCRIPT: %s' % stock.epoch2str(stock.now(),TIMEFORMAT) )


# New ORB object
orbobj = Orbserver( ORB, select=SELECT, reject=REJECT )

data_cache = Cache(ARCHIVE, options.net, options.sta, RRD_NPTS, CHANNELS, BUFFER)
data_cache.go_to_work( orbobj )

#for packet in orbobj:
#    debug( 'Name: %s' % packet.name() )
#    data_cache.add( packet )


notify('END SCRIPT: %s' % stock.epoch2str( stock.now(),TIMEFORMAT ))
logger.info('%s' % stock.strtdelta(stock.now() - sta_timer))
