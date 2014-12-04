#!/usr/bin/env python

#
# {{{ Header
#
# $Id$
#
# Python script for auto generating event plots
# Fires off a Matlab script
#  
# NOTES: (1) Create a parameter file with plot parameters
#        (2) Creates a series of databases in /tmp/staname 
#        for station lifetime (archives and rt db)
#        (3) Fires of a Matlab script to create maps
#        (4) Allow for different networks
#        (5) Allow for adopted stations
#
# @category    Datascope
# @package     N/A
# @author      Rob Newman <rlnewman@ucsd.edu>
# @copyright   Copyright (c) 2010 UCSD
# @license     MIT-style license
# @version     CVS: $Revision$
#
# }}} Header
#

import sys
import os
import tempfile
import shutil
import json
from subprocess import *

# Load datascope functions
sys.path.append( os.environ['ANTELOPE'] + '/data/python' )
from antelope.datascope import *
# from orb import *
from antelope.stock import *

from optparse import OptionParser
from time import *


# Set the Antelope error log environmental variable to have no limit
# putenv( "ELOG_MAXMSG=0" ) ;
# error_reporting( E_ALL ^ E_NOTICE ) ;

# {{{ Local functions
def clean_up(my_temp_directory):

    for dir_file in os.listdir(my_temp_directory):
        os.remove(my_temp_directory+"/"+dir_file)

    try:
        os.removedirs('%s' % my_temp_directory )
    except OSError:
        print "Temp directory %s not removed. Error." % my_temp_directory

    return

# }}} Local functions

# {{{ Get command line arguments

usage = "Usage: %prog [options]"

parser = OptionParser(usage=usage)

parser.add_option("-v", action="store_true", dest="verbose", help="verbose output", default=False)
parser.add_option("-t", action="store_true", dest="type", help="type of station to process", default=False)
parser.add_option("-s", action="store", type="string", dest="station", help="station code to process", default=False)

(options, args) = parser.parse_args()

if options.verbose:
    verbose = True
else:
    verbose = False

if options.type:
    type = options.type
else:
    type = False

if options.station:
    station = options.station
else:
    print "Must define a station code to generate events for!\nExiting..."
    exit()

# }}} Get command line arguments

# {{{ Get common vars and defs
web_root              = '/anf/web/vhosts/anf.ucsd.edu'
common_pf             = web_root + '/conf/common.pf'
pf = pfread(common_pf)
dbcentral             = pf['DBCENTRAL']
dbcentral_pf          = pf['DBCENTRAL_PF']
usarray_cluster       = pf['USARRAY_CLUSTER']
usarray_rt_cluster    = pf['USARRAY_RT_CLUSTER']
rose_plots_dir        = pf['CACHE_ROSEPLOTS']
cache_json            = pf['CACHEJSON']
station_digest_assets = pf['STATION_DIGEST_ASSETS']
event_types           = ['regional','global']
tmp                   = pf['TMP']
tmp_dir               = tmp + 'roseplot_events_%s' % station
tmp_pf                = 'eol_report_runtime.pf'
json_file             = cache_json + '/stations/stations.json'
monthly_dbs           = { 'arrival':'','assoc':'','origin':'','event':'','wfdisc':'' }

if verbose:
    print "Start: Open up configuration parameter file %s" % common_pf
    print " - Generating plots for station: %s" % station
    print " - Using dbcentral: %s" % dbcentral
    print " - Plots target directory: %s/%s" % (rose_plots_dir,station)
    print " - Stations JSON file: %s" % json_file

# }}} Get common vars and defs

# {{{ Dbcentral search and replace functions
"""
Frank claims all dbpath errors are fixed.
Comment out all search and replace
See JIRA ticket TA-354 for more information
"""
if verbose:
    print " - Define search and replace strings and regex"


# This will replace the rt database which just has local file references
wfdisc_dir_search = "^[0-9]{4}/[0-9]{3}" # For more recent > 2006 events
wfdisc_dir_replace =  "/anf/TA/rt/usarray/$0"
"""
wfdisc_dir_search_export_1 = "^/export/home/rt/rtsystems/usarray/db/" # For old < 2006 events
wfdisc_dir_replace_export_1 =  "/anf/TA/dbs/certified/"
wfdisc_dir_search_export_2 = "^../../" # For relative refs
wfdisc_dir_replace_export_2 =  "/anf/TA/dbs/"

# For new disk layout
wfdisc_dir_search_sdsc = "^/anf/anfops1/usarray/db/" # /anf/anfops1/usarray/db/2010/247
wfdisc_dir_replace_sdsc = "/anf/TA/rt/usarray/"      # /anf/TA/rt/usarray/2010/247
wfdisc_dir_search_sdsc_2 = "^/anf/TA/dbs/certified/"
wfdisc_dir_replace_sdsc_2 = "/anf/TA/dbs/wfs/certified/"

# For the error introduced on 2012-01-15 (JIRA TA-354)
wfdisc_dir_search_sdsc_3 = "^/anf/TA/dbs/wfs/wfs/certified/" # /anf/anfops1/usarray/db/2010/247
wfdisc_dir_replace_sdsc_3 = "/anf/TA/dbs/wfs/certified/"      # /anf/TA/rt/usarray/2010/247

# For the error introduced on 2012-01-25 (JIRA TA-354)
wfdisc_dir_search_sdsc_4 = "^/anf/TA/dbs/event_dbs/wfs/certified/"
wfdisc_dir_replace_sdsc_4 = "/anf/TA/dbs/wfs/certified/"
"""
# }}} Dbcentral search and replace functions

# {{{ Create a parameter file with the station name and events of interest

if os.path.exists(tmp_dir) :
    if verbose:
         print " - Removing pre-existing directory: %s" % (tmp_dir)
    shutil.rmtree(tmp_dir)

if not os.path.exists(tmp_dir) :
    if verbose:
         print " - Creating temp directory: %s" % (tmp_dir)
    os.mkdir(tmp_dir)
    filename = '%s/%s' % (tmp_dir,tmp_pf)
    open(filename,'w').close()

pfpath = os.getenv('PFPATH')
new_pfpath = pfpath + ':'+tmp_dir
os.environ['PFPATH'] = new_pfpath

if verbose:
    print " - Adding temp directory to PFPATH. PFPATH is now: %s" % os.getenv('PFPATH')

# }}} Create a parameter file with the station name and events of interest

if verbose:
    print " - Trying to create images for station: %s" % station

# Starting timestamp
t0 = strtime( time() )

if verbose:
    print " - 1. Script for station %s initiated at %s" % (station,t0)

# {{{ Get station values from JSON file
json_dump = json.load( open(json_file,'r') )

if json_dump['active'].has_key(station):
    my_sta_obj = json_dump['active'][station]
elif json_dump['decom'].has_key(station):
    my_sta_obj = json_dump['decom'][station]
else:
    print "  - No station object found for station %s. Exiting." % station
    exit()

sta_name        = my_sta_obj['staname']
sta_snet        = my_sta_obj['snet']
sta_lat         = my_sta_obj['lat']
sta_lon         = my_sta_obj['lon']
sta_cert_time   = 0 if not my_sta_obj['cert_time'] else my_sta_obj['cert_time']
sta_time        = my_sta_obj['time']

# }}} Get values from dbmaster

if verbose:
    print " - 2. Station %s at %s certified on %s" % (station,sta_name,sta_cert_time)

# {{{ Put information into parameter file

# No pfput in Python interface. Comment out and rewrite
'''
pfput( "wvform_image_dir", rose_plots_dir, 'testpf' )
pfput( "sta_chans", "BH.", 'testpf' )

pfput( "sta_code", sta_code, 'testpf' )
pfput( "sta_name", sta_name, 'testpf' )
pfput( "sta_lat", sta_lat, 'testpf' )
pfput( "sta_lon", sta_lon, 'testpf' )

# Give some lead time to the event
pfput( "ev_glo_lead", 300, 'testpf' ) # 5 mins
pfput( "ev_reg_lead", 20, 'testpf' ) # 20 secs
'''
tmp_pf_open = open(filename,'r+')
tmp_pf_open.write("wvform_image_dir    %s/%s/\n" % (rose_plots_dir,station))
tmp_pf_open.write("sta_chans    BH.\n")

tmp_pf_open.write("sta_code    %s\n" % station)
tmp_pf_open.write("sta_name    %s\n" % sta_name)
tmp_pf_open.write("sta_lat     %s\n" % sta_lat)
tmp_pf_open.write("sta_lon     %s\n" % sta_lon)

# Give some lead time to the event
tmp_pf_open.write("ev_glo_lead    300\n") # 5 mins
tmp_pf_open.write("ev_reg_lead    20\n") # 20 secs
tmp_pf_open.close()

# }}} Put information into parameter file

# {{{ Dbcentral work

# {{{ Generate the dbcentral instructions
if verbose:
    content = 'verbose\n'
else:
    content = ''

content += "dbopen arrival\n"
content += "dbsubset sta=~/"+station+"/\n"
content += "dbjoin assoc\n"
content += "dbjoin origin\n"
content += "dbjoin event\n"
content += "dbsubset prefor==orid\n"
content += "dbjoin wfdisc\n"
# content += "dbsubset sta=~/$sta_code/\n" ;
# content += "dbsubset chan=~/BH./\n" ;
# content += "dbsubset time > '$sta_cert_time'\n" ;
# content += "dbsubset time < '$sta_decert_time'\n" ;
# content += "dbsort -u orid\n" ;
content += "db2pipe dbunjoin -o "+tmp_dir+"/" + station + "_%Y_%m_%d -\n"
content += "dbfree\n"
content += "dbclose\n"
# }}} Generate the dbcentral instructions

request_file = tmp_dir+"/" + station + "_request"
composite_db = tmp_dir+"/" + station + "_comp"

file_handle = open(request_file,'w')
file_handle.write(content)
file_handle.close() ;

if verbose:
    print " - 3. Successfully wrote to request file %s" % request_file

if verbose:
    print " - 4a. START: dbcentral on the monthly archives"

# Dbcentral on the archive
retcode = os.system("dbcentral -p %s -q %s %s" % (dbcentral_pf,request_file,usarray_cluster) )

if verbose:
    print " - 4a. END: dbcentral on the monthly archives"
    print " - 4b. START: dbcentral on the real time database"

# Dbcentral on the real time system
retcode_rt = os.system("dbcentral -p %s -q %s %s" % (dbcentral_pf,request_file,usarray_rt_cluster) )

if verbose:
    print " - 4b. END: dbcentral on the real time database"

# {{{ Merge monthly dbs back together
for dir_file in os.listdir(tmp_dir):
    if not "runtime" in dir_file and not "request" in dir_file:
        if "." not in dir_file:
             for ot in sorted(monthly_dbs.iterkeys()):
                  monthly_dbs[ot] += tmp_dir+"/"+dir_file+"."+ot+" "

if verbose:
    print " - 4c. START: Merging dbcentral databases together into database %s" % composite_db

for ot in sorted(monthly_dbs.iterkeys()):
    if monthly_dbs[ot] is not "":
        # Trust that dbunjoin did its job properly and just cat them
        retcode_comp = os.system( "cat "+monthly_dbs[ot]+" > "+composite_db+"."+ot )
    else:
        print " - 4d. EXCEPTION: One or more of the monthly dbs does not have any values. Exiting."
        clean_up(tmp_dir)
        exit()

if verbose:
    print " - 4d. END: Merging dbcentral databases together"

# }}} Merge monthly dbs back together

# {{{ Modify the dir path to the real-time archive

if verbose:
    print " - 5. Find and replace directory name in wfdisc table %s" % composite_db
# Clean up local references 
retcode_clean_1 = os.system( "dbset "+tmp_dir+"/"+station+"_comp.wfdisc dir '*' 'patsub(dir, \""+wfdisc_dir_search+"\", \""+wfdisc_dir_replace+"\")'" )
"""
# Clean up the real time references 1
retcode_clean_2 = os.system( "dbset "+tmp_dir+"/"+station+"_comp.wfdisc dir '*' 'patsub(dir, \""+wfdisc_dir_search_export_1+"\", \""+wfdisc_dir_replace_export_1+"\")'" )
# Clean up the real time references 2
retcode_clean_3 = os.system( "dbset "+tmp_dir+"/"+station+"_comp.wfdisc dir '*' 'patsub(dir, \""+wfdisc_dir_search_export_2+"\", \""+wfdisc_dir_replace_export_2+"\")'" )

# Clean up /anf/anfops1 references so it works with the new SDSC layout
retcode_clean_4 = os.system( "dbset "+tmp_dir+"/"+station+"_comp.wfdisc dir '*' 'patsub(dir, \""+wfdisc_dir_search_sdsc+"\", \""+wfdisc_dir_replace_sdsc+"\")'" )

# Clean up Franks non fix of moving the wfs from /anf/TA/dbs/certified/ to /anf/TA/dbs/wfs/certified/ without fixing the dir and dfile entries across the whole archive
retcode_clean_5 = os.system( "dbset "+tmp_dir+"/"+station+"_comp.wfdisc dir '*' 'patsub(dir, \""+wfdisc_dir_search_sdsc_2+"\", \""+wfdisc_dir_replace_sdsc_2+"\")'" )

# Clean up Franks introduction of /wfs/wfs in the path name. See JIRA ticket TA-354
retcode_clean_6 = os.system( "dbset "+tmp_dir+"/"+sta_code+"_comp.wfdisc dir '*' 'patsub(dir, \""+wfdisc_dir_search_sdsc_3+"\", \""+wfdisc_dir_replace_sdsc_3+"\")'" )

# Clean up Franks introduction of /event_dbs in the path name. See JIRA ticket TA-354
retcode_clean_7 = os.system( "dbset "+tmp_dir+"/"+sta_code+"_comp.wfdisc dir '*' 'patsub(dir, \""+wfdisc_dir_search_sdsc_4+"\", \""+wfdisc_dir_replace_sdsc_4+"\")'" )
"""
# }}} Modify the dir path to the real-time archive

# {{{ Create composite db descriptor file
comp_db_descriptor = open( composite_db, "w" )
comp_db_descriptor.write("# Datascope Database Descriptor file\nschema css3.0\n" )
comp_db_descriptor.close()
# }}} Create composite db descriptor file

# {{{ Write out composite db to pf
tmp_pf_reopen = open(filename,'a')
# pfput( "ev_database", $composite_db, 'testpf' ) ;
tmp_pf_reopen.write("ev_database    %s\n" % composite_db)
tmp_pf_reopen.close()
# }}} Write out composite db to pf

# {{{ Parameter file placeholder for specific station data
info_handle = open(filename,'a')
# pfput( "eventinfopf", $dump_pf, 'testpf' ) # pfput not in Python interface
info_pf = rose_plots_dir + '/' + station + '/' + station + '_info.pf'
eventinfo = "eventinfopf    %s\n" % info_pf
info_handle.write(eventinfo)
info_handle.close()
# }}} Parameter file placeholder for specific station data

if verbose:
    print " - 6. Finished dbcentral subsets and composite database creation"

# }}} Dbcentral work

if verbose:
    print " - 7. START: Loop to get regional and teleseismic events of interest"

# {{{ Dbops on the composite database
db_comp         = dbopen(composite_db,'r')
db_comp_assoc   = db_comp.lookup(table='assoc')
db_comp_arrival = db_comp.lookup(table='arrival')
db_comp_origin  = db_comp.lookup(table='origin')

db_comp_joined  = db_comp_assoc.join(db_comp_arrival)
db_comp_joined  = db_comp_joined.join(db_comp_origin)
db_comp_joined  = db_comp_joined.subset("sta =~ /%s/" % station)

#try :
#    db_comp_joined  = db_comp_joined.subset("time > %s" % int(str2epoch(sta_cert_time)))
#except Exception,e:
#    print "ERROR: on " + "subset(time > %s)" % int(sta_cert_time)

# }}} Dbops on the composite database

# {{{ Regional and global event loop

for dbK in event_types:

    if verbose:
        print "  - Retrieving a %s event" % dbK

    loc = dbK[:3]

    # pfput( "dbs_" + dbK, composite_db, 'testpf' )
    tmp_pf_reopen_2 = open(filename,'a')
    tmp_pf_reopen_2.write("dbs_%s    %s\n" % (dbK,composite_db) )
    tmp_pf_reopen_2.close()

    if dbK is 'global':
        db_comp_joined_type = db_comp_joined.subset("(delta > 10 && delta < 180)")
    else:
        db_comp_joined_type = db_comp_joined.subset("(delta < 10)")


    if db_comp_joined_type.record_count > 0:

        # {{{ At least one event

        db_comp_joined_type = db_comp_joined_type.sort(['mb','ms','ml'],reverse=True)

        db_comp_joined_type.record = 0 # Get the largest event

        ev_lat,ev_lon,ev_time,ev_orid,ev_mb,ev_ms,ev_ml = db_comp_joined_type.getv("lat","lon","time","orid","mb","ms","ml")

        ev_distance    = db_comp_joined_type.ex_eval( "distance(%s,%s,%s,%s)" % (ev_lat,ev_lon,sta_lat,sta_lon) )
        ev_distance_km = int( db_comp_joined_type.ex_eval("deg2km(%s)" % (ev_distance) ) )
        ev_azimuth     = db_comp_joined_type.ex_eval("azimuth(%s,%s,%s,%s)" % (ev_lat,ev_lon,sta_lat,sta_lon) )

        if verbose:
            print "    - ev_distance: %s" % ev_distance
            print "    - ev_distance_km: %s" % ev_distance_km
            print "    - ev_azimuth: %s" % ev_azimuth


        if loc == "reg":

            # {{{ LOCAL EVENT

            if ev_distance < 2:
                ev_time_window = 120 # 2 mins
            elif ev_distance > 2 and ev_distance < 8:
                ev_time_window = 300 # 5 mins
            elif ev_distance > 8 and ev_distance < 18:
                ev_time_window = 600 # 10 mins
            elif ev_distance > 13 and ev_distance < 18:
                ev_time_window = 1200 # 20 mins
            elif ev_distance > 18:
                ev_time_window = 1800 # 30 mins
            else:
                ev_time_window = 120

            if ev_ml < 0:
                if ev_mb < 0:
                    if ev_ms < 0:
                         ev_mag_str = "unknown magnitude"
                    else:
                         ev_mag_str = ev_ms
                else:
                    ev_mag_str = ev_mb
            else:
                ev_mag_str = ev_ml

            # }}} LOCAL EVENT

        elif loc == "glo":

            # {{{ GLOBAL EVENT

            if ev_ml < 0:
                if ev_mb < 0:
                    if ev_ms < 0:
                         ev_mag_str = "unknown magnitude"
                    else:
                         ev_mag_str = ev_ms
                else:
                    ev_mag_str = ev_mb
            else:
                ev_mag_str = ev_ml


            if ev_mag_str > 7.8:

                 ev_time_window = 180 * 60 # 3 hrs

            else:

                if ev_distance < 90:

                    ev_time_window = 45 * 60 # 45 mins

                elif ev_distance > 90:

                    ev_time_window = 90 * 60 # 90 mins

                else:

                    ev_time_window = 45 * 60

            # }}} GLOBAL EVENT

        else:

            print "Regional or global event not defined. Error!"

        if verbose:
            print "    - ev_time_window: %s" % ev_time_window
            print "    - writing out the %s event" % dbK

        # {{{ Add each event to pf
        '''
        pfput not in python interface yet
        pfput( "ev_"+loc+"_distance", ev_distance_km, 'testpf' )
        pfput( "ev_"+loc+"_azimuth", ev_azimuth, 'testpf' )
        pfput( "ev_"+loc+"_lat", ev_lat, 'testpf' )
        pfput( "ev_"+loc+"_lon", ev_lon, 'testpf' )
        pfput( "ev_"+loc+"_time", ev_time, 'testpf' )
        pfput( "ev_"+loc+"_orid", ev_orid, 'testpf' )
        pfput( "ev_"+loc+"_mag", ev_mag_str, 'testpf' )
        pfput( "ev_"+loc+"_window", ev_time_window, 'testpf' )
        '''
        tmp_pf_reopen_3 = open(filename,'a')
        tmp_pf_reopen_3.write("ev_%s_distance    %s\n" % (loc,ev_distance_km) )
        tmp_pf_reopen_3.write("ev_%s_azimuth    %s\n" % (loc,ev_azimuth) )
        tmp_pf_reopen_3.write("ev_%s_lat    %s\n" % (loc,ev_lat) )
        tmp_pf_reopen_3.write("ev_%s_lon    %s\n" % (loc,ev_lon) )
        tmp_pf_reopen_3.write("ev_%s_time    %s\n" % (loc,ev_time) )
        tmp_pf_reopen_3.write("ev_%s_orid    %s\n" % (loc,ev_orid) )
        tmp_pf_reopen_3.write("ev_%s_mag    %s\n" % (loc,ev_mag_str) )
        tmp_pf_reopen_3.write("ev_%s_window    %s\n" % (loc,ev_time_window) )
        tmp_pf_reopen_3.close()
        # }}} Add each event to pf

        # }}} At least one event

    else:

        print "  - No %s event in the specified delta range" % dbK

    # {{{ Free db memory
    db_comp_joined_type.free()

db_comp_joined.free()
db_comp_origin.free()
db_comp_arrival.free()
db_comp_assoc.free()
db_comp.free()
    # }}} Free db memory

#  }}} Regional and global event loop

if verbose:
    print " - 8. END: Loop to get regional and teleseismic events of interest"

# {{{ Write the parameter file out
# Not needed as no pfput function. We have already written out information
# if verbose:
#     print " - 9. Write out parameter file %s" % filename
# pfwrite( filename, 'testpf' ) ;
# }}} Write the parameter file out

# {{{ Create the target dir
target_dir = rose_plots_dir+'/'+station

if not os.path.exists(target_dir) :

    os.mkdir(target_dir)

    if verbose:
        print " - 9. Create the station directory: %s" % target_dir
# }}} Create the target dir

# {{{ Run Matlab script

if verbose:
    print " - 10. START: Matlab script"
#    print " - 10.a. Changing directory to /bin/roseplots"

#os.chdir('bin/eol_plots')
# Cannot use -nodisplay because we need to use Ghostscript
#cmd = "/usr/local/bin/matlab -nojvm -nodisplay -nosplash -r \"addpath('%s','bin/eol_plots/')\" < eol_reports.m" % (tmp_dir)
cmd = "/usr/local/bin/matlab -nodesktop -nosplash -r \"addpath('%s','bin/eol_plots/')\" < bin/eol_plots/eol_reports.m" % (tmp_dir)
if verbose:
    print " - 10.b. Running Matlab script eol_reports.m"
    print " - 10.b. %s" % cmd

output = os.system( cmd )

#if verbose:
#    print " - 10.c. Changing directory back to /export/home/rt/rtsystems/www/"

#os.chdir('../../')

# }}} Run Matlab script

if verbose:
    print " - 11. END: Matlab script"

# {{{ Crop and convert images
iterator = 1

for sda in station_digest_assets:

    if "pf" not in sda:

        if os.path.isfile(rose_plots_dir+"/"+station+"/"+station+sda+".eps"):

            if verbose:
                print " - 12."+str(iterator)+". "+station+sda+".eps image successfully created. Now trim it"

            trim_retcode = os.system( "convert -density 144 "+rose_plots_dir+"/"+station+"/"+station+sda+".eps -trim -resize 50% "+rose_plots_dir+"/"+station+"/"+station+sda+"_final.png" )

        else:

            if verbose:
                print " - 12."+str(iterator)+". Error! "+station+sda+" image not created!"

    iterator += 1

# }}} Crop and convert images

# {{{ Clean up the tmp dir
if verbose:
    print " - 13. Clean up the tmp directory."

clean_up(tmp_dir)

'''
for dir_file in os.listdir(tmp_dir):
    os.remove(tmp_dir+"/"+dir_file)

try:
    os.removedirs('%s' % (tmp_dir) )
except OSError:
    print "Temp directory %s not removed. Error." % (tmp_dir)
'''

# }}} Clean up the tmp dir

# {{{ Clean up the output dir of eps files
if verbose:
   print " - 14. Remove EPS files."
for dir_file in os.listdir(rose_plots_dir+"/"+station):

    if "eps" in dir_file:
        os.remove(rose_plots_dir+"/"+station+"/"+dir_file)

# }}} Clean up the output dir of eps files

# Ending timestamp
t1 = strtime( time() )

if verbose:
    print " - 15. Script for station %s finished at %s" % (station,t1)

# Reset Antelope PFPATH enviromental variable
os.environ['PFPATH'] = pfpath

exit()
