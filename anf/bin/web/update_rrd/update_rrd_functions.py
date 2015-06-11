from __main__ import *



class stateFile:
    """
    Track the state of the ORB read.
    Save value of pktid in file.
    """
    def __init__(self, filename, start='oldest'):

        self.packet = start
        self.time = 0
        self.strtime = 'n/a'
        self.latency = 'n/a'
        self.pid = 'PID %s' % os.getpid()

        if not filename: return

        self.directory, self.filename = os.path.split(filename)

        if self.directory and not os.path.isdir( self.directory ):
            os.makedirs( self.directory )

        self.file = os.path.join( self.directory, self.filename )

        debug( 'Open file for STATE tracking [%s]' % self.file )
        if os.path.isfile( self.file ):
            self.open_file('r+')
            self.read_file()
        else:
            self.open_file('w+')

        if not os.path.isfile( self.file ):
            error( 'Cannot create STATE file %s' % self.file )

    def last_packet(self):
        notify( 'stateFile: last pckt:%s' % self.packet )
        return self.packet

    def last_time(self):
        notify( 'stateFile: last time:%s' % self.time )
        return self.time

    def read_file(self):
        self.pointer.seek(0)

        try:
            temp = self.pointer.read().split('\n')
            notify( 'Previous STATE file %s' % self.file )
            notify( temp )

            self.packet = int(float(temp[0]))
            self.time = float(temp[1])
            self.strtime = temp[2]
            self.latency = temp[3]

            notify( 'Previous - %s PCKT:%s TIME:%s LATENCY:%s' % \
                        (self.pid, self.packet, self.time, self.latency) )

            if not float(self.packet): raise
        except:
            warning( 'Cannot find previous state on STATE file [%s]' % self.file )



    def set(self, pckt, time):
        self.packet = pckt
        self.time = time
        self.strtime = stock.strlocalydtime(time).strip()
        self.latency = stock.strtdelta( stock.now()-time ).strip()

        debug( 'Orb latency: %s' % self.latency )

        if not self.filename: return

        try:
            self.pointer.seek(0)
            self.pointer.write( '%s\n%s\n%s\n%s\n%s\n' % \
                    (self.packet,self.time,self.strtime,self.latency,self.pid) )
        except Exception, e:
            error( 'Problems while writing to state file: %s %s' % (self.file,e) )

    def open_file(self, mode):
        try:
            self.pointer = open(self.file, mode, 0)
        except Exception, e:
            error( 'Problems while opening state file: %s %s' % (self.file,e) )



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

    def __init__(self, src, stateF=False, time_buffer=1200, start_default='oldest', select=False, reject=False, test=False):

        self.src = src
        self.select = select
        self.reject = reject
        self.errors = 0
        self.last = stock.now()
        self.test = test

        self.state = stateFile( stateF, start_default )
        self.time_buffer = time_buffer
        self.last_packet = self.state.last_packet()
        self.last_time = self.state.last_time()
        log( 'Orbserver: last position(%s)' % self.last_packet )
        log( 'Orbserver: last time(%s)' % self.last_time )

        if self.last_time:
            # Fix last time to avoid loosing data
            self.last_time = self.last_time - ( 2 * self.time_buffer )
            log( 'Orbserver: last time fixed(%s)' % self.last_time )


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


        try:
            # Go back the size of buffer to avoid loosing data
            notify("Position ORB to time %s" % self.last_time)
            if not self.last_time: raise
            self.orb.after(self.last_time)
        except Exception,e:
            warning("Cannot position to time %s: %s" % (self.last_time,self.src))
            try:
                # Try with last pkt
                notify("Position ORB to pckt %s" % self.last_packet)
                if not self.last_packet: raise
                self.orb.position(self.last_packet)
            except Exception,e:
                error("Cannot position to %s: %s" % (self.default,self.src))

        #error('end test')

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
            # Try one more time
            self.errors += 1
            pkt = self.next()

        if self.test:
            temp = stock.now()
            notify( 'Orbserver: processing time last pckt: %s' % ( stock.strtdelta(temp-self.last) ) )
            self.last = temp

            # we print this on the statusFile class too...
            #notify( 'Orbserver: latency %s' % ( stock.strtdelta(stock.now()-pkt[2]) ) )

        # reset error counter
        self.errors = 0

        # save ORB id to state file
        self.state.set(pkt[0],pkt[2])

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

        self.archive = archive
        self.rrd_npts = rrd_npts
        self.chan_list = chan_list
        self.max_buffer = max_buffer
        self.data = {}

    def go_to_work(self,orbserver):
        for p in orbserver:
            self.parse( p )


    def parse(self,new_pkt):
        debug( 'Cache: parse new packet: %r' % new_pkt[0] )
        # self.id = new_pkt[0] self.time = new_pkt[2] self.buf = new_pkt[3]

        data_buf = []

        if not new_pkt[0] or int(float(new_pkt[0])) < 1:
            warning( 'Cache: invalid id:%s' % new_pkt[0] )
            return

        # Try to extract name of packet. Default to the orb provided name.
        pkt = Pkt.Packet( new_pkt[1], new_pkt[2], new_pkt[3] )
        srcname = pkt.srcname if pkt.srcname else pkt[1]
        debug( 'Cache: srcname: %s' % srcname )

        # if we have waveforms. (MST, SEED, M1, etc.)
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
                data_buf.append( {
                    'id': str(new_pkt[0]) + '-' + chans.chan,
                    'net': net,
                    'sta': sta,
                    'multiplex': False,
                    'chan': '_'.join( [chans.chan,chans.loc] ) if chans.loc else chans.chan,
                    'samprate': round(float(chans.samprate),4),
                    'time': round(float(chans.time),4),
                    'data': chans.data
                } )

        # If we have pf packets.
        elif pkt.pf.has_key('dls'):
            debug('Cache:  got dls (multiplexed) packet' )

            # sometimes we get the interval on very cool packets. ;-P
            try:
                if pkt.pf.has_key('itvl'):
                    samprate = round(1/float(pkt.pf['itvl']),4)
                else:
                    raise
            except:
                # Defaults to 1/60. No nice way to do this.
                samprate = 0.0166666

            debug('Cache:  samprate: %s' % samprate )

            # Could be 'st' or 'im'.
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

                data_buf.append( {
                    'id': str(new_pkt[0]) + '-' + netsta,
                    'net': net,
                    'sta': sta,
                    'chan': ptype,
                    'multiplex': True,
                    'samprate': samprate,
                    'time': round(float(new_pkt[2]),4),
                    'data': pkt.pf['dls'][netsta]
                } )

        else:
            warning('Cache: UNKNOWN pkt type %s' % (pkt.srcname) )

        debug( 'Cache: add packet to cache ' )
        for bdl in data_buf:
            name = '_'.join( [bdl['net'], bdl['sta'], bdl['chan']] ),

            if not name in self.data:
                log( 'New buffer for %s' % name )
                self.data[ name ] = \
                    ChanBuf(bdl['multiplex'],self.archive, self.rrd_npts, self.max_buffer,
                            bdl['time'], bdl['net'], bdl['sta'], bdl['chan'],
                            chan_list=self.chan_list, samprate=bdl['samprate'])


            self.data[ name ].add( bdl['time'], bdl['data'] )




class ChanBuf:
    def __init__(self, multiplex, archive, npts, maxbuff, stime, net, sta, chan, chan_list=[], samprate=60):

        debug( "ChanBuf: NEW OBJECT: net:%s sta:%s chan:%s samprate:%s" % \
                (net, sta, chan, samprate) )

        self.name = '_'.join( [net, sta, chan] )

        self.multiplex = multiplex
        self.stime = stime
        self.time = False
        self.endtime = False
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

        # Need this to get the flags on the pf/st=>opt fields
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

    def add(self,time, data):
        log( 'ChanBuf: add: %s => %s (%s items)' % \
                    (self.name,stock.strydtime(time),len(data)) )

        debug('ChanBuf: BEFORE %s %s sps data:%s %s' % \
                ( stock.strydtime(self.time), self.samprate, len(self.data), \
                    stock.strtdelta(self.endtime-self.time) ) )

        if self.endtime:

            if time < self.endtime:
                self.flush('out or order %s secs' % (time - self.endtime) )
                # We need to dump the last packet, flush buffer and start clean.
                return

            if time - self.endtime > (self.interval * 1.5):
                self.flush('gap %s secs' % (time - self.endtime) )

            if ( self.endtime - self.time ) > self.max_buffer:
                self.flush('full_buf')


        # Theoretical endtime
        if type(data) is dict:
            endtime = time + self.interval
        else:
            endtime = time + ( len(data) * self.interval )

        self.endtime = endtime
        if not self.time: self.time = time

        self.data.append( data )

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
                # unpack the data
                debug('flush: each_pkt: %s' % each_pkt )
                [channels[ x.upper() ].append( each_pkt[x] ) for x in each_pkt ]
            for c in ['LCQ', 'VCO']:
                if c in channels:
                    # Need to avoid chan on the pf/st channels. Getting
                    # that on the MST channels.
                    debug('flush: remove %s from pf/st' % c)
                    del channels[c]

        else:
            channels[ self.chan ] = data

        # Expand the OPT channel
        if 'OPT' in channels:
            for each_pkt in channels['OPT']:
                # Let's expand the flags and add 0 if missing.
                channels[ 'ACOK' ].append( 1 if self.acok.match( each_pkt ) else 0 )
                channels[ 'API' ].append( 1 if self.api.match( each_pkt )  else 0)
                channels[ 'ISP1' ].append( 1 if self.isp1.match( each_pkt )  else 0)
                channels[ 'ISP2' ].append( 1 if self.isp2.match( each_pkt )  else 0)
                channels[ 'TI' ].append( 1 if self.ti.match( each_pkt )  else 0)

                #debug('New OPT chans: TI:%s ACOK:%s API:%s ISP1:%s ISP2:%s' % ( channels['TI'][-1],
                #    channels['ACOK'][-1], channels['API'][-1], channels['ISP1'][-1], channels['ISP2'][-1]) )


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
                log( 'All data is before last update to RRD %s (end %s)' % (last,endtime) )
                continue

            # Verify that we have valid data to send to rrdtool
            cleandata = [(x[0],isfloat(x[1])) for x in zip(timelist,channels[chan]) if validpoint(x[0],last)]

            if not len(cleandata):
                log( 'No data after cleanup to flush to %s - %s' % (self.name,chan) )
                continue

            for i in xrange(0, len(cleandata), self.RRD_MAX_RECS):
                datasegment = cleandata[i:i+self.RRD_MAX_RECS-1]
                debug('flush: rrdtool update %s %s points' % (self.name, len(datasegment)) )
                run('rrdtool update %s %s ;' % (filePath, \
                        ' '.join(["%s:%s" % (x[0],x[1]) for x in datasegment ])) )

            self.filesCache[chan]['time'] = cleandata[-1][0]



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
    log("run()  -  Running: %s" % cmd)
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
        return 0

    # test for NaN
    if temp != temp:
        return 0

     # test for infinity
    if temp == float("inf"):
        return 0

    # Looks good...
    return value

def validpoint(time, last_update=0):

    if int(time) <= last_update:
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
    if path and not os.path.isdir(path):
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
