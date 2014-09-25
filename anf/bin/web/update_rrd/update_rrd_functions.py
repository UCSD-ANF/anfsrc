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


def check_threads(PROCS,MAX,RRD_PROCS
    """
    Verify each member of the PROCS dict.
    to verify if they are running.
    Loop until the number of elements is
    lower than the MAX value.

    Returns count of active PROCS.
    """
    logger = logging.getLogger().getChild('check_threads')

    while len(PROCS) > MAX:
        logger.debug('.' * len(PROCS) )
        temp_procs = set()
        for p in PROCS:
            pid = p.pid()
            sta = RRD_PROCS[pid]['sta']
            chan = RRD_PROCS[pid]['chan']

            stdout,stderr = p.communicate(input=None,timeout=1)[0];
            if stdout: logger.debug('%s stdout: [%s]' % (pid,stdout) )
            if stderr: logger.error('%s stderr: [%s]' % (pid,stderr) )

            if p.poll() is None:
                temp_procs.add(p)
            else:
                logger.info('Done with proc. %s %s %s' % (pid,sta,chan) )

        PROCS = temp_procs

        logger.debug( 'sleep(1)' )
        time.sleep(1)


    return len(PROCS)

def isfloat(value):
    try:
        temp = float(value)
    except:
        return False

    # TEST FOR NaN
    if temp != temp:
        return False

    if temp == float("inf"):
        return False

    return True

def validpoint(last_update,time,value):

    logger = logging.getLogger().getChild('validpoint')

    logger.debug( 'validpoint(%s,%s,%s)' % (last_update,time,value) )

    if not isfloat(value):
        logger.error( 'NOT FLOAT: %s' % value )
        return False

    if time <= last_update:
        logger.error( 'ILLEGAL UPDATE: %s <= %s' % (time,last_update) )
        return False

    return True

def last_rrd_update(rrd):
    """
    Query RRD database for last update time.
    Returns 0 in case it fails.
    """
    from __main__ import os

    logger = logging.getLogger().getChild('last_rrd_update')

    last_update = 0 # Default to 0

    if os.path.isfile(rrd):
        logger.debug( 'found: %s' % rrd )
        try:
            last_update = int(os.popen('rrdtool lastupdate %s' % rrd)\
                .read().split()[1].split(':')[0])
        except Exception as e:
            try:
                last_update = int(os.popen('rrdtool lastupdate %s' % rrd)\
                    .read().split()[1].split(':')[0])
            except Exception as e:
                logger.error( '\n\nCannot get time of last update' )
                logger.error( '[rrdtool lastupdate %s]\n\n' % rrd )
    else:
        logger.debug( 'missing: %s' % rrd )

    return int(last_update)

def chan_thread(rrd, sta, chan, dbcentral, time, endtime, previous_db=False):
    """
    Perform RRD updates for a given stachan pair and input database
    """
    from __main__ import os
    from __main__ import defaultdict
    from __main__ import datascope
    from __main__ import stock

    RRD_MAX_RECS = 1000


    logger = logging.getLogger().getChild('chan_thread [%s_%s] ' % (sta,chan))

    time = int(time)
    endtime = int(endtime)

    logger.debug('New thread for %s %s:%s  (%s,%s)' %(rrd,sta,chan,time,endtime) )

    last_update = last_rrd_update(rrd)
    if last_update < time:
        last_update = int(time)
    logger.debug( 'last update to rrd: %s' % last_update )

    if previous_db:
        logger.debug( 'previous database: %s' % previous_db )
    else:
        db_valid_list = dbcentral.clean_before(last_update)
        logger.debug('valid dbcentral: %s' % db_valid_list )

    try:
        active_db = dbcentral(last_update)
    except:
        try:
            active_db = dbcentral.list()[0]
        except:
            active_db = False

    if active_db:
        logger.debug('Using database: %s' % active_db )
    else:
        logger.error('No more databases to work with!' )
        return 0

    try:
        db = datascope.dbopen(active_db,'r')
    except Exception,e:
        logger.error('Problems while dbopen [%s]: %s' % (active_db,e) )
        return

    try:
        logger.debug('Lookup %s.wfdisc' % active_db )
        tempdb = db.lookup(table = 'wfdisc')
    except Exception,e:
        logger.error('Problems while lookup [%s]: %s' % (active_db,e) )
        return

    try:
        logger.debug('Subset: sta=~/%s/ && chan=~/%s/' % (sta,chan) )
        tempdb = tempdb.subset('sta=~/%s/ && chan=~/%s/' % (sta,chan) )
        logger.debug('Subset: endtime>= %s' % last_update )
        tempdb = tempdb.subset('endtime >= %s' % last_update )
        records = tempdb.record_count
    except Exception,e:
        logger.error('Problems while subset [%s]: %s' % (active_db,e) )
        return

    logger.debug(' %s records in database' % records )

    if records > 0:
        logger.debug('Sort: time' )
        tempdb = tempdb.sort('time')
        tempdb.record = 0
        first_time = tempdb.getv('time')[0]
        if records > 0: tempdb.record = records - 1
        last_time = tempdb.getv('endtime')[0]
        logger.debug('wfdisc row [%s ,%s]' % (first_time,last_time) )
        logger.debug('%s in wfdisc' % \
                stock.strtdelta(last_time - first_time) )

        #for record in tempdb.iter_record():
        for i in xrange(0,records):
            tempdb.record = i
            logger.debug(' record #%s ' % tempdb.record)
            start = tempdb.getv('time')[0]
            end = tempdb.getv('endtime')[0]
            logger.debug('[time:%s ,endtime:%s]' % (start,end) )
            logger.debug('%s that we need from this wfdisc row' % \
                    stock.strtdelta(end - last_update) )

            if last_update > end: continue
            if last_update > start: start = last_update + 1

            start = int(start)
            end = int(end)

            try:
                data = tempdb.trsample(start, end, sta, chan,apply_calib=True)
            except Exception, e:
                logger.error('Exception on trsample.[%s]' % e)
                continue

            if not data:
                logger.error('Nothing came out of trsample for this row.')
                continue

            for i in xrange(0, len(data), RRD_MAX_RECS):
                #logger.debug('datasegment= data[%s:%s]' %  (i,i+RRD_MAX_RECS-1))
                datasegment = data[i:i+RRD_MAX_RECS-1]
                #logger.debug('datasegment.len(): %s' %  len(datasegment))
                #def validpoint(last_update,time,value):
                try:
                    status = os.system('rrdtool update %s %s ;' % (rrd, \
                            ' '.join(["%s:%s" % (x[0],x[1]) for x in \
                            datasegment if validpoint(last_update,
                                x[0],x[1])])))

                    if status:
                        logger.error('rrdtool update output: %s' % status)
                        logger.error('datasegment[0]: %s,%s' % datasegment[0])
                        logger.error('datasegment[-1]: %s,%s' % datasegment[-1])
                        exit()

                    last_update = last_rrd_update(rrd)
                    #logger.debug('rrdtool update output: %s' %  status )

                except Exception as e:
                    logger.error('\n\n%s - skipping %s:%s %d - %d' \
                        % (e, sta, chan, start, end))


    tempdb.free()
    db.close()

    logger.debug('Using database: %s' % active_db )
    #logger.debug('Last database: %s' % last_db )

    # Do we need to continue to next database?
    #if ( active_db == last_db ):
    #    logger.debug('We are on our last database. Done here.')
    #else:
    dbcentral.purge(active_db)
    #logger.debug('valid dbcentral: %s' % db_valid_list )
    #logger.debug('\n\nNeed to jump to next database.\n\n')
    return chan_thread(rrd, sta, chan, dbcentral, time, endtime, active_db)


def check_rrd(file, sta, chan, chaninfo, npts):
    """
    Get RRD file ready.
    """
    from __main__ import os
    from __main__ import defaultdict
    from __main__ import datascope

    logger = logging.getLogger().getChild('check_rrd [%s_%s] ' % (sta,chan))

    logger.debug('check_rrd()')

    time = chaninfo['time']
    endtime = chaninfo['endtime']

    try:
        samprate = chaninfo['chans'][chan]
    except:
        logger.error('No %s in %s' % (chan,chaninfo['chans']))
        if chan[0] == 'L':
            samprate = 1.0
        elif chan[0] == 'V':
            samprate = 0.1
        else:
            samprate = 0.01
        logger.error('Using %s samprate for %s' % (samprate,chan))

    logger.debug('time:%s endtime:%s samprate:%s' % (time,endtime,samprate))

    # if RRD exists, and doesn't need to be rebuilt, do nothing
    if os.path.exists(file):
        logger.debug('Found (%s)' % file)
        try:
            last_update = int(os.popen('rrdtool lastupdate %s' % file)\
                .read().split()[1].split(':')[0])
        except Exception as e:
            logger.error('Cannot get info from %s [%s]' % (file,e))

        if last_update:
            return last_update
        else:
            logger.error('Cannot get "lastupdate" from %s [%s]' % (file,e))
            os.remove(file)

    # otherwise, build it
    dt = 1.0/samprate
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
                'RRA:%s:0.5:%d:%s' % (cf, rra_step[twin],npts)

    # define command to create RRD
    cmd = [str(x) for x in [
            '--start', int(time),
            '--step', dt,
            'DS:%s:GAUGE:%d:U:U' % (chan, 25*dt)
        ] + [rrd_cmd[key] for key in sorted(rrd_cmd.iterkeys())]
    ]

    logger.debug('RRD cmd (%s)' % cmd)

    logger.debug('rrdtool create %s %s' % (file,' '.join(cmd)))
    try:
        os.system('rrdtool create %s %s' % (file, ' '.join(cmd)))
    except Exception as e:
        raise(Exception(' rrdtool create %s %s - %s' \
            % (file, ' '.join(cmd), e)))

    #test to make sure an RRD exists
    if not os.path.exists(file):
        raise(Exception(' RRD file does not exist- %s' % file))
    else:
        logger.info('New RRD [%s]' % file)


def get_stations(database,options):
    """
    Get list of stations from dbmaster deployment table.
    We can also subset to "active" only stations and/or
    statons in a subset of time.
    """

    from __main__ import defaultdict
    from __main__ import datascope
    from __main__ import stock

    logger = logging.getLogger().getChild('get_staitons')

    #verbose mode logging
    logger.debug('get_stations()')

    #an empty dictionary to hold station metadata
    stations = defaultdict(dict)

    station_subset = options.stations
    network_subset = options.networks

    db = database.list()[-1] # get the last database from our dbcentral
    if not db:
        raise Exception('Cannot access db in dbcentral format: %s' % database)
    else:
        logger.debug('Look for stations on: %s' % db)

    #open deployment table
    with datascope.closing(datascope.dbopen(db, 'r')) as db:
        instrument = db.schema_tables['instrument']

        if instrument.query("dbTABLE_PRESENT") < 1:
            raise Exception('No instrument table present: %s' % instrument)
        instrument = instrument.join('sensor')
        if instrument.query("dbTABLE_PRESENT") < 1:
            raise Exception('Cannot join with sensor: %s' % instrument)

        instrument = instrument.join('snetsta')
        if instrument.query("dbTABLE_PRESENT") < 1:
            raise Exception('Cannot join with snetsta: %s' % instrument)

        db = db.schema_tables['deployment']

        if db.query("dbTABLE_PRESENT") < 1:
            raise Exception('No deployment table present: %s' % db)

        if network_subset:
            if network_subset[0] == "_":
                db = db.subset( "vnet =~ /%s/" % network_subset )
                logger.debug(' vnet =~ /%s/' % network_subset)
            else:
                db = db.subset( "snet =~ /%s/" % network_subset )
                logger.debug(' snet =~ /%s/' % network_subset)
        if station_subset:
            db = db.subset( "sta =~ /%s/" % station_subset )
            logger.debug(' sta =~ /%s/' % station_subset)

        #subset active stations if necessary
        if options.active:
            db = db.subset( "endtime == NULL || endtime > %s" % stock.now() )
            logger.debug(' subset endtime==NULL||endtime>%s' % stock.now())

        db = db.sort( 'time' )

        logger.debug(' got %s records' % db.record_count)

        #raise exception if there are no stations after subsets
        if db.record_count == 0:
            logger.critical(' got %s records' % db.record_count)
            raise(Exception('empty subset to dbmaster [%s]' % db))

        #for each row in view, append metadata to dictionary, then return
        #dictionary
        for record in db.iter_record():
            sta, snet, vnet, t, et = record.getv('sta', 'snet', 'vnet', \
                'time', 'endtime')
            t, et = int(t), int(et)
            stations[snet][sta] = {'chans':{}, 'vnet':vnet, 'time':t, 'endtime':et}

            logger.debug('%s %s %s %s %s' % (sta,snet,vnet,t,et))

            temp = instrument.subset('sta=~/%s/ && snet=~/%s/' % (sta,snet))
            if temp.record_count == 0:
                logger.critical(' got %s records in subset for instrument' % temp.record_count)
                raise(Exception('empty subset to instrument join [%s]' % instrument))
            for r in temp.iter_record():
                chan, sps = r.getv('chan', 'samprate')
                stations[snet][sta]['chans'][chan] = sps

                logger.debug('%s %s %s' % (sta,chan,sps))

            temp.free()

    return stations

