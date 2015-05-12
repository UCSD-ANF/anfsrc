from __main__ import *


class updateRRDException(Exception):
    """
    Local class to raise Exceptions
    """
    def __init__(self, msg):
        self.msg = msg
    def __repr__(self):
        return '\n\n\tupdateRRDException: %s\n\n' % (self.msg)
    def __str__(self):
        return repr(self)


class Orbserver:

    def __init__(self, src, select=False, reject=False):

        self.src = src
        self.select = select
        self.reject = reject
        self.errors = 0

        log( 'Orbserver: init(%s,%s,%s)' % (src,select,reject) )

        # Test for valid ORB name
        match = re.match(re.compile(".*:.*"), self.src)
        if not match:
            error("Not a valid ORB %s" % self.src)

        # Connect to the ORB
        try:
            self.orb = orb.Orb(self.src)
            self.orb.connect()
            self.orb.stashselect(orb.NO_STASH)
        except Exception,e:
            error("Cannot connect to ORB: %s %s" % (self.src,e))

        # Subset the ORB
        if self.select:
            log( 'Orbserver: select(%s)' % self.select )
            self.orb.select( self.select )
        if self.reject:
            log( 'Orbserver: reject(%s)' % self.reject )
            self.orb.reject( self.reject )

        # Get some info from ORB
        log( self.orb.stat() )

        # Go to the first packet in the ORB
        log( 'Orbserver: position(oldest)' )
        try:
            self.orb.position('oldest')
        except Exception,e:
            error("Cannot position to oldest: %s %s" % (self.src,e))


    def __enter__(self):
        return self

    def __exit__(self):
        self.orb.close()

    def __iter__(self):
        return self

    def next(self):
        log("Orbserver: Next orb packet")

        if self.errors > 50:
            error('50 consecutive errors on orb.reap()')

        try:
            pkt = self.orb.reap()

            if int(float(pkt[0])) < 0:
                pkt = self.next()

            pkt = Packet( pkt )
            if not pkt.is_valid():

                raise updateRRDException( "invalid pkt: id:%s name:%s pkttime:%s" % \
                        (pkt[0], pkt[1], pkt[2]) )

        except Exception,e:
            warning("%s Exception in orb.reap [%s]" % (Exception,e))
            self.errors += 1
            pkt = self.next()

        self.errors = 0
        return pkt


class Packet:
    def __init__(self, pkt):

        log( "Packet: id:%s name:%s pkttime:%s" % (pkt[0], pkt[1], pkt[2]) )


        self.id = pkt[0]
        self.time = pkt[2]
        self.buf = pkt[3]
        self.valid = True

        if not self.id or int(float(self.id)) < 1:
            self.valid = False
            return

        log( "Packet: valid" )

        self.pkt = Pkt.Packet( pkt[1], pkt[2], pkt[3] )
        self.data_buf = []

        self.srcname = self.pkt.srcname if self.pkt.srcname else pkt[1]
        log( 'Packet: srcname: %s' % self.srcname )

        #log( 'Packet: channels: %s' % self.pkt.channels )
        if len(self.pkt.channels):
            self.net = self.srcname.net
            self.sta = self.srcname.sta
            for chans in self.pkt.channels:
                debug( 'Packet: extract: %s_%s_%s' % (self.net, self.sta, chans.chan) )
                self.data_buf.append( {
                    'id': str(self.id) + '-' + chans.chan,
                    'pktTime': self.time,
                    'net': self.net,
                    'sta': self.sta,
                    'chan': '_'.join( [chans.chan,chans.loc] ) if chans.loc else chans.chan,
                    'samprate': round(float(chans.samprate),4),
                    'time': round(float(chans.time),4),
                    'data': chans.data
                } )

        elif self.pkt.pf.has_key('dls'):
            if self.pkt.pf.has_key('itvl'):
                samprate = round(1/float(self.pkt.pf['itvl']),4)
            else:
                samprate = round(1/60,4)

            for netsta in self.pkt.pf['dls']:
                debug('Packet: extract: %s' % netsta)
                temp = netsta.split('_')
                net = temp[0]
                sta = temp[1]
                for chan in self.pkt.pf['dls'][netsta]:
                    if not chan.upper(): continue
                    debug( 'Packet: extract: %s_%s_%s' % (net, sta, chan.upper()) )
                    self.data_buf.append( {
                        'id': str(self.id) + '-' + netsta,
                        'pktTime': self.time,
                        'net': net,
                        'sta': sta,
                        'chan': chan.upper(),
                        'samprate': samprate,
                        'time': round(float(self.time),4),
                        'data': self.pkt.pf['dls'][netsta][chan]
                    } )

    def name(self):
        log( 'Packet: name(): %s' % self.srcname )
        return self.srcname

    def data(self):
        log( 'Packet: extract data')
        return self.data_buf

    def is_valid(self):
        log( 'Packet: valid: %r' % self.valid )
        return self.valid

class Cache:
    '''
    Multiplexed cache of data. We only keep packets that match
    the network and station specified on the parameter file.
    '''
    def __init__(self, networks, stations, archive, rrd_npts, channels, max_buffer=18000):

        log( "Cache: networks:%s stations:%s" % (networks, stations) )
        log( "Cache: archive:%s" % archive )
        log( "Cache: channels:%s" % ', '.join(channels) )
        log( "Cache: rrd_npts:%s max_buffer:%s" % (rrd_npts, max_buffer) )

        self.net = networks
        self.sta = stations
        self.net_regex = re.compile( networks )
        self.sta_regex = re.compile( stations )

        self.archive = archive
        self.rrd_npts = rrd_npts
        self.channels = channels
        self.max_buffer = max_buffer
        self.data = {}

    def add(self,pkt):
        debug( 'Cache: add packet to cache: %r' % pkt.id )

        if not pkt.is_valid(): return False


        for bdl in pkt.data():
            if not self.net_regex.match(bdl['net']):
                debug( '%s not match to regex %s' % (bdl['net'], self.net) )
                continue
            if not self.sta_regex.match(bdl['sta']):
                debug( '%s not match to regex %s' % (bdl['sta'], self.sta) )
                continue

            if not bdl['chan'] in self.channels:
                debug( '%s not in channels list %s' % (bdl['chan'], ', '.join(self.channels)) )
                continue

            name = '_'.join( [bdl['net'], bdl['sta'], bdl['chan']] ),
            if not name in self.data:
                log( 'New buffer for %s' % name )
                self.data[ name ] = \
                    ChanBuf(self.archive, self.rrd_npts, self.max_buffer, bdl['time'],
                            bdl['net'], bdl['sta'], bdl['chan'], bdl['samprate'])

            self.data[ name ].add( bdl['pktTime'], bdl['time'], bdl['data'] )

class ChanBuf:
    def __init__(self, archive, npts, buffer, stime, net, sta, chan, samprate=60):

        log( "ChanBuf: NEW OBJECT: net:%s sta:%s chan:%s samprate:%s" % \
                (net, sta, chan, samprate) )

        self.name = '_'.join( [net, sta, chan] )

        self.time = False
        self.endtime = False
        self.lastPkt = False
        self.net = net
        self.sta = sta
        self.chan = chan
        self.samprate = samprate
        self.interval = 1/samprate
        self.max_window = buffer
        self.max_gap = samprate / 2
        self.data = []

        log( "ChanBuf: interval:%s max_window:%s max_gap:%s" % \
                (self.interval, self.max_window, self.max_gap) )

        self.archive = archive
        self.RRD_MAX_RECS = 500
        self.npts = npts
        self.filePath = check_rrd(archive, npts, stime, net, sta, chan, samprate)
        self.fileLastData = last_rrd_update( self.filePath )
        self.fileLastFlush = False

        log( "ChanBuf: filePath:%s fileLastData:%s" % \
                (self.filePath, self.fileLastData) )

    def add(self,pktTime, time, data):
        log( 'ChanBuf: add: %s => %s (%s samples)' % \
                    (self.name,stock.strydtime(time),len(data)) )

        debug('ChanBuf: BEFORE %s %s sps data:%s %s' % \
                ( stock.strydtime(self.time), self.samprate, len(self.data), \
                    stock.strtdelta(self.endtime-self.time) ) )

        if self.endtime and ( time - self.endtime ) > self.max_gap:
            self.flush('max_gap')

        if self.endtime and ( self.endtime - self.time ) > self.max_window:
            self.flush('full_buf')

        # Theoretical endtime
        endtime = time + ( len(data) * self.interval )

        if endtime <= self.fileLastData:
            warning( 'All data precedes last data on RRD:%s (endtime %s)' % \
                        (self.fileLastData,endtime) )
            return

        self.lastPkt = pktTime
        self.endtime = endtime
        if not self.time: self.time = time

        debug( 'ChanBuf: append(%s samples)' % len(data) )
        self.data.extend( data )

        debug('ChanBuf: AFTER %s %s sps data:%s %s' % \
                ( stock.strydtime(self.time), self.samprate, len(self.data), \
                    stock.strtdelta(self.endtime-self.time) ) )

    def flush(self, note):
        log('ChanBuf: %s flush(%s)' % (self.name,note) )

        data = self.data
        time = self.time
        endtime = self.endtime

        # Clean object
        self.time = False
        self.endtime = False
        self.data = []
        self.fileLastFlush = stock.now()


        notify('ChanBuf: start:%s for %s fileLastData:%s' % (stock.strydtime(time), \
            stock.strtdelta(endtime-time),stock.strydtime(self.fileLastData)) )

        if endtime < self.fileLastData:
            error( 'All data is before last update to RRD %s (end %s)' % \
                                                    (self.fileLastData,endtime) )

        if not data or len(data) < 1:
            warning( 'No data to flush to %s on %s' % (self.filePath,self.name) )
            return

        timelist = [(time + (self.interval * x)) for x in range( len(data) ) ]
        log( 'flush: len.data(%s) len.time(%s)' % (len(data),len(timelist)) )

        if len(data) != len(timelist):
            error( 'flush: data(%s) != time(%s) need same elements' % (len(data),len(timelist)) )

        cleandata = [(x[0],x[1]) for x in zip(timelist,data) if validpoint(self.fileLastData, x[0],x[1])]

        log( 'flush: final data(%s)' % len(cleandata) )

        if len(cleandata) < 1:
            warning( 'No data after cleanup to flush to %s on %s' % (self.filePath,self.name) )
            return

        for i in xrange(0, len(cleandata), self.RRD_MAX_RECS):
            datasegment = cleandata[i:i+self.RRD_MAX_RECS-1]
            log('flush: rrdtool update %s %s points' % (self.name, len(datasegment)) )
            run('rrdtool update %s %s ;' % (self.filePath, \
                    ' '.join(["%s:%s" % (x[0],x[1]) for x in datasegment ])) )

        self.fileLastData = last_rrd_update( self.filePath )
        return


def log(msg=''):
    if not isinstance(msg, str):
        msg = pprint(msg)
    logger.info(msg)


def debug(msg=''):
    if not isinstance(msg, str):
        msg = pprint(msg)
    logger.debug(msg)


def warning(msg=''):
    if not isinstance(msg, str):
        msg = pprint(msg)
    logger.warning("\t*** %s ***" % msg)


def notify(msg=''):
    if not isinstance(msg, str):
        msg = pprint(msg)
    logger.log(35,msg)


def error(msg=''):
    if not isinstance(msg, str):
        msg = pprint(msg)
    logger.critical(msg)
    sys.exit("\n\n\t%s\n\n" % msg)


def pprint(obj):
    return "\n%s" % json.dumps( obj, indent=4, separators=(',', ': ') )

def run(cmd,directory='./'):
    debug("run()  -  Running: %s" % cmd)
    p = subprocess.Popen([cmd], stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         cwd=directory, shell=True)
    stdout, stderr = p.communicate()

    if stderr:
        error('STDERR present: %s => \n\t%s'  % (cmd,stderr) )

    for line in iter(stdout.split('\n')):
        debug('stdout:\t%s'  % line)

    if p.returncode != 0:
        notify('stdout:\t%s'  % line)
        error('Exitcode (%s) on [%s]' % (p.returncode,cmd))

    return stdout


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

    if not isfloat(value):
        return False

    if float(time) <= float(last_update):
        warning( 'ILLEGAL UPDATE: time %s <=  last_update %s' % (time,last_update) )
        return False

    return True


def last_rrd_update(rrd):
    """
    Query RRD database for last update time.
    Returns 0 in case it fails.
    """

    debug( 'last_rrd_update: %s' % rrd )
    last_update = 0

    if os.path.isfile(rrd):
        last_update = int(run( 'rrdtool lastupdate %s' % rrd ).split()[1].split(':')[0])
        log( 'Last update to RRD archive: %s' % stock.strydtime(last_update) )

    else:
        error( 'last_rrd_update: Cannot find RRD archive: %s' % rrd )

    return int(last_update)


def check_rrd(archive, npts, stime, net, sta, chan, samprate):
    """
    Get RRD file ready.
    """

    log('check_rrd(%s,%s,%s,%s,%s,%s)' % (archive,npts,net,sta,chan,samprate))

    path = os.path.abspath( '%s/%s/%s/' % (archive, net, sta) )
    if not os.path.isdir(path):
        try:
            log('check_rrd: mkdirs(%s)' % path)
            os.makedirs(path)
        except Exception,e:
            error('Cannot make directory: %s %s' % (path, e))


    rrdfile = os.path.abspath( '%s/%s.rrd' % (path, chan) )
    log('check_rrd: (%s)' % rrdfile)

    # if RRD exists, and doesn't need to be rebuilt, do nothing
    if os.path.exists(rrdfile):
        log('Found (%s)' % rrdfile)

        if last_rrd_update(rrdfile):
            return rrdfile
        else:
            logger.error('check_rrd: Cannot get "lastupdate" %s [%s]' % (rrdfile,e))
            os.remove(file)

    # otherwise, build it
    dt = 1.0/samprate
    rra_step = {
        '1w': int(round(604800*samprate/npts)),
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
            '--start', int(float(stime-1)),
            '--step', dt,
            'DS:%s:GAUGE:%d:U:U' % (chan, 25*dt)
        ] + [rrd_cmd[key] for key in sorted(rrd_cmd.iterkeys())]
    ]

    log('RRD cmd (%s)' % cmd)

    run('rrdtool create %s %s' % (rrdfile, ' '.join(cmd)))

    #test to make sure an RRD exists
    if not os.path.exists(rrdfile):
        error(' RRD file does not exist and cannnot create- %s' % rrdfile)

    log('New RRD [%s]' % rrdfile)

    return rrdfile
