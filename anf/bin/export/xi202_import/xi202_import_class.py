try:
    import os
    import re
    import sys
    from datetime import datetime
except Exception, e:
    raise ImportError("Problems importing system libraries.%s %s" % (Exception, e))

try:
    import antelope.stock as stock
    import antelope.orb as orb
except Exception, e:
    raise ImportError("Problems loading ANTELOPE libraries. %s(%s)" % (Exception, e))


try:
    from xi202_import.logging_class import getLogger
except Exception, e:
    raise ImportError("Problem loading logging_class. %s(%s)" % (Exception, e))


try:
    from xi202_import.packet_class import Packet
except Exception, e:
    raise ImportError("Problem loading packet_class. %s(%s)" % (Exception, e))


try:
    from xi202_import.statefile_class import stateFile
except Exception, e:
    raise ImportError("Problem loading xi202_import private classes. %s(%s)" % (Exception, e))




class xi202_importer():
    def __init__(self, collection, orb, name='test', channel_mapping={}, orbunits=None,
                    q330units=None, mongo_select=None, mongo_reject=None,
                    default_mongo_read=0, statefile=False, mongo_pull_wait=3,
                    pckt_name_type='pf/xi' ):
        """
        xi202_importer():

        Class to read documents from a MongoDB Collection and produce xi202/pf/xeos packets
        that we can import into an ORB in Antelope. The last document read will
        be tracked on a state file.

        """
        self.name = name

        self.logging = getLogger('xi202_importer.%s' % self.name )

        self.logging.debug( "Packet.init( %s )" % self.name )

        #self.dlmon = Dlmon(  stock.yesno(parse_opt) )
        self.cache = {}
        self.orb = False
        self.errors = 0
        self.lastread  = 0
        self.timezone = 'UTC'
        self.error_cache = {}
        #self.indexing = indexing
        self.timeformat = '%D (%j) %H:%M:%S %z'

        # from object options
        self.orbunits = orbunits
        self.q330units = q330units
        self.channel_mapping = channel_mapping
        self.packet = Packet(q330_dlnames=[self.q330units,self.orbunits], channel_mapping=self.channel_mapping)
        self.collection = collection
        self.orbname = orb
        self.mongo_select = mongo_select
        self.mongo_reject  = mongo_reject
        self.statefile  = statefile
        self.state  = None
        self.mongo_pull_wait = int(mongo_pull_wait)
        self.pckt_name_type = pckt_name_type


        if default_mongo_read == 'start':
            self.read_position  = 0
        elif default_mongo_read == 'oldest':
            self.read_position = 0
        elif default_mongo_read == 'newest':
            self.read_position = -1
        elif default_mongo_read == 'end':
            self.read_position = -1
        else:
            try:
                self.read_position = int(default_mongo_read)
            except:
                self.logging.error( 'Cannot convert default_mongo_read [%s]' % default_mongo_read )


        # verify mongodb collection
        if self.collection.count() == 0:
            self.logging.warning( 'MongoDB collection [%s] is empty' % self.name )
            self.valid = False

        else:

            self.valid = True

            # StateFile
            self.state = stateFile( self.statefile, self.name, self.read_position )
            self.read_position = self.state.last_id()

            self.logging.debug( 'Last document read: %s' % self.read_position )

            self.logging.debug( 'Prep internal object' )
            self._prep_orb()


    def isvalid(self):
        return self.valid

    def __str__(self):
        if self.valid:
            return str(self.name)
        else:
            return '*** INVALID INSTANCE *** %s' % self.name

    def _prep_orb(self):
        """
        Look into the Document Collection and pull new
        documents out. Convert them to xi202/pf/xeos packets
        and push them into an ORB.
        """

        # Open output ORB and track status
        self.logging.debug( "Update ORB cache" )

        self.logging.debug( self.orbname )

        if not self.orbname or not isinstance(self.orbname, str):
            raise LookupError( "Problems with output orb [%s]" % (self.orbname) )

        # Expand the object if needed
        if not self.orb:
            self.logging.debug( "orb.Orb(%s)" % (self.orbname) )
            self.orb = {}
            self.orb['orb'] = None
            self.orb['status'] = 'offline'
            self.orb['last_success'] = 0
            self.orb['last_update'] = 0

        self._connect_to_orb()

    def close_orb(self):

        if not self.valid:
            return

        try:
            self.logging.debug( "close orb connection %s" % (self.orbname) )
            if self.orb['orb']:
                self.orb['orb'].close()

        except orb.NotConnectedError:
            self.logging.warning("orb(%s) Already closed" % self.orbname )

        except Exception,e:
            self.logging.warning("orb.close(%s)=>%s" % (self.orbname,e) )

    def _test_orb(self):

        self.orb['status'] = self.orb['orb'].ping()

        self.logging.debug( "orb.ping() => %s" % (self.orb['status']) )

        if int(self.orb['status']) > 0 : return True

        return False


    def _connect_to_orb(self):
        self.logging.debug( "start connection to orb: %s" % (self.orbname) )

        # If previous state then we close first and reconnect
        if self.orb['status']:
            self.close_orb()

        # Now open new connection and save values in object
        try:
            self.logging.debug("connect to orb(%s)" % self.orbname )
            self.orb['orb'] = orb.Orb(self.orbname, permissions='w')
            self.orb['orb'].connect()
            self.orb['orb'].stashselect(orb.NO_STASH)
        except Exception,e:
            raise Exception("Cannot connect to ORB: %s %s" % (self.orbname, e))

        self.logging.debug( "ping orb: %s" % (self.orb['orb']) )


        if not self._test_orb():
            raise Exception("Problems connecting to (%s)" % self.orbname )


    def pull_data(self):
        """
        Look for all packets
        """

        if not self.valid:
            self.logging.debug( '*** INVALID INSTANCE *** %s' % self.name )
            return False

        if float(self.read_position) < 0.:
            ignore_history = True
            logSeqNo = 0
            seqNo = 0
        else:
            ignore_history = False

            # ID has 2 parts. Need to split them.
            try:
                temp = str(self.read_position).split('.')
            except:
                temp = [ int(self.read_position) ]

            if len(temp) == 2:
                logSeqNo = int(temp[0])
                seqNo = int(temp[1])
            else:
                logSeqNo = int(self.read_position)
                seqNo = False

        # Get all documents with id equal or grater than last successful id...
        for post in sorted( self.collection.find({"messageLogSeqNo": {"$gte": logSeqNo}}), key=lambda x: (x['messageLogSeqNo'], x['seqNo'])):

            try:
                # In case we bring an older segNo document...
                if logSeqNo == post['messageLogSeqNo'] and seqNo:
                    if seqNo >= post['seqNo']:
                        self.logging.debug( 'Skipping processed packet %s.%s' % (post['messageLogSeqNo'], post['seqNo']) )
                        continue
            except Exception,e:
                self.logging.warning( 'Invalid document: %s: %s' % (Exception, e) )
                continue

            #self.logging.notify( post )
            self.packet.new( post ,  name_type=self.pckt_name_type, select=self.mongo_select, reject=self.mongo_reject )

            if not self.packet.valid: continue

            # save packet id to state file
            self.state.set(self.packet.id, self.packet.time)

            # track last id
            self.read_position = self.packet.id

            if ignore_history:
                self.logging.info( 'Skip. Ignoring old packets.' )
                continue


            if not self.packet.valid:
                self.logging.warning( '*** SKIP - INVALID PACKET ***' )
                continue

            # Test connection. Reset if missing
            if not self._test_orb():
                self._connect_to_orb()

            self.logging.debug( 'Put new packet in orb: %s' %  self.packet.pkt )
            pkttype, pktbuf, srcname, time = self.packet.pkt.stuff()
            self.packet.orbid = self.orb['orb'].putx( srcname, self.packet.time, pktbuf )

        self.lastread  = stock.now()

        #try:
        #    # REAP new packet from ORB
        #    self.packet.new(  self.orb['orb'].reap(self.reap_wait)  )

        #except orb.OrbIncompleteException, e:
        #    self.logging.debug("OrbIncompleteException orb.reap(%s)" % self.orbname)
        #    return True

        #except Exception,e:
        #    self.logging.warning("%s Exception in orb.reap(%s) [%s]" % (Exception,self.orbname,e))
        #    self.errors += 1
        #    return False

        #self.logging.debug("_extract_data(%s,%s)" % (self.packet.id, self.packet.time) )

        ## reset error counter
        #self.errors = 0

        #if not self.packet.id or not self.packet.valid:
        #    self.logging.debug("_extract_data() => Not a valid packet" )
        #    return False

        ## save ORB id to state file
        #self.state.set(self.packet.id,self.packet.time)

        #self.logging.debug( 'errors:%s' % self.errors )


