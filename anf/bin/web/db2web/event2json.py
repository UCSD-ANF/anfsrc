from __main__ import *

class Events():

    def __init__(self, pfname):
        """
        Load class and get the data
        """
        self.dbs = {}
        self.pf_keys = {
                'verbose':{'type':'bool','default':False},
                'timeformat':{'type':'str','default':'%d (%j) %h:%m:%s %z'},
                'timezone':{'type':'str','default':'utc'},
                'time_limit':{'type':'int','default':7776000},
                'refresh':{'type':'int','default':60},
                'databases':{'type':'dict','default':{}},
                'mongo_host':{'type':'str','default':None},
                'mongo_namespace':{'type':'str','default':'anf'},
                'mongo_user':{'type':'str','default':None},
                'mongo_password':{'type':'str','default':None},
                }

        self._read_pf(pfname)

        try:
            notify( "Events(): mongo instance = %s" % self.mongo_host )
            notify( "Events(): mongo namespace = %s" % self.mongo_namespace )
            self.mongo_instance = MongoClient(self.mongo_host)
            #self.mongo_db_instance = self.mongo_instance[self.mongo_namespace]
            #self.mongo_db_instance.authenticate(self.mongo_user, self.mongo_password)
        except Exception,e:
            sys.exit("Problem with MongoDB Configuration. %s(%s)\n" % (Exception,e) )

        self.event_cache = {}

        self.loading = True

        notify( "Events(): init()" )

        debug( '\t' + '#'*20 )
        debug( '\tLoading Events!' )
        debug( '\t' + '#'*20 )

        for name,path in self.databases.iteritems():
            debug( "Test %s db: %s" % (name,path) )

            for table in ['event','origin','netmag']:
                present = test_table(path,table)
                if not present:
                    error('Empty or missing %s.%s' % (path,table) )

                if table is 'event': event = present
                if table is 'origin': origin = present
                if table is 'netmag': netmag = present

            if not origin:
                error( 'Cannot work without origin table.')
                continue

            #db = datascope.dbopen( path , 'r' )
            self.dbs[name] = { 'db':path, 'path':path, 'mags':{},
                    'md5event':False, 'md5origin':False, 'md5netmag':False,
                    'origin': origin, 'event':event, 'netmag':netmag }

        self._get_event_cache()
        self._dump_cache()


    def _read_pf(self, pfname):
        """
        Read configuration parameters from rtwebserver pf file.
        """

        log( 'Read parameters from pf file: ' + pfname)

        pf = stock.pfread(pfname)

        for attr in self.pf_keys:
            setattr(self, attr, pf.get(attr))
            log( "%s: read_pf[%s]: %s" % (pfname, attr, getattr(self,attr) ) )

    def _cache(self, db=False):
        """
        Return cached data.
        """
        temp = []

        try:
            if db in self.event_cache:
                return self.event_cache[db]
            else:
                return json.dumps({'valid_db': self.event_cache.keys(),
                    'error':'No ?db=*** spefied in URL.'})

        except Exception,e:
            error('Cannot find self.table(%s) => %s' % (db,e) )
            return False

    def _get_magnitudes(self,db):

        mags = {}

        debug('Get magnitudes ' )

        steps = ['dbopen netmag', 'dbsubset orid!=NULL']

        if self.time_limit:
            steps.extend(["dbsubset lddate > %d" % (stock.now() - float(self.time_limit))] )

        with datascope.freeing(db.process( steps )) as dbview:

            debug('Got %s mags from file' % dbview.record_count )

            for record in dbview.iter_record():

                [orid, magid, magnitude, magtype,
                    auth, uncertainty, lddate ] = \
                    record.getv('orid', 'magid', 'magnitude',
                    'magtype', 'auth','uncertainty', 'lddate')

                try:
                    printmag = '%0.1f %s' % ( float(magnitude), magtype )
                except:
                    printmag = '-'

                if not orid in mags:
                    mags[orid] = {}

                mags[orid][magid] = {'magnitude':magnitude, 'printmag':printmag,
                        'lddate':lddate, 'magtype':magtype, 'auth':auth,
                        'uncertainty':uncertainty, 'magid':magid }

        return mags



    def dump(self):
        self._get_event_cache(True)
        self._dump_cache()

    def _get_event_cache(self, forced=False):
        """
        Private function to load the data from the tables
        """

        tempcache = {}

        for name in self.dbs:

            path = self.dbs[name]['path']
            mags = self.dbs[name]['mags']
            path = self.dbs[name]['db']

            with datascope.closing(datascope.dbopen( path , 'r' )) as db:

                origin = self.dbs[name]['origin']
                md5origin = self.dbs[name]['md5origin']

                event = self.dbs[name]['event']
                md5event = self.dbs[name]['md5event']

                netmag = self.dbs[name]['netmag']
                md5netmag = self.dbs[name]['md5netmag']

                debug( "Events(%s): db: %s" % (name,path) )


                testorigin =get_md5(origin)
                testevent = get_md5(event) if event else False
                testnetmag = get_md5(netmag) if netmag else False


                debug('event [old: %s new: %s]' %(md5event,testevent) )
                debug('origin [old: %s new: %s]' %(md5origin,testorigin) )
                debug('netmag [old: %s new: %s]' %(md5netmag,testnetmag) )

                if not forced:
                    if testorigin == md5origin and testevent == md5event and testnetmag == md5netmag:
                        debug('No update needed. Skipping.')
                        continue

                tempcache[name] = []

                self.dbs[name]['md5event'] = testevent
                self.dbs[name]['md5origin'] = testorigin

                if testnetmag != netmag:
                    mags = self._get_magnitudes(db)
                    self.dbs[name]['mags'] = mags
                    self.dbs[name]['md5netmag'] = testnetmag

                if event:
                    steps = ['dbopen event']
                    steps.extend(['dbjoin origin'])
                    steps.extend(['dbsubset orid!=NULL'])
                    steps.extend(['dbsubset orid==prefor'])
                else:
                    steps = ['dbopen origin']

                if self.time_limit:
                    steps.extend(["dbsubset time > %d" % (stock.now() - float(self.time_limit))] )


                steps.extend(['dbsort -r time'])

                if self.verbose:
                    debug( 'Events(%s): updating from %s' % (name,path) )

                debug( ', '.join(steps) )


                with datascope.freeing(db.process( steps )) as dbview:

                    if not dbview.record_count:
                        error( 'Events(%s): No records %s' % (name,path) )
                        continue

                    for temp in dbview.iter_record():

                        (orid,time,lat,lon,depth,auth,nass,ndef,review) = \
                                temp.getv('orid','time','lat','lon','depth',
                                        'auth','nass','ndef','review')

                        evid = orid
                        if event:
                            evid = temp.getv('evid')[0]


                        debug( "Events(%s): new evid #%s" % (name,evid) )

                        allmags = []
                        magnitude = '-'
                        maglddate = 0
                        strtime = stock.epoch2str(time, self.timeformat, self.timezone)
                        try:
                            srname = stock.srname(lat,lon)
                            grname = stock.grname(lat,lon)
                        except Exception,e:
                            error = 'Problems with (s/g)rname for orid %s: %s' % (orid,lat,lon,e) 
                            warning(error)
                            srname = '-'
                            grname = '-'

                        if orid in mags:
                            for o in mags[orid]:
                                allmags.append(mags[orid][o])
                                if mags[orid][o]['lddate'] > maglddate:
                                    magnitude = mags[orid][o]['printmag']
                                    maglddate = mags[orid][o]['lddate']


                        tempcache[name].append({'time':time, 'lat':lat, 'srname':srname,
                                'evid':evid, 'orid':orid, 'lon':lon, 'magnitude':magnitude,
                                'grname': grname, 'review': review, 'strtime':strtime,
                                'allmags': allmags, 'depth':depth, 'auth':auth,
                                'ndef': ndef, 'nass':nass})

                        debug( "Events(): %s add (%s,%s)" % (name,evid,orid) )

                self.event_cache[name] = tempcache[name]
                debug( "Completed updating db. (%s)" % name )


    def _dump_cache(self):
        if not hasattr(self, 'event_cache'):
            error('No event cache loaded, cannot dump to MongoDB.')
            return;

        notify( 'dump_cache()' )
        # USArray, CEUSN, etc.
        for project in self.event_cache:
            notify( 'dump to %s' % project )

            collection = self.mongo_instance[project]['events']

            # Clear old entries
            #collection.remove()

            # Don't flush but set expiration instead
            collection.ensure_index( "time_obj", expireAfterSeconds= self.time_limit )

            # TEST ON AUTO DELETE AFTER 1 DAY
            #collection.ensure_index( "time_obj", expireAfterSeconds= 86400 )


            # Each individual event entry
            for entry in self.event_cache[project]:

                # Convert to JSON then back to dict to stringify numeric keys
                entry = json.loads( json.dumps( entry ) )

                # add entry for autoflush index
                entry['time_obj'] = datetime.fromtimestamp( entry['time'] )

                collection.find_one_and_replace({'_id': entry['evid']}, entry, upsert=True)
