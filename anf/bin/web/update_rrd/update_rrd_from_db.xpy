"""
A script to retroactively generate RRD archives for SOH data.
"""
MAX_THREADS = 32
sys.path.append('/opt/anf/5.4pre/lib/python/python_rrdtool-1.4.7-py2.7-linux-' \
    'x86_64.egg')
import threading
import time
import logging
import rrdtool
import subprocess
from argparse import ArgumentParser
from re import compile
from antelope.datascope import dbopen, closing, freeing, trdestroying
from antelope.stock import epoch2str, now, pfupdate, pfin, pfread, PfReadError
from update_rrd_functions import check_rrd, get_stations, \
    get_dbs, get_data, configure_logger, Timer
from collections import defaultdict

def chan_thread(chan, sta, myrrdpath, stadb, null_run):
    """
    Perform RRD updates for a given stachan pair and input database
    """
    time_logger = logging.getLogger('update_rrd_from_db_time_stats')
    with Timer() as thread_timer:
        #build absolute file name of RRD
        rrd = '%s/%s/%s_%s.rrd' % (myrrdpath, sta, sta, chan)
        #verbose mode logging
        if verbose:
            main_logger.info(' subset for %s:%s  %s' \
                % (sta, chan, rrd))
        #subset the input wfdisc for correct channel and time sort
        with freeing(stadb.subset('chan =~ /%s/' % chan)) as tempdb:
            nrecs = tempdb.record_count
            if nrecs > 0:
                tempdb = tempdb.sort('time')
                tempdb.record = 0
                first_time = tempdb.getv('time')[0]
                tempdb.record = nrecs - 1
                last_time = tempdb.getv('endtime')[0]
            #verbose mode logging
            if verbose:
                main_logger.info(' %s records in database' \
                    % tempdb.record_count)
            #loop over all wfdisc rows, extract data and update RRD
            for record in tempdb.iter_record():
                #verbose mode logging
                if verbose:
                    main_logger.info(' record #%s ' % record.record)
                #extract some info from db
                starttime, endtime, nsamp = record.getv('time', 'endtime', \
                    'nsamp')
                #if there are no samples in wfdisc row, log it, and 
                #move to next row
                if nsamp == 0:
                    main_logger.info(' no elements in wfdisc record %s %s:%s ' \
                        '%s - %s' % (db, sta, chan, \
                        epoch2str(starttime, '%Y%j %T'), \
                        epoch2str(endtime, '%Y%j %T')))
                    continue
                #verbose mode logging
                if verbose:
                    main_logger.info(' %s %s [%s samples]' \
                        % (starttime,endtime,nsamp))
                #try to get info (need last update time) from RRD
                try:
                    info = rrdtool.info(rrd)
                except Exception as e:
                    raise(Exception('chan_thread: rrdtool.info(rrd) - %s' \
                        % e))
                #make sure that the start time of the data segment to
                #be requested is later than the RRD last update time
                #and skip the segment if the data RRD has already been
                #updated beyond the end of the segment
                starttime_save = starttime
                if starttime <= info['last_update']:
                    if endtime <= info['last_update']: continue
                    else: starttime = info['last_update'] + 1
                #get the waveform data from the database
                #move on to the next wfdisc row if data can't be
                #retrieved
                try:
                    subset_list, endtime = get_data(record, sta, chan, \
                        starttime, endtime, rrd_max_recs, verbose)
                except Exception as e:
                    main_logger.error(' %s\t- skipping %s:%s' \
                        % (e, sta, chan))
                    continue
                #update the RRD with all of the waveform data retrieved
                if not null_run:
                    for subset in subset_list:
                        try:
                            rrdtool.update([rrd] + [str(x) for x in subset])
                        except Exception as e:
                            main_logger.error(' %s - skipping %s:%s %d - %d ' \
                                '(%d)' % (e, sta, chan, starttime, endtime, \
                                starttime_save))
                            continue
                        #verbose mode logging
                        if verbose:
                            main_logger.info(' rrdtool update %s_%s.rrd [%d] ' \
                                'recs' % (sta, chan, len(subset)))
    if nrecs > 0:
        time_logger.info('\tTHREAD:RRD creation took %f seconds for thread ' \
            '%s:%s %s-%s' % (thread_timer.elapsed, sta, chan, \
            epoch2str(first_time, '%Y%j %T'), epoch2str(last_time, '%Y%j %T')))

#create command line argument parser
parser = ArgumentParser()
parser.add_argument('db', type=str, help='input db, use -c to specify ' \
    'cluster name if db is dbcentral cluster table.')
parser.add_argument('dbmaster', type=str, \
    help='dbmaster')
parser.add_argument('rrd_path', type=str, \
    help='base path to house RRD sub-directories')
parser.add_argument('-c', '--cluster_name', type=str, \
    help='use dbcentral clusters table')
parser.add_argument('-s', '--sta_subset', type=str, \
    help='station subset (regex)')
parser.add_argument('-z', '--chan_subset', type=str, \
    help='channel subset (regex)')
parser.add_argument('-n', '--net_code', type=str, \
    help='only process stations belonging to net_code network')
parser.add_argument('-p', '--parameter_file', type=str, \
    help='parameter file')
parser.add_argument('-l', '--log_file', type=str, \
    help='log file')
parser.add_argument('-v', '--verbose', action='store_true', \
    help='verbose output')
parser.add_argument('-a', '--active', action='store_true', \
    help='active only')
parser.add_argument('-r', '--rebuild', action='store_true', \
    help='rebuild RRD from scratch')
parser.add_argument('-N', '--null_run', action='store_true', \
    help='perform null run (ie. no writes except to log)')
#parse command line arguments
args = parser.parse_args()
#create a log
if args.log_file: logfile = args.log_file
else: logfile = '/anf/TA/work/white/update_rrd_from_db_%s' \
    % epoch2str(now(), '%Y%j%H%M%S')
configure_logger(logfile)
main_logger = logging.getLogger('update_rrd_from_db')
time_logger = logging.getLogger('update_rrd_from_db_time_stats')
#log the start time of script execution
main_logger.info(' START SCRIPT TIME: %s' \
    % epoch2str( now(),'%Y-%m-%d (%j) %T' ))
#parse parameter file
if args.parameter_file:
    pf = pfin(args.parameter_file)
else:
    try:
        pf = pfread(sys.argv[0])
    except PfReadError:
        m = 'parameter file not found, exiting.'
        main_logger.error(' %s' % m)
        sys.exit(m)
#store command line arguments in easily accessible variables
verbose = args.verbose
active = args.active
rebuild = args.rebuild
null_run = args.null_run
sta_subset = args.sta_subset if args.sta_subset else False
chan_subset = args.chan_subset if args.chan_subset else False
#dbmaster path
dbmaster = args.dbmaster
#dbcentral path
dbcentral = args.db
#active RRD output path
#rrdpath = '/anf/web/vhosts/anf.ucsd.edu/dbs/'
rrdpath = args.rrd_path
#maximum number of entries per RRD update (arbitrary)
rrd_max_recs = 10000
rrd_npts = 1600
#verbose mode logging
if verbose:
    main_logger.info(' get databases from %s:' % dbcentral)
#get a time ordered dictionary of SOH dbs from dbcentral
if args.cluster_name:
    dbcentral_dbs = get_dbs(dbcentral, args.cluster_name,verbose)
else:
    if os.path.exists('%s.clusters' % dbcentral):
        sys.exit('%s looks like a dbcentral cluster, specify \'-c\' option. ' \
            'quitting.' % dbcentral)
    dbcentral_dbs = {1: {'dir': os.path.dirname(dbcentral), \
        'dfile': os.path.basename(dbcentral)}}
#verbose mode logging
if verbose:
    for db in sorted(dbcentral_dbs.keys()):
        main_logger.info( ' %s:' % db)
        main_logger.info( ' dir  %s' % dbcentral_dbs[db]['dir'])
        main_logger.info( ' dfile  %s' % dbcentral_dbs[db]['dfile'])
#verbose mode logging
if verbose:
    main_logger.info(' get stations from %s:' % dbmaster)
#get list of stations to process from dbmaster
try:
    stations = get_stations(dbmaster,sta_subset,active,verbose)
except Exception as e:
    main_logger.info(' %s' % e)
    raise
#verbose mode logging
if verbose:
    main_logger.info(' processing the following stations:')
    for net in sorted(stations.keys()):
        for sta in sorted(stations[net].keys()):
            main_logger.info( ' %s_%s:\tvnet: %s\ttime: %s\tendtime:%s' \
                % (net, sta,stations[net][sta]['vnet'], \
                stations[net][sta]['time'], \
                stations[net][sta]['endtime']))
#loop over and process data for each network
for net in sorted(stations.keys()):
    #only do TA for now
    if args.net_code and net != args.net_code:
        continue
    #loop over and process each station in network
    for sta in sorted(stations[net].keys()):
        with Timer() as sta_timer:
            vnet = stations[net][sta]['vnet']
            mytime = stations[net][sta]['time']
            endtime = stations[net][sta]['endtime']
            #verbose mode logging
            if verbose:
                main_logger.info(' %s_%s: [%s] %s %s' \
                    % (net, sta, vnet, mytime, endtime))
            #create the vnet directory to house the RRDs if necessary
            for path in ['%s/rrd' % rrdpath, '%s/rrd/%s' % (rrdpath, vnet)]:
                if not os.path.exists(path) and not null_run:
                    main_logger.info(' make directory %s ' % path)
                    try:
                        os.mkdir(path)
                    except Exception as e:
                        e = ' %s - os.mkdir(path)' % e
                        main_logger.error(e)
                        raise(Exception(e))
            #build RRD folder path using the vnet value.
            myrrdpath = '%s/rrd/%s' % (rrdpath, vnet)
            #retain only channels matching chan_subset in list of
            #channels to process
            if chan_subset:
                pattern = compile(chan_subset.replace('*', '.'))
                pf['Q330_SOH_CHANNELS'] = [chan for chan in \
                    pf['Q330_SOH_CHANNELS'] if pattern.search(chan)]
                if verbose:
                    main_logger.info(' subset channels =~ /%s/' % chan_subset)
            #Create a dictionary that stores flags to determine whether
            #or not the RRD for each channel at this station has been
            #checked.
            rrd_checked = {}
            for chan in pf['Q330_SOH_CHANNELS']: rrd_checked[chan] = False
            #loop over and process each database in dbcentral.
            for dbtime in sorted(dbcentral_dbs.keys()):
                with Timer() as db_timer:
                    dbdir = dbcentral_dbs[dbtime]['dir']
                    dbdfile = dbcentral_dbs[dbtime]['dfile']
                    db = '%s/%s' % (dbdir,dbdfile)
                    #verbose mode logging
                    if verbose:
                        main_logger.info(' %s' % db)
                    #subset database for all rows with matching station
                    with closing(dbopen(db, 'r')) as stadb:
                        stadb = stadb.schema_tables['wfdisc']
                        stadb = stadb.subset('sta =~ /%s/' % sta )
                        #if there are no matching rows, continue with
                        #next database
                        if stadb.record_count == 0:
                            continue
                        #check RRD for each channel at station if not
                        #already checked
                        for chan in pf['Q330_SOH_CHANNELS']:
                            if not rrd_checked[chan]:
                                #build the path to the RRD directory
                                rrd = myrrdpath+'/'+sta
                                #create the station directory to house
                                #the RRDs if necessary
                                if not os.path.exists(rrd) and not null_run:
                                    main_logger.info(' make RRD directory %s ' \
                                        % rrd)
                                    try:
                                        os.mkdir(rrd)
                                    except Exception as e:
                                        e = ' %s - os.mkdir(rrd)' % e
                                        main_logger.error(e)
                                        raise(Exception(e))
                                #build the absolute path to the RRD file
                                rrd = '%s/%s/%s_%s.rrd' \
                                    % (myrrdpath, sta, sta, chan)
                                #verbose mode logging
                                if verbose and rebuild:
                                    main_logger.info(' clean RRD table for ' \
                                        '%s:%s %s' % (sta, chan, rrd))
                                #check that rrd exists and if specified,
                                #create a new, empty RRD
                                try:
                                    check_rrd(rrd, chan, stadb, verbose, \
                                        rebuild, rrd_npts, null_run)
                                except Exception as e:
                                    e = '%s' % e
                                    raise(Exception(e))
                                rrd_checked[chan] = True
                        #loop over all channels for station and create
                        #a new thread for each. If there are MAX_THREAD
                        #active channel threads, sleep for a minute
                        #then try again. +1 is for main thread.
                        for chan in pf['Q330_SOH_CHANNELS']:
                            while not threading.active_count() < MAX_THREADS+1:
                                main_logger.info(' active thread count: %d' \
                                    '\tsleeping...' \
                                    % threading.active_count()-1)
                                time.sleep(60)
                            #keep trying until a new thread is
                            #successfully created
                            successful = False
                            while not successful:
                                try:
                                    #create new thread
                                    new_thread = threading.Thread(\
                                        target=chan_thread, \
                                        args=(chan, sta, myrrdpath, stadb, \
                                        null_run))
                                    #start new thread
                                    new_thread.start()
                                    successful = True
                                    main_logger.info(' new thread started for '\
                                        '%s:%s\tactive thread count: %d' \
                                        % (sta, chan, \
                                        threading.active_count()-1))
                                except Exception as e:
                                    main_logger.error(e)
                        #make sure all threads reading from this
                        #database are finished before closing database
                        while threading.active_count() > 1:
                            main_logger.info(' station %s still has %d ' \
                                'channel threads actively accessing db %s' \
                                '\twaiting to close db...' \
                                % (sta, threading.active_count()-1, db))
                            time.sleep(60)
                        main_logger.info(' station %s RRD writes complete for '\
                            'db %s/%s' % (sta, dbcentral_dbs[dbtime]['dir'], \
                            dbcentral_dbs[dbtime]['dfile']))
                time_logger.info('\tDB:RRD creation took %f seconds for ' \
                    'database %s/%s' % (db_timer.elapsed, \
                        dbcentral_dbs[dbtime]['dir'], \
                        dbcentral_dbs[dbtime]['dfile']))
        time_logger.info('\tSTA:RRD creation took %f seconds for station %s' \
            % (sta_timer.elapsed, sta))

main_logger.info(' END SCRIPT TIME: %s' \
    % epoch2str( now(),'%Y-%m-%d (%j) %T' ))

#if __name__ == '__main__': sys.exit(main())
#else:
#    print 'Not a module to import!!'
#    sys.exit(-1)
