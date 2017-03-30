try:
    import re
    import os
    import sys
    import datetime
    import collections
except Exception, e:
    raise ImportError("Problems importing libraries.%s %s" % (Exception, e))

try:
    import antelope.stock as stock
    import antelope.Pkt as Pkt
except Exception, e:
    raise ImportError("Problems loading ANTELOPE libraries. %s(%s)" % (Exception, e))


try:
    from xi202_import.logging_class import getLogger
except Exception, e:
    raise ImportError("Problem loading logging_class. %s(%s)" % (Exception, e))


try:
    from xi202_import.imei_buffer import IMEIbuffer
except Exception, e:
    raise ImportError("Problem loading xi202_import private classes. %s(%s)" % (Exception, e))

class Packet():
    """Implementation of perl's autovivification feature."""
    def __init__(self, q330_dlnames=[],  channel_mapping={} ):

        self._clean()

        self.imei_buffer = IMEIbuffer()
        self.channel_mapping = channel_mapping
        self.q330_serial_dlname = q330_dlnames

        self.logging = getLogger('Packet')

    def _clean(self):
        self.id = False
        self.orbid = False
        self.seqNo = False
        self.logSeqNo = False
        self.time = False
        self.datetime = False
        self.strtime = False
        self.valid = False
        self.srcname = ''
        self.name = ''
        self.sn = False
        self.q330 = False
        self.dlname = False
        self.imei = False
        self.src = False
        self.valueMap = dict()
        self.rawpkt = dict()
        self.payload = dict()
        self.pcktbuf = dict()
        self.pkt = Pkt.Packet()
        self.pkt.type_suffix = 'pf'

    def new( self, rawpkt, name='unknown/pf/st', select=False, reject=False ):

        self.logging.debug( 'new packet' )

        if not rawpkt['_id'] :
            self.logging.warning( 'Bad Packet: %s' % rawpkt )
            return

        self._clean()

        self.name = name

        self.rawpkt = self._convert_unicode( rawpkt )

        if reject and re.search( reject, self.rawpkt['srcType'] ):
            self.logging.debug( 'type [%s] rejected by configuration' % self.rawpkt['srcType'] )
            return

        if select and not re.search( select, self.rawpkt['srcType'] ):
            self.logging.debug( 'type [%s] missed selection by configuration' % self.rawpkt['srcType'] )
            return

        self.logging.debug( self.rawpkt )

        # Track IDs
        self.logSeqNo = self.rawpkt['messageLogSeqNo']
        self.seqNo = self.rawpkt['seqNo']
        self.id = "%s.%s" % ( self.logSeqNo, self.seqNo )

        # Date object
        self.datetime = self.rawpkt[ 'timestamp' ]
        # Epoch string
        self.time = (self.datetime-datetime.datetime(1970,1,1)).total_seconds()
        # Time string
        self.strtime = stock.epoch2str( self.time, '%D %H:%M:%S %Z', tz='UTC' ).strip()

        self.q330 = self.rawpkt['q330Sn']
        self.imei = self.rawpkt['deviceIMEI']
        self.src = self.rawpkt['srcType']
        self.srcname = self.src.lower()


        if not self.imei_buffer.add( imei=self.imei, serial=self.q330 ):
            self.logging.warning( 'Invalid Q330 serial [%s] for IMEI [%s]' % ( self.q330, self.imei ) )
            self.q330 = self.imei_buffer( self.imei )

            if not self.q330:
                self.logging.warning( 'UNKNOWN IMEI [%s]: SKIP DATA PACKET!!!' % self.imei )
                return
            else:
                self.logging.warning( 'USING CACHED Q330 SERIAL [%s] FOR IMEI [%s]' % ( self.q330, self.imei ) )

        for test in self.q330_serial_dlname:
            if test( self.q330 ):
                self.dlname = test( self.q330 )
                self.logging.debug( '%s => %s' % (self.q330, self.dlname) )

        if not self.dlname:
            self.logging.warning( 'NO DLNAME FOR Q330 SERIAL: %s ' % self.q330 )
            return

        self.logging.debug( self.src )
        self.logging.debug( self.valueMap )

        # Verify if we have data pairs
        if 'valueMap' in self.rawpkt:
            self.valueMap = self.rawpkt['valueMap']

            # Extract each value to a new key:value on the dict
            for chan in self.valueMap:
                if chan in self.channel_mapping:
                    if not self.channel_mapping[chan]: continue

                    self.payload[ self.channel_mapping[chan] ] = self.valueMap[chan]

                    self.logging.debug( '%s -> %s:%s' % (chan, self.channel_mapping[chan], self.valueMap[chan]) )
                else:
                    self.logging.warning( '[%s] NOT DEFINED IN PF FILE' % chan )

            self.pcktbuf = {
                    'dls': { self.dlname: self.payload },
                    'q330' : self.q330,
                    'imei' : self.imei,
                    'src' : self.src,
                    'srcname' : self.srcname
                }


        self.logging.debug( self.payload )


        # Try to build packet from info
        if self.name and self.time and self.payload:

            self.pkt.srcname = Pkt.SrcName( self.name )
            #self.pkt.type_suffix = 'pf'
            self.pkt.time = self.time
            #self.logging.debug( self.pkt.type )
            #self.logging.debug( self.pkt.srcname )

            # Extract pf structure, update it and return it.
            temp = self.pkt.pf
            temp.update( self.pcktbuf )
            self.pkt.pf = temp

            self.logging.debug( self.pkt.type )
            self.logging.debug( self.pkt.srcname )

            self.logging.debug( 'Pkt( %s, %s) => {%s}' % (self.pkt.srcname, self.pkt.time, self.pkt.pf.pf2string().replace('\n',', ').replace('\t',':') ) )

            self.valid = True

        else:
            self.logging.warning( 'NO VALUABLE INFORMATION IN PACKET. dlname:%s  time:%s' % (self.dlname, self.time ) )

        self.logging.info( str(self) )

    def _convert_unicode( self, data ):
        if isinstance(data, basestring):
            return data.encode('utf-8')
        elif isinstance(data, collections.Mapping):
            return dict(map(self._convert_unicode, data.iteritems()))
        elif isinstance(data, collections.Iterable):
            return type(data)(map(self._convert_unicode, data))
        else:
            return data




    def __str__(self):

        temp = ''

        if not self.valid: temp = '*** INVALID *** '

        return '%sid:%s time:%s q330:%s imei:%s %s' % \
                ( temp, self.id, self.strtime, self.q330, self.imei, self.src )


    def __getitem__(self, name):
        if self.valid:
            return self.valueMap
        else:
            return False


    def __iter__(self):
        if self.valid:
            return iter( self.valueMap.keys() )
        else:
            return iter()


    def data(self):
        if self.valid:

            return {
                'pcktid': self.id,
                'time': int(self.time),
                'strtime': self.strtime,
                'srcname': "%s" % self.srcname,
                'valueMap': self.valueMap
                }
        else:
            return {}


