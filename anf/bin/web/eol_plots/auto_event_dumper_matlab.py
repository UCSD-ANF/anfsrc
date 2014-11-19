#!/usr/bin/env python


# {{{ Import all the relevant modules

import sys
import os
import json

# Load time functions
import time
# from time import gmtime, strftime

# Load Antelope datascope functions
sys.path.append( os.environ['ANTELOPE'] + '/data/python' )
from antelope.datascope import *
from antelope.stock import *

from optparse import OptionParser

# }}} Import all the relevant modules

os.putenv('ELOG_MAXMSG','0' ) ;
# error_reporting( E_ALL ^ E_NOTICE ) ;

# {{{ Get command line arguments

usage = "Usage: %prog [options]"

parser = OptionParser(usage=usage)

parser.add_option("-v", action="store_true", dest="verbose", help="verbose output", default=False) 
parser.add_option("-s", "--sta", action="store", type="string", dest="sta", help="station code", default=False) 

(options, args) = parser.parse_args()

if options.verbose:
    verbose = True
else:
    verbose = False

if options.sta:
    sta_code = options.sta
else:
    print "- ERROR: you must provide a station code as one of the script arguments"
    exit()

# }}} Command line options


# {{{ Get common vars and defs
common_pf = 'common.pf'
pf = pfread(common_pf)

tmp = pf['TMP']
cache_json = pf['CACHEJSON']
station_digest_assets = pf['STATION_DIGEST_ASSETS']
usarray_dbmaster = pf['USARRAY_DBMASTER']
usarray_dbcentral = pf['DBCENTRAL']
dbcentral_pf = pf['DBCENTRAL_PF']
usarray_rt = pf['USARRAY_RTDB']
eol_plots_dir = pf['CACHE_EOLPLOTS']
monthly_dbs = { 'arrival':'','assoc':'','origin':'','event':'','wfdisc':'' }

if verbose:
    print "Variables used in this script:"
    print " - Cache JSON:     '%s'" % cache_json
    print " - Dbmaster:       '%s'" % usarray_dbmaster
    print " - USArray dbcentral path: '%s'" % usarray_dbcentral
    print " - dbcentral pf: '%s'" % dbcentral_pf
    print " - USArray rtdb path: '%s'" % usarray_rt
    print " - Output path:    '%s'" % eol_plots_dir

# WHAT ARE THESE NEEDED FOR?
# require( "/anf/web/vhosts/anf.ucsd.edu/conf/common.conf" ) ;
# require( "/anf/web/vhosts/anf.ucsd.edu/conf/functions-loader.php" ) ;
# }}} Get common vars and defs

# {{{ Dbcentral search and replace functions
"""
This will replace the rt database which 
just has local file references

Update 2012-01-30:
Frank says that all dbpaths are fixed. See JIRA ticket TA-354.
Commenting out all search and replaces
"""
wfdisc_dir_search  = "^[0-9]{4}/[0-9]{3}" # For real time events with relative paths
wfdisc_dir_replace =  "/anf/TA/rt/usarray/$0"
"""
wfdisc_dir_search_export_1  = "^/export/home/rt/rtsystems/usarray/db/" # For old < 2006 events
# wfdisc_dir_replace_export_1 = "/anf/TA/dbs/certified/"
wfdisc_dir_replace_export_1 = "/anf/TA/dbs/wfs/certified/"

wfdisc_dir_search_export_2  = "^../../" # For relative refs
# wfdisc_dir_replace_export_2 = "/anf/TA/dbs/"
wfdisc_dir_replace_export_2 = "/anf/TA/dbs/wfs/certified/"
# wfdisc_dir_replace_export_2 =  "/anf/TA/dbs/certified/"

# For new disk layout
wfdisc_dir_search_sdsc = "^/anf/anfops1/usarray/db/" # /anf/anfops1/usarray/db/2010/247
# wfdisc_dir_replace_sdsc = "/anf/TA/rt/usarray/"      # /anf/TA/rt/usarray/2010/247
wfdisc_dir_replace_sdsc = "/anf/TA/dbs/wfs/certified/"      # /anf/TA/rt/usarray/2010/247

wfdisc_dir_search_sdsc_2 = "^/anf/TA/dbs/certified/" # /anf/anfops1/usarray/db/2010/247
wfdisc_dir_replace_sdsc_2 = "/anf/TA/dbs/wfs/certified/"      # /anf/TA/rt/usarray/2010/247

wfdisc_dir_search_sdsc_3 = "^/anf/TA/dbs/wfs/wfs/certified/" # /anf/anfops1/usarray/db/2010/247
wfdisc_dir_replace_sdsc_3 = "/anf/TA/dbs/wfs/certified/"      # /anf/TA/rt/usarray/2010/247
# wfdisc_dir_search_sdsc_3 = ".*[0-9]{4}_dmc/" # /anf/anfops1/usarray/db/2010/247
# wfdisc_dir_replace_sdsc_3 = "/anf/TA/dbs/wfs/certified/"      # /anf/TA/rt/usarray/2010/247

wfdisc_dir_search_sdsc_4 = "^/anf/TA/dbs/event_dbs/wfs/certified/"
wfdisc_dir_replace_sdsc_4 = "/anf/TA/dbs/wfs/certified/"
"""
# }}} Dbcentral search and replace functions

event_types = ["regional","global"]

# {{{ Open dbmaster
if verbose:
    print "\nOpening dbmaster %s" % usarray_dbmaster

db = dbopen(usarray_dbmaster,"r")
db_site       = db.lookup(table='site')
db_snetsta    = db.lookup(table='snetsta')
db_deployment = db.lookup(table='deployment')

db_join = db_site.join(db_snetsta)
db_join = db_join.join(db_deployment)

mydb = db_join.subset("sta=~/%s/" % sta_code)
# }}} Open dbmaster

# {{{ Create a parameter file with the station name and events of interest
tmp_dir = tmp + "eol_events_%s"  % sta_code
if not os.path.exists( tmp_dir ):
    os.mkdir( tmp_dir, 0777 )
filename = "%s/eol_report_runtime.pf" % tmp_dir
os.system( "touch %s" % filename )

saved_pfpath_env = os.environ['PFPATH']
os.environ['PFPATH'] = tmp_dir + ':' + saved_pfpath_env

if verbose:
    print "PFPATH variable set to %s" % os.environ['PFPATH']

# }}} Create a parameter file with the station name and events of interest

if verbose:
    print "----------------------------------------"
    print "Trying to create images for station %s" % sta_code
    print "----------------------------------------"

# Starting timestamp
if verbose:
    print " - 1. START: Script for %s initiated at %s" % (sta_code,epoch2str( time.time(), "%Y-%m-%d %H:%M:%S" ))

mydb.record = 0
sta_name, sta_snet, sta_lat, sta_lon, sta_cert_time, sta_decert_time, sta_time = mydb.getv('staname', 'snet', 'lat', 'lon', 'cert_time', 'decert_time', 'time')

if verbose:
    print " - 2. START: %s certified %s, decertified %s" % (sta_code,epoch2str(sta_cert_time,"%Y-%m-%d %H:%M:%S"),epoch2str(sta_decert_time,"%Y-%m-%d %H:%M:%S"))

# {{{ Put information into parameter file
my_pffile = open(filename,'w')
my_pffile.write("wvform_image_dir    %s/%s/\n" % (eol_plots_dir,sta_code))
my_pffile.write("sta_chans    BH.\n")
my_pffile.write("sta_code    %s\n" % sta_code)
my_pffile.write("sta_name    %s\n" % sta_name)
my_pffile.write("sta_lat    %s\n" % sta_lat)
my_pffile.write("sta_lon    %s\n" % sta_lon)

# Give some lead time to the event
my_pffile.write("ev_glo_lead    %s\n" % 300) # 5 mins
my_pffile.write("ev_reg_lead    %s\n" % 20) # 20 secs

my_pffile.close()

# }}} Put information into parameter file

# {{{ Dbcentral work
# Open up dbcluster, get events, output dbs, merge into database
# +-+-+- my_dbc = dbopen(usarray_dbcentral, "r")
# +-+-+- my_dbc_clusters = dblookup(mydbc,'','clusters','','')
# +-+-+- expr = "clustername == 'usarray'" ;
# $expr = "clustername == 'usarray' || clustername == 'usarray_rt'" ;
# $expr2 = "clustername == 'usarray_rt'" ;
# +-+-+- usarray_dbcentral_events = dbsubset(my_dbc_clusters, expr )
# +-+-+- usarray_dbcentral_nrecs  = dbnrecs(usarray_dbcentral_events ) # Should only be one record!

# DONT NEED THIS RIGHT NOW
'''
for i in range(usarray_dbcentral_nrecs):
    usarray_dbcentral_events[3] = i
    events_path = dbextfile(usarray_dbcentral_events)

    if verbose:
        print "Event path: %s" % events_path # Are we getting the correct dbcentral row?
'''
    
# {{{ Generate the dbcentral instructions
if verbose:
    content = "verbose\n"
else:
    content = ''

content += "dbopen arrival\n"
content += "dbsubset sta=~/%s/\n" % sta_code
content += "dbjoin assoc\n"
content += "dbjoin origin\n"
content += "dbjoin event\n"
content += "dbsubset prefor==orid\n"
content += "dbjoin wfdisc\n"
# $content .= "dbsubset sta=~/%s/\n" % sta_code
# $content .= "dbsubset chan=~/BH./\n"
# $content .= "dbsubset time > '%s'\n" % sta_cert_time
# $content .= "dbsubset time < '%s'\n" % sta_decert_time
# $content .= "dbsort -u orid\n"
content += "db2pipe dbunjoin -f -o "+tmp_dir+"/"+sta_code+"_%Y_%m_%d -\n"
content += "dbfree\n"
content += "dbclose\n"
# }}} Generate the dbcentral instructions

f = tmp_dir+"/"+sta_code+"_request"
composite_db = tmp_dir+"/"+sta_code+"_comp"

open_file_handle = open(f,"w+")
open_file_handle.write(content)

if verbose:
    print " - 3. Successfully wrote to request file (%s)" % f

open_file_handle.close()

if verbose:
    print " - 4a. START: dbcentral on the monthly archives"

# Hard code the parameter file for the archive
test = os.system( "dbcentral -p %s -q %s usarray" % (dbcentral_pf,f) )

if verbose:
    print " - 4a. END: dbcentral on the monthly archives"
    print " - 4b. START: dbcentral on the real time database"

# Hard code the parameter file for the real time db
test_rt = os.system( "dbcentral -p %s -q %s usarray_rt" % (dbcentral_pf,f) )

if verbose:
    print " - 4b. END: dbcentral on the real time database"
    print "%s" % test

# {{{ Merge monthly dbs back together
for dir_name in os.listdir( tmp_dir ):
    if "." not in dir_name or ".." not in dir_name or "_request" not in dir_name:
        if "." not in dir_name:
            if verbose:
                print "  - %s will be included in the list of database tables to merge" % dir_name
            for ot in sorted(monthly_dbs.iterkeys()):
                if verbose:
                    print "  - %s/%s.%s will be included in the list of database tables to merge" % (tmp_dir, dir_name, ot)
                monthly_dbs[ot] += tmp_dir+"/"+dir_name+"."+ot+" "

if verbose:
    print " - 4c. START: Merging dbcentral databases together into database %s" % composite_db

for ot in sorted(monthly_dbs.iterkeys()):
    # Trust that dbunjoin did its job properly and just cat them
    retcode = os.system( "cat "+monthly_dbs[ot]+" > "+composite_db+"."+ot )

if verbose:
    print " - 4d. END: Merging dbcentral databases together"

# }}} Merge monthly dbs back together

# {{{ Modify the dir path to the real-time archive

if verbose:
    print " - 5. Find and replace directory name in wfdisc table %s" % composite_db
# Clean up local references 
retcode_clean_1 = os.system( "dbset "+tmp_dir+"/"+sta_code+"_comp.wfdisc dir '*' 'patsub(dir, \""+wfdisc_dir_search+"\", \""+wfdisc_dir_replace+"\")'" )
"""
# Clean up the real time references 1
retcode_clean_2 = os.system( "dbset "+tmp_dir+"/"+sta_code+"_comp.wfdisc dir '*' 'patsub(dir, \""+wfdisc_dir_search_export_1+"\", \""+wfdisc_dir_replace_export_1+"\")'" )
# Clean up the real time references 2
retcode_clean_3 = os.system( "dbset "+tmp_dir+"/"+sta_code+"_comp.wfdisc dir '*' 'patsub(dir, \""+wfdisc_dir_search_export_2+"\", \""+wfdisc_dir_replace_export_2+"\")'" )

# Clean up /anf/anfops1 references so it works with the new SDSC layout
retcode_clean_4 = os.system( "dbset "+tmp_dir+"/"+sta_code+"_comp.wfdisc dir '*' 'patsub(dir, \""+wfdisc_dir_search_sdsc+"\", \""+wfdisc_dir_replace_sdsc+"\")'" )

# Clean up Franks non fix of moving the wfs from /anf/TA/dbs/certified/ to /anf/TA/dbs/wfs/certified/ without fixing the dir and dfile entries across the whole archive
retcode_clean_5 = os.system( "dbset "+tmp_dir+"/"+sta_code+"_comp.wfdisc dir '*' 'patsub(dir, \""+wfdisc_dir_search_sdsc_2+"\", \""+wfdisc_dir_replace_sdsc_2+"\")'" )

# Clean up Franks introduction of /wfs/wfs in the path name. See JIRA ticket TA-354
retcode_clean_6 = os.system( "dbset "+tmp_dir+"/"+sta_code+"_comp.wfdisc dir '*' 'patsub(dir, \""+wfdisc_dir_search_sdsc_3+"\", \""+wfdisc_dir_replace_sdsc_3+"\")'" )

# Clean up Franks introduction of /event_dbs in the path name. See JIRA ticket TA-354
retcode_clean_7 = os.system( "dbset "+tmp_dir+"/"+sta_code+"_comp.wfdisc dir '*' 'patsub(dir, \""+wfdisc_dir_search_sdsc_4+"\", \""+wfdisc_dir_replace_sdsc_4+"\")'" )

# Clean up links to non-existent dmc dirs
# retcode_clean_6 = os.system( "dbset "+tmp_dir+"/"+sta_code+"_comp.wfdisc dir '*' 'patsub(dir, \""+wfdisc_dir_search_sdsc_3+"\", \""+wfdisc_dir_replace_sdsc_3+"\")'" )
"""

# }}} Modify the dir path to the real-time archive

# {{{ Create composite db descriptor file
comp_db_descriptor = open( composite_db, "w" )
comp_db_descriptor.write("# Datascope Database Descriptor file\nschema css3.0\n" )
comp_db_descriptor.close()
# }}} Create composite db descriptor file

# {{{ Write out composite db to pf
tmp_pf_reopen = open(filename,'a')
# pfput( "ev_database", composite_db, 'testpf' )
tmp_pf_reopen.write("ev_database    %s\n" % composite_db)
tmp_pf_reopen.close()
# }}} Write out composite db to pf

# {{{ Parameter file placeholder for specific station data
info_handle = open(filename,'a')
# pfput( "eventinfopf", $dump_pf, 'testpf' ) # pfput not in Python interface
info_pf = eol_plots_dir + '/' + sta_code + '/' + sta_code + '_info.pf'
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

db_comp_joined = db_comp_assoc.join(db_comp_arrival)
db_comp_joined = db_comp_joined.join(db_comp_origin)
db_comp_joined = db_comp_joined.subset("sta =~ /%s/" % sta_code)
db_comp_joined = db_comp_joined.subset("time > %s" % sta_cert_time)
# }}} Dbops on the composite database

# {{{ Regional and global event loop

for dbK in event_types:

    if verbose:
        print "  - Retrieving a %s event" % dbK

    loc = dbK[:3]

    # pfput( "dbs_".$dbK, $composite_db, 'testpf' )
    tmp_pf_reopen_2 = open(filename,'a')
    tmp_pf_reopen_2.write("dbs_%s    %s\n" % (dbK,composite_db) )
    tmp_pf_reopen_2.close()

    if dbK is 'global':
        db_comp_joined_type = db_comp_joined.subset("(delta > 10 && delta < 180)")
    else:
        db_comp_joined_type = db_comp_joined.subset("(delta < 10)")


    if db_comp_joined_type.record_count > 0:

        # {{{ At least one event

        db_comp_joined_type.sort(['mb','ms','ml'],reverse=True)

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

# }}} Regional and global event loop

if verbose:
    print " - 8. END: Loop to get regional and teleseismic events of interest"

# {{{ Write the parameter file out
# Not needed as no pfput function. We have already written out information
# if verbose:
#     print " - 9. Write out parameter file %s" % filename
# pfwrite( filename, 'testpf' )
# }}} Write the parameter file out

# {{{ Create a directory for writing to if not already there
if verbose:
    print " - 9. Create output directory %s/%s" % (eol_plots_dir,sta_code)

if not os.path.exists( eol_plots_dir+"/"+sta_code ):
    os.mkdir( eol_plots_dir+"/"+sta_code, 0777 )
# }}} Create a directory for writing to if not already there

# {{{ Run Matlab script

if verbose:
    print " - 10. START: Matlab script"
#    print " - 10.a. Changing directory to /bin/eol_plots"

#os.chdir('bin/eol_plots')

# Cannot use -nodisplay because we need to use Ghostscript
# cmd = "/usr/local/bin/matlab -nodisplay -nodesktop -nosplash -r \"addpath('%s','bin/eol_plots/')\" < bin/eol_plots/eol_reports.m" % tmp_dir
cmd = "/usr/local/bin/matlab -nosplash -r \"addpath('%s','bin/eol_plots/')\" < bin/eol_plots/eol_reports.m" % tmp_dir

if verbose:
    print " - 10.b. Running Matlab script /export/home/rt/rtsystems/www/bin/eol_plots/eol_reports.m"
    print " - 10.c. %s" % cmd

output = os.system( "%s" % cmd )

if verbose:
    print " - 10.c. Changing directory back to /export/home/rt/rtsystems/www/"

#os.chdir('../../')

# }}} Run Matlab script

if verbose:
    print " - 11. END: Matlab script"

# {{{ Crop and convert images
iterator = 1
errors = 0

for sda in station_digest_assets:
    if "pf" not in sda:
        if os.path.isfile("%s/%s/%s%s.eps" % (eol_plots_dir, sta_code, sta_code, sda)):
            if verbose:
                print " - 12."+str(iterator)+". "+sta_code+sda+".eps image successfully created. Now trim it"
            trim_retcode = os.system( "convert -density 144 "+eol_plots_dir+"/"+sta_code+"/"+sta_code+sda+".eps -trim -resize 50% "+eol_plots_dir+"/"+sta_code+"/"+sta_code+sda+"_final.png" )
        else:
            errors += 1
            if verbose:
                print " - 12."+str(iterator)+". Error! "+sta_code+sda+" image not created!"
    iterator += 1

# }}} Crop and convert images

# {{{ Clean up the tmp dir

if errors == 0:
    if verbose:
        print " - 13. Clean up the tmp directory."
    for dir_file in os.listdir(tmp_dir):
        os.remove(tmp_dir+"/"+dir_file)
    try:
        os.removedirs('%s' % tmp_dir )
    except OSError:
        print "Temp directory %s not removed. Error." % tmp_dir
else:
    if verbose:
        print " - 13. ***NOT*** cleaning up the tmp directory. Errors were encountered. Leaving for diagnostics."

# }}} Clean up the tmp dir

# Ending timestamp
if verbose:
    print " - 14. END: Script for %s finished at %s" % (sta_code,epoch2str( time.time(), "%Y-%m-%d %H:%M:%S" ))

# Reset Antelope PFPATH enviromental variable
os.environ['PFPATH'] = saved_pfpath_env

