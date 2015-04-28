try:
    import sys
    import json
    import string
    import tempfile
    import re
    import gzip
    from optparse import OptionParser
    from time import time, gmtime, strftime
    from pprint import pprint
    from collections import defaultdict
except Exception,e:
    sys.exit( "\n\tProblems importing libraries.%s %s\n" % (Exception,e) )


try:
    import antelope.datascope as datascope
    import antelope.orb as orb
    import antelope.stock as stock
except Exception,e:
    sys.exit( "\n\tProblems loading ANTELOPE libraries. %s(%s)\n"  % (Exception,e))


try:
    from db2json.global_variables import *
except Exception,e:
    sys.exit("Problem loading global_variables.py file. %s(%s)\n" % (Exception,e) )


try:
    from db2web.sta2json import Stations
except Exception,e:
    sys.exit("Problem loading Stations class. %s(%s)\n" % (Exception,e) )

try:
    from db2web.event2json import Events
except Exception,e:
    sys.exit("Problem loading Events class. %s(%s)\n" % (Exception,e) )

def configure():
    """ Parse command line args

    Return the values as a list.
        (verbose, zipper, subtype, pfname, force)

    """

    usage = "Usage: %prog [options]"

    parser = OptionParser(usage=usage)
    parser.add_option("-f", action="store_true", dest="force",
        help="force new build", default=False)
    parser.add_option("-v", action="store_true", dest="verbose",
        help="verbose output", default=False)
    parser.add_option("-t", "--type", action="store", type="string",
        dest="subtype", help="type of station to process", default='all')
    parser.add_option("-z", action="store_true", dest="zipper",
        help="create a gzipped version of the file", default=True)
    parser.add_option("-p", "--pf", action="store", dest="pf", type="string",
        help="parameter file path", default="db2web")

    (options, args) = parser.parse_args()

    if options.subtype not in subtype_list:
        log("Subtype '%s' not recognized" % subtype)
        log("\tEither don't define it or use: %s" % ', '.join(subtype_list))
        sys.exit("Subtype '%s' not recognized" % subtype)

    for p in list(stock.pffiles(options.pf)):
        if os.path.isfile(p):
            options.pf = p

    if not os.path.isfile(options.pf):
        sys.exit("parameter file '%s' does not exist." % options.pf)

    return options.verbose, options.zipper, options.subtype, options.pf, options.force

def database_existence_test(db):
    """DB path verify

    Test that the disk mount point is visible
    with a simple os.path.isfile() command.

    """
    if not os.path.isfile(db):
        log("Error: Cannot read the dbmaster file (%s)" % db)
        log("NFS or permissions problems? Check file exists...")
        sys.exit("Error on dbmaster file (%s)" % db)
    return

def make_zip_copy(myfile):
    """Create a gzipped file

    Makes the file in the argument and creates a
    commpressed version of it. It will append a
    .gz to the end of the name and will put
    the new file in the same folder.
    """

    fzip_in = open(myfile, 'rb')

    log("Make gzipped version of the file: %s" % myfile)

    try:
        fzip_out = gzip.open('%s.gz' % myfile, 'wb' )
    except Exception,e:
        sys.exit("Cannot create new gzipped version of file: %s %s" % (fzip_out, e))

    fzip_out.writelines(fzip_in)
    fzip_out.close()
    fzip_in.close()

    return True


def main():
    """Main processing script
    for all JSON summary & individual
    files
    """
    verbose, zipper, subtype, db2webpf, force = configure()
    stations = Stations('db2web')
    events = Events('db2web')

    # print stations.orbnames
    # print stations.orbs

    # Setup MongoDB
    # while(True):
    stations.get_all_sta_cache()
    stations.get_all_orb_cache()
    stations.dump_cache(to_mongo=True, to_json=True)

    events._get_event_cache()
    events.dump_cache(to_mongo=True, to_json=True)
        # sleep(300)

    

    if verbose :
        log("Parse stations configuration parameter file (%s)" % stations_pf)


if __name__ == '__main__':
    sys.exit( main() )
