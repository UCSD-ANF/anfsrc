"""
Antelope Datascope output to JSON files

"""

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
    from global_variables import *
except Exception,e:
    sys.exit("Problem loading global_variables.py file. %s(%s)\n" % (Exception,e) )


try:
    from parseorb import ParseOrb
except Exception,e:
    sys.exit("Problem loading ParseOrb module. %s(%s)\n" % (Exception,e) )


try:
    from parsedb import ParseDB
except Exception,e:
    sys.exit("Problem loading ParseDB module. %s(%s)\n" % (Exception,e) )


def log(message):
    """Format our print commands

    Prepend  a timestamp and the name of the
    script to the log msg.

    """
    curtime = stock.epoch2str(stock.now(),"%d(%j)%H:%M:%S")
    print "%s db2json: %s" % (curtime, message)

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
        help="parameter file path", default="db2jons")

    (options, args) = parser.parse_args()

    if options.subtype not in subtype_list:
        log("Subtype '%s' not recognized" % subtype)
        log("\tEither don't define it or use: %s" % ', '.join(subtype_list))
        sys.exit("Subtype '%s' not recognized" % subtype)

    for p in list(stock.pffiles(options.pf)):
        if os.path.isfile(p):
            options.pf = p

    if not os.path.isfile(options.pf):
        sys.exit("parameter file '%s' does not exist." % pfname)

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

    verbose, zipper, subtype, db2jsonpf, force = configure()


    if verbose :
        log("Parse stations configuration parameter file (%s)" % stations_pf)

    parseDbConfig = defaultdict()
    #stock.pfupdate(stations_pf)
    pf = stock.pfread(stations_pf)

    parseDbConfig['network'] = pf.get('network')
    parseDbConfig['provider'] = pf.get('comms_provider')
    parseDbConfig['comms'] = pf.get('comms_type')
    parseDbConfig['dataloggers'] = pf.get('datalogger')
    parseDbConfig['sensors'] = pf.get('sensor')


    # Parse deployment specific option from db2json
    db_subset = False
    auth_snet = False
    adoptions = False
    balers = False
    infrasound = False
    calibrations = False
    dlevents = False

    pf = stock.pfread(db2jsonpf)
    try:
        json_path  = pf.get('json_path')
    except Exception, e:
        sys.exit("No 'json_path' defined in pf '%s' [%s]" % (db2jsonpf,e))

    try:
        all_stations_json_file  = pf.get('all_stations_json_file')
    except Exception, e:
        sys.exit("No 'all_stations_json_file' defined in pf '%s'" % db2jsonpf)

    try:
        dbmaster  = pf.get('dbmaster')
    except Exception, e:
        sys.exit("No 'dbmaster' defined in pf '%s'" % db2jsonpf)

    try:
        tables_to_check  = pf.get('tables_to_check')
    except Exception, e:
        sys.exit("No 'tables_to_check' defined in pf '%s'" % db2jsonpf)


    try:
        q330comms = pf.get('q330comms')
    except Exception, e:
        sys.exit("No 'q330comms' defined in pf '%s'" % db2jsonpf)

    try:
        orb = pf.get('orb')
    except Exception, e:
        sys.exit("No 'orb' defined in pf '%s'" % db2jsonpf)

    try:
        orb_stations_select = pf.get('orb_stations_select')
    except Exception, e:
        sys.exit("No 'orb_stations_select' defined in pf '%s'" % db2jsonpf)


    try:
        orbstat_alerts = pf.get('orbstat_alerts')
    except Exception, e:
        sys.exit("No 'orbstat_alerts' defined in pf '%s'" % db2jsonpf)


    try:
        infrasound_mapping = pf.get('infrasound_mapping')
    except Exception, e:
        sys.exit("No 'infrasound_mapping' defined in pf '%s'" % db2jsonpf)


    try:
        dbcalibrations = pf.get('dbcalibrations')
    except Exception, e:
        sys.exit("No 'dbcalibrations' defined in pf '%s'" % db2jsonpf)

    try:
        dbops_q330 = pf.get('dbops_q330')
    except Exception, e:
        sys.exit("No 'dbops_q330' defined in pf '%s'" % db2jsonpf)

    try:
        db_subset = pf.get('db_subset')
    except Exception, e:
        sys.exit("No 'db_subset' defined in pf '%s'" % db2jsonpf)

    try:
        auth_snet = pf.get('auth_snet')
    except Exception, e:
        sys.exit("No 'auth_snet' defined in pf '%s'" % db2jsonpf)

    try:
        adoptions = pf.get('adoptions')
    except Exception, e:
        sys.exit("No 'adoptions' defined in pf '%s'" % db2jsonpf)

    try:
        balers = pf.get('balers')
    except Exception, e:
        sys.exit("No 'balers' defined in pf '%s'" % db2jsonpf)

    try:
        infrasound = pf.get('infrasound')
    except Exception, e:
        sys.exit("No 'infrasound' defined in pf '%s'" % db2jsonpf)

    try:
        calibrations = pf.get('calibrations')
    except Exception, e:
        sys.exit("No 'calibrations' defined in pf '%s'" % db2jsonpf)

    try:
        dlevents = pf.get('dlevents')
    except Exception, e:
        sys.exit("No 'dlevents' defined in pf '%s'" % db2jsonpf)


    if verbose:

        log("Dbmaster path: '%s'" % dbmaster)
        for eachorb in orb:
            log("Orb path: '%s'" % eachorb)
        if auth_snet:
            log("Authoritative network: '%s'" % auth_snet)
        for p in orb_stations_select.strip('()').split('|'):
            log("\t%s" % p)

        log("Infrasound mapping:")
        log("\t%s" % infrasound_mapping)

        log("Other vars:")
        log("\t%s" % json_path)
        log("\t%s" % all_stations_json_file)
        log("\t%s" % dbmaster)
        log("\t%s" % q330comms)
        log("\t%s" % orb_stations_select)
        log("\t%s" % orbstat_alerts)
        log("\t%s" % infrasound_mapping)
        log("\t%s" % dbcalibrations)
        log("\t%s" % dbops_q330)
    
        for p in tables_to_check:
            log("\ttables_to_chekc: %s" % p)



    """
    Pull information from ORBS
    """
    orbstatus = defaultdict()
    myorb = ParseOrb(orbstat_alerts, verbose)

    for eachorb in orb:
        if verbose:
            log("Call orb_interaction for :'%s'" % eachorb)
        orbstatus.update(myorb.get_status(eachorb, orb_stations_select))



    """
    Pull information from DBS
    """
    database_existence_test(dbmaster)
    db = ParseDB(dbmaster, parseDbConfig, db_subset, verbose)

    if verbose:
        log("JSON file '%s'" % all_stations_json_file)

    if not force and not db.table_test(tables_to_check, all_stations_json_file):
        log("**** Database tables not updated since JSON files last created.")
        return 0

    log("Summary JSON file processing")

    #db.get_css_metadata()

    #log("Create deployment pointer")
    #db.create_deploy_pointer(db_subset)

    station_dict['decom'] = db.process_decom_stations('summary', adoptions)

    if adoptions:
        station_dict['adopt'] = db.process_adopted_stations('summary')

    station_dict['active'] = db.process_active_stations('summary')
    instrument_history = db.create_instrument_history(db_subset)

    if balers:
        baler_history = db.baler_history()

    if infrasound:
        infrasound_history = db.infrasound_sensors(infrasound_mapping)

    log("Decom stations: Add most recent instrument & baler history")
    for sta in sorted(station_dict['decom'].iterkeys()):

        dlsta = '%s_%s' % (station_dict['decom'][sta]['snet'], sta)

        if verbose:
            log("\tProcessing decom station: %s" % sta)

        if station_dict['decom'][sta]['snet'] == auth_snet:

            try:
                summary_instrument = db.summary_instrument_history(instrument_history[sta], sta)
            except LookupError,e:
                log("\tsummary_instrument_history(): LookupError: %s" % e)
            else:
                # More than one sensor allowed. Only one datalogger allowed
                station_dict['decom'][sta]['sensor'] = []
                station_dict['decom'][sta]['datalogger'] = {}
                if summary_instrument['sensor']:
                    for i in range(len(summary_instrument['sensor'][-1])):
                        station_dict['decom'][sta]['sensor'].append({
                            'value':summary_instrument['sensor'][-1][i]['model'], 
                            'css':summary_instrument['sensor'][-1][i]['css'],
                            'ssident':summary_instrument['sensor'][-1][i]['ssident']
                        })

                station_dict['decom'][sta]['datalogger']['value'] = summary_instrument['datalogger'][-1][-1]['model']
                station_dict['decom'][sta]['datalogger']['css'] = summary_instrument['datalogger'][-1][-1]['css']
                station_dict['decom'][sta]['datalogger']['idtag'] = summary_instrument['datalogger'][-1][-1]['idtag']

            if balers and dlsta in baler_history:
                station_dict['decom'][sta]['baler'] = baler_history[dlsta][-1]

            # Need this for most recent sensor in top right
            if infrasound and sta in infrasound_history:
                if 'current' in infrasound_history[sta]:
                    station_dict['decom'][sta]['infrasound'] = infrasound_history[sta]['current']
                else:
                    station_dict['decom'][sta]['infrasound'] = infrasound_history[sta]['history'][-1]
            else:
                station_dict['decom'][sta]['infrasound'] = 'unknown'

    log("Active stations: Add most recent instrument & baler history")
    for sta in sorted(station_dict['active'].iterkeys()):
        dlsta = '%s_%s' % (station_dict['active'][sta]['snet'], sta)

        if verbose:
            log("\tProcessing active station: %s" % sta)

        if sta in orbstatus:
            station_dict['active'][sta]['orbstat'] = orbstatus[sta]
            if verbose:
                log("\t\t%s found in orb" % sta)
        else:
            station_dict['active'][sta]['orbstat'] = {
                'latency':-1,
                'alert':'down',
                'status':0
            }
            log("\t\t**** %s NOT found in orb ****" % sta)

        if station_dict['active'][sta]['snet'] == auth_snet:

            summary_instrument = db.summary_instrument_history(instrument_history[sta], sta)

            # More than one sensor allowed. Only one datalogger allowed
            station_dict['active'][sta]['sensor'] = []
            station_dict['active'][sta]['datalogger'] = {}

            if summary_instrument['sensor'] :

                for i in range(len(summary_instrument['sensor'][-1])):
                    station_dict['active'][sta]['sensor'].append({
                        'value':summary_instrument['sensor'][-1][i]['model'], 
                        'css':summary_instrument['sensor'][-1][i]['css'],
                        'ssident':summary_instrument['sensor'][-1][i]['ssident']
                })

            if summary_instrument['datalogger'] :
                station_dict['active'][sta]['datalogger']['value'] = summary_instrument['datalogger'][-1][-1]['model']
                station_dict['active'][sta]['datalogger']['css'] = summary_instrument['datalogger'][-1][-1]['css']
                station_dict['active'][sta]['datalogger']['idtag'] = summary_instrument['datalogger'][-1][-1]['idtag']


            if infrasound and sta in infrasound_history:
                station_dict['active'][sta]['infrasound'] = infrasound_history[sta]['current']
            else:
                station_dict['active'][sta]['infrasound'] = 'unknown'

            if balers and dlsta in baler_history:
                station_dict['active'][sta]['baler'] = baler_history[dlsta][-1]
        else:
            station_dict['active'][sta]['infrasound'] = 'unknown'
            station_dict['active'][sta]['baler'] = 'unknown'

    if verbose:
        log("Dump summary JSON file for all stations")

    f = open(all_stations_json_file+'+', 'w') 

    json.dump(station_dict, f, sort_keys=True, indent=2)

    f.flush()

    log("\tCreate file: %s" % all_stations_json_file)

    try:
        os.rename(all_stations_json_file+'+', all_stations_json_file)
    except OSError,e:
        log("\tCannot rename summary JSON file. Error: %s-%s" % (OSError, e))

    if zipper:
        if verbose:
            log("\tCreate gzip file: %s.gz" % all_stations_json_file)
        make_zip_copy(all_stations_json_file)


    return 0


if __name__ == '__main__':
    status = main()
    sys.exit(status)
