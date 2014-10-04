'''
Datascope output to JSON run via cron every 5 mins
without the need of a database. We don't have a dbmaster
for GLISN so this will run out a the orb and a hardcoded
JSON file with locations.

'''

import json
import string
import tempfile
from pprint import pprint
from time import time, gmtime, strftime

# Load datascope functions
import antelope.datascope as datascope
import antelope.orb as orb
import antelope.stock as stock
from optparse import OptionParser

# Get command line arguments
usage = "Usage: %prog [options]"
parser = OptionParser(usage=usage)
parser.add_option("-p", action="store", dest="pf", help="parameter file", default='orb2json.pf')
parser.add_option("-v", action="store_true", dest="verbose", help="verbose output", default=False)
(options, args) = parser.parse_args()

if options.verbose:
    verbose = True

#try:
#    orbserver = args[0]
#    stations = args[1]
#except:
#    parser.print_help()
#    sys.exit('\nMissing argument(s)\n')
#
#os.path.isfile(stations) or sys.exit('\nNo valid JSON file\n')

def orbstat_alert_level(secs, alerts=False):
    """
    Determine the alert level
    """
    if secs >= int(alerts['offline']):
        return 'down', 0
    elif secs >= int(alerts['warning']):
        return 'warning', 1
    else:
        return 'ok', 1

def humanize_time(secs):
    """
    Create human readable timestamp
    """
    return stock.strtdelta(secs)

def add_orbstat(orbstat, sta, qtype=False):
    """
    Return station specific orbstat values
    """
    orbstat_dict = {}
    if sta in orbstat:
        orbstat_dict['latency'] = orbstat[sta]['latency']
        orbstat_dict['latency_readable'] = humanize_time(orbstat[sta]['latency'])
        orbstat_dict['alert'] = orbstat[sta]['alert']
        orbstat_dict['status'] = orbstat[sta]['offon']
        orbstat_dict['slatest_time'] = orbstat[sta]['slatest_time']
        orbstat_dict['soldest_time'] = orbstat[sta]['soldest_time']
    else:
        orbstat_dict['latency'] = -1
        orbstat_dict['alert'] = 'down'
        orbstat_dict['status'] = 0
    return orbstat_dict

def parse_orb_sources(sources, alerts=False):
    """Parse the sources
    and return a dictionary
    """
    source_dict = {}
    for s in sources:
        srcname = s['srcname']

        try:
            parts = srcname.split('/')
            snet_sta = parts[0].split('_')
            snet = snet_sta[0]
            sta = snet_sta[1]
        except:
            continue

        if options.verbose:
            print " - Parse orb sorce: %s" % srcname
            print " - %s => %s %s" % (srcname,snet,sta)

        latency = time() - s['slatest_time']
        alert, off_on = orbstat_alert_level(latency, alerts)
        source_dict[sta] = {}
        source_dict[sta]['latency'] = latency
        source_dict[sta]['latency_readable'] = humanize_time(latency)
        source_dict[sta]['snet'] = snet
        source_dict[sta]['alert'] = alert
        source_dict[sta]['offon'] = off_on
        #source_dict[sta]['soldest_time'] = stock.epoch2str(s['soldest_time'], "%Y-%m-%d %H:%M:%S")
        #source_dict[sta]['slatest_time'] = stock.epoch2str(s['slatest_time'], "%Y-%m-%d %H:%M:%S")
        source_dict[sta]['soldest_time'] = s['soldest_time']
        source_dict[sta]['slatest_time'] = s['slatest_time']

    return source_dict
 
def orb_interaction(orbname, selection_string='.*', alerts=False):
    """Open & select orb
    """
    if options.verbose:
        print " - Connect to orbserver (%s)" % orbname

    try:
        myorb = orb.orbopen(orbname,'r')
    except Exception, e:
        print "\nCannot open the orb %s. Caught exception: (%s)\n" % (orbname, e)
        sys.exit()

    if myorb.select(selection_string) < 1:
        print "  - Problem with the orb select functionality!"
    else:
        if options.verbose:
            print "  - Number of sources selected: %d" % myorb.select(selection_string)
        when, sources = myorb.sources()
        orb_dict = parse_orb_sources(sources, alerts)

    myorb.close()

    return orb_dict
 
def main():
    """Main processing script
    for the JSON file
    """
    orb_dict = {}

    try:
        pf = stock.pfread(options.pf)
    except:
        sys.exit('Problems looking PF: %s' % options.pf)

    json_cache = pf['json_cache']
    stations_json = pf['stations_json']

    orbserver = pf['orb']

    orb_select = pf['orb_select']

    orbstat_alerts = pf['orbstat_alerts']
    warning_time = orbstat_alerts['warning']
    offline_time = orbstat_alerts['offline']

    if options.verbose:
        print "- Opening up orb (%s)" % orbserver

    orbstatus = {}
    for orbname in orbserver:
        orbstatus.update( orb_interaction(orbname, orb_select, orbstat_alerts) )

    if options.verbose:
        pprint(orbstatus)


    if stations_json:
        if not os.path.isfile(stations_json):
            sys.exit('\nCannot read STATIONS_JSON file: [%s]\n' %
                    stations_json)

        with open( stations_json ) as data_file:
            station_data = json.load(data_file)

        if options.verbose:
            pprint(station_data)

        for station in station_data:
            if station in orbstatus:
                orbstatus[station].update(station_data[station])
            else:
                orbstatus[station] = station_data[station]
                orbstatus[station]['latency'] = '-none-'
                orbstatus[station]['latency_readable'] ='-none-'
                orbstatus[station]['alert'] = 0
                orbstatus[station]['offon'] = 'down'
                orbstatus[station]['soldest_time'] = '-none-'
                orbstatus[station]['slatest_time'] = '-none-'


    if options.verbose:
        print ' - Last object:'
        pprint(orbstatus)

    if options.verbose:
        print "- Save JSON file %s" % json_cache

    f = open(json_cache, 'w') 
    json.dump(orbstatus, f, sort_keys=True)
    f.flush()

if __name__ == '__main__':
    main()
