def signal_term_handler(signal, frame):
    raise KeyboardInterrupt

import signal
signal.signal(signal.SIGINT, signal_term_handler)

import sys
import time

from optparse import OptionParser
from pymongo import MongoClient
import antelope.stock as stock
from anf.logging import getLogger
from xi202_import import XI202Importer
from xi202_import.q330_serials import Q330serials
from xi202_import.orb_serials import ORBserials

def main(argv=None):
    """main function for xi202_import"""

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
    logger = getLogger(loglevel=loglevel)


    # Get PF file values
    logger.info('Read parameters from pf file %s' % options.pf)
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

    logger.debug( 'mongo_host => [%s]' % mongo_host )
    logger.debug( 'mongo_user => [%s]' % mongo_user )
    logger.debug( 'mongo_password => [%s]' % mongo_password )
    logger.debug( 'mongo_namespace => [%s]' % mongo_namespace )

    for c in mongo_collections:
        logger.debug( 'mongo_collections => [%s: %s]' % (c, mongo_collections[c]) )

    # Configure MongoDb instance
    try:
        logger.info( 'Init MongoClient( %s )' % mongo_host )
        mongo_instance = MongoClient(mongo_host)

        logger.info( 'Namespace [ %s ] in mongo_db' % mongo_namespace )
        mongo_db = mongo_instance.get_database( mongo_namespace )

        logger.info( 'Authenticate MongoDB instance' )
        mongo_db.authenticate(mongo_user, mongo_password)

    except Exception as e:
        logger.exception("Problem connecting to MongoDB.")
        return -1


    # Load Q330 serial numbers from PF files
    orb_q330units = ORBserials( q330_orbs )
    q330units = Q330serials( q330_pf_files )

    # READ PF CONFIGURATION
    mongo_pull_wait = float( pf.get('mongo_pull_wait') )
    logger.debug( 'mongo_pull_wait => [%s]' % mongo_pull_wait)

    default_mongo_read = pf.get('default_mongo_read')
    logger.debug( 'default_mongo_read => [%s]' % default_mongo_read)

    orbserver = pf.get('orbserver')
    logger.debug( 'orbserver => [%s]' % orbserver)

    mongo_select = pf.get('mongo_select')
    logger.debug( 'mongo_select => [%s]' % mongo_select )

    mongo_reject = pf.get('mongo_reject')
    logger.debug( 'mongo_reject => [%s]' % mongo_reject )


    result = 0
    active_instances = []

    for c in mongo_collections:
        # clean list
        logger.debug( '%s: [%s]' % (c, mongo_collections[c] ) )
        if not mongo_collections[c]: continue

        logger.debug( 'Create new instance for [%s]' % c )
        active_instances.append(
                XI202Importer( mongo_db[c], orbserver, name=c, orbunits=orb_q330units,
                    q330units=q330units, channel_mapping=channel_mapping,
                    mongo_select=mongo_select, mongo_reject=mongo_reject,
                    default_mongo_read=default_mongo_read, statefile=options.state,
                    mongo_pull_wait=mongo_pull_wait, pckt_name_type=mongo_collections[c],
                    silent_pkt_fail=options.silent_fail ),
                )

    if not len( active_instances ):
        logger.error( 'No active instances from list.' )
        result = -1

    else:
        try:
            while True:
                for instance in active_instances:
                    logger.debug( 'Pull on next on [%s]' % instance )

                    if instance.isvalid():
                        instance.pull_data()
                    else:
                        logger.warning( 'Problems with [%s]' % instance )

                    logger.debug( 'Done with [%s]' % instance )

                if mongo_pull_wait:
                    logger.debug( 'Wait before next cycle: [%s]secs' % mongo_pull_wait )
                    time.sleep( mongo_pull_wait )

        except (KeyboardInterrupt, SystemExit):
            logger.debug( "KeyboardInterrupt or SystemExit" )

        except Exception as e:
            logger.exception('Problem on instance init for instance ' + str(instance))
            result = -1

        finally:
            for instance in active_instances:
                logger.info( "Close ORB connection for %s" % instance )
                instance.close_orb()


    logger.notify("Exiting with status %s" % result)
    return result

if __name__ == '__main__':
    exit(main(sys.argv))
