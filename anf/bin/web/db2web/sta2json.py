from __main__ import *


class Stations():
    def __init__(self, pf):
        """
        Load class and get the data
        """

        notify( "Stations(): init()" )

        self.loading = True

        self.dbs = {}
        self.orbs = {}

        self.db_cache = {}

        self.tables = ['deployment','site','comm','sensor','dlsensor','dlsite']

        self.pf_keys = {
                'verbose':{'type':'bool','default':False},
                # 'timeformat':{'type':'str','default':'%d (%j) %h:%m:%s %z'},
                'timezone':{'type':'str','default':'utc'},
                'sta_subset':{'type':'str','default':False},
                'refresh':{'type':'int','default':60},
                'databases':{'type':'dict','default':{}},
                'orbnames':{'type':'dict','default':{}},
                'readableJSON':{'type':'int','default':None},
                'mongo_host':{'type':'str','default':None},
                'mongo_namespace':{'type':'str','default':'admin'},
                'mongo_user':{'type':'str','default':None},
                'mongo_password':{'type':'str','default':None},
                }

        self.verbose = False
        self._read_pf(pf)

        try:
            self.mongo_instance = MongoClient(self.mongo_host)
            self.mongo_db_instance = self.mongo_instance[self.mongo_namespace]
            self.mongo_db_instance.authenticate(self.mongo_user, self.mongo_password)
        except Exception,e:
            sys.exit("Problem with MongoDB Configuration. %s(%s)\n" % (Exception,e) )

        # if not self.refresh:
        self.refresh = 60 # every minute default

        # Check DBs
        self.get_all_sta_cache()

        # Check ORBS
        self.get_all_orb_cache()

        self.loading = False


        notify( 'Done loading Stations()' )


    def _read_pf(self, pfname):
        """
        Read configuration parameters from rtwebserver pf file.
        """

        log( 'Read parameters from pf file')

        pf = stock.pfread(pfname)

        for attr in self.pf_keys:
            setattr(self, attr, pf.get(attr))
            log( "%s: read_pf[%s]: %s" % (pfname, attr, getattr(self,attr) ) )

    def get_all_orb_cache(self):
        for name,orbname in self.orbnames.iteritems():
            debug( "init %s ORB: %s" % (name,orbname) )

            self.orbs[name] = {}
            self.orbs[name]['clients'] = {}
            self.orbs[name]['sources'] = {}
            self.orbs[name]['info'] = {
                    'status':'offline',
                    'last_check':0,
                    'name':orbname
                    }

            self.orbs[name]['orb'] = orb.Orb(orbname)
            self._get_orb_cache(name)

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
                            net = pkt.srcname.net
                            sta = pkt.srcname.sta

                            del stash['srcname']

                            debug("orb(%s) update %s %s" % (name,net,sta) )

                            if not net in self.orbs[name]['sources']:
                                self.orbs[name]['sources'][net] = {}

                            if not sta in self.orbs[name]['sources'][net]:
                                self.orbs[name]['sources'][net][sta] = {}

                            self.orbs[name]['sources'][net][sta][srcname] = stash

                            m_station = self.mongo_instance[name]["metadata"].find_one({'id': net+'_'+sta})

                            if m_station:
                                if 'orb' not in m_station:
                                    log("Adding empty orb container to: "+name+":"+net+"_"+sta)
                                    oldOrb = {}
                                else:
                                    log(m_station['orb']) 
                                    oldOrb = m_station['orb']
                                oldOrb[srcname] = stash['slatest_time']
                                self.mongo_instance[name]["metadata"].update_one({
                                    'id': net+'_'+sta,
                                    'snet': net,
                                    'sta': sta
                                }, {'$set':{'orb':oldOrb}}, upsert=True)
            except Exception,e:
                error("Cannot query orb(%s) %s %s" % (name, Exception, e) )

        self.orbs[name]['orb'].close()

    def _get_sensor(self, db, tempcache):

        debug( "Stations(): dlsensor()")

        steps = [ 'dbopen dlsite', 'dbsort -u dlname ssident', 'dbjoin dlsensor ssident#dlident']

        debug( ', '.join(steps) )

        steps.extend(['dbsort dlname snmodel dlsite.time'])

        with datascope.freeing(db.process( steps )) as dbview:
            if not dbview.record_count:
                warning( 'No records in dlsensor join %s' % \
                        db.query(datascope.dbDATABASE_NAME) )
                return tempcache

            for temp in dbview.iter_record():
                (name,chident,snident,snmodel,time,endtime) = \
                    temp.getv('dlname','chident','snident','snmodel',
                            'dlsensor.time','dlsensor.endtime')

                snet,sta = name.split('_',1)
                time = int(time)
                endtime = int(endtime)

                status = find_status(tempcache,sta)
                if not status: continue

                try:
                    if not chident in tempcache[status][snet][sta]['sensor']:
                        tempcache[status][snet][sta]['sensor'][chident] = {}

                    if not snmodel in tempcache[status][snet][sta]['sensor'][chident]:
                        tempcache[status][snet][sta]['sensor'][chident][snmodel] = {}

                    if not snident in tempcache[status][snet][sta]['sensor'][chident][snmodel]:
                        tempcache[status][snet][sta]['sensor'][chident][snmodel][snident] = []

                    try:
                        if not len(tempcache[status][snet][sta]['sensor'][chident][snmodel][snident]): raise
                        original_list = []
                        for value in tempcache[status][snet][sta]['sensor'][chident][snmodel][snident]:

                            if value[0]-1 == endtime or value[0] == endtime:
                                value[0] = time
                                debug( "update(%s) " % (value) )

                            if value[1]+1 == time or value[1] == time:
                                value[1] = endtime
                                debug( "update(%s) " % (value) )

                            original_list.append(value)

                        tempcache[status][snet][sta]['sensor'][chident][snmodel][snident] = original_list

                    except Exception,e:
                        tempcache[status][snet][sta]['sensor'][chident][snmodel][snident].append( \
                                    [ time, endtime] )
                        debug( "push(%s %s) " % (time,endtime) )

                except Exception,e:
                    pass

        return tempcache


    def _get_stabaler(self, db, tempcache):

        debug( "_get_stabaler()")

        steps = [ 'dbopen stabaler']

        debug( ', '.join(steps) )

        steps.extend(['dbsort dlsta time'])

        fields = ['nreg24','nreboot','firm','ssident']

        with datascope.freeing(db.process( steps )) as dbview:
            if not dbview.record_count:
                warning( 'No records after stabler join %s' % \
                        db.query(datascope.dbDATABASE_NAME) )
                return tempcache

            for temp in dbview.iter_record():
                snet = temp.getv('net')[0]
                sta = temp.getv('sta')[0]
                time = int(temp.getv('time')[0])
                touple = dict( zip(fields, temp.getv(*fields)) )

                status = find_status(tempcache,sta)
                if not status: continue

                try:
                    tempcache[status][snet][sta]['baler'][time] = touple
                    tempcache[status][snet][sta]['baler_ssident'] = touple['ssident']
                    tempcache[status][snet][sta]['baler_firm'] = touple['firm']

                    debug("baler(%s):%s" % (sta,time) )
                except:
                    pass

        return tempcache


    def _get_comm(self, db, tempcache):

        debug( "_get_comm()")

        steps = [ 'dbopen comm']

        debug( ', '.join(steps) )

        steps.extend(['dbsort sta time'])

        fields = ['time','endtime','commtype','provider']

        with datascope.freeing(db.process( steps )) as dbview:
            if not dbview.record_count:
                warning( 'No records in %s after comm join' % \
                        db.query(datascope.dbDATABASE_NAME) )
                return tempcache

            for temp in dbview.iter_record():
                sta = temp.getv('sta')[0]

                results = dict( zip(fields, temp.getv(*fields)) )
                results['time'] = int(results['time'])
                results['endtime'] = int(results['endtime'])

                status = find_status(tempcache,sta)
                if not status: continue
                snet = find_snet(tempcache,sta)
                if not snet: continue


                tempcache[status][snet][sta]['comm'].append( results )

        return tempcache



    def _get_dlsite(self, db, tempcache):

        debug( "_get_dlsite()" )

        steps = [ 'dbopen dlsite']

        steps.extend(['dbsort ssident time'])

        debug( ', '.join(steps) )

        fields = ['model','time','endtime','idtag']

        with datascope.freeing(db.process( steps )) as dbview:
            if not dbview.record_count:
                debug( 'No records in after dlsite join %s' %
                        db.query(datascope.dbDATABASE_NAME) )
                return tempcache

            for temp in dbview.iter_record():

                snet,sta = temp.getv('dlname')[0].split('_',1)
                ssident = temp.getv('ssident')[0]

                dl = dict( zip(fields, temp.getv(*fields)) )

                status = find_status(tempcache,sta)
                if not status: continue

                try:
                    if ssident in tempcache[status][snet][sta]['datalogger']:
                        tempcache[status][snet][sta]['datalogger'][ssident]['endtime'] = \
                                dl['endtime']
                    else:
                        tempcache[status][snet][sta]['datalogger'][ssident] = dl

                    debug( "_get_dlsite(%s_%s)" % (snet,sta) )
                except Exception,e:
                    #debug("#### No deployment entry for %s_%s %s %s" % \
                    #        (snet,sta,Exception,e) )
                    pass


        return tempcache


    def _get_deployment_list(self,db):

        tempcache = { 'active':{}, 'decom':{}, 'list':{} }

        steps = [ 'dbopen deployment', 'dbjoin -o site']

        if self.sta_subset:
            steps.extend(["dbsubset %s" % self.sta_subset])

        steps.extend(['dbsort snet sta'])

        debug( ', '.join(steps) )

        with datascope.freeing(db.process( steps )) as dbview:
            if not dbview.record_count:
                warning( 'No records after deployment-site join %s' % \
                        db.query(datascope.dbDATABASE_NAME) )
                return tempcache

            for temp in dbview.iter_record():

                fields = ['vnet','snet','sta','time','endtime','equip_install',
                    'equip_remove', 'cert_time','decert_time','pdcc',
                    'lat','lon','elev','staname','statype']

                db_v = dict( zip(fields, temp.getv(*fields)) )

                sta = db_v['sta']
                snet = db_v['snet']

                debug( "_get_deployment_list(%s_%s)" % (snet,sta) )

                for k in db_v:
                    try:
                        if abs(int(db_v[k])) == 9999999999:
                            db_v[k] = '-'
                    except:
                        pass

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


                if not snet in tempcache['active']:
                    tempcache['decom'][snet] = {}
                    tempcache['active'][snet] = {}

                if not db_v['endtime'] is '-' and db_v['endtime'] < stock.now():
                    tempcache['decom'][snet][sta] = db_v
                    tempcache['decom'][snet][sta]['datalogger'] = {}
                    tempcache['decom'][snet][sta]['sensor'] = {}
                    tempcache['decom'][snet][sta]['baler'] = {}
                    tempcache['decom'][snet][sta]['comm'] = []
                else:
                    tempcache['active'][snet][sta] = db_v
                    tempcache['active'][snet][sta]['datalogger'] = {}
                    tempcache['active'][snet][sta]['sensor'] = {}
                    tempcache['active'][snet][sta]['baler'] = {}
                    tempcache['active'][snet][sta]['comm'] = []

        return tempcache

    def get_all_sta_cache(self):
        # Check DATABASES
        for name,path in self.databases.iteritems():
            try:
                self.dbs[name] = {}
                self.dbs[name] = { 'tables':{} }
                for table in self.tables:
                    present = test_table(path,table)
                    if not present:
                        raise sta2jsonException('Empty or missing %s.%s' % (path,table) )

                    self.dbs[name]['tables'][table] = { 'path':present, 'md5':False }
                db = datascope.dbopen( path , 'r' )
                self.dbs[name]['db'] = db
                self.dbs[name]['path'] = path
                debug( "init %s DB: %s" % (name,path) )

                self._get_sta_cache(name)
            except Exception,e:
                raise sta2jsonException( 'Problems on configured dbs: %s' % e )

    def _get_sta_cache(self,database):
        """
        Private function to load the data from the tables
        """
        tempcache = {}

        db = self.dbs[database]['db']
        dbpath = self.dbs[database]['path']
        need_update = False
        debug( "(%s) path:%s" % (database,dbpath) )

        for name in self.tables:

            path = self.dbs[database]['tables'][name]['path']
            md5 = self.dbs[database]['tables'][name]['md5']

            test = get_md5(path)

            debug('(%s) table:%s path:%s md5:[old: %s new: %s]' % \
                        (database,name,path,md5,test) )

            if test != md5:
                debug('Update needed.')
                self.dbs[database]['tables'][name]['md5'] = test
                need_update = True

        if need_update:
            tempcache[database] = self._get_deployment_list(db)
            tempcache[database] = self._get_dlsite(db, tempcache[database] )
            tempcache[database] = self._get_comm(db, tempcache[database] )
            tempcache[database] = self._get_sensor(db, tempcache[database] )
            tempcache[database] = self._get_stabaler(db, tempcache[database] )

            self.db_cache[database] = tempcache[database]

            debug( "Completed updating db. (%s)" % database )

    def flatten_cache(self, cache):
        newCache = []

        # Active, list, decom
        for category in cache:
            for snet in cache[category]:
                for sta in cache[category][snet]:
                    oldEntry = cache[category][snet][sta]
                    oldEntry['id'] = snet + '_' + sta
                    newCache.append(oldEntry)

        return newCache

    def dump_cache(self, to_mongo=False, to_json=False, jsonPath="default.json"):
        # USArray, CEUSN, etc.
        for db in self.db_cache:
            flatCache = self.flatten_cache(self.db_cache[db])

            if to_mongo:
                currCollection = self.mongo_instance[db]["metadata"]
                for entry in flatCache:
                    # Convert to JSON then back to dict to stringify numeric keys
                    jsonEntry = json.dumps(entry)
                    revertedEntry = json.loads(jsonEntry)
                    currCollection.update({'id': entry['id']}, {'$set':revertedEntry}, upsert=True)

            if to_json:
                with open(jsonPath, 'w') as outfile:
                    json.dump(flatCache, outfile)
