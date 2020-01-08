import sys
import importlib
from optparse import OptionParser
from time import sleep
from pymongo import MongoClient
import antelope.stock as stock
from db2mongo.logging_class import getLogger
from db2mongo.db2mongo_libs import update_collection


# Read configuration from command-line
usage = "Usage: %prog [options]"

parser = OptionParser(usage=usage)
parser.add_option("-c", action="store_true", dest="clean",
                    help="clean 'drop' collection on start", default=False)
parser.add_option("-v", action="store_true", dest="verbose",
                    help="verbose output", default=False)
parser.add_option("-d", action="store_true", dest="debug",
                    help="debug output", default=False)
parser.add_option("-p", "--pf", action="store", dest="pf", type="string",
                    help="parameter file path", default="db2mongo")

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

# Veriyf if we have "refresh" time variable in PF file
try:
    refresh = int(pf['refresh'])
    if not refresh:
        raise
except:
    refresh = 60

logging.info("refresh every [%s]secs" % refresh)



# Now load modules listed on the PF file
index = {}
loadedmodules = {}
#requiredmodules = {
#        'metadata': ['metadata_class', 'Metadata']
#        }


# Get list from PF file
logging.notify('List of modules to load.' )
modules = pf.get('modules')
logging.notify( modules )

# DYNAMIC LOAD OF MODULES
for m in modules:
    logging.notify( "Loading module %s" % (m) )

    # Load parameters for this module
    logging.debug( "Parameters for module %s" % (m) )
    params = pf[ modules[ m ] ]
    logging.debug( params )
    if not params:
        sys.exit('Missing parameters for module %s' % m)


    # File and class name should be on parameter blob
    filename = 'db2mongo.%s' % params['filename']
    classname = params['class']
    logging.debug( "filename:%s     class:%s" % (filename,classname) )

    # Import class into namespace
    try:
        logging.notify( "load %s import %s and init()" % (classname,filename) )
        loadedmodules[m] = getattr( importlib.import_module(filename), classname )()
        logging.debug('New loaded object:')
        logging.debug(dir(loadedmodules[m]) )
    except Exception as e:
        sys.exit("Problem loading %s() [%s]\n" % (classname,e))

    # Configure new object from values in PF file
    for key, val in params.iteritems():
        # We avoid "index", this is for the MongoDB collection
        if key == 'index':
            index[m] =  val
            continue
        # Already used class and filename
        if key == 'class': continue
        if key == 'filename': continue

        # The rest we send to the class
        try:
            logging.info('setattr(%s,%s,%s)' % (classname,key,val) )
            setattr(loadedmodules[m], key, val)
        except Exception as e:
            sys.exit('Problems on setattr(%s,%s,%s)' % (classname,key,val) )

    # We want to validate the configuration provided to
    # the new object.
    try:
        if loadedmodules[m].validate():
            logging.info('Module %s is ready.' % m )
        else:
            raise
    except Exception as e:
        sys.exit( 'Problem validating module %s: %s' % (m,e) )


logging.notify('ALL MODULES READY!' )

# Configure MongoDb instance
try:
    logging.debug( 'Init MongoClient(%s)' % mongo_host )
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
    for m in loadedmodules:
        logging.info('Drop collection %s.%s' % (mongo_namespace, m) )
        mongo_db.drop_collection(m)
        logging.info('Drop collection %s.%s_errors' % (mongo_namespace, m) )
        mongo_db.drop_collection("%s_errors" % m)


# Main process here. Run forever.
while(True):

    # for each module loaded...
    for m in loadedmodules:
        logging.debug( '%s.need_update()' % m )

        # Verify if there is new data
        if loadedmodules[m].need_update():

            if m in index:
                useindex = index[m]
            else:
                useindex = None

            # Update the internal cache of the object
            logging.debug( '%s.refresh()' % m )
            loadedmodules[m].update()

            # Dump the cached data into local variables
            logging.debug( '%s.data()' % m )
            data, errors = loadedmodules[m].data()

            # Send the data to MongoDB
            update_collection(mongo_db, m, data, useindex)
            update_collection(mongo_db, "%s_error" % m, errors)


    # Pause this loop
    logging.debug('Pause for [%s] seconds' % refresh)
    sleep(refresh)
