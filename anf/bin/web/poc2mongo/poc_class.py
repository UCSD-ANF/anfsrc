try:
    #import inspect
    import os
    import sys
    import json
    from datetime import datetime
    from collections import defaultdict
except Exception, e:
    raise pocException("Problems importing libraries.%s %s" % (Exception, e))

try:
    import antelope.datascope as datascope
    import antelope.stock as stock
    import antelope.orb as orb
    import antelope.Pkt as Pkt
except Exception, e:
    raise pocException("Problems loading ANTELOPE libraries. %s(%s)" % (Exception, e))


try:
    from db2mongo.logging_class import getLogger
except Exception, e:
    raise pocException("Problem loading logging_class. %s(%s)" % (Exception, e))



class stateFile:
    """
    Track the state of the ORB read.
    Save value of pktid in file.
    """
    def __init__(self, filename=False, start='oldest'):

        self.logging = getLogger('stateFile')

        self.logging.debug( "stateFile.init()" )

        self.filename = filename
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

        self.logging.debug( 'Open file for STATE tracking [%s]' % self.file )
        if os.path.isfile( self.file ):
            self.open_file('r+')
            self.read_file()
        else:
            self.open_file('w+')

        if not os.path.isfile( self.file ):
            raise pocException( 'Cannot create STATE file %s' % self.file )

    def last_packet(self):
        self.logging.info( 'last pckt:%s' % self.packet )
        return self.packet

    def last_time(self):
        self.logging.info( 'last time:%s' % self.time )
        return self.time

    def read_file(self):
        self.pointer.seek(0)

        try:
            temp = self.pointer.read().split('\n')
            self.logging.info( 'Previous STATE file %s' % self.file )
            self.logging.info( temp )

            self.packet = int(float(temp[0]))
            self.time = float(temp[1])
            self.strtime = temp[2]
            self.latency = temp[3]

            self.logging.info( 'Previous - %s PCKT:%s TIME:%s LATENCY:%s' % \
                        (self.pid, self.packet, self.time, self.latency) )

            if not float(self.packet): raise
        except:
            self.logging.warning( 'Cannot find previous state on STATE file [%s]' % self.file )



    def set(self, pckt, time):
        if not self.filename: return

        self.packet = pckt
        self.time = time
        self.strtime = stock.strlocalydtime(time).strip()
        self.latency = stock.strtdelta( stock.now()-time ).strip()

        #self.logging.debug( 'Orb latency: %s' % self.latency )

        try:
            self.pointer.seek(0)
            self.pointer.write( '%s\n%s\n%s\n%s\n%s\n' % \
                    (self.packet,self.time,self.strtime,self.latency,self.pid) )
        except Exception, e:
            raise pocException( 'Problems while writing to state file: %s %s' % (self.file,e) )

    def open_file(self, mode):
        try:
            self.pointer = open(self.file, mode, 0)
        except Exception, e:
            raise pocException( 'Problems while opening state file: %s %s' % (self.file,e) )



class pocException(Exception):
    """
    Local class to raise Exceptions to the
    rtwebserver framework.
    """
    def __init__(self, message):
        super(pocException, self).__init__(message)
        self.message = message


class Poc():
    """Implementation of perl's autovivification feature."""
    def __init__(self):
        self._clean()

    def _clean(self):
        self.id = False
        self.valid = False
        self.srcname = False
        self.sn = False
        self.srcip = False
        self.poctime = False
        self.pocc2 = {}
        self.rawpkt = {}

    def new( self, rawpkt ):

        self._clean()

        self.rawpkt = rawpkt

        if not rawpkt[0] or int(float(rawpkt[0])) < 1:
            return

        self.id = rawpkt[0]
        self.time = rawpkt[2]

        # Try to extract information from packet
        pkt = Pkt.Packet( rawpkt[1], rawpkt[2], rawpkt[3] )

        self.srcname = pkt.srcname if pkt.srcname else rawpkt[1]

        if pkt.pf.has_key('sn'):
            self.sn = pkt.pf['sn']
        else:
            return

        if pkt.pf.has_key('srcip'):
            self.srcip = pkt.pf['srcip']
        else:
            return

        if pkt.pf.has_key('time'):
            self.poctime = float(pkt.pf['time'])
        else:
            return

        self.valid = True

        # Maybe we have some extra data...
        if pkt.pf.has_key('pocc2'):
            self.pocc2 = pkt.pf['pocc2']
        else:
            self.pocc2 = {}

    def __str__(self):
        if self.valid:
            return "(%s) => [sn:%s ip:%s time:%s]" % \
                        (self.srcname, self.sn, self.srcip, self.poctime)
        else:
            return "(**invalid**) => [pkid:%s pktsrc:%s pktime:%s]" % \
                        (self.rawpkt[0], self.rawpkt[1], self.rawpkt[2])

    def data(self):
        return {
            'pcktid': self.id,
            'time': int(self.poctime),
            'srcname': "%s" % self.srcname,
            'srcip': self.srcip,
            'sn': self.sn,
            'pocc2': self.pocc2
            }



class poc2mongo():
    def __init__(self, collection, orb, orb_select=None, orb_reject=None,
                    default_orb_read=0, statefile=False, reap_wait=3,
                    timeout_exit=True, reap_timeout=5 ):
        """
        Class to read an ORB for POC packets and update a MongoDatabase
        with the values. Set the serial of the instrumetn as the main
        id and just update that entry with the latest packet that comes
        into the ORB. We can also run with the clean option and clean the
        archive before we start putting data in it.
        There is a position flag to force the reader to jump to a particular part
        of the ORB and the usual statefile to look for a previous value
        for the last packet id read.

        """
        self.logging = getLogger('poc_class')

        self.logging.debug( "Pocs.init()" )

        self.poc = Poc()
        self.cache = {}
        self.orb = False
        self.errors = 0
        self.orbname = orb
        self.lastread  = 0
        self.timezone = 'UTC'
        self.position = False
        self.error_cache = {}
        self.timeout_exit = timeout_exit
        self.reap_wait = int(reap_wait)
        self.statefile  = statefile
        self.collection = collection
        self.orb_select = orb_select
        self.orb_reject  = orb_reject
        self.reap_timeout = int(reap_timeout)
        self.timeformat = '%D (%j) %H:%M:%S %z'
        self.default_orb_read  = default_orb_read

        # StateFile
        self.state = stateFile( self.statefile, self.default_orb_read )
        self.position = self.state.last_packet()
        #self.last_time = self.state.last_time()



        if not self.orb_select: self.orb_select = None
        if not self.orb_reject: self.orb_reject = None


    def get_pocs(self):
        """
        Look into every ORB listed on the parameter file
        and track some information from them.
        """

        self.logging.debug( "Updat ORB cache" )

        self.logging.debug( self.orbname )

        if not self.orbname or not isinstance(self.orbname, str):
            raise pocException( "Problems with orbname [%s]" % (self.orbname) )

        # Expand the object if needed
        if not self.orb:
            self.logging.debug( "orb.Orb(%s)" % (self.orbname) )
            self.orb = {}
            self.orb['orb'] = None
            self.orb['status'] = 'offline'
            self.orb['last_success'] = 0
            self.orb['last_check'] = 0

        self._connect_to_orb()

        while True:
            # Reset the connection if no packets in reap_timeout window
            if self.orb['last_success'] and self.reap_timeout and \
                    ( (stock.now() - self.orb['last_success']) > self.reap_timeout):
                self.logging.warning('Possible stale ORB connection %s' % self.orbname)
                if stock.yesno(self.timeout_exit):
                    break
                else:
                    self._connect_to_orb()

            if self._extract_data():
                #self.logging.debug( "Success on extract_data(%s)" % (self.orbname) )
                pass
            else:
                self.logging.warning( "Problem on extract_data(%s)" % (self.orbname) )
                self._connect_to_orb()

        self.orb['orb'].close()

    def _test_orb(self):
        self.logging.debug( "test orb connection %s" % (self.orbname) )
        try:
            self.orb['status'] = self.orb['orb'].ping()
        except Exception,e:
            return False
        else:
            return True


    def _connect_to_orb(self):
        self.logging.debug( "start connection to orb: %s" % (self.orbname) )
        if self.orb['status']:
            try:
                self.logging.debug( "close orb connection %s" % (self.orbname) )
                self.orb['orb'].close()
            except Exception,e:
                #self.logging.warning("orb.close(%s)=>%s" % (self.orbname,e) )
                pass

        try:
            self.logging.debug("connect to orb(%s)" % self.orbname )
            self.orb['orb'] = orb.Orb(self.orbname)
            self.orb['orb'].connect()
            self.orb['orb'].stashselect(orb.NO_STASH)
        except Exception,e:
            raise pocException("Cannot connect to ORB: %s %s" % (self.orbname, e))


        if self.position:
            try:
                self.orb['orb'].position( 'p%s' % int(self.position) )
                self.logging.debug( "position orb on pckt: %s" % (self.position) )
            except:
                self.orb['orb'].position(self.default_orb_read)
                self.logging.debug( "default_orb_read: %s" % (self.default_orb_read) )


        if self.orb_select:
            self.logging.debug("orb.select(%s)" % self.orb_select )
            if not self.orb['orb'].select( self.orb_select):
                raise pocException("NOTHING LEFT AFTER orb.select(%s)" % self.orb_select )

        if self.orb_reject:
            self.logging.debug("orb.reject(%s)" % self.orb_reject )
            if not self.orb['orb'].reject( self.orb_reject):
                raise pocException("NOTHING LEFT AFTER orb.reject(%s)" % self.orb_reject )

        self.logging.debug( "ping orb: %s" % (self.orb['orb']) )
        try:
            self.logging.debug( "orb position: %s" % (self.orb['orb'].tell()) )
        except:
            self.logging.debug( "orb position: NONE"  )




    def _extract_data(self):
        """
        Look for all poc packets
        """

        self.orb['last_check'] = stock.now()

        if self.errors > 10:
            raise pocException('10 consecutive errors on orb.reap()')

        try:
            self.poc.new( self.orb['orb'].reap(self.reap_wait) )
        except orb.OrbIncompleteException, e:
            self.logging.debug("OrbIncompleteException orb.reap(%s)" % self.orbname)
            return True
        except Exception,e:
            self.logging.warning("%s Exception in orb.reap(%s) [%s]" % (Exception,self.orbname,e))
            self.errors += 1
            return False
        else:
            # reset error counter
            self.errors = 0
            # save ORB id to state file
            self.state.set(self.poc.id,self.poc.time)

        if self.poc.valid:
            self.logging.info( '%s' % self.poc )
            # we print this on the statusFile class too...
            self.logging.debug( 'orblatency %s' % \
                    ( stock.strtdelta( stock.now() - self.poc.time ) ) )
            self.position = self.poc.id
            self.logging.debug( 'orbposition %s' % self.position )
            self.orb['last_success'] = stock.now()

            self._update_collection()

        return True

    def _update_collection(self):

        self.logging.info( 'update_collection()' )

        # Verify if we need to update MongoDB
        if self.poc.valid:
            self.logging.debug('collection.update(%s)' % self.poc.sn)
            self.collection.update({'sn': self.poc.sn}, {'$set':self.poc.data()}, upsert=True)

