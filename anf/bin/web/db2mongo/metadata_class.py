class metadataException(Exception):
    """
    Local class to raise Exceptions to the
    rtwebserver framework.
    """
    def __init__(self, message):
        super(metadataException, self).__init__(message)
        self.message = message


try:
    #import inspect
    import re
    import sys
    import json
    #from datetime import datetime, timedelta
    from pylab import mean
    from datetime import datetime
    from collections import defaultdict
except Exception, e:
    raise metadataException("Problems importing libraries.%s %s" % (Exception, e))

try:
    import antelope.datascope as datascope
    import antelope.orb as orb
    import antelope.Pkt as Pkt
    import antelope.stock as stock
except Exception, e:
    raise metadataException("Problems loading ANTELOPE libraries. %s(%s)" % (Exception, e))


try:
    from db2mongo.logging_class import getLogger
except Exception, e:
    raise metadataException("Problem loading logging_class. %s(%s)" % (Exception, e))

try:
    from db2mongo.db2mongo_libs import *
except Exception, e:
    raise metadataException("Problem loading db2mongo_libs.py file. %s(%s)" % (Exception, e))




class AutoVivification(dict):
    """Implementation of perl's autovivification feature."""
    def __getitem__(self, item):
        try:
            return dict.__getitem__(self, item)
        except KeyError:
            value = self[item] = type(self)()
            return value



class dlsensor_cache():
    def __init__(self):
        """
        Need a class to load the information in the dlsensor table
        and stores all values in a local dict. The tool returns the name
        for the provided serial. You can search for a sensor or for
        a digitizer. If not found then you get NULL value. In this case
        we set NULL to be "-".

        Usage:
            cache_object = dlsensor_cache()

            cache_object.add( dlident, dlmodel, snident, snmodel, time, endtime )

            sname = cache_object.sensor(snident, time)
            dname = cache_object.digitizer(dlident, time)

        """

        self.logging = getLogger(self.__class__.__name__)

        self.logging.debug( "dlsensor_cache.init()" )

        self.defaultTime = 0.0
        self.defaultEndtime = 9999999999.9
        self.sensors = {}
        self.digitizers = {}

    def add(self, dlident, dlmodel, snident, snmodel,
            time='-', endtime='-'):
        """
        New rows from the dlsensor table are sent to this
        class using the add method. This will create an
        object for each type of instrument tracked.
        """

        try:
            time = float(time)
        except:
            time = self.defaultTime

        try:
            endtime = float(endtime)
        except:
            endtime = self.defaultEndtime

        if not snident in self.sensors:
            self.sensors[snident] = []

        self.logging.debug( "dlsensor_cache.add(%s,%s,%s,%s,%s,%s)" % \
                (dlident, dlmodel, snident, snmodel, time, endtime) )

        #Add a new entry to the sensor cache.
        if not snident in self.sensors:
            self.sensors[dlident] = []

        self.sensors[snident].append({'time':time, 'endtime':endtime,
                                    'model':snmodel} )

        #Add a new entry to the digitizer cache.
        if not dlident in self.digitizers:
            self.digitizers[dlident] = []

        self.digitizers[dlident].append({'time':time, 'endtime':endtime,
                                    'model':dlmodel} )

    def _search(self, group, ident, time=False):
        """
        Find dlmodel for this serial.
        Generic internal function for looking at the cached
        data for a match entry.
        """

        self.logging.debug( "dlsensor_cache.search(%s,%s,%s)" % \
                (group, ident, time) )

        name = '-'
        timeless = False

        if not time:
            timeless = True

        else:
            try:
                time = float(time) + 1.0
            except:
                timeless = True
                time = False

        test = getattr(self, group)

        if ident in test:
            for k in test[ident]:
                self.logging.debug( "Look for %s in time:%s,endtime:%s )" % \
                        ( time, k['time'], k['endtime'] ) )
                if timeless or time >= k['time'] and time <= k['endtime']:
                    name = k['model']
                    break

        self.logging.debug( "dlsensor_cache.search() => %s" % name )

        return name


    def digitizer(self, ident, time=False):
        return self._search('digitizers', ident, time)

    def sensor(self, ident, time=False):
        return self._search('sensors', ident, time)




class Metadata(dlsensor_cache):
    def __init__(self, db=False, orbs={}, db_subset=False, orb_select=False):
        """
        Class to load information from multiple Datascope tables that track
        station configuration and metadata values. Some information is
        appended to the objects if a value for an ORB is provided and the
        station is found on it. We track all packets related to the station
        and we have the option to extract some information from the pf/st
        packets.

        Usage:
            metadata = Metadata(db,orbs,db_subset,orb_select)

            metadata.validate()

            while True:
                if metadata.need_update():
                    metadata.update()
                    data,error = metadata.data()
                sleep(time)

        """
        self.logging = getLogger(self.__class__.__name__)

        self.logging.debug( "Metadata.init()" )

        self.orbs = {}
        self.cache = {}
        self.db = False
        self.database = db
        self.dbs_tables = {}
        self.perf_db = False
        self.perf_subset = False
        self.orbservers = orbs
        self.timezone = 'UTC'
        self.error_cache = {}
        self.perf_days_back = 30
        self.db_subset  = db_subset
        self.orb_select = orb_select
        self.timeformat = '%D (%j) %H:%M:%S %z'

        self.tables = ['site']

        self.tags       = False
        self.deployment = False
        self.sensor     = False
        self.comm       = False
        self.digitizer  = False
        self.balers     = False

        self.dlsensor_cache = False


    def validate(self):
        self.logging.debug( 'validate()' )

        if self.db: return True

        # Vefiry database files
        if self.database:
            if verify_db(self.database):
                self.db = self.database
            else:
                raise metadataException("Not a vaild database: %s" % (self.database))
        else:
            raise metadataException("Missing value for database" )

        # Test configuration to see how many
        # tables we are using.

        if test_yesno( self.deployment ):
            self.tables.append( 'deployment')

        if test_yesno( self.sensor ):
            self.tables.append( 'stage')
            self.tables.append( 'calibration')
            self.tables.append( 'snetsta')

        if test_yesno( self.comm ):
            self.tables.append( 'comm')
            self.tables.append( 'snetsta')

        if test_yesno( self.digitizer ):
            self.tables.append( 'stage')
            self.tables.append( 'snetsta')

        if test_yesno( self.balers ):
            self.tables.append( 'stabaler')

        # Verify tables
        for table in self.tables:
            path = test_table(self.db,table)
            if not path:
                raise metadataException("Empty or missing: %s %s" % (self.db, table))

            # Save this info for tracking of the tales later
            self.dbs_tables[table] = { 'path':path, 'md5':False }
            self.logging.debug( 'run validate(%s) => %s' % (table, path) )

        # Track Channel Perf database if needed
        if ( self.perf_db ):
            path = test_table(self.perf_db,'chanperf')
            if not path:
                raise metadataException("Empty or missing: %s %s" % (self.perf_db, 'chanperf'))

            # Save this info for tracking of the tales later
            self.dbs_tables['chanperf'] = { 'path':path, 'md5':False }
            self.logging.debug( 'run validate(%s) => %s' % ('chanperf', path) )

        return True


    def need_update(self, dbonly=False):
        """
        Verify if the md5 checksum changed on any table.
        By default we return True because we want to update
        any ORB data that we can find for the sites.
        We can overwrite this and verify
        the actual checksums by setting dbonly=True or if
        we don't specify any ORBs to check.
        """
        self.logging.debug( "need_update()" )

        if not dbonly and len( self.orbs ) > 0: return True

        for name in self.tables:

            md5 = self.dbs_tables[name]['md5']
            test = get_md5(self.dbs_tables[name]['path'])

            self.logging.debug('(%s) table:%s md5:[old: %s new: %s]' % \
                        (self.db,name,md5,test) )

            if test != md5: return True

        return False

    def update(self, forced=False):
        """
        Update cached data from database
            forced:    Maybe we want to force an update to the cache.
        """
        if not self.db: self.validate()

        if forced or self.need_update(dbonly=True):
            for name in self.tables:
                self.dbs_tables[name]['md5'] = get_md5( self.dbs_tables[name]['path'] )
            self._get_db_data()

        self._get_orb_data()

    def data(self):
        """
        Function to export the data from the tables
        """
        self.logging.debug( "data(%s)" % (self.db) )

        if not self.db: self.validate()

        return ( self._clean_cache(self.cache),  self._clean_cache(self.error_cache) )


    def _verify_cache(self,snet,sta,group=False,primary=False):
        """
        Not sure if we already have an entry for the snet-sta value
        in the local cache. Make one if missing if this is set to
        be PRIMARY. If not PRIMARY then return False and DON'T update.
        """
        if not snet: return False
        if not sta: return False

        if not snet in self.cache:
            if not primary: return False
            self.cache[snet] = {}

        if not sta in self.cache[snet]:
            if not primary: return False
            self.cache[snet][sta] = {}

        if group and not group in self.cache[snet][sta]:
            self.cache[snet][sta][group] = defaultdict(lambda: defaultdict())

        return True

    def _not_in_db(self, snet, sta, table):
        """
        Sometimes the tables will have invalid entries. Some snet or sta
        values that are not real sites. If we identify any using the function
        self._verify_cache() then we use this method to put that information
        on the "ERROR" cache that we send out to the user during the .data() call.
        """
        self.logging.warning('ERROR ON DATABASE [%s_%s] %s' % (snet,sta,table) )

        if not snet in self.error_cache:
            self.error_cache[snet] = {}

        if not sta in self.error_cache[snet]:
            self.error_cache[snet][sta] = {}

        try:
            len(self.error_cache[snet][sta][table])
        except:
            self.error_cache[snet][sta][table] = []

        self.error_cache[snet][sta][table].append(
            'FOUND DATA ON TABLE BUT NOT A VALID SNET_STA ON DEPLOYMENT' )

    def _get_orb_data(self):
        """
        Look into every ORB listed on the parameter file
        and get some information from them.
        1) The clients of the ORB (not using this now)
        2) List of sources.

        Then we track the time of every packet type that
        we see for every station.
        """

        self.logging.debug( "Updat ORB cache" )

        self.logging.debug( self.orbservers )

        for orbname in self.orbservers:
            if not orbname or not isinstance(orbname, str): continue
            self.logging.debug( "init ORB %s" % (orbname) )

            # Expand the object if needed
            if not orbname in self.orbs:
                self.orbs[orbname] = {}
                self.logging.debug( "orb.Orb(%s)" % (orbname) )
                self.orbs[orbname]['orb'] = orb.Orb( orbname )


            # Clean all local info related to this ORB
            self.orbs[orbname]['clients'] = {}
            self.orbs[orbname]['sources'] = {}
            self.orbs[orbname]['info'] = {
                    'status':'offline',
                    'last_check':0,
                    }

            try:
                self.logging.debug("connect to orb(%s)" % orbname )
                self.orbs[orbname]['orb'].connect()
                self.orbs[orbname]['orb'].stashselect(orb.NO_STASH)
            except Exception,e:
                raise metadataException("Cannot connect to ORB: %s %s" % (orbname, e))

            # Extract the information
            self._get_orb_sta_latency( orbname )
            self._get_orb_sta_inp( orbname )

            self.orbs[orbname]['orb'].close()

    def _get_orb_sta_latency(self, name):
        """
        Look for all CLIENTS and SOURCES.
        """

        self.logging.debug( 'Check ORB(%s) sources' % name)

        pkt = Pkt.Packet()

        self.orbs[name]['orb'].select( self.orb_select )
        self.orbs[name]['orb'].reject('.*/pf.*|.*/log|/db/.*|.*/MSTC')

        self.orbs[name]['info']['status'] = 'online'
        self.orbs[name]['info']['last_check'] = stock.now()

        # get clients
        self.logging.debug("get clients orb(%s)" % name )
        result = self.orbs[name]['orb'].clients()

        for r in result:
            if isinstance(r,float):
                self.orbs[name]['info']['clients_time'] = r
                self.logging.debug("orb(%s) client time %s" % (name, r) )
            else:
                self.orbs[name]['clients'] = r

        # get sources
        self.logging.debug("get sources orb(%s)" % name )
        result = self.orbs[name]['orb'].sources()

        for r in result:
            # Verify if this is a valid field or just the reported time
            if isinstance(r,float):
                self.orbs[name]['info']['sources_time'] = r
                self.logging.debug("orb(%s) sources time %s" % (name, r) )
            else:
                for stash in r:
                    srcname = stash['srcname']
                    pkt.srcname = Pkt.SrcName(srcname)
                    snet = pkt.srcname.net
                    sta = pkt.srcname.sta

                    # Not sure if this will ever occur
                    if not snet or not sta: continue

                    self.logging.debug("orb(%s) update %s %s" % (name,snet,sta) )

                    self._verify_cache(snet,sta,'orb',primary=True)

                    self.cache[snet][sta]['orb'][srcname] = parse_sta_time( stash['slatest_time'] )

                    if not 'lastpacket' in self.cache[snet][sta]:
                        self.cache[snet][sta]['lastpacket'] = 0

                    if self.cache[snet][sta]['lastpacket'] < self.cache[snet][sta]['orb'][srcname]:
                        self.cache[snet][sta]['lastpacket'] = self.cache[snet][sta]['orb'][srcname]


    def _get_orb_sta_inp(self, name):

        self.logging.debug( 'Check ORB(%s) sources' % name)

        pkt = Pkt.Packet()

        self.logging.debug("get pf/st packets from orb(%s)" % name )
        self.orbs[name]['orb'].reject( '' )
        self.orbs[name]['orb'].select( '.*/pf/st' )

        # get pf/st packet sources
        sources = self.orbs[name]['orb'].sources()
        self.logging.debug( sources )

        # Make list of all valid packet names
        valid_packets = []
        for r in sources:
            if isinstance(r,float): continue
            for stash in r:
                srcname = stash['srcname']
                pkt.srcname = Pkt.SrcName(srcname)
                self.logging.debug("sources => %s" % srcname )
                valid_packets.append( srcname )

        # loop over each source
        for pckname in valid_packets:
            # get pf/st packets
            self.logging.debug("get %s packets from orb(%s)" % (pckname, name) )
            self.orbs[name]['orb'].select( pckname )
            attempts = 0
            while True:
                attempts += 1
                self.logging.debug("get ORBNEWEST packet from orb(%s) for %s" % (name, pckname) )
                pktid, srcname, pkttime, pktbuf = self.orbs[name]['orb'].get(orb.ORBNEWEST)
                self.logging.debug("pktid(%s)" % pktid )
                # Verify pckt id
                if int(float(pktid)) > 0: break
                if attempts > 10: break

            # Don't have anything useful here
            if attempts > 10: continue

            # Try to extract name of packet. Default to the orb provided name.
            pkt = Pkt.Packet( srcname, pkttime, pktbuf )
            srcname = pkt.srcname if pkt.srcname else srcname
            self.logging.debug( 'srcname: %s' % srcname )

            if pkt.pf.has_key('dls'):
                for netsta in pkt.pf['dls']:
                    self.logging.debug('Packet: extract: %s' % netsta)
                    temp = netsta.split('_')
                    snet = temp[0]
                    sta = temp[1]

                    self._verify_cache(snet,sta,'orbcomms',primary=True)

                    if not 'inp' in pkt.pf['dls'][netsta]:
                        self.logging.debug('NO inp value in pkt: %s' % pckname)
                        continue

                    self.cache[snet][sta]['orbcomms'] = {
                        'id': pktid,
                        'name': pckname,
                        'time': pkttime,
                        'inp': pkt.pf['dls'][netsta]['inp']
                        }


    def _get_db_data(self):
        """
        Private function to load the data from the tables
        """
        self.logging.debug( "_get_db_data(%s)" % (self.db) )

        self.cache = {}
        self.error_cache = {}

        if test_yesno( self.deployment ):
            self._get_deployment_list()
        else:
            self._get_main_list()

        if test_yesno( self.digitizer ): self._get_digitizer()
        if test_yesno( self.sensor ):    self._get_sensor()
        if test_yesno( self.comm ):      self._get_comm()
        if test_yesno( self.balers ):    self._get_stabaler()
        if test_yesno( self.adoption ):  self._get_adoption()
        if test_yesno( self.tags ):      self._set_tags()
        if ( self.perf_db ):             self._get_chanperf()

    def _get_chanperf(self):

        self.logging.debug( "_get_chanperf()")

        today = stock.str2epoch( str(stock.yearday( stock.now() )) )
        lastmonth =  today - (86400 * int(self.perf_days_back))

        month = {}
        week = {}

        fields = ['snet','sta','chan','time','perf']
        steps = [ 'dbopen chanperf', 'dbjoin -o snetsta',
                    'dbsubset time >= %s' % lastmonth ]

        if self.perf_subset:
                    steps.append ( 'dbsubset %s' % self.perf_subset )

        for v in extract_from_db(self.perf_db, steps, fields, self.db_subset):
            snet = v.pop('snet')
            sta = v.pop('sta')
            chan = v.pop('chan')

            fullname = "%s.%s.%s" % ( snet, sta, chan )

            self.logging.debug( "_get_chanperf(%s_%s)" % (snet,sta) )

            if self._verify_cache(snet,sta,'chanperf'):
                try:
                    if len( self.cache[snet][sta]['chanperf'][chan] ) < 1: raise
                except:
                    self.cache[snet][sta]['chanperf'][chan] = {}

                #v['time'] = readable_time( v['time'], '%Y-%m-%d' )
                v['time'] = int( v['time'] )
                self.cache[snet][sta]['chanperf'][chan][ v['time'] ] = v['perf']


    def _get_adoption(self):

        self.logging.debug( "_get_adoption()")

        steps = [ 'dbopen adoption']

        fields = ['sta','snet','time','newsnet','newsta','atype','auth']


        for v in extract_from_db(self.db, steps, fields, self.db_subset):
            sta = v.pop('sta')
            snet = v.pop('snet')
            v['time']= parse_sta_time( v['time'] )

            self.logging.debug( "_get_adoption(%s_%s)" % (snet,sta) )

            if self._verify_cache(snet,sta,'adoption'):
                try:
                    if len( self.cache[snet][sta]['adoption'] ) < 1: raise
                except:
                    self.cache[snet][sta]['adoption'] = []

                self.cache[snet][sta]['adoption'].append( v )

            else:
                self._not_in_db(snet, sta, 'adoption')


    def _get_sensor(self):

        self.logging.debug( "_get_sensor()")

        tempcache = AutoVivification()

        # We need dlsensor information for this.
        if not self.dlsensor_cache:
            self.dlsensor_cache = dlsensor_cache()
            self._load_dlsensor_table()

        steps = [ 'dbopen stage',
                'dbsubset gtype !~ /digitizer|Q330.*|FIR.*/',
                'dbjoin -o calibration sta chan stage.time#calibration.time::calibration.endtime',
                'dbjoin -o snetsta',
                'dbsort sta chan stage.time stage.endtime']

        fields = ['snet', 'sta', 'chan', 'calibration.samprate', 'segtype',
                'calib', 'ssident', 'snname', 'dlname', 'gtype', 'stage.time',
                'calibration.insname', 'calibration.units', 'stage.endtime']

        for db_v in extract_from_db(self.db, steps, fields, self.db_subset):
            sta = db_v['sta']
            snet = db_v['snet']
            ssident = db_v['ssident']
            snname = db_v['snname']
            dlname = db_v['dlname']
            gtype = db_v['gtype']
            chan = db_v['chan']
            samprate = db_v['calibration.samprate']
            units = db_v['calibration.units']
            segtype = db_v['segtype']
            calib = db_v['calib']
            insname = db_v['calibration.insname']

            time = parse_sta_time( db_v['stage.time'] )
            endtime = parse_sta_time( db_v['stage.endtime'] )
            twin = "%s.%s" % (time, endtime)

            self.logging.debug( "_get_sensor(%s_%s)" % (snet,sta) )

            if re.match( "\@.+", snname):
                snname = dlname

            if re.match( "q330.*", snname):
                snname = 'soh-internal'

            if re.match( "\qep_soh_only", snname):
                snname = 'qep'

            # Translate "sensor" to a value from the dlsensor table
            #if gtype == 'sensor':
            #    #gtype = self.dlsensor_cache.sensor(ssident,time)
            #    gtype = snname

            #if snname == '-':
            #    snname = gtype
            if snname == '-':
                try:
                    snname = re.split('/|,|=|',insname)[0].lower().replace (".", "_").replace (" ", "_")
                except:
                    if dlname != '-':
                        snname = dlname
                    else:
                        snnname = gtype

            #self.logging.debug( "gtype:%s snname:%s)" % (gtype,snname) )
            self.logging.debug( "snname:%s)" % (snname) )

            if self._verify_cache(snet,sta,'sensor'):
                # Saving to temp var to limit dups
                tempcache[snet][sta][snname][ssident][twin][chan] = insname

                # Saving channels and calibs to new list
                try:
                    len(self.cache[snet][sta]['channels'][chan])
                except:
                    try:
                        len(self.cache[snet][sta]['channels'])
                    except:
                        self.cache[snet][sta]['channels'] = {}
                    self.cache[snet][sta]['channels'][chan] = []

                self.cache[snet][sta]['channels'][chan].append( {
                        'time': time,
                        'endtime': endtime,
                        'samprate': samprate,
                        'segtype': segtype,
                        'units': units,
                        'calib': calib
                        } )

            else:
                self._not_in_db(snet, sta, 'sensor')


        for snet in tempcache:
            for sta in tempcache[snet]:

                activesensors = {}
                for snname in tempcache[snet][sta]:
                    for ssident in tempcache[snet][sta][snname]:
                        for twin in tempcache[snet][sta][snname][ssident]:

                            # Option to add variable with channel list
                            tempchans = []
                            tempname = '-'
                            for chan in tempcache[snet][sta][snname][ssident][twin]:
                                tempchans.append( chan )
                                tempname = tempcache[snet][sta][snname][ssident][twin][chan]

                            start, end = twin.split('.')
                            if end == '-': activesensors[snname] = 1

                            try:
                                len(self.cache[snet][sta]['sensor'][snname][ssident])
                            except:
                                self.cache[snet][sta]['sensor'][snname][ssident] = []

                            self.cache[snet][sta]['sensor'][snname][ssident].append( {
                                    'time': start,
                                    'endtime': end,
                                    'channels': tempchans,
                                    'insname': tempname
                                    } )
                if len(activesensors) > 0:
                    self.cache[snet][sta]['activesensors'] = activesensors.keys()



    def _load_dlsensor_table(self):
        self.logging.debug( "_load_dlsensor_table()")

        steps = [ 'dbopen dlsensor']

        fields = ['dlmodel','dlident','chident','time','endtime','snmodel','snident']

        for k in extract_from_db(self.db, steps, fields):
            self.dlsensor_cache.add( k['dlident'], k['dlmodel'],
                    k['snident'], k['snmodel'], k['time'], k['endtime'])


    def _get_stabaler(self):
        self.logging.debug( "_get_stabaler()")

        steps = [ 'dbopen stabaler','dbsort net sta time']

        fields = ['net','sta','time','inp','last_reg','last_reboot',
                    'model','nreg24','nreboot','firm','ssident']

        for v in extract_from_db(self.db, steps, fields):
            snet = v.pop('net')
            sta = v.pop('sta')

            v['time']= parse_sta_time( v['time'] )
            v['last_reg'] = parse_sta_time( v['last_reg'] )
            v['last_reboot'] = parse_sta_time( v['last_reboot'] )

            self.logging.debug('_get_stabaler(%s_%s)' % (snet,sta) )

            if self._verify_cache(snet,sta,'stabaler'):
                try:
                    if len(self.cache[snet][sta]['stabaler']) < 1: raise
                except:
                    self.cache[snet][sta]['stabaler'] = []

                self.cache[snet][sta]['stabaler'].append( v )

            else:
                # We cannot run with self.db_subset. Ignore this error
                #self._not_in_db(snet, sta, 'stabaler')
                pass


    def _get_comm(self):

        self.logging.debug( "_get_comm()")

        steps = [ 'dbopen comm', 'dbjoin -o snetsta']

        fields = ['sta','snet','time','endtime','commtype','provider','power','dutycycle']

        for v in extract_from_db(self.db, steps, fields, self.db_subset):
            sta = v.pop('sta')
            snet = v.pop('snet')
            v['time']= parse_sta_time( v['time'] )
            v['endtime']= parse_sta_time( v['endtime'] )

            self.logging.debug( "_get_comm(%s_%s)" % (snet,sta) )

            if self._verify_cache(snet,sta,'comm'):
                try:
                    if len( self.cache[snet][sta]['comm'] ) < 1: raise
                except:
                    self.cache[snet][sta]['comm'] = []

                self.cache[snet][sta]['comm'].append( v )

                if v['endtime'] == '-':
                    self.cache[snet][sta]['power'] = v['power']
                    self.cache[snet][sta]['dutycycle'] = v['dutycycle']
                    self.cache[snet][sta]['activecommtype'] = v['commtype']
                    self.cache[snet][sta]['activeprovider'] = v['provider']

            else:
                self._not_in_db(snet, sta, 'comm')


    def _get_digitizer(self):

        self.logging.debug( "get_digitizer()")

        # We need dlsensor information for this.
        if not self.dlsensor_cache:
            self.dlsensor_cache = dlsensor_cache()
            self._load_dlsensor_table()

        steps = [ 'dbopen stage',
                'dbsubset gtype =~ /digitizer/ && iunits =~ /V/ && ounits =~ /COUNT|COUNTS|counts/',
                'dbjoin calibration sta chan time',
                'dbsort -u sta time endtime ssident dlname', 'dbjoin -o snetsta']

        fields = ['snet', 'sta', 'ssident', 'gtype', 'time', 'endtime', 'insname', 'dlname']

        activedigitizers = {}

        for v in extract_from_db(self.db, steps, fields, self.db_subset):
            sta = v.pop('sta')
            snet = v.pop('snet')
            fullname  = "%s_%s" % (snet, sta)
            ssident = v.pop('ssident')
            gtype = v.pop('gtype')
            dlname = v.pop('dlname')
            v['time']= parse_sta_time( v['time'] )
            v['endtime']= parse_sta_time( v['endtime'] )
            time = v['time']
            endtime = v['endtime']


            if re.match( "\qep_.+", dlname):
                dlname = 'qep'

            if dlname == '-':
                dlname = gtype

            self.logging.debug( "_get_digitizer(%s_%s, %s, %s)" % (snet,sta,time,endtime) )


            # Translate "digitizer" to a value from the dlsensor table
            #if ssident:
            #    gtype = self.dlsensor_cache.digitizer(ssident,time)

            #self.logging.debug( "gtype:%s ssident:%s)" % (gtype,ssident) )
            self.logging.debug( "dlname:%s ssident:%s)" % (dlname,ssident) )

            # Track active values
            if endtime == '-':
                try:
                    len( activedigitizers[fullname] )
                except:
                    activedigitizers[fullname] = {}

                #activedigitizers[fullname][gtype] = 1
                activedigitizers[fullname][dlname] = 1


            if self._verify_cache(snet,sta,'digitizer'):

                try:
                    #len(self.cache[snet][sta]['digitizer'][gtype][ssident])
                    len(self.cache[snet][sta]['digitizer'][dlname][ssident])
                except:
                    #self.cache[snet][sta]['digitizer'][gtype][ssident] = []
                    self.cache[snet][sta]['digitizer'][dlname][ssident] = []

                #self.cache[snet][sta]['digitizer'][gtype][ssident].append( v )
                self.cache[snet][sta]['digitizer'][dlname][ssident].append( v )

            else:
                self._not_in_db(snet, sta, 'digitizer')


        for name in activedigitizers.iterkeys():
            temp = name.split('_')
            snet = temp[0]
            sta = temp[1]
            try:
                self.cache[snet][sta]['activedigitizers'] = activedigitizers[name].keys()
            except:
                self._not_in_db(snet, sta, 'activedigitizers')


    def _get_main_list(self):

        self.logging.debug( "_get_main_list()" )

        # Default is with no snetsta
        steps = [ 'dbopen site', 'dbsort sta']
        fields = ['sta','ondate','offdate','lat','lon','elev','staname','statype',
                'dnorth','deast']

        # Test if we have snetsta table
        with datascope.closing(datascope.dbopen(self.db, 'r')) as db:
            dbtable = db.lookup(table='snetsta')
            if dbtable.query(datascope.dbTABLE_PRESENT):
                steps = [ 'dbopen site', 'dbjoin -o snetsta', 'dbsort sta']
                fields = ['snet','sta','ondate','offdate','lat','lon','elev','staname','statype',
                        'dnorth','deast']

        for v in extract_from_db(self.db, steps, fields, self.db_subset):
            sta = v['sta']
            if 'snet' in v:
                snet = v['snet']
            else:
                snet = '-'

            self.logging.debug( "_get_main_list(%s_%s)" % (snet,sta) )

            # Fix values of time and endtime
            v['time'] = parse_sta_date( v['ondate'],epoch=True )
            v['endtime'] = parse_sta_date( v['offdate'],epoch=True )

            # Readable times
            v['strtime'] = readable_time(v['time'], self.timeformat, self.timezone)
            v['strendtime'] = readable_time(v['endtime'], self.timeformat, self.timezone)


            # Need lat and lon with 2 decimals only
            v['latlat'] = v['lat']
            v['lonlon'] = v['lon']
            v['lat'] = round(v['lat'],2)
            v['lon'] = round(v['lon'],2)


            self._verify_cache(snet,sta,primary=True)

            self.cache[snet][sta] = v

    def _get_deployment_list(self):

        self.logging.debug( "_get_deployment_list()" )

        steps = [ 'dbopen deployment', 'dbjoin -o site']

        fields = ['vnet','snet','sta','time','endtime','equip_install',
            'equip_remove', 'cert_time','decert_time','pdcc',
            'lat','lon','elev','staname','statype','ondate','offdate']

        for v in extract_from_db(self.db, steps, fields, self.db_subset):
            sta = v['sta']
            snet = v['snet']

            self.logging.debug( "_get_deployment_list(%s_%s)" % (snet,sta) )

            # fix values of date
            for f in ['ondate','offdate']:
                v[f] = parse_sta_date( v[f] )

            # fix values of time
            for f in ['time', 'endtime', 'equip_install','equip_remove',
                    'cert_time','decert_time']:
                v[f] = parse_sta_time( v[f] )

            # Readable times
            v['strtime'] = readable_time(v['time'], self.timeformat, self.timezone)
            v['strendtime'] = readable_time(v['endtime'], self.timeformat, self.timezone)

            # Need lat and lon with 2 decimals only
            v['latlat'] = v['lat']
            v['lonlon'] = v['lon']
            v['lat'] = round(v['lat'],2)
            v['lon'] = round(v['lon'],2)


            self._verify_cache(snet,sta,primary=True)

            self.cache[snet][sta] = v

    def _set_tags( self ):
        """
        TA array expands into multiple geographical regions.
        We need to add some quick identifier to the data blob.
        """
        for snet in self.cache:
            if not snet: continue
            for sta in self.cache[snet]:
                if not sta: continue

                self.logging.debug( "_set_tags(%s_%s)" % (snet,sta) )

                if self._verify_cache(snet,sta,'tags'):
                    try:
                        if len(self.cache[snet][sta]['tags']) < 1: raise
                    except:
                        self.cache[snet][sta]['tags'] = []

                    # Tags for sites on the YUKON area
                    if self.cache[snet][sta]['lat'] > 58.0 and \
                            self.cache[snet][sta]['lon'] > -147.0:
                        self.cache[snet][sta]['tags'].append( 'yukon' )

                    # Tags for TA **ONLY**
                    if snet == 'TA':
                        self.cache[snet][sta]['tags'].append( 'usarray' )

                        if self.cache[snet][sta]['vnet'] == '_CASCADIA-TA':
                            self.cache[snet][sta]['tags'].append( 'cascadia' )

                        if self.cache[snet][sta]['lat'] > 50:
                            self.cache[snet][sta]['tags'].append( 'alaska' )
                        else:
                            self.cache[snet][sta]['tags'].append( 'low48' )

                        # Need to identify active BGAN connections
                        bgantag = 'non-bgan'
                        try:
                            for c in self.cache[snet][sta]['comm']:
                                # active?
                                if c['endtime'] == '-':
                                    # BGAN?
                                    if c['commtype'] == 'BGAN':
                                        # matched
                                        bgantag = 'bgan'
                        except:
                            pass

                        # Add BGAN results
                        self.cache[snet][sta]['tags'].append( bgantag )

                    # Activity tag
                    if self.cache[snet][sta]['time'] == '-' or \
                            self.cache[snet][sta]['time'] > stock.now():
                        self.cache[snet][sta]['tags'].append( 'prelim' )
                    elif self.cache[snet][sta]['endtime'] == '-' or \
                            self.cache[snet][sta]['endtime'] > stock.now():
                        self.cache[snet][sta]['tags'].append( 'active' )
                    else:
                        self.cache[snet][sta]['tags'].append( 'decommissioned' )

                    # Adoption tag
                    if 'adoption' in self.cache[snet][sta]:
                        self.cache[snet][sta]['tags'].append( 'adopted' )

                    # Certification tag
                    if 'cert_time' in self.cache[snet][sta]:
                        if self.cache[snet][sta]['cert_time'] == '-' or \
                                self.cache[snet][sta]['cert_time'] > stock.now():
                            self.cache[snet][sta]['tags'].append( 'uncertified' )
                        elif self.cache[snet][sta]['decert_time'] == '-' or \
                                self.cache[snet][sta]['decert_time'] < stock.now():
                            self.cache[snet][sta]['tags'].append( 'certified' )
                        else:
                            self.cache[snet][sta]['tags'].append( 'decertified' )

    def _clean_cache( self, cache ):
        """
        Need to reshape the dict
        """
        results = []

        for snet in cache:
            if not snet: continue
            for sta in cache[snet]:
                if not sta: continue
                # Stringify the dict. This will avoid loosing decimal places
                oldEntry = json.loads( json.dumps( cache[snet][sta] ) )

                # Generic id for this entry
                oldEntry['id'] = snet + '_' + sta
                oldEntry['dlname'] = snet + '_' + sta

                if not 'snet' in oldEntry: oldEntry['snet'] = snet
                if not 'sta' in oldEntry: oldEntry['sta'] = sta

                # add entry for autoflush index and IM checks
                oldEntry['lddate'] = datetime.fromtimestamp( stock.now() )
                results.append(oldEntry)

        return results
