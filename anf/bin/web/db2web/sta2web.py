from __main__ import *


class Stations():
    def __init__(self, pf, clean=False):
        """
        Load class and get the data
        """

        notify( "Stations(): init()" )

        self.db = False
        self.orbs = {}
        self.cache = {}
        self.dbs_tables = {}

        self.tables = ['deployment','site','comm','sensor','dlsensor','dlsite']

        # not implementing type for now.
        self.pf_keys = {
                'timezone':{'type':'str','default':'utc'},
                'db_subset':{'type':'str','default':False},
                'orb_select':{'type':'str','default':False},
                'adoptions':{'type':'bool','default':False},
                'sensor':{'type':'bool','default':False},
                'comm':{'type':'bool','default':False},
                'dataloggers':{'type':'bool','default':False},
                'balers':{'type':'bool','default':False},
                'calib_vals':{'type':'bool','default':False},
                'database':{'type':'str','default':False},
                'orbservers':{'type':'dict','default':{}},
                'db_mongo_index':{'type':'dict','default':{}},
                'mongo_host':{'type':'str','default':None},
                'mongo_namespace':{'type':'str','default':'dev'},
                'mongo_user':{'type':'str','default':None},
                'mongo_password':{'type':'str','default':None},
                }

        self._read_pf(pf)

        try:
            self.mongo_instance = MongoClient(self.mongo_host)
            self.mongo_db = self.mongo_instance.get_database( self.mongo_namespace )
            self.mongo_db.authenticate(self.mongo_user, self.mongo_password)
            if clean:
                self.mongo_db.drop_collection("metadata")

        except Exception,e:
            sys.exit("Problem with MongoDB Configuration. %s(%s)\n" % (Exception,e) )

        # if not self.refresh:
        self.refresh = 60 # every minute default

        # Check DBs
        self._init_db()



    def _verify_cache(self,snet,sta,group=False):
        if not snet in self.cache:
            self.cache[snet] = {}

        if not sta in self.cache[snet]:
            self.cache[snet][sta] = {}

        if group and not group in self.cache[snet][sta]:
            self.cache[snet][sta][group] = defaultdict(lambda: defaultdict(defaultdict))

    def dump(self):
        """
        Call this method 'dump' from parent to trigger an update
        to the MongoDB instance.
        """
        if not self._get_sta_cache(): return
        self._get_all_orb_cache()
        self._dump_cache()


    def _read_pf(self, pfname):
        """
        Read configuration parameters from rtwebserver pf file.
        """

        log( 'Read parameters from pf file')

        pf = stock.pfread(pfname)

        for attr in self.pf_keys:
            temp = pf.get(attr, self.pf_keys[attr]['default'])

            setattr(self, attr, temp)
            log( "%s: read_pf[%s]: %s" % (pfname, attr, getattr(self,attr) ) )


    def _get_all_orb_cache(self):
        debug( "Updat ORB cache" )

        debug( self.orbservers )

        for orbname in self.orbservers:
            debug( "init ORB %s" % (orbname) )

            self.orbs[orbname] = {}
            self.orbs[orbname]['clients'] = {}
            self.orbs[orbname]['sources'] = {}
            self.orbs[orbname]['info'] = {
                    'status':'offline',
                    'last_check':0,
                    }

            self.orbs[orbname]['orb'] = orb.Orb(orbname)
            self._get_orb_cache(orbname)

    def _get_orb_cache(self, name):

        debug( 'Check ORB(%s) sources' % name)

        pkt = Pkt.Packet()

        try:
            debug("connect to orb(%s)" % name )
            self.orbs[name]['orb'].connect()
        except Exception,e:
            self.orbs[name]['info']['status'] = e
            error('Cannot connect ORB [%s]: %s' % (orbname,e) )
        else:
            self.orbs[name]['info']['status'] = 'online'
            self.orbs[name]['info']['last_check'] = stock.now()
            try:
                # get clients
                debug("get clients orb(%s)" % name )
                result = self.orbs[name]['orb'].clients()

                for r in result:
                    if isinstance(r,float):
                        self.orbs[name]['info']['clients_time'] = r
                        debug("orb(%s) client time %s" % (name, r) )
                    else:
                        self.orbs[name]['clients'] = r
            except Exception,e:
                error("Cannot query orb(%s) %s %s" % (name, Exception, e) )

            try:
                # get sources
                debug("get sources orb(%s)" % name )
                result = self.orbs[name]['orb'].sources()

                for r in result:
                    if isinstance(r,float):
                        self.orbs[name]['info']['sources_time'] = r
                        debug("orb(%s) sources time %s" % (name, r) )
                    else:
                        for stash in r:

                            srcname = stash['srcname']
                            pkt.srcname = Pkt.SrcName(srcname)
                            snet = pkt.srcname.net
                            sta = pkt.srcname.sta

                            #del stash['srcname']

                            debug("orb(%s) update %s %s" % (name,snet,sta) )

                            self._verify_cache(snet,sta,'orb')

                            self.cache[snet][sta]['orb'][srcname] = parse_time( stash['slatest_time'] )

            except Exception,e:
                error("Cannot query orb(%s) %s %s" % (name, Exception, e) )

        self.orbs[name]['orb'].close()

    def _get_sensor(self):

        debug( "Stations(): dlsensor()")

        steps = [ 'dbopen dlsite', 'dbsort -u dlname ssident', 'dbjoin dlsensor ssident#dlident']

        debug( ', '.join(steps) )

        #steps.extend(['dbsort dlname snmodel dlsite.time'])

        with datascope.freeing(self.db.process( steps )) as dbview:
            if not dbview.record_count:
                warning( 'No records in dlsensor join %s' % \
                        dbview.query(datascope.dbDATABASE_NAME) )
                return

            for temp in dbview.iter_record():
                (name,chident,snident,snmodel,time,endtime) = \
                    temp.getv('dlname','chident','snident','snmodel',
                            'dlsensor.time','dlsensor.endtime')

                snet,sta = name.split('_',1)
                time = parse_time(time)
                endtime = parse_time(endtime)

                debug( 'get_sensor %s_%s' % ( snet, sta ) )

                self._verify_cache(snet,sta,'sensor')

                try:
                    len(self.cache[snet][sta]['sensor'][chident][snmodel][snident])
                except:
                    self.cache[snet][sta]['sensor'][chident][snmodel][snident] = []

                self.cache[snet][sta]['sensor'][chident][snmodel][snident].append(
                        { 'time':time, 'endtime':endtime} )


    def _get_stabaler(self):

        debug( "_get_stabaler()")

        steps = [ 'dbopen stabaler']

        debug( ', '.join(steps) )

        #steps.extend(['dbsort dlsta time'])

        fields = ['model','nreg24','nreboot','firm','ssident']

        with datascope.freeing(self.db.process( steps )) as dbview:
            if not dbview.record_count:
                warning( 'No records after stabler join %s' % \
                        dbview.query(datascope.dbDATABASE_NAME) )
                return

            for temp in dbview.iter_record():
                snet = temp.getv('net')[0]
                sta = temp.getv('sta')[0]
                time = int(temp.getv('time')[0])
                touple = dict( zip(fields, temp.getv(*fields)) )

                self._verify_cache(snet,sta,'baler')
                self._verify_cache(snet,sta,'baler_ssident')
                self._verify_cache(snet,sta,'baler_firm')
                self._verify_cache(snet,sta)

                debug('baler(%s_%s)' % (snet,sta) )

                try:
                    self.cache[snet][sta]['baler'][time] = touple
                    self.cache[snet][sta]['baler_ssident'] = touple['ssident']
                    self.cache[snet][sta]['baler_firm'] = touple['firm']

                except Exception,e:
                    warning( "Cannot complete stabaler table for %s %s => %s" % (snet,sta,e) )

    def _get_calib_vals(self):

        debug( "_get_calib_vals()")

        #steps = [ 'dbopen calibration', 'dbjoin -o snetsta', 'dbsort snet sta chan time']
        steps = [ 'dbopen calibration', 'dbjoin -o snetsta']

        debug( ', '.join(steps) )

        fields = ['time','endtime','snname','samprate','segtype','calib','units']

        with datascope.freeing(self.db.process( steps )) as dbview:
            if not dbview.record_count:
                warning( 'No records after calibration join %s' % \
                        dbview.query(datascope.dbDATABASE_NAME) )
                return

            for temp in dbview.iter_record():
                #snet,sta = temp.getv('dlsta')[0].split('_',1)
                snet = temp.getv('snet')[0]
                sta = temp.getv('sta')[0]
                chan = temp.getv('chan')[0]
                touple = dict( zip(fields, temp.getv(*fields)) )

                debug( "%s_%s to calib" % (snet,sta))

                touple['time'] = parse_time( touple['time'] )
                touple['endtime'] = parse_time( touple['endtime'] )

                self._verify_cache(snet,sta,'calib')

                try:
                    if not len(self.cache[snet][sta]['calib'][chan]): raise
                except:
                    self.cache[snet][sta]['calib'][chan] = [ touple ]
                else:
                    self.cache[snet][sta]['calib'][chan].append( touple )


    def _get_comm(self):

        debug( "_get_comm()")

        steps = [ 'dbopen comm']
        steps = [ 'dbopen comm', 'dbjoin -o snetsta']

        debug( ', '.join(steps) )

        #steps.extend(['dbsort sta time'])

        fields = ['time','endtime','commtype','provider']

        with datascope.freeing(self.db.process( steps )) as dbview:
            if not dbview.record_count:
                warning( 'No records in %s after comm join' % \
                        dbview.query(datascope.dbDATABASE_NAME) )
                return

            for temp in dbview.iter_record():
                snet = temp.getv('snet')[0]
                sta = temp.getv('sta')[0]
                results = dict( zip(fields, temp.getv(*fields)) )
                results['time'] = parse_time(results['time'])
                results['endtime'] = parse_time(results['endtime'])

                self._verify_cache(snet,sta,'comm')
                debug('comm(%s_%s)' % (snet,sta) )

                try:
                    if not len(self.cache[snet][sta]['comm']): raise
                except:
                    self.cache[snet][sta]['comm'] = [ results ]
                else:
                    self.cache[snet][sta]['comm'].append( results )



    def _get_dlsite(self):

        debug( "_get_dlsite()" )

        steps = [ 'dbopen dlsite']

        #steps.extend(['dbsort ssident time'])

        debug( ', '.join(steps) )

        fields = ['model','time','endtime','idtag']

        with datascope.freeing(self.db.process( steps )) as dbview:
            if not dbview.record_count:
                debug( 'No records in after dlsite join %s' %
                        dbview.query(datascope.dbDATABASE_NAME) )
                return

            for temp in dbview.iter_record():

                snet,sta = temp.getv('dlname')[0].split('_',1)
                ssident = temp.getv('ssident')[0]

                dl = dict( zip(fields, temp.getv(*fields)) )

                dl['time'] = parse_time( dl['time'] )
                dl['endtime'] = parse_time( dl['endtime'] )

                debug( "_get_dlsite(%s_%s)" % (snet,sta) )
                self._verify_cache(snet,sta,'datalogger')

                self.cache[snet][sta]['datalogger'][ssident] = dl


    def _get_deployment_list(self):

        steps = [ 'dbopen deployment', 'dbjoin -o site']

        if self.db_subset:
            steps.extend(["dbsubset %s" % self.db_subset])

        debug( ', '.join(steps) )

        with datascope.freeing(self.db.process( steps )) as dbview:
            if not dbview.record_count:
                warning( 'No records after deployment-site join %s' % \
                        dbview.query(datascope.dbDATABASE_NAME) )
                return

            for temp in dbview.iter_record():

                fields = ['vnet','snet','sta','time','endtime','equip_install',
                    'equip_remove', 'cert_time','decert_time','pdcc',
                    'lat','lon','elev','staname','statype']

                db_v = dict( zip(fields, temp.getv(*fields)) )

                sta = db_v['sta']
                snet = db_v['snet']

                debug( "_get_deployment_list(%s_%s)" % (snet,sta) )

                # fix values of time
                for f in ['time', 'endtime', 'equip_install','equip_remove','cert_time','decert_time']:
                    db_v[f] = parse_time( db_v[f] )

                try:
                    db_v['strtime'] = stock.epoch2str(db_v['time'],
                            self.timeformat, self.timezone)
                except:
                    db_v['strtime'] = '-'

                try:
                    db_v['strendtime'] = stock.epoch2str(db_v['endtime'],
                            self.timeformat, self.timezone)
                except:
                    db_v['strendtime'] = '-'

                # Need lat and lon with 2 decimals only
                db_v['latlat'] = db_v['lat']
                db_v['lonlon'] = db_v['lon']
                db_v['lat'] = round(db_v['lat'],2)
                db_v['lon'] = round(db_v['lon'],2)


                self._verify_cache(snet,sta)

                self.cache[snet][sta] = db_v


    def _init_db(self):
        # Check DATABASE

        try:
            for table in self.tables:

                tablepath = test_table(self.database,table)
                if not tablepath:
                    error('Empty or missing %s.%s' % (self.database,table) )

                self.dbs_tables[table] = { 'path':tablepath, 'md5':False }

        except Exception,e:
            raise sta2jsonException( 'Problems on configured dbs: %s' % e )

    def _get_sta_cache(self):
        """
        Private function to load the data from the tables
        """
        need_update = False
        debug( "Stations._get_sta_cache(%s)" % (self.database) )

        if not self.db:
            self.db = datascope.dbopen( self.database , 'r' )
            debug( "init DB: %s" % (self.database) )

        for name in self.tables:

            md5 = self.dbs_tables[name]['md5']
            test = get_md5(self.dbs_tables[name]['path'])

            debug('(%s) table:%s md5:[old: %s new: %s]' % \
                        (self.database,name,md5,test) )

            if test != md5:
                notify('Update needed. Change in %s table' % name)
                self.dbs_tables[name]['md5'] = test
                need_update = True

        if need_update:
            self.cache = {}
            try:
                self._get_deployment_list()
                if self.sensor:      self._get_sensor()
                if self.comm:        self._get_comm()
                if self.dataloggers: self._get_dlsite()
                if self.balers:      self._get_stabaler()
                if self.calib_vals:  self._get_calib_vals()
            except Exception,e:
                warning('Exception %s' % e)
                self.db = False
                return False

        return True

    def _dump_cache(self):

        currCollection = self.mongo_db["metadata"]
        for entry in flatten_cache( self.cache ):
            # Convert to JSON then back to dict to stringify numeric keys
            entry = json.loads( json.dumps( entry ) )

            currCollection.update({'_id': entry['dlname']}, {'$set':entry}, upsert=True)
        index_db(currCollection, self.db_mongo_index)
