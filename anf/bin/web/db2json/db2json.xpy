"""
Antelope Datascope output to JSON files


Global summary & individual stations


Only have dbpointers open for a short while - Datascope 
does not like realtime dbs being open when edits 
can happen (dbpointers all become invalid and the script crashes).

Datascope does not correctly free up memory. Triage this by 
forcing memory cleanup with datascope.dbfree() and 
datascope.dbclose(). 

Polaris, Canada (snet PO) stations only have HH.* channels.
This means some additional exceptions code to account for 
this (we don't want to include BK or CI stations that 
use HH.* channels) Create and use a parameter 
file (db2json.pf) that has the specific network and 
channel subsets to account for multiple networks 
(look for 'db_subset' in code).
Account for stations that have more than one sensor
installed, such as an STS-2 (broadband) and Episensor
(strong-motion).

Author:     Rob Newman
Maintainer: Juan Reyes <reyes@ucsd.edu>
Date:       10/2013
Status:     Production

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
    from db2json.global_variables import *
except Exception,e:
    sys.exit("Problem loading global_variables.py file. %s(%s)\n" % (Exception,e) )


try:
    from db2json.parseorb import ParseOrb
except Exception,e:
    sys.exit("Problem loading ParseOrb module. %s(%s)\n" % (Exception,e) )


try:
    from db2json.parsedb import ParseDB
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

    #station_dict['decom'] = db.process_decom_stations('summary', adoptions)

    #if adoptions:
    #    station_dict['adopt'] = db.process_adopted_stations('summary')

    #station_dict['active'] = db.process_active_stations('summary')
    #instrument_history = db.create_instrument_history(db_subset)

    #if balers:
    #    baler_history = db.baler_history()

    #if infrasound:
    #    infrasound_history = db.infrasound_sensors(infrasound_mapping)

    #log("Decom stations: Add most recent instrument & baler history")
    #for sta in sorted(station_dict['decom'].iterkeys()):

    #    dlsta = '%s_%s' % (station_dict['decom'][sta]['snet'], sta)

    #    if verbose:
    #        log("\tProcessing decom station: %s" % sta)

    #    if station_dict['decom'][sta]['snet'] == auth_snet:

    #        try:
    #            summary_instrument = db.summary_instrument_history(instrument_history[sta], sta)
    #        except LookupError,e:
    #            log("\tsummary_instrument_history(): LookupError: %s" % e)
    #        else:
    #            # More than one sensor allowed. Only one datalogger allowed
    #            station_dict['decom'][sta]['sensor'] = []
    #            station_dict['decom'][sta]['datalogger'] = {}
    #            for i in range(len(summary_instrument['sensor'][-1])):
    #                station_dict['decom'][sta]['sensor'].append({
    #                    'value':summary_instrument['sensor'][-1][i]['model'], 
    #                    'css':summary_instrument['sensor'][-1][i]['css'],
    #                    'ssident':summary_instrument['sensor'][-1][i]['ssident']
    #                })

    #            station_dict['decom'][sta]['datalogger']['value'] = summary_instrument['datalogger'][-1][-1]['model']
    #            station_dict['decom'][sta]['datalogger']['css'] = summary_instrument['datalogger'][-1][-1]['css']
    #            station_dict['decom'][sta]['datalogger']['idtag'] = summary_instrument['datalogger'][-1][-1]['idtag']

    #        if balers and dlsta in baler_history:
    #            station_dict['decom'][sta]['baler'] = baler_history[dlsta][-1]

    #        # Need this for most recent sensor in top right
    #        if infrasound and sta in infrasound_history:
    #            if 'current' in infrasound_history[sta]:
    #                station_dict['decom'][sta]['infrasound'] = infrasound_history[sta]['current']
    #            else:
    #                station_dict['decom'][sta]['infrasound'] = infrasound_history[sta]['history'][-1]
    #        else:
    #            station_dict['decom'][sta]['infrasound'] = 'unknown'

    #log("Active stations: Add most recent instrument & baler history")
    #for sta in sorted(station_dict['active'].iterkeys()):
    #    dlsta = '%s_%s' % (station_dict['active'][sta]['snet'], sta)

    #    if verbose:
    #        log("\tProcessing active station: %s" % sta)

    #    if sta in orbstatus:
    #        station_dict['active'][sta]['orbstat'] = orbstatus[sta]
    #        if verbose:
    #            log("\t\t%s found in orb" % sta)
    #    else:
    #        station_dict['active'][sta]['orbstat'] = {
    #            'latency':-1,
    #            'alert':'down',
    #            'status':0
    #        }
    #        log("\t\t**** %s NOT found in orb ****" % sta)

    #    if station_dict['active'][sta]['snet'] == auth_snet:

    #        summary_instrument = db.summary_instrument_history(instrument_history[sta], sta)

    #        # More than one sensor allowed. Only one datalogger allowed
    #        station_dict['active'][sta]['sensor'] = []
    #        station_dict['active'][sta]['datalogger'] = {}

    #        for i in range(len(summary_instrument['sensor'][-1])):
    #            station_dict['active'][sta]['sensor'].append({
    #                'value':summary_instrument['sensor'][-1][i]['model'], 
    #                'css':summary_instrument['sensor'][-1][i]['css'],
    #                'ssident':summary_instrument['sensor'][-1][i]['ssident']
    #        })

    #        station_dict['active'][sta]['datalogger']['value'] = summary_instrument['datalogger'][-1][-1]['model']
    #        station_dict['active'][sta]['datalogger']['css'] = summary_instrument['datalogger'][-1][-1]['css']
    #        station_dict['active'][sta]['datalogger']['idtag'] = summary_instrument['datalogger'][-1][-1]['idtag']

    #        if infrasound and sta in infrasound_history:
    #            station_dict['active'][sta]['infrasound'] = infrasound_history[sta]['current']
    #        else:
    #            station_dict['active'][sta]['infrasound'] = 'unknown'

    #        if balers and dlsta in baler_history:
    #            station_dict['active'][sta]['baler'] = baler_history[dlsta][-1]
    #    else:
    #        station_dict['active'][sta]['infrasound'] = 'unknown'
    #        station_dict['active'][sta]['baler'] = 'unknown'

    #if verbose:
    #    log("Dump summary JSON file for all stations")

    #f = open(all_stations_json_file+'+', 'w') 

    #json.dump(station_dict, f, sort_keys=True, indent=2)

    #f.flush()

    #try:
    #    os.rename(all_stations_json_file+'+', all_stations_json_file)
    #except OSError,e:
    #    log("\tCannot rename summary JSON file. Error: %s-%s" % (OSError, e))

    #if zipper:
    #    if verbose:
    #        log("\tCreate gzip file: %s.gz" % all_stations_json_file)
    #    make_zip_copy(all_stations_json_file)


    log("Create per station data objects")

    # Create list of the station types to process in detail


    #db.free()
    #db = ParseDB(dbmaster, parseDbConfig, verbose)
    #db.open()
    #persta = db
    #db.get_metadata()
    #db.create_deploy_pointer(db_subset)


    instrument_history = db.create_instrument_history()
    baler_history = db.baler_history()

    infrasound_history = db.infrasound_sensors(infrasound_mapping)

    if calibrations:
        calibration_history = db.calibration_history(dbcalibrations)

    if dlevents:
        dlevents_history = db.dlevents_history(dbops_q330)

    comms_history = db.comms_history()

    #db.create_deploy_pointer(db_subset)
    deployment_history = db.deployment_history()

    log("Start to create individual station JSON files")
    # Process each station type

    if not subtype or subtype == 'all':
        my_station_types = ['decom', 'adopt', 'active']
    else:
        my_station_types = [subtype]

    for sta_type in my_station_types:
        log("Start working on '%s' stations" % sta_type)
        if sta_type == 'decom':
            sta_type_dict = db.process_decom_stations('detail')
        elif sta_type == 'adopt' and adoptions:
            sta_type_dict = db.process_adopted_stations('detail')
        elif sta_type == 'active':
            sta_type_dict = db.process_active_stations('detail')

        for sta in sorted(sta_type_dict.iterkeys()):
            dlsta = '%s_%s' % (sta_type_dict[sta]['snet'], sta)
            sta_dict = defaultdict(lambda: defaultdict(dict))
            '''
            sta_dict = {
                "baler_history": {}, 
                "calibration_history": {}, 
                "comms_history": {}, 
                "dlevents": {}, 
                "infrasound_history": {},
                "instrument_history": {}, 
                "metadata": {}
            }
            '''

            if verbose:
                log("\tProcessing station detail for %s" % sta)
                log("\tMap stype_dict[%s] to this_sta_dict['metadata']" % sta)
                log("\tCurrent instrumentation processing")

            sta_dict['metadata'] = sta_type_dict[sta]

            summary_instrument = db.summary_instrument_history(instrument_history[sta], sta)


            if summary_instrument and 'sensor' in summary_instrument and 'datalogger' in summary_instrument:
                sta_dict['metadata']['sensor'] = []
                sta_dict['metadata']['datalogger'] = {}

                if len(summary_instrument['sensor']) > 0:
                    for i in range(len(summary_instrument['sensor'][-1])):
                        sta_dict['metadata']['sensor'].append({
                            'value':summary_instrument['sensor'][-1][i]['model'], 
                            'css':summary_instrument['sensor'][-1][i]['css'],
                            'ssident':summary_instrument['sensor'][-1][i]['ssident']
                    })

                if len(summary_instrument['datalogger']) > 0:
                    sta_dict['metadata']['datalogger']['value'] = summary_instrument['datalogger'][-1][-1]['model']
                    sta_dict['metadata']['datalogger']['css'] = summary_instrument['datalogger'][-1][-1]['css']
                    sta_dict['metadata']['datalogger']['idtag'] = summary_instrument['datalogger'][-1][-1]['idtag']
            else:
                log("\tError: summary_instrument() failed")
                pprint(summary_instrument)

            if sta_dict['metadata']['snet'] == auth_snet:

                if infrasound and sta in infrasound_history:
                    sta_dict['infrasound_history'] = infrasound_history[sta]['history']

                if balers and dlsta in baler_history:
                    sta_dict['baler_history'] = baler_history[dlsta]

                if sta in instrument_history:
                    sta_dict['instrument_history'] = instrument_history[sta]

                if calibrations and sta in calibration_history:
                    sta_dict['calibration_history'] = calibration_history[sta]

                if dlevents and dlsta in dlevents_history:
                    sta_dict['dlevents'] = dlevents_history[dlsta]

            if sta in comms_history:
                sta_dict['comms_history'] = comms_history[sta]

            if sta in deployment_history:
                sta_dict['deployment_history'] = deployment_history[sta]

            if verbose:
                log("\tSaving per station JSON file")
            sta_file = '%s/%s_%s.json' % (json_path, sta_dict['metadata']['snet'], sta)
            sta_file_pre = '%s+' % sta_file
            fs = open(sta_file_pre, 'w') 

            json.dump(sta_dict, fs, sort_keys=True, indent=2)

            fs.flush()

            try:
                os.rename(sta_file_pre, sta_file)
            except OSError,e:
                log("\tRenaming JSON file to %s failed: Error: %s-%s" % (sta_file, OSError, e))
    return 0


if __name__ == '__main__':
    status = main()
    sys.exit(status)
