
# Need to bring back the capacity to catch KeyboardInterrupt
def signal_term_handler(signal, frame):
    raise KeyboardInterrupt

signal.signal(signal.SIGINT, signal_term_handler)



import time

try:
    from optparse import OptionParser
except Exception, e:
    sys.exit("\n\tProblems importing libraries.%s %s\n" % (Exception, e))



try:
    from pymongo import MongoClient
except Exception,e:
    sys.exit("\n\tProblem loading Pymongo library. %s(%s)\n" % (Exception,e) )



try:
    import antelope.stock as stock
except Exception, e:
    sys.exit("\n\tProblems loading ANTELOPE libraries. %s(%s)\n" % (Exception, e))

try:
    from logging_class import getLogger
except Exception, e:
    sys.exit("\n\tProblem loading logging_class. %s(%s)" % (Exception, e))



try:
    from xi202_import.xi202_import_class import xi202_importer
except Exception, e:
    sys.exit("Problem loading xi202_import_class file. %s(%s)\n" % (Exception, e))


try:
    from xi202_import.q330_serials import Q330serials
    from xi202_import.orb_serials import ORBserials
    from xi202_import.imei_buffer import IMEIbuffer
except Exception, e:
    sys.exit("Problem loading xi202_import private classes. %s(%s)\n" % (Exception, e))



# Read configuration from command-line
usage = "Usage: %prog [options]"

parser = OptionParser(usage=usage)
parser.add_option("-s", action="store", dest="state",
                    help="track orb id on this state file", default=False)
parser.add_option("-v", action="store_true", dest="verbose",
                    help="verbose output", default=False)
parser.add_option("-d", action="store_true", dest="debug",
                    help="debug output", default=False)
parser.add_option("-p", "--pf", action="store", dest="pf", type="string",
                    help="parameter file path", default="xi202_import")
parser.add_option("-x", action="store_true", dest="silent_fail",
                    help="silent on packet fails", default=False)

(options, args) = parser.parse_args()

loglevel = 'WARNING'
if options.debug:
    loglevel = 'DEBUG'
elif options.verbose:
    loglevel = 'INFO'

# Need new object for logging work.
logging = getLogger(loglevel=loglevel)


# Get PF file values
logging.info('Read parameters from pf file %s' % options.pf)
pf = stock.pfread(options.pf)


# Get MongoDb parameters from PF file
mongo_user = pf.get('mongo_user')
mongo_host = pf.get('mongo_host')
mongo_password = pf.get('mongo_password')
mongo_namespace = pf.get('mongo_namespace')
mongo_collections = pf.get('mongo_collections')
channel_mapping = pf.get('channel_mapping')
q330_pf_files = pf.get('q330_pf_files')
q330_orbs = pf.get('q330_orbs')

logging.debug( 'mongo_host => [%s]' % mongo_host )
logging.debug( 'mongo_user => [%s]' % mongo_user )
logging.debug( 'mongo_password => [%s]' % mongo_password )
logging.debug( 'mongo_namespace => [%s]' % mongo_namespace )

for c in mongo_collections:
    logging.debug( 'mongo_collections => [%s: %s]' % (c, mongo_collections[c]) )

# Configure MongoDb instance
try:
    logging.info( 'Init MongoClient( %s )' % mongo_host )
    mongo_instance = MongoClient(mongo_host)

    logging.info( 'Namespace [ %s ] in mongo_db' % mongo_namespace )
    mongo_db = mongo_instance.get_database( mongo_namespace )

    logging.info( 'Authenticate MongoDB instance' )
    mongo_db.authenticate(mongo_user, mongo_password)

except Exception,e:
    sys.exit("Problem with MongoDB Configuration. [ %s ]\n" % e )


# Load Q330 serial numbers from PF files
orb_q330units = ORBserials( q330_orbs )
q330units = Q330serials( q330_pf_files )

# READ PF CONFIGURATION
mongo_pull_wait = float( pf.get('mongo_pull_wait') )
logging.debug( 'mongo_pull_wait => [%s]' % mongo_pull_wait)

default_mongo_read = pf.get('default_mongo_read')
logging.debug( 'default_mongo_read => [%s]' % default_mongo_read)

orbserver = pf.get('orbserver')
logging.debug( 'orbserver => [%s]' % orbserver)

mongo_select = pf.get('mongo_select')
logging.debug( 'mongo_select => [%s]' % mongo_select )

mongo_reject = pf.get('mongo_reject')
logging.debug( 'mongo_reject => [%s]' % mongo_reject )


active_instances = []
for c in mongo_collections:
    # clean list
    logging.debug( '%s: [%s]' % (c, mongo_collections[c] ) )
    if not mongo_collections[c]: continue

    logging.debug( 'Create new instance for [%s]' % c )
    active_instances.append(
            xi202_importer( mongo_db[c], orbserver, name=c, orbunits=orb_q330units,
                q330units=q330units, channel_mapping=channel_mapping,
                mongo_select=mongo_select, mongo_reject=mongo_reject,
                default_mongo_read=default_mongo_read, statefile=options.state,
                mongo_pull_wait=mongo_pull_wait, pckt_name_type=mongo_collections[c]),
                silent_pkt_fail=options.silent_fail
            )

if not len( active_instances ):
    logging.error( 'No active instances from list.' )


try:
    while True:
        for instance in active_instances:
            logging.debug( 'Pull on next on [%s]' % instance )

            if instance.isvalid():
                instance.pull_data()
            else:
                logging.warning( 'Problems with [%s]' % instance )

            logging.debug( 'Done with [%s]' % instance )

        if mongo_pull_wait:
            logging.debug( 'Wait before next cycle: [%s]secs' % mongo_pull_wait )
            time.sleep( mongo_pull_wait )

except (KeyboardInterrupt, SystemExit):
    logging.debug( "KeyboardInterrupt or SystemExit" )
    for instance in active_instances:
        logging.info( "Close ORB connection for %s" % instance )
        instance.close_orb()

except Exception, e:
    logging.critical( 'Problem on instance init: %s:[ %s ]' % (Exception,e) )
    for instance in active_instances:
        logging.info( "Close ORB connection for %s" % instance )
        instance.close_orb()


logging.notify( "Exit" )

