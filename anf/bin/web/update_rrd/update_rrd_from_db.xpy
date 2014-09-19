"""
Produce and maintain RRD archives base on some Antelope
database with a wfdisc table. It's intention is to replace
orb2rrd since now we can run directly from the database and
not from the orb. There is an option to rebuild the RRD archive
with a simple removal of the previous database. The tools will
simple look for the oldest data in the archive and will populate
the RRD with everything it finds.

Juan Reyes
reyes@ucsd.edu

Malcolm White
mcwhite@ucsd.edu
"""

try:
    import antelope.datascope as datascope
    import antelope.stock as stock
except Exception,e:
    sys.exit( "\n\tProblems with Antelope libraries.%s %s\n" % (Exception,e) )

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
    # logger.setLevel(logging.WARNING)
    logger.setLevel(logging.INFO)

except Exception, e:
    sys.exit("Problem building logging handler. %s(%s)\n" % (Exception,e) )


#import threading
import time
import subprocess
import re
from optparse import OptionParser
from collections import defaultdict

try:
    from update_rrd_functions import *
    import dbcentral as dbcentral
except Exception,e:
    sys.exit( "\n\tProblems with required libraries.%s %s\n" % (Exception,e) )


##################
#MAIN
##################

MAX_THREADS = 0  # SET THIS AFTER OptionParser
TIMEFORMAT = '%Y(%j)%H:%M:%S'
RRD_NPTS = 1600 # aprox. number of points per RRD window

PROCESSES = set()

logger.debug( stock.epoch2str(stock.now(),TIMEFORMAT) )
logger.debug( ' '.join(sys.argv) )

usage = "usage: %prog [options] database rrd_archive"
parser = OptionParser(usage=usage)

parser.add_option("-m", action="store", dest="dbmaster",
    help="Optional dbmaster db", default=False)
parser.add_option("-d", action="store", dest="cluster",
    help="Nickname of cluster dbcentral paramerter", default=False)
parser.add_option("-n", action="store", dest="networks",
    help="Subset on vnet or snet", default=False)
parser.add_option("-s", action="store", dest="stations",
    help="Subset on stations", default=False)
parser.add_option("-c", action="store", dest="channels",
    help="Subset on channels", default='.*')
parser.add_option("-r", action="store_true", dest="rebuild",
    help="force re-build of archives", default=False)
parser.add_option("-t", action="store", dest="maxthreads",
    help="Max number of threads", default=10)
parser.add_option("-p", action="store", dest="pf",
    help="Parameter file to use", default=sys.argv[0])
parser.add_option("-a", action="store_true", dest="active",
    help="Active stations only", default=False)
parser.add_option("-v", action="store_true", dest="verbose",
    help="verbose output", default=False)
parser.add_option("-q", action="store_true", dest="quiet",
    help="quiet run - NO INFO LOGGING", default=False)

(options, args) = parser.parse_args()

MAX_THREADS = options.maxthreads

if options.verbose:
    logger.setLevel(logging.DEBUG)

if options.quiet:
    logger.setLevel(logging.WARNING)

if len(args) == 2:
    database = os.path.abspath(args[0])
    archive  = os.path.abspath(args[1])
else:
    parser.print_help()
    parser.error("incorrect number of arguments")

if not os.path.isdir(archive):
    logger.critical('Cannot find specified directory: %s' % archive )
    parser.print_help()
    sys.exit()

logger.info('Using database: %s' % database)



#
# Parse parameter file
#
options.pf = stock.pffiles(options.pf)[-1]
logger.info('Read PF "%s"' % options.pf)
try:
    pf = stock.pfread(options.pf)
except Exception,e:
    logger.critical('Problems with PF %s' % options.pf)
    logger.critical('%s: %s' % (Exception,e) )
    sys.exit()
SOH_CHANNELS = pf['Q330_SOH_CHANNELS']


#
# Get list of databases
#
logger.debug( 'get databases from %s:' % database)
if options.cluster: logger.debug( 'using cluster: %s:' % options.cluster)
dbcentral_dbs = dbcentral.dbcentral(database,options.cluster,options.verbose)

logger.debug( 'dbcntl.path => %s' % dbcentral_dbs.path )
logger.debug( 'dbcntl.nickname => %s' % dbcentral_dbs.nickname )
logger.debug( 'dbcntl.type => %s' % dbcentral_dbs.type )
logger.debug( 'dbcntl.nickname => %s' % dbcentral_dbs.nickname )
logger.debug( 'dbcntl.list() => %s' % dbcentral_dbs.list() )
logger.debug( '%s' % dbcentral_dbs )


#
# Get list of stations to process from dbmaster
#
logger.debug(' get stations from %s:' % database)
try:
    if options.dbmaster:
        # We need to look for the data on a different db...
        dbmaster = dbcentral.dbcentral(options.dbmaster,False,options.verbose)
        stations = get_stations(dbmaster,options)
    else:
        # Just use the same dbcentral_dbs that we use for the data...
        stations = get_stations(dbcentral_dbs,options)
except Exception as e:
    logger.critical('Cannot get dbmaster: %s %s' % (Exception,e))
    sys.exit()


#
# Loop over and process data for each network
#
logger.debug(' START SCRIPT TIME: %s' % stock.epoch2str( stock.now(),TIMEFORMAT ))
sta_timer = stock.now()

for net in sorted(stations.keys()):
    for sta in sorted(stations[net].keys()):
        vnet = stations[net][sta]['vnet']
        chaninfo = stations[net][sta]

        logger.info(' %s %s_%s' % (vnet, net, sta))


        #create the vnet directory to house the RRDs if necessary
        #build RRD folder path using the vnet value.
        myrrdpath = '%s/rrd/%s/%s' % (archive, vnet, sta)
        logger.debug('RRD archive: %s' % archive)

        try:
            os.mkdirs(myrrdpath)
        except:
            pass

        if not os.path.exists(myrrdpath):
            logger.error('Cannot make dir %s' % myrrdpath)
            sys.exit()

        logger.debug('subset channels =~ /%s/' % options.channels)
        channel_list = [c for c in SOH_CHANNELS \
                if re.search(r"^%s$" % options.channels,c)]
        logger.debug('channel_list: %s' % channel_list)

        for chan in channel_list:
            #build the absolute path to the RRD file
            rrd = '%s/%s_%s.rrd' % (myrrdpath, sta, chan)

            if options.rebuild:
                logger.debug('clean RRD for %s:%s %s' % (sta, chan, rrd))
                os.remove(rrd)

            try:
                check_rrd(rrd, sta, chan, chaninfo, RRD_NPTS)
            except Exception as e:
                e = '%s' % e
                raise(Exception(e))

            #Create a dictionary that stores flags to determine whether
            #or not the RRD for each channel at this station has been
            #checked.
            rrd_checked = {}

            while len(PROCESSES) > MAX_THREADS:
                logger.debug('.' * len(PROCESSES) )
                #logger.debug('threads: %d' % (len(PROCESSES)) )
                temp_procs = set()
                for p in PROCESSES:
                    #stdout,stderr = p.communicate(input=None,timeout=1)[0];
                    #if stdout: logger.debug('PARENT stdout: [%s]' % stdout)
                    #if stderr: logger.warning('PARENT stderr: [%s]' % stderr)
                    if p.poll() is None:
                        temp_procs.add(p)
                    else:
                        logger.info('Done with proc. %s' % p)

                PROCESSES = temp_procs
                #logger.debug( 'sleep(1)' )
                time.sleep(1)

            cmd = 'update_rrd_chan_thread'
            if options.rebuild: cmd += ' -r'
            if options.verbose: cmd += ' -v'
            if options.quiet:   cmd += ' -q'
            if options.cluster: cmd += ' -d "%s"' % options.cluster
            cmd += ' %s' % rrd
            cmd += ' %s' % database
            cmd += ' %s' % sta
            cmd += ' %s' % chan
            cmd += ' %s' % chaninfo['time']
            cmd += ' %s' % chaninfo['endtime']

            #cmd = 'sleep 20'
            logger.info('\n\nRUN:\t%s' % cmd)
            try:
                new_proc = subprocess.Popen( [cmd] ,shell=True)
                #stderr=subprocess.PIPE,stdout=subprocess.PIPE )
            except Exception,e:
                logger.critical('Cannot spawn thread: [%s] %s %s' \
                        % (e.child_traceback,Exception,e))
            else:
                PROCESSES.add( new_proc )
            logger.info('\n\n')

    while len(PROCESSES) > 0:
        #logger.debug('threads: %d' % (len(PROCESSES)) )
        logger.debug('.' * len(PROCESSES) )
        temp_procs = set()
        for p in PROCESSES:
            #stdout,stderr = p.communicate(input=None,timeout=1)[0];
            #if stdout: logger.debug('PARENT stdout: [%s]' % stdout)
            #if stderr: logger.warning('PARENT stderr: [%s]' % stderr)
            if p.poll() is None:
                temp_procs.add(p)
            else:
                logger.info('Done with proc. %s' % p)

        PROCESSES = temp_procs
        #logger.debug( 'sleep(1)' )
        time.sleep(1)


logger.debug('END SCRIPT TIME: %s' % stock.epoch2str( stock.now(),TIMEFORMAT ))
logger.debug('%s' % stock.strtdelta(stock.now() - sta_timer))
