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
    import dbcentral as dbcentral
except Exception,e:
    sys.exit( "\n\tProblems with required libraries.%s %s\n" % (Exception,e) )

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
    #####
    # Set logging handler
    #####
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


TIMEFORMAT = '%Y(%j)%H:%M:%S'

#check_rrd(rrd, chan, chaninfo, options, RRD_NPTS)
usage = "usage: %prog [-r] [-q] [-v] [-d cluster] rrd_archive database sta chan start [end]"
parser = OptionParser(usage=usage)
parser.add_option("-r", action="store_true", dest="rebuild",
    help="force re-build of archives", default=False)
parser.add_option("-v", action="store_true", dest="verbose",
    help="verbose output", default=False)
parser.add_option("-q", action="store_true", dest="quiet",
    help="quiet run - NO INFO LOGGING", default=False)
parser.add_option("-d", action="store", dest="cluster",
    help="Nickname of cluster dbcentral paramerter", default=False)

(options, args) = parser.parse_args()

if options.verbose:
    logger.setLevel(logging.DEBUG)

if options.quiet:
    logger.setLevel(logging.WARNING)

if len(args) >= 5 and len(args) <= 6:
    rrd_archive  = os.path.abspath(args[0])
    database = os.path.abspath(args[1])
    station  = args[2]
    channel  = args[3]
    start    = args[4]
else:
    parser.print_help()
    parser.error("incorrect number of arguments")

if len(args) == 6:
    end = args[5]
else:
    end = stock.now()


logger = logging.getLogger().getChild( '%s_%s' % (station,channel) )
logger.info( stock.epoch2str(stock.now(),TIMEFORMAT) )
logger.info( ' '.join(sys.argv) )

#
# Get list of databases
#
logger.debug( 'get databases from %s:' % database)
if options.cluster: logger.debug( 'using cluster: %s:' % options.cluster)
try:
    dbcentral_dbs = dbcentral.dbcentral(database,options.cluster,options.verbose)
except Exception, e:
    logger.error( 'Cannot init dbcentral object: => %s' % e )
    sys.exit(1)

logger.debug( 'dbcntl.path => %s' % dbcentral_dbs.path )
logger.debug( 'dbcntl.nickname => %s' % dbcentral_dbs.nickname )
logger.debug( 'dbcntl.type => %s' % dbcentral_dbs.type )
logger.debug( 'dbcntl.nickname => %s' % dbcentral_dbs.nickname )
logger.debug( 'dbcntl.list() => %s' % dbcentral_dbs.list() )
logger.debug( '%s' % dbcentral_dbs )



if not os.path.isfile(rrd_archive):
    logger.critical('Cannot find specified rrd_archive: %s' % rrd_archive )
    parser.print_help()
    sys.exit()
else:
    logger.debug('Using rrd_archive: %s' % rrd_archive)

if not os.path.isfile(database):
    logger.critical('Cannot find specified database: %s' % database )
    parser.print_help()
    sys.exit()
else:
    logger.debug('Using database: %s' % database)


# MAIN
try:
    code = chan_thread(rrd_archive, station, channel, dbcentral_dbs, start, end )
except Exception,e:
    logger.error('Problem during chan_thread(): %s' % e)
    code = 9

sys.exit( code )

