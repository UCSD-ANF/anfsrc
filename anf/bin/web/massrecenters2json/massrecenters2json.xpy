
"""
Network-wide mass recenters to JSON run via cron daily
"""

import sys
import os
import json
import gzip
import string
import tempfile
from optparse import OptionParser
from collections import defaultdict
from pprint import pprint
from time import time, mktime
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Load datascope functions
import antelope.datascope as datascope
from antelope.stock import pfupdate, pfget, strtime, epoch2str, str2epoch

# {{{ General vars
common_pf = 'common.pf'
pfupdate(common_pf)
cache_json = pfget(common_pf, 'CACHEJSON')
massrecenters_scale = pfget(common_pf, 'MASSRECENTERS_SCALE')
massrecenters_arr = pfget(common_pf, 'MASSRECENTERS_ARR')
massrecenters_periods = pfget(common_pf, 'MASSRECENTERS_PERIODS')
massrecenters_periods_scale = pfget(common_pf, 'MASSRECENTERS_PERIODS_SCALE')

json_path = '%s/tools' % cache_json
dbmaster = pfget(common_pf, 'USARRAY_DBMASTER')
cache_file_path  = '%s/massrecenters/mrs.json' % json_path
output_file_path = '%s+' % cache_file_path
# }}}

def logfmt(message):
    """Output a log
    message with a
    timestamp"""
    # {{{ logfmt
    curtime = strtime(time())
    print curtime, message
    # }}}

def configure():
    """Parse command
    line args
    """
    # {{{ configure
    usage = "Usage: %prog [options]"
    parser = OptionParser(usage=usage)
    parser.add_option("-v", action="store_true", dest="verbose",
        help="verbose output", default=False)
    parser.add_option("-x", action="store_true", dest="debug",
        help="debug output", default=False)
    (options, args) = parser.parse_args()
    if options.verbose:
        verbose = True
    else:
        verbose = False
    if options.debug:
        debug = True
    else:
        debug = False
    return verbose, debug
    # }}}

def get_sta_dict(verbosity=False):
    """Get station and
    null fields dictionaries
    """
    # {{{ get_sta_dict
    if verbosity > 0:
        logfmt('Create the stations dictionary')
    stations = defaultdict(dict)
    nulls = defaultdict(dict)

    db = datascope.dbopen(dbmaster, 'r')
    db.lookup(table='deployment')
    db.join('site', outer=True)

    for tblfield in db.query('dbTABLE_FIELDS'):
        db.lookup(field=tblfield, record='dbNULL')
        nulls[tblfield] = db.getv(tblfield)[0]

    db.subset('snet =~ /TA/')

    for i in range(db.query('dbRECORD_COUNT')):
         db[3] = i
         (snet,
          sta,
          time,
          endtime,
          lat,
          lon,
          elev,
          staname) = db.getv('snet',
                             'sta',
                             'time',
                             'endtime',
                             'lat',
                             'lon',
                             'elev',
                             'staname')
         dlname = '%s_%s' % (snet, sta)
         stations[dlname]['time'] = epoch2str(time, '%Y-%m-%d %H:%M:%D')
         stations[dlname]['endtime'] = endtime
         if endtime == nulls['endtime']:
             stations[dlname]['endtime_readable'] = '&mdash;'
             stations[dlname]['status'] = 'online'
         else:
             stations[dlname]['endtime_readable'] = epoch2str(endtime, '%Y-%m-%d %H:%M:%S') 
             stations[dlname]['status'] = 'offline'
         stations[dlname]['lat'] = lat
         stations[dlname]['lon'] = lon
         stations[dlname]['elev'] = elev
         stations[dlname]['staname'] = staname

    if verbosity > 1:
        pprint(stations)
    return stations, nulls
    # }}}

def get_dlname_events(verbosity=False):
    """Get all mass recenter
    events associated with
    a dlname"""
    # {{{ get_dlname_events
    if verbosity > 0:
        logfmt('Generate the dlevents dictionary')
    dlevents = defaultdict(list)
    dlev_db = datascope.dbopen(dbmaster, 'r')
    dlev_db.lookup(table='dlevent')
    dlev_db.subset('dlevtype =~ /^massrecenter.*/')
    dlev_db.sort(('dlname','time'))
    dlev_grp = datascope.dbgroup(dlev_db, 'dlname')
    for i in range(dlev_grp.query('dbRECORD_COUNT')):
        dlev_grp[3] = i
        (dlname, [db,
                  view,
                  end_rec,
                  start_rec]) = dlev_grp.getv('dlname',
                                              'bundle')
        for j in range(start_rec, end_rec):
            dlev_db[3] = j
            (dlname, time) = dlev_db.getv('dlname', 'time')
            dlevents[dlname].append(int(time))
    if verbosity > 1:
        logfmt('Historical massrecenters:')
        pprint(dlevents)
    return dlevents
    # }}}

def process_dlevents(stations, dlevents, nulls, verbosity=False):
    """Iterate over stations
    and append all the mass
    recenters
    """
    # {{{ process_dlevents
    if verbosity > 0:
        logfmt('Add dlevents to the stations dictionary')
    for i in sorted(stations.iterkeys()):
        if i in dlevents:
            stations[i].update(dlevs=dlevents[i])
            chron_color = chronology_color_calc(dlevents[i], i, stations[i], nulls, verbosity)
            stations[i].update(dlevs_chronology=chron_color)
            total = len(dlevents[i])
        else:
            if verbosity > 1:
                logfmt('\t\tStation %s: no massrecenters' % i)
            stations[i].update(dlevs=[])
            stations[i].update(dlevs_chronology="FFFFFF")
            total = 0
        stations[i].update(dlevstotal=total)

        # Scale color
        for j in massrecenters_scale:
            if massrecenters_arr[j]['max'] == -1:
                maximum = 99999999
            else:
                maximum = massrecenters_arr[j]['max']
            if massrecenters_arr[j]['min'] == -1:
                if total == maximum:
                    color = massrecenters_arr[j]['hexadecimal']
            else:
                if total <= maximum and total >= massrecenters_arr[j]['min']:
                    color = massrecenters_arr[j]['hexadecimal']
        if color:
            stations[i].update(dlevscolor=color)
        else:
            logfmt('\tNo color for dlname %s' % stations[i])

    if verbosity > 1:
        logfmt('\tPretty print for dlname TA_034A for debugging:')
        pprint(stations['TA_034A'])

    return stations
    # }}}

def chronology_color_calc(per_sta_dlevents,
                          stacode=False,
                          station_info=False,
                          nulls=False,
                          verbosity=False):
    """Calculate the hexadecimal
    of the most recent mass recenter
    at this station"""
    # {{{ chronology_color_calc
    if station_info['endtime'] == nulls['endtime']:
        if verbosity > 1:
            print "Station '%s' is online" % stacode
        stanow = datetime.now()
    else:
        if verbosity > 1:
            print "Station '%s' is offline" % stacode
        stanow = datetime.fromtimestamp(station_info['endtime'])

    # {{{ Calc times for offline stations
    six_hrs = stanow + relativedelta(hours=-6)
    twelve_hrs = stanow + relativedelta(days=-12)
    day = stanow + relativedelta(days=-1)
    week = stanow + relativedelta(weeks=-1)
    month = stanow + relativedelta(months=-1)
    six_months = stanow + relativedelta(months=-6)
    one_year = stanow + relativedelta(years=-1)
    two_year = stanow + relativedelta(years=-2)
    three_year = stanow + relativedelta(years=-3)
    three_year_plus = stanow + relativedelta(years=-20) # Twenty years default
    # }}}

    # {{{ Periods
    periods = {
        'six_hrs': {
            'epoch':mktime(six_hrs.timetuple()),
            'hexadecimal': massrecenters_periods['six_hrs']['hexadecimal']
        },
        'twelve_hrs': {
            'epoch': mktime(twelve_hrs.timetuple()),
            'hexadecimal': massrecenters_periods['twelve_hrs']['hexadecimal']
        },
        'day': {
            'epoch': mktime(day.timetuple()),
            'hexadecimal': massrecenters_periods['day']['hexadecimal']
        },
        'week': {
            'epoch': mktime(week.timetuple()),
            'hexadecimal': massrecenters_periods['week']['hexadecimal']
        },
        'month': {
            'epoch': mktime(month.timetuple()),
            'hexadecimal': massrecenters_periods['month']['hexadecimal']
        },
        'six_months': {
            'epoch': mktime(six_months.timetuple()),
            'hexadecimal': massrecenters_periods['six_months']['hexadecimal']
        },
        'year': {
            'epoch': mktime(one_year.timetuple()),
            'hexadecimal': massrecenters_periods['year']['hexadecimal']
        },
        'two_year': {
            'epoch': mktime(two_year.timetuple()),
            'hexadecimal': massrecenters_periods['two_year']['hexadecimal']
        },
        'three_year': {
            'epoch': mktime(three_year.timetuple()),
            'hexadecimal': massrecenters_periods['three_year']['hexadecimal']
        },
        'three_year_plus': {
            'epoch': mktime(three_year_plus.timetuple()),
            'hexadecimal': massrecenters_periods['three_year_plus']['hexadecimal']
        }
    }
    # }}}

    if len(per_sta_dlevents) > 0:
        for p in massrecenters_periods_scale:
            if per_sta_dlevents[-1] > periods[p]['epoch']:
                hexadecimal = periods[p]['hexadecimal']
                break
    else:
        hexadecimal = massrecenters_periods['never']['hexadecimal']

    return hexadecimal
    # }}}

def create_scale(verbosity):
    """Create scale
    dictionary
    """
    # {{{ create_scale
    scale = []
    for i in massrecenters_scale:
        scale.append(massrecenters_arr[i])

    if verbosity > 1:
        pprint(scale)

    return scale
    # }}}

def create_chronology_scale(verbosity):
    """Create chronology
    scale dictionary
    """
    # {{{ create_scale
    chron_scale = []
    for i in massrecenters_periods_scale:
        chron_scale.append({'value': massrecenters_periods[i]['value'], 'hexadecimal':massrecenters_periods[i]['hexadecimal']})
    chron_scale.append({'value': massrecenters_periods['never']['value'], 'hexadecimal':massrecenters_periods['never']['hexadecimal']})
    if verbosity > 1:
        pprint(chron_scale)

    return chron_scale
    # }}}

def create_metadata(verbosity):
    """Create metadata
    dictionary
    """
    # {{{ create_metadata
    metadata = defaultdict(dict)
    metadata['last_modified_readable'] = epoch2str(int(time()), "%Y-%m-%d %H:%M:%S")
    metadata['last_modified'] = int(time())
    metadata['caption'] = 'Total number of mass recenters'
    metadata['caption_alt'] = 'Most recent mass recenter time'

    if verbosity > 1:
        pprint(metadata)

    return metadata
    # }}}

def main():
    """Process photo
    directory contents
    """
    logfmt('Process network-wide mass recenters')
    verbosity = 0
    verbose, debug = configure()
    if verbose:
        verbosity += 1
    if debug:
        verbosity += 2
    stations, nulls = get_sta_dict(verbosity)
    dlevents = get_dlname_events(verbosity)

    per_sta_dlevents = defaultdict(dict)

    per_sta_dlevents['stations'] = process_dlevents(stations,
                                                    dlevents,
                                                    nulls,
                                                    verbosity)

    scale = create_scale(verbosity)
    per_sta_dlevents.update(scale=scale)

    chron_scale = create_chronology_scale(verbosity)
    per_sta_dlevents.update(chron_scale=chron_scale)

    metadata = create_metadata(verbosity)
    per_sta_dlevents.update(metadata=metadata)

    logfmt("Dump JSON file '%s'" % cache_file_path)
    f = open(output_file_path, 'w')
    json.dump(per_sta_dlevents, f, sort_keys=True, indent=2)
    f.flush()

    # Move the file to replace the older one
    try:
        os.rename(output_file_path, cache_file_path)
    except OSError,e:
        logfmt("OSError: %s when renaming '%s' to '%s'" % (e, output_file_path, cache_file_path))

    return 0

if __name__ == '__main__':
    status = main()
    sys.exit(status)
