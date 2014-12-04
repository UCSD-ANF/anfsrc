"""
Produce and maintain RRD archives base on some Antelope
database with a wfdisc table. It's intention is to replace
orb2rrd since now we can run directly from the database and
not from the orb. There is an option to rebuild the RRD archive
with a removal of the previous rrd database. 
The tools will simple look for the oldest data in the archive
and will populate the RRD with everything it finds.

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
    logger.setLevel(logging.WARNING)
    # logger.setLevel(logging.INFO)

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

PROCESSES = set()

usage = "usage: %prog [options] project"
parser = OptionParser(usage=usage)

parser.add_option("-n", action="store", dest="networks",
    help="Subset on vnet or snet", default=False)
parser.add_option("-s", action="store", dest="stations",
    help="Subset on stations", default=False)
parser.add_option("-c", action="store", dest="channels",
    help="Subset on channels", default='.*')
parser.add_option("-r", action="store_true", dest="rebuild",
    help="force re-build of archives", default=False)
parser.add_option("-p", action="store", dest="pffile",
    help="Parameter file to use", default=sys.argv[0])
parser.add_option("-a", action="store_true", dest="active",
    help="Active stations only", default=False)
parser.add_option("-v", action="store_true", dest="verbose",
    help="verbose output", default=False)
parser.add_option("-d", action="store_true", dest="debug",
    help="Super verbose mode. Debugging use.", default=False)

(options, args) = parser.parse_args()

if options.verbose:
    logger.setLevel(logging.INFO)

if options.debug:
    logger.setLevel(logging.DEBUG)

if len(args) == 1:
    project = args[0]
else:
    parser.print_help()
    parser.error("incorrect number of arguments")

#
# Parse parameter file
#
options.pf = stock.pffiles(options.pffile)[-1]
logger.info('Read PF "%s"' % options.pf)
try:
    pf = stock.pfread(options.pf)
except Exception,e:
    logger.critical('Problems with PF %s' % options.pf)
    logger.critical('%s: %s' % (Exception,e) )
    sys.exit()

SOH_CHANNELS = pf['Q330_SOH_CHANNELS']
MAX_THREADS = pf['MAX_THREADS']
TIMEFORMAT = pf['TIMEFORMAT']
RRD_NPTS = pf['RRD_NPTS']

if project in pf['project']:
    dbmaster = os.path.abspath( pf['project'][project]['dbmaster'] )
    database = os.path.abspath( pf['project'][project]['db'] )
    archive = os.path.abspath( pf['project'][project]['archive'] )
    nickname = pf['project'][project]['nickname']
else:
    logger.critical('Specified project not defined in pf. [%s] [%s] ' \
            % (project, options.pf) )
    sys.exit()

if not os.path.isdir(archive):
    logger.critical('Cannot find specified directory: %s' % archive )
    parser.print_help()
    sys.exit()

logger.debug( stock.epoch2str(stock.now(),TIMEFORMAT) )
logger.debug( ' '.join(sys.argv) )

logger.info('Using dbmaster: %s' % dbmaster)
if nickname: logger.info('Using nickname: %s' % nickname)
logger.info('Using database: %s' % database)
logger.info('Using archive: %s' % archive)


#
# Get list of databases
#
logger.info( 'get databases from %s:' % database)
dbcentral_dbs = dbcentral.dbcentral(database,nickname=nickname,debug=options.debug)

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
    if dbmaster:
        # We need to look for the data on a different db...
        dbmaster_ptr = dbcentral.dbcentral(dbmaster,debug=options.debug)
        stations = get_stations(dbmaster_ptr,options)
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
active = {}

for net in sorted(stations.keys()):
    for sta in sorted(stations[net].keys()):
        vnet = stations[net][sta]['vnet']
        chaninfo = stations[net][sta]

        logger.info(' %s %s_%s' % (vnet, net, sta))


        #create the vnet directory to house the RRDs if necessary
        #build RRD folder path using the vnet value.
        myrrdpath = os.path.abspath( '%s/rrd/%s/%s' % (archive, vnet, sta) )
        logger.debug('RRD archive: %s' % archive)

        if not os.path.exists(myrrdpath):
            logger.info('mkdir %s' % myrrdpath)
            try:
                os.makedirs(myrrdpath)
            except Exception,e:
                logger.error('Cannot make dir %s [%s]' % (myrrdpath,e) )
                sys.exit()

        logger.debug('subset channels =~ /%s/' % options.channels)
        channel_list = [c for c in SOH_CHANNELS \
                if re.search(r"^%s$" % options.channels,c)]
        logger.debug('channel_list: %s' % channel_list)

        for chan in channel_list:
            #build the absolute path to the RRD file
            rrd = os.path.abspath( '%s/%s_%s.rrd' % (myrrdpath, sta, chan) )

            if options.rebuild:
                logger.debug('clean RRD for %s:%s %s' % (sta, chan, rrd))
                try:
                    os.remove(rrd)
                except:
                    pass

            try:
                check_rrd(rrd, sta, chan, chaninfo, RRD_NPTS)
            except Exception as e:
                e = '%s' % e
                raise(Exception(e))

            logger.debug('calling check_threads(%s,%s)' \
                    % (len(active),MAX_THREADS))

            active = check_threads(active,MAX_THREADS)

            cmd = 'update_rrd_chan_thread'
            if options.rebuild: cmd += ' -r'
            if options.debug:   cmd += ' -d'
            if options.verbose: cmd += ' -v'
            if options.pf:      cmd += ' -p "%s"' % options.pf
            cmd += ' %s' % project
            cmd += ' %s' % rrd
            cmd += ' %s' % sta
            cmd += ' %s' % chan
            cmd += ' %s' % chaninfo['time']
            cmd += ' %s' % chaninfo['endtime']

            try:
                logger.debug('subprocess.Popen( %s )' % cmd)
                new_proc = subprocess.Popen( [cmd] ,shell=True)
            except Exception,e:
                logger.critical('Cannot spawn thread: [%s] %s %s' \
                        % (e.child_traceback,Exception,e))
            else:
                active[new_proc.pid] = {'sta':sta, 'chan':chan, 'cmd':cmd, \
                        'proc':new_proc}

            logger.info('RUN: \t%s' % cmd )


    logger.debug('calling check_threads(%s,%s)' \
            % (len(active),MAX_THREADS))
    check_threads(active) # runs until no threads are active

logger.info('END SCRIPT TIME: %s' % stock.epoch2str( stock.now(),TIMEFORMAT ))
logger.info('%s' % stock.strtdelta(stock.now() - sta_timer))
