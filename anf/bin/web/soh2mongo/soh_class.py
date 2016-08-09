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
    from soh2mongo.logging_class import getLogger
except Exception, e:
    raise ImportError("Problem loading logging_class. %s(%s)" % (Exception, e))


try:
    from soh2mongo.packet_class import Packet
except Exception, e:
    raise ImportError("Problem loading packet_class. %s(%s)" % (Exception, e))


try:
    from soh2mongo.statefile_class import stateFile
except Exception, e:
    raise ImportError("Problem loading statefile_class. %s(%s)" % (Exception, e))


try:
    from soh2mongo.dlmon_class import *
except Exception, e:
    raise ImportError("Problem loading dlmon_class. %s(%s)" % (Exception, e))




class SOH_mongo():
    def __init__(self, collection, orb, orb_select=None, orb_reject=None,
                    default_orb_read=0, statefile=False, reap_wait=3,
                    timeout_exit=True, reap_timeout=5, parse_opt=False,
                    indexing=[] ):
        """
        Class to read an ORB for pf/st and pf/im packets and update a MongoDatabase
        with the values. We can run with the clean option and clean the
        archive before we start putting data in it.
        There is a position flag to force the reader to jump to a particular part
        of the ORB and the usual statefile to look for a previous value
        for the last packet id read.

        """
        self.logging = getLogger('soh_mongo')

        self.logging.debug( "Packet.init()" )

        self.dlmon = Dlmon(  stock.yesno(parse_opt) )
        self.packet = Packet()
        self.cache = {}
        self.orb = False
        self.errors = 0
        self.orbname = orb
        self.lastread  = 0
        self.timezone = 'UTC'
        self.position = False
        self.error_cache = {}
        self.indexing = indexing
        self.statefile  = statefile
        self.collection = collection
        self.orb_select = orb_select
        self.orb_reject  = orb_reject
        self.reap_wait = int(reap_wait)
        self.timeout_exit = timeout_exit
        self.reap_timeout = int(reap_timeout)
        self.timeformat = '%D (%j) %H:%M:%S %z'
        self.default_orb_read  = default_orb_read

        # StateFile
        self.state = stateFile( self.statefile, self.default_orb_read )
        self.position = self.state.last_packet()
        #self.last_time = self.state.last_time()

        self.logging.debug( 'Need ORB position: %s' % self.position )


        if not self.orb_select: self.orb_select = None
        if not self.orb_reject: self.orb_reject = None


    def start_daemon(self):
        """
        Look into every ORB listed on the parameter file
        and track some information from them.
        """

        self.logging.debug( "Update ORB cache" )

        self.logging.debug( self.orbname )

        if not self.orbname or not isinstance(self.orbname, str):
            raise LookupError( "Problems with orbname [%s]" % (self.orbname) )

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
                self.logging.debug( "Success on extract_data(%s)" % (self.orbname) )
                pass
            else:
                self.logging.warning( "Problem on extract_data(%s)" % (self.orbname) )

        self.orb['orb'].close()

        return 0

    def _test_orb(self):

        self.orb['status'] = self.orb['orb'].ping()

        self.logging.debug( "orb.ping() => %s" % (self.orb['status']) )

        if int(self.orb['status']) > 0 : return True

        return False


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
            raise Exception("Cannot connect to ORB: %s %s" % (self.orbname, e))

        #self.logging.info( self.orb['orb'].stat() )

        if self.orb_select:
            self.logging.debug("orb.select(%s)" % self.orb_select )
            if not self.orb['orb'].select( self.orb_select):
                raise Exception("NOTHING LEFT AFTER orb.select(%s)" % self.orb_select )

        if self.orb_reject:
            self.logging.debug("orb.reject(%s)" % self.orb_reject )
            if not self.orb['orb'].reject( self.orb_reject):
                raise Exception("NOTHING LEFT AFTER orb.reject(%s)" % self.orb_reject )

        self.logging.debug( "ping orb: %s" % (self.orb['orb']) )


        try:
            if int(self.position) > 0:
                self.logging.info( "Go to orb position: %s" % (self.position) )
                self.orb['orb'].position( 'p%d' % int(self.position) )
            else:
                raise
        except:
            try:
                self.logging.info( "Go to orb default position: %s" % (self.default_orb_read) )
                self.orb['orb'].position( self.default_orb_read )
            except Exception,e:
                self.logging.error( "orb.position: %s, %s" % (Exception,e) )


        try:
            self.logging.info( "orb.tell()"  )
            self.logging.info( self.orb['orb'].tell() )
        except orb.OrbTellError:
            self.logging.info( "orb.seek( orb.ORBOLDEST )"  )
            #self.logging.info( self.orb['orb'].seek( orb.ORBOLDEST ) )
            self.logging.info( self.orb['orb'].after(0) )
        except Exception,e:
            self.logging.error( 'orb.tell() => %s, %s' % (Exception,e) )


        #try:
        #    self.logging.debug( "orb position: %s" % (self.orb['orb'].tell()) )
        #except Exception,e:
        #    self.orb['orb'].after(0)
        #    self.orb['orb'].position(self.default_orb_read)
        #    try:
        #        self.logging.debug( "orb position: %s" % (self.orb['orb'].tell()) )
        #    except Exception,e:
        #        self.logging.error( "orb position: %s,%s" % (Exception,e) )

        if not self._test_orb():
            raise Exception("Problems connecting to (%s)" % self.orbname )


    def _extract_data(self):
        """
        Look for all packets
        """

        self.orb['last_check'] = stock.now()

        if self.errors > 10:
            raise Exception('10 consecutive errors on orb.reap()')

        try:
            # REAP new packet from ORB
            self.packet.new(  self.orb['orb'].reap(self.reap_wait)  )

        except orb.OrbIncompleteException, e:
            self.logging.debug("OrbIncompleteException orb.reap(%s)" % self.orbname)
            return True

        except Exception,e:
            self.logging.warning("%s Exception in orb.reap(%s) [%s]" % (Exception,self.orbname,e))
            self.errors += 1
            return False

        self.logging.debug("_extract_data(%s,%s)" % (self.packet.id, self.packet.time) )

        # reset error counter
        self.errors = 0

        if not self.packet.id or not self.packet.valid:
            self.logging.debug("_extract_data() => Not a valid packet" )
            return False

        # save ORB id to state file
        self.state.set(self.packet.id,self.packet.time)

        self.logging.debug( 'errors:%s' % self.errors )

        if self.packet.valid:
            self.logging.debug( '%s' % self.packet )
            # we print this on the statusFile class too...
            self.logging.debug( 'orblatency %s' % \
                    ( stock.strtdelta( stock.now() - self.packet.time ) ) )
            self.position = self.packet.id
            self.logging.debug( 'orbposition %s' % self.position )
            self.orb['last_success'] = stock.now()

            self._update_collection()
        else:
            self.logging.debug( 'invalid packet: %s %s' % (self.packet.id, self.packet.srcname) )

        return True

    def _update_collection(self):

        self.logging.debug( 'update_collection()' )

        # Verify if we need to update MongoDB
        if self.packet.valid:
            self.logging.debug('collection.update()')

            # Loop over packet and look for OPT channels
            for snetsta in self.packet:

                self.logging.info( 'Update entry: %s' % snetsta )
                documentid = "%s-%s" % ( snetsta,str(self.packet.srcname).replace('/','-') )

                parts = snetsta.split('_')

                #self.logging.debug( self.packet.dls[snetsta] )

                # Use dlmon class to parse all values on packet
                self.dlmon.new( self.packet.dls[snetsta] )

                # expand object with some info from packet
                self.dlmon.set( 'station', snetsta )
                self.dlmon.set( 'srcname', str(self.packet.srcname).replace('/','-') )
                self.dlmon.set( 'pckttime', self.packet.time )
                self.dlmon.set( 'pcktid', self.packet.id )
                self.dlmon.set( 'snet', parts[0] )
                self.dlmon.set( 'sta', parts[1] )


                # add entry for autoflush index
                self.dlmon.set( 'time_obj', datetime.fromtimestamp( self.packet.time ) )

                #self.logging.error( self.packet.dls[snetsta] )
                #self.logging.debug( self.dlmon.dump() )

                #self.collection.update({'id': snetsta}, {'$set':self.packet.dls[snetsta]}, upsert=True)
                self.collection.update({'id': documentid}, {'$set':self.dlmon.dump()}, upsert=True)
                #self.logging.error( 'end test' )

            # Create/update some indexes for the collection
            self._index_db()




    def _index_db(self):
        """
        Set index values on MongoDB
        """

        self.logging.debug( 'index_db()' )

        #Stop if we don't have any index defined.
        if not self.indexing or len( self.indexing ) < 1: return

        re_simple = re.compile( '.*simple.*' )
        re_text = re.compile( '.*text.*' )
        re_sparse = re.compile( '.*sparse.*' )
        re_hashed = re.compile( '.*hashed.*' )
        re_unique = re.compile( '.*unique.*' )

        for field, param in self.indexing.iteritems():

            unique = 1 if re_unique.match( param ) else 0
            sparse = 1 if re_sparse.match( param ) else 0

            style = 1
            if re_text.match( param ):
                style = 'text'
            elif re_hashed.match( param ):
                style = 'hashed'
            elif re_simple.match( param ):
                style = 1

            try:
                expireAfter = float( param )
            except:
                expireAfter = False

            self.logging.debug("ensure_index( [(%s,%s)], expireAfterSeconds = %s, unique=%s, sparse=%s)" % \
                    (field,style,expireAfter,unique,sparse) )
            self.collection.ensure_index( [(field,style)], expireAfterSeconds = expireAfter,
                    unique=unique, sparse=sparse)

        self.collection.reindex()
