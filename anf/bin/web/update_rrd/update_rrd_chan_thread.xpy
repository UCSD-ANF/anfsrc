"""

__DO_NOT_RUN_DIRECTLY__

I'm finding some issues with multithreading this
and Datascope. The first database opens fine but
subsequent databses could fail. One alternative is
to run an independent process to do the data extraction
instead of calling a thread in the multiporcessing lib.

In general this should be a better setup than the single
process handling everything. Not sure how to do the loggin
for now. Need to investigate a little.

    The main program is "update_rrd_from_db"

Juan Reyes
reyes@ucsd.edu

Malcolm White
mcwhite@ucsd.edu
"""


import subprocess
import re
from optparse import OptionParser
from collections import defaultdict

try:
    import antelope.datascope as datascope
    import antelope.stock as stock
except Exception,e:
    sys.exit( "\n\tProblems with Antelope libraries.%s %s\n" % (Exception,e) )

try:
    from update_rrd_functions import *
except Exception,e:
    sys.exit( "\n\tProblems with required libraries.%s %s\n" % (Exception,e) )

try:
    import logging
    from anf.eloghandler import ElogHandler
except Exception,e:
    sys.exit( "\n\tProblems loading ANF logging libs. %s(%s)\n"  % (Exception,e))

try:
    logger = logging.getLogger().getChild( '%s_%s' % (station,channel) )
except:
    try:
        logging.basicConfig()
        logger = logging.getLogger()
        formatter = logging.Formatter('[%(name)s] %(message)s')
        handler = ElogHandler()
        handler.setFormatter(formatter)
        logger.handlers=[]
        logger.addHandler(handler)

        # Set the default logging level
        logger.setLevel(logging.WARNING)

    except Exception, e:
        sys.exit("Problem building logging handler. %s(%s)\n" % (Exception,e) )

#check_rrd(rrd, chan, chaninfo, options, RRD_NPTS)
usage = "usage: %prog [-r] [-q] [-v] [-d] database rrd_archive sta chan start [end]"
parser = OptionParser(usage=usage)
parser.add_option("-r", action="store_true", dest="rebuild",
    help="force re-build of archives", default=False)
parser.add_option("-v", action="store_true", dest="verbose",
    help="verbose output", default=False)
parser.add_option("-d", action="store_true", dest="debug",
    help="Very verbose output.", default=False)

(options, args) = parser.parse_args()

if len(args) >= 5 and len(args) <= 6:
    database = args[0]
    rrd_archive  = os.path.abspath(args[1])
    station  = args[2]
    channel  = args[3]
    start    = args[4]
    end = args[5] if len(args) == 6 else stock.now()
else:
    parser.print_help()
    parser.error("incorrect number of arguments")
    sys.exit(1)

if options.verbose:
    logger.setLevel(logging.INFO)

if options.debug:
    logger.setLevel(logging.DEBUG)


logger.info('database: %s' % database)
logger.info('rrd_archive: %s' % rrd_archive)
logger.info('station: %s' % station)
logger.info('channel: %s' % channel)
logger.info('start: %s' % start)
logger.info('end: %s' % end)



if not os.path.isfile(database):
    logger.critical('Cannot find specified database: %s' % database )
    parser.print_help()
    sys.exit(4)
else:
    logger.debug('Using database: %s' % database)


if not os.path.isfile(rrd_archive):
    logger.critical('Cannot find specified rrd_archive: %s' % rrd_archive )
    parser.print_help()
    sys.exit(7)
else:
    logger.debug('Using rrd_archive: %s' % rrd_archive)

# MAIN
logger.info('chan_thread( %s,%s,%s,%s,%s,%s )' \
        % (rrd_archive, station, channel, database, start, end ) )

sys.exit( chan_thread(rrd_archive, station, channel, database, start, end ) )

sys.exit( 9 )
