

import json
import string
from time import strftime

import antelope.datascope as datascope
import antelope.stock as stock


verbose = False


# {{{ General vars
web_root = '/anf/web/vhosts/anf.ucsd.edu'
common_pf = web_root + "/conf/common.pf"

common_pf = stock.pfread(common_pf)

cache_json = common_pf.get('CACHEJSON' )
json_path = cache_json + '/stations'
cache_file_path = json_path + '/stalist.json'
temp_file_path = cache_file_path + '+'

cache_file_path_TA = json_path + '/stalistTA.json'
temp_file_path_TA = cache_file_path_TA + '+'

station_dict = { 'stations': [] }
sta_list = []

sta_list_TA = []

if verbose:
  print "\tweb_root = %s\n " % web_root
  print "\tcommon_pf = %s\n " % common_pf
  print "\tcache_json = %s\n " % cache_json
  print "\tjson_path = %s\n " % json_path
  print "\tcache_file_path = %s\n " % cache_file_path
  print "\ttemp_file_path = %s\n " % temp_file_path
  print "\tcache_file_path_TA = %s\n " % cache_file_path_TA
  print "\ttemp_file_path_TA = %s\n " % temp_file_path_TA
# }}} General vars

# {{{ Dbops
dbmaster = common_pf.get('USARRAY_DBMASTER' )

with datascope.closing(datascope.dbopen( dbmaster, "r" )) as db:
    db_stations = db.lookup( '', 'snetsta', '', '' ) 
    db_stations_TA = db_stations.subset(  'snet=~/TA/' )

    db_uniq_stations = db_stations.sort( "sta", unique=True )
    db_uniq_stations_TA = db_stations_TA.sort( "sta", unique=True )

    db_sorted_stations = db_uniq_stations.sort(["snet","sta"])
    db_sorted_stations_TA = db_uniq_stations_TA.sort(["snet","sta"])

    nrecs = db_sorted_stations.query( datascope.dbRECORD_COUNT )
    nrecs_TA = db_sorted_stations_TA.query( datascope.dbRECORD_COUNT )
# }}} Dbops

# {{{ All stations
    if verbose: print "ALL STATIONS:"
    for i in range(nrecs):
        db_sorted_stations3.record = i
        my_sta = db_sorted_stations.getv( "sta" )[0]
        if verbose: print "\t%s" % my_sta
        sta_list.append( my_sta )

    station_dict['stations'] = sta_list

    f = open( temp_file_path, 'w' )
    json.dump( station_dict, f, sort_keys=True, indent=2 )
    f.flush()

# Move the file to replace the older one
    os.rename(temp_file_path,cache_file_path)
# }}} All stations

# {{{ TA stations
    if verbose: print "TA STATIONS:"
    for i in range(nrecs_TA):
        db_sorted_stations_TA.record = i
        my_sta = db_sorted_stations_TA.getv("sta" )[0]
        if verbose: print "\t%s" % my_sta
        sta_list_TA.append( my_sta )


    f_ta = open( temp_file_path_TA, 'w' )
    json.dump( sta_list_TA, f_ta, sort_keys=True, indent=2 )
    f_ta.flush()

# Move the file to replace the older one
    os.rename(temp_file_path_TA,cache_file_path_TA)
# }}} TA stations

exit()
