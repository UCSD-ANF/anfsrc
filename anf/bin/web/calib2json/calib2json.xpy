import sys
import os
import json
import time
import string
import gzip
import tempfile
import inspect
from optparse import OptionParser
from time import strftime

from antelope.datascope import *
from antelope.stock import *


usage = "Usage: %prog [options]"

parser = OptionParser(usage=usage)

parser.add_option("-v", action="store_true", dest="verbose", help="verbose output", default=False)
parser.add_option("-t", action="store_true", dest="type", help="type of station to process", default=False)

(options, args) = parser.parse_args()

if options.verbose:
    verbose = True
else:
    verbose = False



def _db_table_check(dbpointer,tblname):

    table_list = dbpointer.query(dbSCHEMA_TABLES)
    if tblname in table_list:
        return 0
    else:
        return -1


db_path = '/anf/TA/'
#web_path = '/data/'
web_path = './'

colors = {
    '0_white':'#E6E6E6',
    '1_red':'#990000',
    '1_red_half':'red_stripe.png',
    '2_orange':'#FFB366',
    '2_orange_half':'orange_stripe.png',
    '3_yellow':'#FFFF66',
    '3_yellow_half':'yellow_stripe.png',
    '4_green':'#B3FF66',
    '4_green_half':'green_stripe.png',
    '5_blue':'#66B3FF',
    '5_blue_half':'blue_stripe.png',
    '6_gray':'#A3A3A3',
    '6_gray_half':'gray_stripe.png'
}

wfdisc_latest = {} # Holds the most recent wfdisc entries for all channels

summary_dict = { 'colors':colors, 'stations':{} }

temp_calib_status = {} # This is an internal dictionary that just tracks if a station was successfully calibrated

now       = time.time()
hour      = 60*60
day       = hour*24
week      = day*7
month     = week*4
six_month = month*6

common_pf = "/anf/web/vhosts/anf.ucsd.edu/conf/common.pf"
pf = pfupdate( common_pf )

cache_json = pf['CACHEJSON']
dbmaster   = pf['USARRAY_DBMASTER']
dbcalib    = pf['DBCALIB']

cal_fields     = ( "time", "endtime", "dlcaltype", "dlcalerr" )
dlevent_fields = ( "dlname", "time", "dlevtype", "dlcomment" )
# plot_fields    = ( "chan", "time", "endtime" )
wfdisc_fields  = ( "sta", "chan", "time", "endtime" )

hrs = 7*24 # Hours between successful pairs of calibrations, any longer and it is considered unrelated
calib_pair_time_gap = hrs*60*60 # In secs


if verbose:
    print "Station calibration to JSON started at %s" % time.strftime( "%a, %d %b %Y %H:%M:%S UTC" )

db            = dbopen( dbmaster, "r" )
db_deploy     = db.lookup(table='deployment')
db_site       = db.lookup(table='site')
db_adopt      = db.lookup(table='adoption')
db_snetsta    = db.lookup(table='snetsta')
db_comm       = db.lookup(table='comm')
db_sensor     = db.lookup(table='sensor')
db_instrument = db.lookup(table='instrument')

# These working are reliant on the schema extensions being installed...
dbc         = dbopen( dbcalib, "r" )
dlcalwf_tbl = 'dlcalwf'
dlevent_tbl = 'dlevent'
calplot_tbl = 'calplot'
wfdisc_tbl  = 'wfdisc'
calib_tables = [dlcalwf_tbl, dlevent_tbl, calplot_tbl, wfdisc_tbl]

# Quick test of all required db tables
for tbl in calib_tables:
    if _db_table_check(dbc, tbl) < 0:
        print "  - Cannot open %s.%s. Check schema..." % (dbcalib,tbl)
        exit()

db_dlcalwf = dbc.lookup(table='dlcalwf')
db_dlevent = dbc.lookup(table='dlevent')
db_calplot = dbc.lookup(table='calplot')
db_wfdisc  = dbc.lookup(table='wfdisc')

db_join_active = db_site.join(db_snetsta)
db_join_active = db_join_active.join(db_deploy)
db_join_active = db_join_active.subset("offdate == NULL || offdate >= now()")
db_join_active = db_join_active.subset("endtime >= now()")
db_join_active = db_join_active.subset("time <= now()")
db_join_active = db_join_active.join(db_comm,outer=True)
db_join_active = db_join_active.subset("comm.endtime == NULL || comm.endtime >= now()")
db_join_active = db_join_active.join(db_sensor,outer=True)
db_join_active = db_join_active.join(db_instrument,outer=True)
db_join_active = db_join_active.subset("sensor.endtime == NULL || sensor.endtime >= now()")
db_join_active = db_join_active.subset("insname != NULL")
db_join_active = db_join_active.subset("snet =~ /TA/ && chan =~ /BHZ.*/")
mydb_active = db_join_active.sort(tuple(["sta"]),unique=True)
nrecs_active = mydb_active.query(dbRECORD_COUNT)

for i in range(0,nrecs_active):

    mydb_active.record = i
    sta = mydb_active.getv("fsta")[0]
    snet = mydb_active.getv("snet")[0]

    # Get the records for each station
    sub_dlcalwf = "fsta=~/%s/ && dlcaltype =~ /white/" % sta
    sub_dlevent = "dlname=~/%s_%s/" % (snet,sta)
    sub_calplot = "sta=~/%s/" % sta
    sub_wfdisc = "sta=~/%s/ && chan =~ /BH.*/" % sta

    db_dlcalwf_sta = db_dlcalwf.subset(sub_dlcalwf)
    db_dlevent_sta = db_dlevent.subset(sub_dlevent)

    # db_dlcalwf_sta[3] = 0
    # db_dlevent_sta[3] = 0

    print "- Station %s_%s" % (snet,sta)

    station_dict = { 'dlcalwf':{}, 'dlevent':{}, 'calplot':{} }
    summary_dict['stations'][sta] = {}
    wfdisc_latest = {} # Holds the most recent wfdisc entries for all channels


    db_wfdisc_sta       = db_wfdisc.subset(sub_wfdisc)
    db_wfdisc_sta       = db_wfdisc_sta.sort(tuple(["time"]),reverse=True)
    db_wfdisc_sta_nrecs = db_wfdisc_sta.record_count

    wfdisc_latest = {}

    if db_wfdisc_sta_nrecs > 0:


        # db_wfdisc_sta[3] = 0
        # db_wfdisc_latest_time = (dbgetv( db_wfdisc_sta, "time" ) )[0]
        # db_wfdisc_latest_endtime = (dbgetv( db_wfdisc_sta, "endtime" ) )[0]

        # Group by time
        db_wfdisc_grp = db_wfdisc_sta.group("time" )

        # Get the most recent two groups (should be BHE|BHZ and BHN|BHZ)
        for w in range(db_wfdisc_grp.record_count):

            db_wfdisc_grp.record  = w

            wfdisc_latest[w] = {'BHE':{'time':'','endtime':''}, 'BHN':{'time':'','endtime':''}, 'BHZ':{'time':'','endtime':''}}

            wf_grp_time = db_wfdisc_grp.getv("time")[0]

            db_wfdisc_grp_sub = db_wfdisc_grp.subset("time == %f" % db_wfdisc_grp.getv("time")[0])


            db_wfdisc_ungrp   = db_wfdisc_grp_sub.ungroup()

            db_wfdisc_ungrp_sort = db_wfdisc_ungrp.sort( "chan" )

            for x in range(db_wfdisc_ungrp_sort.record_count):

                db_wfdisc_ungrp_sort.record = x

                this_chan    = db_wfdisc_ungrp_sort.getv("chan")[0]
                this_time    = db_wfdisc_ungrp_sort.getv("time")[0]
                this_endtime = db_wfdisc_ungrp_sort.getv("endtime")[0]

                wfdisc_latest[w][this_chan] = {}

                wfdisc_latest[w][this_chan]['time']    = this_time
                wfdisc_latest[w][this_chan]['endtime'] = this_endtime

                del( this_chan, this_time, this_endtime )

        # For troubleshooting
        # print "Time is: %s Endtime is: %s" % (db_wfdisc_latest_time,db_wfdisc_latest_endtime)
        # db_wfdisc_latest_time = strtime( (dbgetv( db_wfdisc_sta, "time" ) )[0] ) + " UTC"
        # db_wfdisc_latest_endtime = strtime( (dbgetv( db_wfdisc_sta, "endtime" ) )[0] ) + " UTC"
        # print "    - Latest wfdisc time is %s and endtime is %s" % (db_wfdisc_latest_time,db_wfdisc_latest_endtime)

        # print wfdisc_latest




    db_calplot_sta       = db_calplot.subset( sub_calplot )

    if db_calplot_sta.record_count > 2 :

        temp_calib_status = 1


        db_calplot_sta_sort      = db_calplot_sta.sort( "time" )
        db_calplot_grouped       = db_calplot_sta_sort.group( "time" ) # Group by time
        db_calplot_grouped_nrecs = db_calplot_grouped.record_count

        # Assume that a successful calibration has 
        # two groups of times, seperated by less
        # than var calib_pair_time_gap

        # Create a list for the entries
        groups = []

        for dcg in range(0,db_calplot_grouped_nrecs,2):

            db_calplot_grouped.record = dcg
            dcg_time = db_calplot_grouped.getv('time')[0]

            # Get the next record (so long as we are not on the last record)

            if dcg < (db_calplot_grouped_nrecs-1):

                # Increment the pointer
                db_calplot_grouped.record = dcg + 1
                dcg_time_next = db_calplot_grouped.getv('time')[0]

                # Only create pairs if less than predefined N hours
                # and append to groups list
                if (dcg_time_next-dcg_time) < calib_pair_time_gap:
                    groups.append( {'t0':dcg_time,'t0_str':epoch2str(dcg_time, '%Y-%m-%d %H:%M:%S'),'t1':dcg_time_next,'t1_str':epoch2str(dcg_time_next,'%Y-%m-%d %H:%M:%S')} )

                # Reset the pointer
                db_calplot_grouped.record = dcg - 1

            else:

                dcg_time_next = False


            del dcg_time
            del dcg_time_next

        if len(groups) > 0:


            last_times = groups[-1]

            group1 = db_calplot_grouped.subset("time == %.5f" % last_times['t0'])
            group2 = db_calplot_grouped.subset("time == %.5f" % last_times['t1'])

            station_dict['calplot'] = {}

            try:
                group1_ungrp = group1.ungroup()
                group1_ungrp.sort('chan')


                if group1_ungrp.record_count > 1 and group1_ungrp.record_count < 3:

                    group1_ungrp.record = 0
                    this_chan = group1_ungrp.getv('chan')[0]
                    this_time = group1_ungrp.getv('time')[0]
                    this_endtime = group1_ungrp.getv('endtime')[0]
                    this_filename = group1_ungrp.filename()[1]
                    this_file = this_filename.replace( db_path, web_path )
                    station_dict['calplot'][this_chan] = {'endtime':this_endtime,'endtime_readable':strtime(this_endtime)+" UTC",'file':this_file,'time':this_time,'time_readable':strtime(this_time)+" UTC"}

                    del this_chan
                    del this_time
                    del this_endtime
                    del this_filename
                    del this_file

                else:

                    print "    - Unexpected number of records for %s group 1 record set: %d" % (sta, group1_ungrp.record_count)


                group1_ungrp.free()

            except Exception,e:
                print "    - Caught exception (%s) for ungrouping group1: %s" % (Exception,e)
                print "    - Station %s: Last times, t0: %d, t0_str: %s" % (sta, last_times['t0'], last_times['t0_str'])
                print "    - Number of records in group1: %d" % group1.record_count

            group1.free()

            try:
                group2_ungrp = group2.ungroup()
                group2_ungrp.sort('chan')


                if group2_ungrp.record_count > 1 and group2_ungrp.record_count < 3:

                    for j in range(group2_ungrp.record_count):

                        group2_ungrp.record = j
                        this_chan = group2_ungrp.getv('chan')[0]
                        this_time = group2_ungrp.getv('time')[0]
                        this_endtime = group2_ungrp.getv('endtime')[0]
                        this_filename = group2_ungrp.filename()[1]
                        this_file = this_filename.replace( db_path, web_path )
                        station_dict['calplot'][this_chan] = {'endtime':this_endtime,'endtime_readable':strtime(this_endtime)+" UTC",'file':this_file,'time':this_time,'time_readable':strtime(this_time)+" UTC"}

                        del this_chan
                        del this_time
                        del this_endtime
                        del this_filename
                        del this_file

                else:

                    print "    - Unexpected number of records for %s group 2 record set: %d" % (sta, group2_ungrp,record_count)


                group2_ungrp.free()

            except Exception,e:
                print "    - Caught exception (%s) for ungrouping group2: %s" % (Exception,e)
                print "    - Station %s: Last times, t1: %d, t1_str: %s" % (sta, last_times['t1'], last_times['t1_str'])
                print "    - Number of records in group2: %d" % group2.record_count

            group2.free()

            #-+-+-+- calplot_counter = 0 # Start counter for array keys

            # Only care about the most recent plots, so only get last result from group
            # for j in range(0,db_calplot_grouped_nrecs):

            #-+-+-+- if db_calplot_grouped_nrecs <= 4:
            #-+-+-+-     calrange = 1
            #-+-+-+- else:
            #-+-+-+-     calrange = 2

            '''
            for j in range(calrange):


                db_calplot_grouped[3] = j

                # Get the group of interest
                group_time = dbgetv( db_calplot_grouped, "time" )[0]
                # print "Time is %s" % group_time
                group_sub  = dbsubset( db_calplot_grouped, "time == %f" % group_time )
                ungrouped  = dbungroup( group_sub )


                ungrouped_sort    = dbsort( ungrouped,"chan" )
                ungrouped_sort[3] = 0

                if dbgetv(ungrouped_sort,"chan")[0] == "BHE":

                    ungrouped_sort = dbprocess( ungrouped_sort, "dbsubset chan =~ /BHE/" )

                # Should only ever be one record (BHE) or two records (BHN|BHZ) now!
                ungrouped_sort_nrecs = dbnrecs( ungrouped_sort )

                for k in range(0,ungrouped_sort_nrecs): # 1 or 2

                    ungrouped_sort[3] = k

                    calplot_chan = dbgetv(ungrouped_sort,"chan")[0]

                    # print "Working on chan %s" % calplot_chan

                    station_dict['calplot'][calplot_counter] = {} # Make sure we create a dictionary

                    station_dict['calplot'][calplot_counter]['chan'] = calplot_chan

                    # Get filename & add to dictionary
                    filename = dbfilename( ungrouped_sort )
                    station_dict['calplot'][calplot_counter]['file'] = string.replace( filename, db_path, web_path )

                    # Need to make sure there are waveforms for the time of interest
                    # Need to subset wfdisc records by channel to match chan from calplot

                    if db_wfdisc_sta_nrecs > 0:

                        # print "Time is %s" % dbgetv(ungrouped_sort,'time')[0]
                        # print "Counter is %s" % j
                        # print wfdisc_latest[j][calplot_chan]

                        if int(dbgetv(ungrouped_sort,'time')[0]) >= int(wfdisc_latest[0][calplot_chan]['time']):

                            # print "    - SUCCESS: Chan is: %s\tTime is: %s\tWfdisc time is: %s" % ( calplot_chan, dbgetv(ungrouped_sort,'time')[0], wfdisc_latest[0][calplot_chan]['time'] )
                            station_dict['calplot'][calplot_counter]['time']          =  dbgetv(ungrouped_sort,'time')[0]
                            station_dict['calplot'][calplot_counter]['time_readable'] = strtime( dbgetv(ungrouped_sort,'time')[0] ) + " UTC"

                        elif int(dbgetv(ungrouped_sort,'time')[0]) >= int(wfdisc_latest[1][calplot_chan]['time']):

                            # print "    - SUCCESS: Chan is: %s\tTime is: %s\tWfdisc time is: %s" % ( calplot_chan, dbgetv(ungrouped_sort,'time')[0], wfdisc_latest[1][calplot_chan]['time'] )
                            station_dict['calplot'][calplot_counter]['time']          =  dbgetv(ungrouped_sort,'time')[0]
                            station_dict['calplot'][calplot_counter]['time_readable'] = strtime( dbgetv(ungrouped_sort,'time')[0] ) + " UTC"

                        else:

                            print "    - Calibration plot time is less than wfdisc time, error"


                        if int(dbgetv(ungrouped_sort,'endtime')[0]) <= int(wfdisc_latest[0][calplot_chan]['endtime']):

                            station_dict['calplot'][calplot_counter]['endtime']          =  dbgetv(ungrouped_sort,'endtime')[0]
                            station_dict['calplot'][calplot_counter]['endtime_readable'] = strtime( dbgetv(ungrouped_sort,'endtime')[0] ) + " UTC"

                        elif int(dbgetv(ungrouped_sort,'endtime')[0]) <= int(wfdisc_latest[1][calplot_chan]['endtime']):

                            station_dict['calplot'][calplot_counter]['endtime']          =  dbgetv(ungrouped_sort,'endtime')[0]
                            station_dict['calplot'][calplot_counter]['endtime_readable'] = strtime( dbgetv(ungrouped_sort,'endtime')[0] ) + " UTC"

                        else:

                            print "    - Calibration plot endtime is greater than wfdisc endtime, error"

                    else:

                        print "    - No matching entries in the wfdisc table: no successful calibration"

                    calplot_counter = calplot_counter + 1


            '''


        else:

            print "    - No calibration plots for %s" % sta


    elif int(db_calplot_sta.record_count) > 0 :

        temp_calib_status = 0.5

        print "    - Only one pair of calibration plots for %s" % sta

    else:

        temp_calib_status = 0

        print "    - No calibration plots for %s" % sta


    db_dlcalwf_sta_nrecs = int( db_dlcalwf_sta.record_count )

    # TODO: Subset for duration being longer than an hour

    if( db_dlcalwf_sta_nrecs > 0):

        db_dlcalwf_sta_sort = db_dlcalwf_sta.sort("time", False, True )

        db_dlcalwf_sta_sort.record = 0 # Get the first record


        for cf in cal_fields:

            dlcalwf_pointer = db_dlcalwf_sta_sort.lookup('', '', cf, 'dbNULL' );
            dlcalwf_detail = dlcalwf_pointer.query( dbFIELD_DETAIL ) ;
            dlcalwf_description = dlcalwf_pointer.query( dbFIELD_DESCRIPTION ) ;
            dlcalwf_type = dlcalwf_pointer.query( dbFIELD_TYPE ) ;
            dlcalwf_null = dlcalwf_pointer.getv( cf )[0]
            dlcalwf_value = db_dlcalwf_sta_sort.getv( cf )[0]

            if( dlcalwf_value == dlcalwf_null ):

                    station_dict['dlcalwf'][cf] = "null"

            else:

                if( dlcalwf_type == 4 ):
                    station_dict['dlcalwf'][cf] = dlcalwf_value
                    cf_readable = cf+'_readable'
                    station_dict['dlcalwf'][cf_readable] = strtime(dlcalwf_value) + " UTC"
                else:
                    station_dict['dlcalwf'][cf] = dlcalwf_value



        # print "Time now: %s" % str( now )
        # print "Time of calib: %s" % str( station_dict['dlcalwf']['time'] )

        if station_dict['dlcalwf']['endtime'] > time.time():
            station_dict['dlcalwf']['color'] = colors['1_red']
            summary_dict['stations'][sta]['color'] = colors['1_red']
            summary_dict['stations'][sta]['order'] = 1
            print "    - Calibration is currently running for %s" % sta
        else:
            if station_dict['dlcalwf']['time']:
                time_since_calib = now - station_dict['dlcalwf']['time']
                if time_since_calib < day:
                    if temp_calib_status == 1:
                        station_dict['dlcalwf']['color'] = colors['2_orange']
                        summary_dict['stations'][sta]['color'] = colors['2_orange']
                        summary_dict['stations'][sta]['order'] = 2
                    else:
                        station_dict['dlcalwf']['color'] = colors['2_orange_half']
                        summary_dict['stations'][sta]['color'] = colors['2_orange_half']
                        summary_dict['stations'][sta]['order'] = 2
                elif time_since_calib < week:
                    if temp_calib_status == 1:
                        station_dict['dlcalwf']['color'] = colors['3_yellow']
                        summary_dict['stations'][sta]['color'] = colors['3_yellow']
                        summary_dict['stations'][sta]['order'] = 3
                    else:
                        station_dict['dlcalwf']['color'] = colors['3_yellow_half']
                        summary_dict['stations'][sta]['color'] = colors['3_yellow_half']
                        summary_dict['stations'][sta]['order'] = 3
                elif time_since_calib < month:
                    if temp_calib_status == 1:
                        station_dict['dlcalwf']['color'] = colors['4_green']
                        summary_dict['stations'][sta]['color'] = colors['4_green']
                        summary_dict['stations'][sta]['order'] = 4
                    else:
                        station_dict['dlcalwf']['color'] = colors['4_green_half']
                        summary_dict['stations'][sta]['color'] = colors['4_green_half']
                        summary_dict['stations'][sta]['order'] = 4
                elif time_since_calib < six_month:
                    if temp_calib_status == 1:
                        station_dict['dlcalwf']['color'] = colors['5_blue']
                        summary_dict['stations'][sta]['color'] = colors['5_blue']
                        summary_dict['stations'][sta]['order'] = 5
                    else:
                        station_dict['dlcalwf']['color'] = colors['5_blue_half']
                        summary_dict['stations'][sta]['color'] = colors['5_blue_half']
                        summary_dict['stations'][sta]['order'] = 5
                else:
                    if temp_calib_status == 1:
                        station_dict['dlcalwf']['color'] = colors['6_gray']
                        summary_dict['stations'][sta]['color'] = colors['6_gray']
                        summary_dict['stations'][sta]['order'] = 6
                    else:
                        station_dict['dlcalwf']['color'] = colors['6_gray_half']
                        summary_dict['stations'][sta]['color'] = colors['6_gray_half']
                        summary_dict['stations'][sta]['order'] = 6
            else:
                if temp_calib_status == 1:
                    station_dict['dlcalwf']['color'] = colors['0_white']
                    summary_dict['stations'][sta]['color'] = colors['0_white']
                    summary_dict['stations'][sta]['order'] = 0
                else:
                    station_dict['dlcalwf']['color'] = colors['0_white_half']
                    summary_dict['stations'][sta]['color'] = colors['0_white_half']
                    summary_dict['stations'][sta]['order'] = 0
                # print "Time since last calibration in seconds for station %s:" % sta


    else:
        station_dict['dlcalwf']['color'] = colors['0_white']
        summary_dict['stations'][sta]['color'] = colors['0_white']
        summary_dict['stations'][sta]['order'] = 0


    db_dlevent_sta_nrecs = db_dlevent_sta.record_count

    if( db_dlevent_sta_nrecs > 0):

        db_dlevent_sta_sort = db_dlevent_sta.sort("time", False, True )

        db_dlevent_sta_sort.record = 0 # Get the first record

        for df in dlevent_fields:

            dlevent_pointer = db_dlevent_sta_sort.lookup('', '', df, 'dbNULL' );
            dlevent_detail = dlevent_pointer.query( dbFIELD_DETAIL ) ;
            dlevent_description = dlevent_pointer.query( dbFIELD_DESCRIPTION ) ;
            dlevent_type = dlevent_pointer.query( dbFIELD_TYPE ) ;
            dlevent_null = dlevent_pointer.getv( df )[0]
            dlevent_value = db_dlevent_sta_sort.getv( df )[0]

            # print "Pointer: '%s', Detail: '%s', Description: '%s', Type: '%s', Value: '%s', Null: '%s'" % (pointer,detail,description,type,value,null)

            if( dlevent_value == dlevent_null ):

                station_dict['dlevent'][cf] = "null"

            else:

                if( dlevent_type == 4 ):
                    station_dict['dlevent'][cf] = strtime(dlevent_value) + " UTC"
                else:
                    station_dict['dlevent'][cf] = dlevent_value

    else:
        print "    - No dlevents for %s" % sta



    sta_output_file_path = cache_json + '/calibrations/%s_%s.json+' % (snet,sta)

    f = open( sta_output_file_path, 'w' ) 
    json.dump( station_dict, f, sort_keys=True, indent=2 )
    f.flush()

    # Move each file to replace the older one
    sta_cache_file_path = cache_json + '/calibrations/%s_%s.json' % (snet,sta)
    os.rename(sta_output_file_path,sta_cache_file_path)

    # Gzip content
    # f_zip_in = open(sta_cache_file_path)
    # f_zip_out = gzip.open(cache_json+'/calibrations/%s_%s_gzip.json' % (snet,sta),'wb')
    # f_zip_out.writelines(f_zip_in)
    # f_zip_out.close()
    # f_zip_in.close()


    del wfdisc_latest


for key,value in sorted( summary_dict.iteritems(), key=lambda(k,v):(v,k)):
    print "%s: %s" % (key,value)

summary_output_file_path = cache_json + '/calibrations/calibration_summary.json+'
summary = open( summary_output_file_path, 'w' ) 
json.dump( summary_dict, summary, sort_keys=True, indent=2 )
summary.flush()

# Move each file to replace the older one
summary_cache_file_path = cache_json + '/calibrations/calibration_summary.json'
os.rename(summary_output_file_path,summary_cache_file_path)


if verbose:
    print "Station calibration to JSON ended at %s\n\n" % time.strftime( "%a, %d %b %Y %H:%M:%S UTC" )
