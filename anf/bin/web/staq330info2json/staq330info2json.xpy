'''
Datascope output to JSON run via cron every 5 mins
'''

import json
# import gzip
from time import *

# Load datascope functions
from  antelope.datascope import *
from antelope.stock import pfupdate, strtime, epoch2str
from time import time
from pprint import pprint

from optparse import OptionParser

def logfmt(message):
    """Output a log
    message with a
    timestamp"""
    curtime = strtime(time())
    print curtime, message

def initial_q330_reboot_state(dbptr, verbose=False):
    """Return a dict
    of initial reboot
    history of a q330
    """
    q330_history = {}
    db_q330_history = dbptr.lookup(table='staq330')
    # Get rid of bad records (they have time set to 0.0)
    db_q330_history = db_q330_history.subset('time > 1')
    db_q330_history = db_q330_history.sort(('ssident', 'time'))
    db_q330_history_grp = db_q330_history.group('ssident')

    for i in range(db_q330_history_grp.record_count):
        db_q330_history_grp.record = i
        ssident, [this_db, this_view, this_end_rec, this_start_rec] = db_q330_history_grp.getv('ssident', 'bundle')
        db_q330_history.record = this_start_rec
        ssident, time, nreboot = db_q330_history.getv('ssident', 'time', 'nreboot')
        if verbose:
            logfmt('ssident: %s, time: %s, nreboot:%s' % (ssident, time, nreboot))
        q330_history[ssident] = nreboot
    return q330_history 

def calc_this_station_reboots(dlsta, dlsta_dict, q330_history, verbose=False):
    """Calculate how many reboots this
    station has had since the q330 was
    installed """
    this_q330 = dlsta_dict['ssident']
    initial_reboots = q330_history[this_q330]
    current_reboots = dlsta_dict['nreboot']
    this_dlsta_reboots = current_reboots - initial_reboots
    if verbose:
        output_str = ', '.join([
            'Dlsta: %s' % dlsta,
            'Q330 ssident: %s' % this_q330,
            'Current Q330 reboots: %s' % current_reboots,
            'Initial Q330 reboots: %s' % initial_reboots,
            'This dlsta reboots: %s' % this_dlsta_reboots
        ])
        logfmt(output_str)
    return this_dlsta_reboots

usage = "Usage: %prog [options]"
parser = OptionParser(usage=usage)
parser.add_option("-v", action="store_true", dest="verbose", help="verbose output", default=False)
(options, args) = parser.parse_args()

verbose = False
if options.verbose:
    verbose = True

def main():

    if verbose:
        logfmt("Start script")

    common_pf = 'pf/common.pf'

    pf = pfupdate( common_pf )

    cache_json = pf['CACHEJSON']
    json_path = '%s/stations/staq330.json' % cache_json

    field_exclusion = [
        'calratio',
        'calper',
        'tshift',
        'instant',
        'band',
        'digital',
        'ncalib',
        'ncalper',
        'dir',
        'dfile',
        'chan',
        'samprate',
        'inid',
        'chanid',
        'jdate',
        'rsptype',
        'dlident',
        'lddate'
    ]

    staq330_dict = {} 
    staq330_dict['metadata'] = {}
    staq330_dict['view_fields'] = {}
    staq330_dict['stations'] = {}


    dbops_q330 = pf['DBOPS_Q330']
    db_q330 = dbopen(dbops_q330, 'r')

    q330_history = initial_q330_reboot_state(db_q330, verbose)
    pprint(q330_history)

    db_staq330 = db_q330.lookup(table='staq330')
    staq330_dict['metadata']['staq330_fields'] = db_staq330.query('dbTABLE_FIELDS')
    db_staq330 = db_staq330.subset('endtime == NULL && endtime > now()')

    db_comm = db_q330.lookup(table='comm')
    staq330_dict['metadata']['comm_fields'] = db_comm.query('dbTABLE_FIELDS')
    db_comm = db_comm.subset('endtime == NULL && endtime > now()')

    db_dlsensor = db_q330.lookup(table='dlsensor')
    staq330_dict['metadata']['dlsensor_fields'] = db_dlsensor.query('dbTABLE_FIELDS')
    db_dlsensor = db_dlsensor.subset('endtime == NULL && endtime > now()')

    if verbose:
        logfmt('Outer joins to generate custom view')

    db_staq330_joined = db_staq330.join(db_comm, outer=True, pattern1="sta", pattern2="time::endtime")
    db_staq330_joined = db_staq330_joined.join(db_dlsensor, outer=True, pattern1="ssident", pattern2="dlident")

    db_staq330_joined_fields = db_staq330_joined.query('dbTABLE_FIELDS')
    db_staq330_joined = db_staq330_joined.sort('dlsta')

    if verbose:
        logfmt('Generate fields from current view')

    db_staq330_joined.record = 0
    for f in db_staq330_joined_fields:
        staq330_dict['view_fields'][f] = {}
        if f not in field_exclusion:
            pointer = db_staq330_joined.lookup('', '', f, 'dbNULL')
            # staq330_dict['view_fields'][f]['detail'] = pointer.query('dbFIELD_DETAIL')
            staq330_dict['view_fields'][f]['description'] = pointer.query('dbFIELD_DESCRIPTION')
            staq330_dict['view_fields'][f]['type'] = pointer.query('dbFIELD_TYPE')
            staq330_dict['view_fields'][f]['null'] = pointer.getv(f)[0]

    if verbose:
        logfmt('Grouping')

    db_staq330_joined = db_staq330_joined.group('dlsta')

    if verbose:
        logfmt('Dbmaster ops')

    dbmaster = pf['USARRAY_DBMASTER']
    db = dbopen(dbmaster, "r")
    db = db.lookup(table='deployment')
    db = db.subset('snet=~/TA/ && endtime == NULL')


    if verbose:
        logfmt('Get active station list')
    stations = []
    for i in range(db.record_count):
        db.record = i
        sta = db.getv('sta')[0]
        stations.append('TA_%s' % sta)
    stations.sort()


    if verbose:
        logfmt('Create dictionary of active station values')
    for i in range(db_staq330_joined.record_count):
        db_staq330_joined.record = i
        dlsta = db_staq330_joined.getv('dlsta')[0]
        if dlsta in stations:
            staq330_dict['stations'][dlsta] = {}
            db_staq330_sub = db_staq330_joined.subset("dlsta =~ /%s/" % dlsta)
            db_staq330_sub = db_staq330_sub.ungroup()
            # Need to force the sort key to be from the dlsensor table
            db_staq330_sub = db_staq330_sub.sort('dlsensor.time', reverse=True)
            db_staq330_sub.record = 0
            for f in db_staq330_joined_fields:
                if f not in field_exclusion:
                    staq330_dict['stations'][dlsta][f] = db_staq330_sub.getv(f)[0]
            this_sta_reboots = calc_this_station_reboots(dlsta, staq330_dict['stations'][dlsta], q330_history, verbose)
            staq330_dict['stations'][dlsta]['this_dlsta_reboots'] = this_sta_reboots

    if verbose:
        logfmt('Convert to JSON format and replace')
    output_file_path = '%s+' % json_path
    f = open(output_file_path, 'w')
    json.dump(staq330_dict, f, sort_keys=True, indent=2)
    f.flush()

    try:
        os.rename(output_file_path, json_path)
    except Exception,e: 
        logfmt('%s:%s' % (Exception, e))

    '''
    if verbose:
        logfmt('Zip file')

    try:
        gz_in = open( json_path, 'rb' )
        gz_out = gzip.open( json_path+'.gz', 'wb' )
        gz_out.writelines(gz_in)
        gz_out.close()
        gz_in.close()
    except Exception,e:
        logfmt('%s:%s' % (Exception,e))
    '''

    if verbose:
        logfmt("End script")

    return 0

if __name__ == '__main__':
    status = main()
    sys.exit(status)
