#
# Instrument history from stage table to a JSON file: sensor and digitizer
#

import json
from collections import defaultdict

# Load datascope functions
from antelope.datascope import *
from antelope.stock import *

from optparse import OptionParser
from time import time, gmtime, strftime



web_root   = '/anf/web/vhosts/anf.ucsd.edu'
pffile         = '%s/conf/report_exceptions.pf' % web_root

common_pf  = '%s/conf/common.pf' % web_root

pf = pfupdate( common_pf )

dbmaster   = pf['USARRAY_DBMASTER']
cache_json = pf['CACHEJSON']
output_dir = pf['CACHE_EOLPLOTS']

json_file_path = cache_json + '/tools/instrument_history/'
instrument_history = {} # Dictionary to hold everything
instrument_types = ['sensor','digitizer']
now_time = time()



usage = "Usage: %prog [options]"
parser = OptionParser(usage=usage)
parser.add_option("-v", action="store_true", dest="verbose", help="verbose output", default=False)
(options, args) = parser.parse_args()

verbose = False
if options.verbose:
    verbose = True


if verbose:
    print "- Start of script at time %s" % strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())

db = dbopen(dbmaster, 'r')
db_stage = db.lookup(table='stage')
db_snetsta = db.lookup(table='snetsta')

db_stage = db_stage.join(db_snetsta)

if verbose:
    print " - Getting NULL values from table fields"

db_stage.record = 0
nulls = {}
db_fields = db_stage.query(dbTABLE_FIELDS)

for dbf in db_fields:
    field_null = db_stage.lookup('', '', dbf, 'dbNULL')
    nulls[dbf] = field_null.getv(dbf)[0]


for type in instrument_types:

    if verbose:
        print "\n - Working on %s" % type

    # Make list placeholder
    instrument_history = []
    instrument_summary = []

    db_pointer           = db_stage.subset("snet=~/TA/ && gtype=~/%s/ && ssident!=NULL && chan=~/BHZ/" % type)
    db_pointer           = db_pointer.sort(["ssident"])
    db_pointer_grp       = db_pointer.group("ssident")
    db_pointer_grp_nrecs = db_pointer_grp.record_count

    if verbose:
        print " - Number of grouped records: %s" % db_pointer_grp_nrecs

    for i in range(db_pointer_grp_nrecs):


        db_pointer_grp.record = i

        ssident = db_pointer_grp.getv('ssident')[0]

        db_pointer_grp_sub = db_pointer_grp.subset("ssident=~/%s/" % ssident)
        db_pointer_ungrp = db_pointer_grp_sub.ungroup()

        db_pointer_ungrp_sort = db_pointer_ungrp.sort(['time','sta'])
        db_pointer_ungrp_nrecs = db_pointer_ungrp_sort.record_count

        # List container for time series
        series = []

        if verbose:
            print "  - Number of ungrouped records: %s" % db_pointer_ungrp_nrecs

        for j in range(db_pointer_ungrp_nrecs):


            db_pointer_ungrp_sort.record = j

            [sta,time,endtime] = db_pointer_ungrp_sort.getv('sta','time','endtime')

            if time == nulls['time']:
                readable_time = "N/A"
                js_time = epoch2str(now_time, "%b %d %Y %H:%M:%S")
            else:
                readable_time = epoch2str(time, "%Y-%m-%d %H:%M:%S")
                js_time = epoch2str(time, "%b %d %Y %H:%M:%S")

            if endtime == nulls['endtime']:
                readable_endtime = "N/A"
                js_endtime = epoch2str(now_time, "%b %d %Y %H:%M:%S")
            else:
                readable_endtime = epoch2str(endtime, "%Y-%m-%d %H:%M:%S")
                js_endtime = epoch2str(endtime, "%b %d %Y %H:%M:%S")

            series.append({'name':sta, 'start':js_time, 'end':js_endtime})

            if verbose:
                print "   - Type: %s, Ssident: %s, Sta: %s, Time: %d, Endtime: %d" % (type, ssident, sta, time, endtime)

            del readable_time, js_time, readable_endtime, js_endtime


        # Add to dictionary
        instrument_history.append({ 'id':i, 'name':ssident, 'series':series})
        instrument_summary.append(ssident)

        del series



    if verbose:
        print "\n- Start: Creating JSON file for type %s" % type

    output_file_path = "%s%s.json+" % (json_file_path, type)
    json_file        = "%s%s.json" % (json_file_path, type)

    f = open(output_file_path, 'w') 
    json.dump(instrument_history, f, sort_keys=True, indent=2)

    f.flush()

    try:
        # Move the file to replace the older one
        os.rename(output_file_path, json_file)

    except OSError:
        print "- Cannot rename JSON file for type %s" % type

    del output_file_path
    del f

    if verbose:
        print "- End: Creating JSON file for type %s" % type



    if verbose:
        print "\n- Start: Creating summary serial numbers JSON file for type %s" % type

    summary_output_file_path = "%s%s_summary.json+" % (json_file_path,type)
    summary_json_file        = "%s%s_summary.json" % (json_file_path,type)

    f = open( summary_output_file_path, 'w' ) 
    json.dump( instrument_summary, f, sort_keys=True, indent=2 )

    f.flush()

    try:
        # Move the file to replace the older one
        os.rename(summary_output_file_path,summary_json_file)

    except OSError:
        print "- Cannot rename summary serial numbers JSON file for type %s" % type

    del summary_output_file_path
    del f

    if verbose:
        print "- End: Creating summary serial numbers JSON file for type %s" % type


    del instrument_history
    del instrument_summary

if verbose:
    print "\n- End of script at time %s" % strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())

exit()
