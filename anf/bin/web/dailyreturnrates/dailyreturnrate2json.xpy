import json
from time import time
from optparse import OptionParser

from pprint import pprint

# For Antelope
from antelope.datascope import *
from antelope.stock import *

import pythondbcentral as dbcentral

from collections import defaultdict

verbose = False


def configure():
    """Parse command line arguments
    """
    usage = "Usage: %prog [options]"
    parser = OptionParser(usage=usage)
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose", 
                      help="verbose output", default=False)
    parser.add_option("-n", "--network", action="store", dest="network_override", 
                      help="network override", default=False)
    (options, args) = parser.parse_args()

    snets = False

    if options.verbose:
        global verbose
        verbose = True

    if options.network_override:
        snets = options.network_override

    return snets

def parse_pf():
    """Parse parameter file
    """
    parsed_pf = {}

    #pf = pfupdate( 'stations.pf' )
    pf = pfupdate( '/anf/web/vhosts/anf.ucsd.edu/conf/stations.pf' )

    parsed_pf['pf_snets'] = pf['network']
    parsed_pf['pf_colors'] = pf['colors']
    logfmt(" - pf_snets %s" % parsed_pf['pf_snets'])
    logfmt(" - pf_colors %s" % parsed_pf['pf_colors'])

    #pf = pfupdate( 'common.pf' )
    pf = pfupdate( '/anf/web/vhosts/anf.ucsd.edu/conf/common.pf' )
    parsed_pf['dbcentral'] = pf['DBCENTRAL']
    parsed_pf['jsonpath'] = pf['CACHEJSON']
    parsed_pf['webroot'] = pf['WEBROOT']
    logfmt(" - dbcentral %s" % parsed_pf['dbcentral'])
    logfmt(" - jsonpath %s" % parsed_pf['jsonpath'])
    logfmt(" - webroot %s" % parsed_pf['webroot'])

    return parsed_pf

def logfmt(message):
    """Output a log message with a timestamp"""
    global verbose
    if verbose: print "%s: %s" % ( strtime(time() ), message)

def getmetadata():
    """Return metadata
    """
    metadata = {}
    metadata['modification_time'] = int(time())
    metadata['modification_time_readable'] = epoch2str(int(time()), "%H:%M UTC %A %B %o, %Y")
    return metadata

def getsnets(dblist):
    """Determine all
    the networks returning
    data"""
    snets_all = []
    for dbpath in dblist:
        logfmt(" - open database %s" % dbpath)
        perf_ptr = dbopen(dbpath, 'r')
        perf_ptr = perf_ptr.lookup(table='netperf')
        perf_ptr = perf_ptr.sort('snet', unique=True)
        for j in range(perf_ptr.record_count):
            perf_ptr.record = j
            snets_all.append(perf_ptr.getv('snet')[0])
    perf_ptr.free()
    perf_ptr.close()
    snets = sorted(list(set(snets_all)))
    return snets

def getperformance(dblist, snets):
    """Get the performance
    metrics for the networks
    """
    final_performance = defaultdict(dict)
    performance = defaultdict(list)
    logfmt(" - Iterate over databases")
    for i, dbpath in enumerate(dblist):
        logfmt(" - open database %s" % dbpath)
        sperf = dbopen(dbpath, 'r')
        sperf = sperf.lookup(table='netperf')
        sperf = sperf.sort('time')
        for s in snets:
            logfmt("  - Working on performance for %s (%s)" % (s, dbpath))
            try:
                mysnet = sperf.subset('snet=~/%s/' % s)
            except ValueError,e:
                print "%s:%s" % (mysnet, e)
            else:
                data_list = []
                for mys in range(mysnet.record_count):
                    mysnet.record = mys
                    snet, time, npsta, perf = mysnet.getv('snet', 'time', 'npsta', 'perf')
                    readable_time = epoch2str(int(time), "%Y-%m-%d")
                    data_list.append({'time':time, 'readable_time':readable_time, 'value':perf, 'nsta':npsta})
                performance[s].append(data_list)
            mysnet.free()
        sperf.free()

    for s in performance:
        logfmt(" - Concatenate performance lists for %s to generate final performance metrics" % s)
        final_list = []
        for mylist in performance[s]:
            final_list += mylist
        final_performance[s] = final_list

    return final_performance

def calcstats(performance_data):
    """Calculate some stats
    from the performance data
    """
    logfmt("Calculate statistics")
    stats = {
        'average': 0,
        'median':0,
        'all_days':0,
        'perfect_days':0,
        'longest_perfect_period':0
    }
    just_the_data = [i['value'] for i in performance_data]
    logfmt(" - Length of data: %s" % len(just_the_data))
    stats['average'] = round(float(sum(just_the_data))/len(just_the_data))

    if len(just_the_data) % 2 == 0:
        median = []
        median.append(sorted(just_the_data)[len(just_the_data)/2])
        median.append(sorted(just_the_data)[len(just_the_data)/2 + 1])
        stats['median'] = round(float(sum(median))/len(median))
    else:
        stats['median'] = round(sorted(just_the_data)[len(just_the_data)/2])

    longest_perfect = []
    one_hundred = 0

    for i in performance_data:
        if i['value'] == 100:
            one_hundred += 1
        else:
            longest_perfect.append(one_hundred)
            one_hundred = 0

    # Possible to get 100% days for whole period
    if len(longest_perfect) == 0:
        stats['longest_perfect_period'] = one_hundred
    else:
        stats['longest_perfect_period'] = max(longest_perfect)

    stats['perfect_days'] = just_the_data.count(100)
    stats['all_days'] = len(just_the_data)
    return stats

def dumpjson(mydict, jsonfile):
    """Dump dictionary to
    json"""
    f = open(jsonfile+'+', 'w')
    try:
        json.dump(mydict, f, sort_keys=True, indent=2)
    except Exception, e:
        logfmt("JSON dump() error")
    else:
        f.flush()

    try:
        os.rename(jsonfile+'+', jsonfile)
    except OSError,e:
        logfmt("Error: Renaming JSON file (%s) failed: %s-%s" % (jsonfile, OSError, e))

""" Main functionality """
snet = configure()
pfvars = parse_pf()

logfmt("Determine dbpaths using dbcentral")

logfmt("For 'usarray_perf'")

dbc_rt = dbcentral.DbCentral(pfvars['dbcentral'], 'usarray_perf')
db_rt_perf_path = dbc_rt.namelist()

logfmt("For 'usarray_perf_archive'")

dbc_archive = dbcentral.DbCentral(pfvars['dbcentral'], 'usarray_perf_archive')
db_perf_paths = dbc_archive.namelist()
#db_perf_paths.append(db_rt_perf_path)

logfmt("Get all snets")

snets = getsnets(db_perf_paths)

logfmt("Get performance metrics")

performance = getperformance(db_perf_paths, snets)
metadata = getmetadata()

json_dir = '%s/tools/data_return_rates' % pfvars['jsonpath']

files = {}
for s in snets:
    per_snet_stats = calcstats(performance[s])
    snet_meta = pfvars['pf_snets'][s]
    color = pfvars['pf_colors'][snet_meta['color']]['hexidecimal']
    this_snet_json = {'data':performance[s], 
                        'snetmeta':pfvars['pf_snets'][s], 
                        'color':color,
                        'stats':per_snet_stats}
    json_file = '%s/%s.json' % (json_dir, s)
    files[s] = json_file.replace(pfvars['webroot'], '')
    logfmt("Dump JSON to file '%s'" % json_file)
    dumpjson(this_snet_json, json_file)

json_obj = {'metadata':metadata, 'files':files}
json_file = '%s/usarray.json' % json_dir
logfmt("Dump JSON to file '%s'" % json_file)
dumpjson(json_obj, json_file)
