try:
    import os
    import sys
except Exception, e:
    raise ImportError("Problems importing libraries.%s %s" % (Exception, e))

try:
    import antelope.stock as stock
    import antelope.Pkt as Pkt
except Exception, e:
    raise ImportError("Problems loading ANTELOPE libraries. %s(%s)" % (Exception, e))


try:
    from soh2mongo.logging_class import getLogger
except Exception, e:
    raise ImportError("Problem loading logging_class. %s(%s)" % (Exception, e))



class Packet():
    """Implementation of perl's autovivification feature."""
    def __init__(self):
        self._clean()
        self.logging = getLogger('Packet')

    def _clean(self):
        self.id = False
        self.time = False
        self.strtime = False
        self.valid = False
        self.srcname = '-'
        self.sn = False
        self.q330 = False
        self.imei = False
        self.dls = False
        self.rawpkt = {}

    def new( self, rawpkt ):

        if not rawpkt[0] or int(float(rawpkt[0])) < 1:
            self.logging.info( 'Bad Packet: %s %s %s' % (rawpkt[0], rawpkt[1], rawpkt[2] ) )
            return

        self._clean()

        self.rawpkt = rawpkt

        self.logging.debug( rawpkt )

        self.id = rawpkt[0]
        self.time = float( rawpkt[2] )
        self.strtime = stock.epoch2str( self.time, '%D %H:%M:%S %Z' ).strip()

        # Try to extract information from packet
        pkt = Pkt.Packet( rawpkt[1], rawpkt[2], rawpkt[3] )

        self.srcname = pkt.srcname if pkt.srcname else rawpkt[1]

        self.logging.info( '%s %s %s' % (self.id, self.time, self.strtime) )
        #self.logging.debug( pkt.pf )

        if pkt.pf.has_key('dls'):
            self.dls = pkt.pf['dls']

            if pkt.pf.has_key('imei'):
                self.logging.info( 'Found imei: %s' % (pkt.pf['imei']) )
                self.imei = pkt.pf['imei']
            if pkt.pf.has_key('q330'):
                self.logging.info( 'Found q330: %s' % (pkt.pf['q330']) )
                self.q330 = pkt.pf['q330']

            self.valid = True
            self.__str__()

        else:
            self.dls = {}
            self.valid = False


    def __str__(self):
        if self.valid:
            return "(%s) => [time:%s] %s " % \
                        (self.srcname, self.strtime, str(self.dls.keys()) )
        else:
            return "(**invalid**) => [pkid:%s pktsrc:%s pktime:%s]" % \
                        (self.rawpkt[0], self.rawpkt[1], self.rawpkt[2])


    def __getitem__(self, name):
        if self.valid:
            return self.dls[ name ]
        else:
            return False


    def __iter__(self):
        if self.valid:
            return iter( self.dls.keys() )
        else:
            return iter()


    def data(self):
        if self.valid:

            return {
                'pcktid': self.id,
                'time': int(self.time),
                'strtime': self.strtime,
                'srcname': "%s" % self.srcname,
                'dls': self.dls
                }
        else:
            return {}


