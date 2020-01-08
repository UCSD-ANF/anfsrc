import sys
from optparse import OptionParser
from pymongo import MongoClient
import antelope.stock as stock
from logging_class import getLogger
from soh2mongo.soh_class import SOH_mongo

# Read configuration from command-line
usage = "Usage: %prog [options]"

parser = OptionParser(usage=usage)
parser.add_option("-s", action="store", dest="state",
                    help="track orb id on this state file", default=False)
parser.add_option("-c", action="store_true", dest="clean",
                    help="clean 'drop' collection on start", default=False)
parser.add_option("-v", action="store_true", dest="verbose",
                    help="verbose output", default=False)
parser.add_option("-d", action="store_true", dest="debug",
                    help="debug output", default=False)
parser.add_option("-p", "--pf", action="store", dest="pf", type="string",
                    help="parameter file path", default="soh2mongo")

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
mongo_collection = pf.get('mongo_collection')

logging.debug( 'mongo_host => [%s]' % mongo_host )
logging.debug( 'mongo_user => [%s]' % mongo_user )
logging.debug( 'mongo_password => [%s]' % mongo_password )
logging.debug( 'mongo_namespace => [%s]' % mongo_namespace )
logging.debug( 'mongo_collection => [%s]' % mongo_collection )


# Configure MongoDb instance
try:
    logging.info( 'Init MongoClient(%s)' % mongo_host )
    mongo_instance = MongoClient(mongo_host)

    logging.info( 'Get namespace %s in mongo_db' % mongo_namespace )
    mongo_db = mongo_instance.get_database( mongo_namespace )

    logging.info( 'Authenticate mongo_db' )
    mongo_db.authenticate(mongo_user, mongo_password)

except Exception as e:
    sys.exit("Problem with MongoDB Configuration. %s(%s)\n" % (Exception,e) )


# May need to nuke the collection before we start updating it
# Get this mode by running with the -c flag.
if options.clean:
    logging.info('Drop collection %s.%s' % (mongo_namespace, mongo_collection) )
    mongo_db.drop_collection(mongo_collection)
    logging.info('Drop collection %s.%s_errors' % (mongo_namespace, mongo_collection) )
    mongo_db.drop_collection("%s_errors" % mongo_collection)



# READ PF CONFIGURATION
orbserver = pf.get('orbserver')
logging.debug( 'orbserver => [%s]' % orbserver)

orb_select = pf.get('orb_select')
logging.debug( 'orb_select => [%s]' % orb_select )

orb_reject = pf.get('orb_reject')
logging.debug( 'orb_reject => [%s]' % orb_reject )

default_orb_read = pf.get('default_orb_read')
logging.debug( 'default_orb_read => [%s]' % default_orb_read )

reap_wait = pf.get('reap_wait')
logging.debug( 'reap_wait => [%s]' % reap_wait)

reap_timeout = pf.get('reap_timeout')
logging.debug( 'reap_timeout => [%s]' % reap_timeout)

timeout_exit = pf.get('timeout_exit')
logging.debug( 'timeout_exit => [%s]' % timeout_exit)

opt_chan = pf.get('parse_opt')
logging.debug( 'opt_chan => [%s]' % opt_chan)

indexing = pf.get('indexing')
logging.debug( 'indexing => [%s]' % indexing)



# Run main process now
try:
    SOH_mongo( mongo_db[mongo_collection], orbserver, orb_select=orb_select,
        orb_reject=orb_reject, default_orb_read=default_orb_read, statefile=options.state,
        reap_wait=reap_wait, reap_timeout=reap_timeout, timeout_exit=timeout_exit,
        parse_opt=opt_chan, indexing=indexing).start_daemon()
except Exception as e:
    logging.critical( 'exit daemon: %s:[ %s ]' % (Exception,e) )

