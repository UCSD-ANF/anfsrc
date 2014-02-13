"""
Functions that we need for the script
update_rrd_from_db

This file should be imported at the top
of the script. 

Juan Reyes
reyes@ucsd.edu

Malcolm White
mcwhite@ucsd.edu
"""
import logging
#import rrdtool

def check_rrd(file, chan, db, verbose, rebuild, npts, null_run):
    """
    Get RRD file ready.
    """
    from __main__ import subprocess
    from __main__ import sys
    from __main__ import os
    from __main__ import freeing
    from __main__ import rrdtool
    main_logger = logging.getLogger('update_rrd_from_db')
    #if RRD exists, and doesn't need to be rebuilt, do nothing
    if os.path.exists(file) and not rebuild: return
    #otherwise, build it
    with freeing(db.sort('time')) as dbview:
        dbview.record = 0
        time, samprate = dbview.getv('time', 'samprate')
        rra_step = {
            '7d': int(round(604800*samprate/npts)),
            '1m': int(round(2678400*samprate/npts)),
            '1y': int(round(31536000*samprate/npts)), 
            '3y': int(round(94608000*samprate/npts))
        }
        rrd_cmd = {}
        for twin in rra_step:
            for cf in ['MIN', 'MAX', 'AVERAGE']:
                rrd_cmd['%s_%s' % (twin, cf)] = \
                    'RRA:%s:0.5:%d:1600' % (cf, rra_step[twin])
        #define command to create RRD
        cmd = [str(x) for x in [
         '--start', int(time),
         '--step', samprate,
         'DS:%s:GAUGE:%d:U:U' % (chan, 10*samprate)
        ] + [rrd_cmd[key] for key in sorted(rrd_cmd.iterkeys())]
        ]
        #if rebuilding, remove old RRD
        if rebuild and not null_run:
            #if an RRD already exists, remove it
            if os.path.exists(file):
                try:
                    os.remove(file)
                except Exception as e:
                    raise(Exception('check_rrd(): %s' % e))
        #create new, empty RRD
        if not null_run:
            try:
                rrdtool.create(file, cmd)
            except Exception as e:
                raise(Exception('check_rrd(): rrdtool.create(file, cmd) - %s' % e))
            main_logger.info('check_rrd(): make %s \'%s\'' % (file, ' '.join(cmd)))
    #test to make sure an RRD exists
    if not os.path.exists(file):
        raise(Exception('check_rrd(): RRD file does not exist- %s' % file))

#def get_channels(verbose):
#    """
#    Get mapping of channels from miniseed to rrd.
#    """
#    from __main__ import pfupdate, pfin
#    #define where to find channel mapping
#    common_pf = '/anf/web/vhosts/anf.ucsd.edu/conf/common.pf'
#    var       = 'Q330_RRD_SOH_CHAN_MAPPING'
#    #verbose mode logging
#    if verbose:
#        logging.info('get_channels(): getting mapping of channels')
#        logging.info( 'get_channels(): reading %s' % common_pf)
#        logging.info( 'get_channels(): variable %s' % var)
#    #get and return channel mapping from pf
#    pfupdate( common_pf )
#    pf = pfin(common_pf)
#    return pf[var]

def get_dbs(dbcentral,clustername,verbose):
    """
    Get list of databases from the dbcentral list
    and return in a dictionary. Include the time
    metadata of each. 
    """
    from __main__ import dbopen, closing, epoch2str
    main_logger = logging.getLogger('update_rrd_from_db')
    #verbose mode logging
    if verbose:
        main_logger.info('get_dbs(): getting list of dbs from dbcentral')
    #an empty dictionary to hold database metadata
    clusters = {}
    #open dbcentral and subset for cluster of interest
    with closing(dbopen(dbcentral, 'r')) as db:
        db = db.schema_tables['clusters']
        db = db.subset('clustername =~ /%s/' % clustername)
        db = db.sort('time')
        #verbose mode logging
        if verbose:
            main_logger.info('get_dbs(): got %s records' % db.record_count)
        #if there are no dbcentral entries for cluster, close db and raise
        #exception
        if db.record_count == 0:
            e = 'get_dbs(): no clusters named %s in %s' % (clustername, dbcentral)
            raise(Exception(e))
        #if there is only one row for this clustername, and the volumes
        #are year volumes, construct the proper paths
        elif db.record_count == 1:
            db.record = 0
            if db.getv('volumes')[0] != 'year':
                e = 'get_dbs(): clustername %s in %s consists of %s volumes, ' \
                    'only year volumes are currently accepted.' \
                    % (clustername, dbcentral, db.getv('volumes')[0])
                raise(Exception(e))
            time, endtime, cdir, cdfile = db.getv('time', 'endtime', 'dir', \
                'dfile')
            ys, ye = int(epoch2str(time, '%Y')), int(epoch2str(endtime, '%Y'))
            for year in range(ys, ye+1):
                clusters[year] = {'dir': cdir.replace('%Y', str(year)), \
                    'dfile': cdfile.replace('%Y', str(year))}
                if verbose:
                    main_logger.info('get_dbs(): %s/%s %s %s' % (cdir, cdfile, t))
        #if the are multiple rows for the cluster, the volumes are 'single'
        #volumes and each row needs to be looped over
        else:
            for record in db.iter_record():
                cdir, cdfile, t = record.getv('dir', 'dfile', 'time')
                clusters[t] = {'dir': cdir, 'dfile': cdfile}
                #verbose mode logging
                if verbose:
                    main_logger.info('get_dbs(): %s/%s %s %s' % (cdir, cdfile, t))
    return clusters

def get_stations(database,subset,active,verbose):
    """
    Get list of stations from dbmaster deployment table.
    We can also subset to "active" only stations and/or
    statons in a subset of time.
    """
    from __main__ import defaultdict
    from __main__ import dbopen, closing, now
    main_logger = logging.getLogger('update_rrd_from_db')
    #verbose mode logging
    if verbose:
        main_logger.info('get_stations(): opening up and subsetting dbmaster')
    #an empty dictionary to hold station metadata
    stations = defaultdict(dict)
    #open deployment table
    with closing(dbopen(database, 'r')) as db:
        db = db.schema_tables['deployment']
        #subset stations if necessary
        if subset:
            db = db.subset( "sta =~ /%s/" % subset )
            #verbose mode logging
            if verbose:
                main_logger.info('get_stations(): subset sta =~ /%s/' % subset)
        #subset active stations if necessary
        if active:
            db = db.subset( "endtime == NULL || endtime > %s" % now() )
            #verbose mode logging
            if verbose:
                main_logger.info('get_stations(): subset endtime == NULL || endtime '\
                   ' > %s' % now())
        #sort view by time
        db = db.sort( 'time' )
        #verbose mode logging
        if verbose:
            main_logger.info('get_stations(): got %s records' % nrecs)
        #raise exception if there are no stations after subsets
        if db.record_count == 0:
            raise(Exception('get_stations(): no stations after subset to dbmaster' \
                ' [%s]' % db))
        #for each row in view, append metadata to dictionary, then return
        #dictionary
        for record in db.iter_record():
            sta, snet, vnet, t, et = record.getv('sta', 'snet', 'vnet', 'time', \
                'endtime')
            t, et = int(t), int(et)
            stations[snet][sta] = {'vnet':vnet, 'time':t, 'endtime':et}
            #verbose mode logging
            if verbose:
                main_logger.info('get_stations(): %s %s %s %s %s' % (sta,snet,vnet,t,et))
    return stations

def get_data(db,sta,chan,time,endtime,rrd_max,verbose):
    """
    Retrieve waveform data from databse. Return in list of time:value pairs
    """
    from __main__ import defaultdict
    from __main__ import sys
    from __main__ import os
    from __main__ import trdestroying
    from pylab import arange
    main_logger = logging.getLogger('update_rrd_from_db')
    #verbose mode logging
    if verbose:
        main_logger.info('get_data(): getting data values from db')
    #initialize some empty variables
    v, start, end, step, last_endtime = [], 0, 0, 0, 0
    #load requested data into trace object
    with trdestroying(db.trloadchan(time, endtime, sta, chan)) as tr:
        tr.trsplice()
        tr.trsplit()
        #get number of records in trace table
        if tr.record_count == 0: return [], 0
        #verbose mode logging
        if verbose:
            main_logger.info('get_data(): trloadchan [%s records]' % tr.record_count)
        #for each record in trace table, get data and metadata to calculate
        #sample times, then create properly formatted list of time:value
        #pairs
        #for tr.record in range(nseg):
        for record in tr.iter_record():
            start, end, samprate = record.getv('time', 'endtime', 'samprate')
            #calculate sample interval
            step  = 1/samprate
            #get waveform data
            temp_v = record.trdata()
            #make sure there are no values overlapping in time
            #even though tr.trsplice() should take care of this
            flag = False
            if start <= last_endtime:
                flag = True
                if end <= last_endtime: continue
                else:
                    temp_v = temp_v[int((last_endtime - start)*samprate) + 1:]
                    start = last_endtime + step
            #store the endtime of the last sample retrieved, to ensure
            #later waveform segments don't overlap
            last_endtime = end
            #create list of sample times
            time_list = [int(x) for x in arange(start, end+step, step)]
            #verbose mode logging
            if verbose:
                main_logger.info('get_data(): temp_v [%s samples]' % len(temp_v))
                main_logger.info('get_data(): time_list [%s samples]' % len(time_list))
            #append newly acquired time:value pairs to list of those
            #already retrieved, filtering out all time values prior to 'time'
            #ie. no data prior to RRD last update
            try:
                if len(time_list) <= len(temp_v):
                    v += ["%i:%i" % (time_list[ii], temp_v[ii]) \
                        for ii in range(len(time_list)) if time_list[ii] >= time]
                    #for ii in range(len(time_list)):
                    #    v.extend( ["%i:%i" % (time_list[ii],temp_v[ii])] )
                else:
                    v += ["%i:%i" % (time_list[ii], temp_v[ii]) \
                        for ii in range(len(temp_v)) if time_list[ii] >= time]
                    #for ii in range(len(temp_v)):
                    #    v.extend( ["%i:%i" % (time_list[ii],temp_v[ii])] )
            except Exception as e:
                raise(Exception('get_data(): %s' % e))
        #verbose mode logging
        if verbose:
            main_logger.info('get_data(): data vector [%s samples]' % len(v))
    #create subset lists of length rrd_max
    subset_list = [v[i:i+rrd_max] for i in xrange(0, len(v), rrd_max)]
    #verbose mode logging
    if verbose:
        main_logger.info('get_data(): subset List  [%s segments]' % len(subset_list))
    return subset_list, end

def configure_logger(logfile):
    import logging
    logger = logging.getLogger('update_rrd_from_db')
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler('%s.log' % logfile)
    fh.setLevel(logging.INFO)
    logger.addHandler(fh)
    sh = logging.StreamHandler()
    sh.setLevel(logging.ERROR)
    logger.addHandler(sh)
    logger = logging.getLogger('update_rrd_from_db_time_stats')
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler('%s_time_stats.log' % logfile)
    fh.setLevel(logging.INFO)
    logger.addHandler(fh)

class Timer:
    def __enter__(self):
        import time
        self.start = time.time()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        import time
        self.end = time.time()
        self.elapsed = self.end - self.start
        return self
