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

    #def __init__(self, src, net=False, sta=False, chan_list=[], select=False, reject=False):
    def __init__(self, src, select=False, reject=False):

        self.src = src
        self.select = select
        self.reject = reject
        self.errors = 0
        #self.net = net
        #self.sta = sta
        #self.chan_list = chan_list
        #self.net_regex = re.compile( net ) if net else False
        #self.sta_regex = re.compile( sta ) if sta else False

        log( 'Orbserver: init(%s,%s,%s)' % (src,select,reject) )
        #log( "Orbserver: networks:%s stations:%s" % (self.net, self.sta) )
        #log( "Orbserver: channels:%s" % ', '.join(self.chan_list) )

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
        '''
        If running the object on a for loop then
        this will return each packet from the orb in order.
        '''
        debug("Orbserver: Next orb packet")

        if self.errors > 50:
            error('50 consecutive errors on orb.reap()')

        try:
            pkt = self.orb.reap()

            if int(float(pkt[0])) < 0:
                pkt = self.next()

        except Exception,e:
            warning("%s Exception in orb.reap [%s]" % (Exception,e))
            self.errors += 1
            pkt = self.next()

        notify( 'Orbserver: latency %s' % ( stock.strtdelta(stock.now()-pkt[2]) ) )

        return pkt

class Cache:
    '''
    Multiplexed cache of data. We only keep packets that match
    the network and station specified on the parameter file.
    '''
    def __init__(self, archive, net, sta, rrd_npts, chan_list=[], max_buffer=18000):

        log( "Cache: networks:%s stations:%s" % (net, sta) )
        log( "Cache: archive:%s" % archive )
        log( "Cache: rrd_npts:%s max_buffer:%s" % (rrd_npts, max_buffer) )

        self.net = net
        self.sta = sta
        self.net_regex = re.compile( net ) if net else False
        self.sta_regex = re.compile( sta ) if sta else False
        #self.net_regex = re.compile( networks )
        #self.sta_regex = re.compile( stations )

        self.archive = archive
        self.rrd_npts = rrd_npts
        self.chan_list = chan_list
        self.max_buffer = max_buffer
        self.data = {}

        #self.id = False
        #self.time = False
        #self.buf = False
        self.valid = False
        #self.pkt = False
        self.data_buf = []

    def go_to_work(self,orbserver):
        for p in orbserver:
            #self.add( Packet( p, self.net_regex, self.sta_regex, self.chan_list ) )
            self.parse( p )
            if self.valid: self.add()

    def add(self):
        debug( 'Cache: add packet to cache ' )

        for bdl in self.data_buf:
            name = '_'.join( [bdl['net'], bdl['sta'], bdl['chan']] ),

            if not name in self.data:
                log( 'New buffer for %s' % name )
                self.data[ name ] = \
                    ChanBuf(bdl['multiplex'],self.archive, self.rrd_npts, self.max_buffer,
                            bdl['time'], bdl['net'], bdl['sta'], bdl['chan'],
                            chan_list=self.chan_list, samprate=bdl['samprate'])


            #self.data[ name ].add( bdl['pktTime'], bdl['time'], bdl['data'] )
            self.data[ name ].add( bdl['time'], bdl['data'] )

        self.data_buf = []

    def parse(self,new_pkt):
        debug( 'Cache: parse new packet: %r' % new_pkt[0] )
        #self.id = new_pkt[0]
        #self.time = new_pkt[2]
        #self.buf = new_pkt[3]
        self.valid = False

        if not new_pkt[0] or int(float(new_pkt[0])) < 1:
            warning( 'Cache: invalid id:%s' % new_pkt[0] )
            return

        debug( "Cache: valid packet" )

        pkt = Pkt.Packet( new_pkt[1], new_pkt[2], new_pkt[3] )

        srcname = pkt.srcname if pkt.srcname else pkt[1]
        debug( 'Cache: srcname: %s' % srcname )

        if len(pkt.channels):
            net = srcname.net
            sta = srcname.sta
            if self.net and not self.net_regex.match(net):
                debug( '%s not match to net regex %s' % (net, self.net) )
                return

            if self.sta and not self.sta_regex.match(sta):
                debug( '%s not match to sta regex %s' % (sta, self.sta_regex) )
                return

            for chans in pkt.channels:
                if len(self.chan_list) and not chans.chan in self.chan_list:
                    debug( '%s not in channels list %s' % (chans.chan, ', '.join(self.chan_list)) )
                    continue

                debug( 'Cache: extract: %s_%s_%s' % (net, sta, chans.chan) )
                self.data_buf.append( {
                    'id': str(new_pkt[0]) + '-' + chans.chan,
                    #'pktTime': new_pkt[2],
                    'net': net,
                    'sta': sta,
                    'multiplex': False,
                    'chan': '_'.join( [chans.chan,chans.loc] ) if chans.loc else chans.chan,
                    'samprate': round(float(chans.samprate),4),
                    'time': round(float(chans.time),4),
                    'data': chans.data
                } )

            self.valid = True

        elif pkt.pf.has_key('dls'):
            debug('Cache:  got dls (multiplexed) packet' )

            try:
                if pkt.pf.has_key('itvl'):
                    samprate = round(1/float(pkt.pf['itvl']),4)
                else:
                    raise
            except:
                samprate = 0.0166666

            debug('Cache:  samprate: %s' % samprate )

            ptype = new_pkt[1].split('/')[-1]
            debug('Packet: ptype: %s' % ptype)

            for netsta in pkt.pf['dls']:
                debug('Packet: extract: %s' % netsta)
                temp = netsta.split('_')
                net = temp[0]
                sta = temp[1]

                if self.net and not self.net_regex.match(net):
                    debug( '%s not match to net regex %s' % (net, self.net) )
                    continue

                if self.sta and not self.sta_regex.match(sta):
                    debug( '%s not match to sta regex %s' % (sta, self.sta) )
                    continue

                self.data_buf.append( {
                    'id': str(new_pkt[0]) + '-' + netsta,
                    #'pktTime': new_pkt[2],
                    'net': net,
                    'sta': sta,
                    'chan': ptype,
                    'multiplex': True,
                    'samprate': samprate,
                    'time': round(float(new_pkt[2]),4),
                    'data': pkt.pf['dls'][netsta]
                } )

                self.valid = True

        else:
            warning('Cache: UNKNOWN pkt type %s %s' % (pkt[0],pkt[2]) )



class ChanBuf:
    def __init__(self, multiplex, archive, npts, maxbuff, stime, net, sta, chan, chan_list=[], samprate=60):

        debug( "ChanBuf: NEW OBJECT: net:%s sta:%s chan:%s samprate:%s" % \
                (net, sta, chan, samprate) )

        self.name = '_'.join( [net, sta, chan] )

        self.multiplex = multiplex
        self.stime = stime
        self.time = False
        self.endtime = False
        #self.lastPkt = False
        self.net = net
        self.sta = sta
        self.chan = chan
        self.chan_list = chan_list
        self.samprate = samprate
        self.interval = 1/samprate
        self.max_buffer = float(maxbuff)
        self.max_gap = samprate / 2
        self.data = []

        debug( "ChanBuf: interval:%s max_buffer:%s" % \
                (self.interval, self.max_buffer) )

        self.archive = archive
        self.RRD_MAX_RECS = 500
        self.npts = npts
        self.filesCache = {}

        self.acok = re.compile( '.*acok.*' )
        self.api = re.compile( '.*api.*' )
        self.isp1 = re.compile( '.*isp1.*' )
        self.isp2 = re.compile( '.*isp2.*' )
        self.ti = re.compile( '.*ti.*' )

    def get_files(self, chan):
        debug( 'ChanBuf: look for file on chan: %s => %s ' % (self.sta,chan) )

        filePath, fileLastUpdate = check_rrd(self.archive, self.npts,
                                    self.stime, self.net, self.sta,
                                    chan, self.samprate)
        if not filePath:
            error('ChanBuf: Cannot get filename for %s %s' % self.sta,chan )

        self.filesCache[ chan ] = {
                'path': filePath,
                'time': fileLastUpdate
                }

        #if self.chan:
        #    self.filePath = check_rrd(archive, npts, stime, net, sta, chan, samprate)
        #    self.fileLastData = last_rrd_update( self.filePath )
        #else:
        #self.filePath = False
        #self.fileLastData = False
        #self.fileLastFlush = False

        #log( "ChanBuf: filePath:%s fileLastData:%s" % \
        #        (self.filePath, self.fileLastData) )

    #def add(self,pktTime, time, data):
    def add(self,time, data):
        log( 'ChanBuf: add: %s => %s (%s items)' % \
                    (self.name,stock.strydtime(time),len(data)) )

        debug('ChanBuf: BEFORE %s %s sps data:%s %s' % \
                ( stock.strydtime(self.time), self.samprate, len(self.data), \
                    stock.strtdelta(self.endtime-self.time) ) )

        #debug( data )
        #debug( self.data )

        if self.endtime:

            if time <= self.endtime:
                self.flush('out or order %s secs' % (time - self.endtime) )
                return

            if time - self.endtime > (self.interval * 1.5):
                self.flush('gap %s secs' % (time - self.endtime) )

            if ( self.endtime - self.time ) > self.max_buffer:
                self.flush('full_buf')
            #else:
            #    debug('ChanBuf: %s Buffer:%s limit:%s' % \
            #            ( stock.strtdelta(self.endtime-self.time),
            #                (self.endtime-self.time),self.max_buffer ) )


        # Theoretical endtime
        if type(data) is dict:
            endtime = time + self.interval
        else:
            endtime = time + ( len(data) * self.interval )

        #if self.fileLastData and endtime <= self.fileLastData:
        #    warning( 'All data precedes last data on RRD:%s (endtime %s)' % \
        #                (self.fileLastData,endtime) )
        #    return

        #self.lastPkt = pktTime
        self.endtime = endtime
        if not self.time: self.time = time

        debug( 'ChanBuf: self.data(%s items)' % len(self.data) )
        debug( 'ChanBuf: append(%s items) %s' % (len(data),type(data)) )
        self.data.append( data )
        debug( 'ChanBuf: self.data(%s items)' % len(self.data) )

        debug('ChanBuf: AFTER %s %s sps data:%s %s' % \
                ( stock.strydtime(self.time), self.samprate, len(self.data), \
                    stock.strtdelta(self.endtime-self.time) ) )

    def flush(self, note):
        debug('ChanBuf: %s flush(%s)' % (self.name,note) )

        data = self.data
        time = self.time
        endtime = self.endtime

        # Clean object
        self.time = False
        self.endtime = False
        self.data = []
        channels = defaultdict(list)
        self.fileLastFlush = stock.now()

        debug('ChanBuf: start:%s for %s' % (stock.strydtime(time), \
            stock.strtdelta(endtime-time)) )

        if not data or len(data) < 1:
            log( 'No data to flush to %s on %s' % (self.filePath,self.name) )
            return

        timelist = [(time + (self.interval * x)) for x in range( len(data) ) ]
        debug( 'flush: len.data(%s) len.time(%s)' % (len(data),len(timelist)) )

        if self.multiplex:
            # For multiplexed packets
            debug( data )
            for each_pkt in data:
                debug('flush: each_pkt: %s' % each_pkt )
                [channels[ x.upper() ].append( each_pkt[x] ) for x in each_pkt ]

        else:
            channels[ self.chan ] = data

        # Expand the OPT channel
        if 'OPT' in channels:
            for each_pkt in channels['OPT']:
                channels[ 'ACOK' ].append( 1 if self.acok.match( each_pkt ) else 0 )
                channels[ 'API' ].append( 1 if self.api.match( each_pkt )  else 0)
                channels[ 'ISP1' ].append( 1 if self.isp1.match( each_pkt )  else 0)
                channels[ 'ISP2' ].append( 1 if self.isp2.match( each_pkt )  else 0)
                channels[ 'TI' ].append( 1 if self.ti.match( each_pkt )  else 0)


        for chan in  channels:

            debug( "ChanBuf: chan:%s " % chan )

            if len(self.chan_list) and not chan in self.chan_list:
                    debug( '%s not in channels list %s' % (chan, ', '.join(self.chan_list)) )
                    continue

            if not chan in self.filesCache:
                self.get_files(chan)

            filePath = self.filesCache[chan]['path']
            last = self.filesCache[chan]['time']

            debug( "ChanBuf: filePath:%s last:%s" % (filePath, last) )

            if endtime < last:
                warning( 'All data is before last update to RRD %s (end %s)' % \
                                                    (last,endtime) )

            cleandata = \
                [(x[0],x[1]) for x in zip(timelist,channels[chan]) if validpoint(x[0],x[1],last)]

            if len(cleandata) < 1:
                debug( 'No data after cleanup to flush to %s - %s' % (self.name,chan) )
                continue

            log( 'flush: final data(%s)' % len(cleandata) )

            #filePath, fileLastData = check_rrd(self.archive, self.npts, \
            #        self.stime, self.net, self.sta, chan, self.samprate)
            #fileLastData = last_rrd_update( filePath )
            #cleandata = \
            #    [(x[0],x[1]) for x in zip(timelist,channels[chan]) if validpoint(fileLastData, x[0],x[1])]

            #if len(data) != len(timelist):
            #    error( 'flush: data(%s) != time(%s) need same elements' % (len(data),len(timelist)) )


            for i in xrange(0, len(cleandata), self.RRD_MAX_RECS):
                datasegment = cleandata[i:i+self.RRD_MAX_RECS-1]
                debug('flush: rrdtool update %s %s points' % (self.name, len(datasegment)) )
                run('rrdtool update %s %s ;' % (filePath, \
                        ' '.join(["%s:%s" % (x[0],x[1]) for x in datasegment ])) )

        #self.fileLastData = last_rrd_update( self.filePath )
        #return
        #error( "end test " )


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

def validpoint(time, value, last_update=0):

    if not isfloat(value):
        #warning( 'ILLEGAL UPDATE: %s not float' % value )
        return False

    if int(time) <= last_update:
        #warning( 'ILLEGAL UPDATE: time %s <=  last_update %s' % (time,last_update) )
        return False

    #warning('valid point %s,%s last:%s' % (time,value,last_update) )

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
        debug( 'Last update to RRD archive: %s' % stock.strydtime(last_update) )

    else:
        error( 'last_rrd_update: Cannot find RRD archive: %s' % rrd )

    return int(last_update)


def check_rrd(archive, npts, stime, net, sta, chan, samprate):
    """
    Get RRD file ready.
    """

    debug('check_rrd(%s,%s,%s,%s,%s,%s)' % (archive,npts,net,sta,chan,samprate))

    path = os.path.abspath( '%s/%s/%s/' % (archive, net, sta) )
    if not os.path.isdir(path):
        try:
            log('check_rrd: mkdirs(%s)' % path)
            os.makedirs(path)
        except Exception,e:
            error('Cannot make directory: %s %s' % (path, e))


    rrdfile = os.path.abspath( '%s/%s_%s.rrd' % (path, sta, chan) )
    debug('check_rrd: (%s)' % rrdfile)

    # if RRD exists, and doesn't need to be rebuilt, do nothing
    if os.path.exists(rrdfile):
        debug('Found (%s)' % rrdfile)

        last_update = last_rrd_update(rrdfile)

        if last_update:
            return ( rrdfile, last_update )
        else:
            error('check_rrd: Cannot get "lastupdate" %s [%s]' % (rrdfile,e))
            #os.remove(file)

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
            '--start', int(stime-1),
            '--step', dt,
            'DS:%s:GAUGE:%d:U:U' % (chan, 25*dt)
        ] + [rrd_cmd[key] for key in sorted(rrd_cmd.iterkeys())]
    ]

    debug('RRD cmd (%s)' % cmd)

    run('rrdtool create %s %s' % (rrdfile, ' '.join(cmd)))

    #test to make sure an RRD exists
    if not os.path.exists(rrdfile):
        error(' RRD file does not exist and cannnot create- %s' % rrdfile)

    log('New RRD [%s]' % rrdfile)

    return ( rrdfile, int(stime-1) )
