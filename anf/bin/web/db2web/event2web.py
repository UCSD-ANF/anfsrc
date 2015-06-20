from __main__ import *

class Events():

    def __init__(self, pfname, clean=False):
        """
        Load class and get the data
        """
        self.db = False
        self.cache = []
        self.mags = {}

        self.tables = ['event','origin','netmag']
        self.dbs_tables = {}

        self.pf_keys = {
                'timeformat':{'type':'str','default':'%d (%j) %h:%m:%s %z'},
                'timezone':{'type':'str','default':'utc'},
                'event_database':{'type':'str','default':None},
                'event_mongo_index':{'type':'dict','default':None},
                'mongo_host':{'type':'str','default':None},
                'mongo_namespace':{'type':'str','default':'anf'},
                'mongo_user':{'type':'str','default':None},
                'mongo_password':{'type':'str','default':None},
                }

        self._read_pf(pfname)

        try:
            self.mongo_instance = MongoClient(self.mongo_host)
            self.mongo_db = self.mongo_instance.get_database( self.mongo_namespace )
            self.mongo_db.authenticate(self.mongo_user, self.mongo_password)
            if clean:
                self.mongo_db.drop_collection("events")

        except Exception,e:
            sys.exit("Problem with MongoDB Configuration. %s(%s)\n" % (Exception,e) )


        self._init_db()

    def dump(self):
        self._get_event_cache()
        self._dump_cache()


    def _init_db(self):

        try:
            for table in self.tables:

                tablepath = test_table(self.event_database,table)
                if not tablepath:
                    error('Empty or missing %s.%s' % (self.event_database,table) )

                self.dbs_tables[table] = { 'path':tablepath, 'md5':False }

        except Exception,e:
            raise sta2jsonException( 'Problems on configured dbs: %s' % e ) 


    def _read_pf(self, pfname):
        """
        Read configuration parameters from rtwebserver pf file.
        """

        log( 'Read parameters from pf file: ' + pfname)

        pf = stock.pfread(pfname)

        for attr in self.pf_keys:
            setattr(self, attr, pf.get(attr))
            log( "%s: read_pf[%s]: %s" % (pfname, attr, getattr(self,attr) ) )


    def _get_magnitudes(self):

        debug('Get magnitudes ' )

        self.mags = {}

        steps = ['dbopen netmag', 'dbsubset orid!=NULL']

        with datascope.freeing(self.db.process( steps )) as dbview:

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

                if not orid in self.mags:
                    self.mags[orid] = {}

                self.mags[orid][magid] = {'magnitude':magnitude, 'printmag':printmag,
                        'lddate':lddate, 'magtype':magtype, 'auth':auth,
                        'uncertainty':uncertainty, 'magid':magid }



    def _get_event_cache(self):
        """
        Private function to load the data from the tables
        """
        need_update = False
        debug( "Events._get_event_cache(%s)" % (self.event_database) )


        if not self.db:
            self.db = datascope.dbopen( self.event_database , 'r' )
            debug( "init DB: %s" % (self.event_database) )

        for name in self.tables:

            md5 = self.dbs_tables[name]['md5']
            test = get_md5(self.dbs_tables[name]['path'])

            debug('(%s) table:%s md5:[old: %s new: %s]' % \
                        (self.event_database,name,md5,test) )

            if test != md5:
                notify('Update needed. Change in %s table' % name)
                self.dbs_tables[name]['md5'] = test
                need_update = True

        if need_update:
            self.cache = []
            self._get_events()

            debug( "Completed updating db. (%s)" % self.event_database )
            return True
        else:
            return False



    def _get_events(self):

            self._get_magnitudes()

            steps = ['dbopen event']
            steps.extend(['dbjoin origin'])
            steps.extend(['dbsubset orid!=NULL'])
            steps.extend(['dbsubset orid==prefor'])


            debug( ', '.join(steps) )


            with datascope.freeing(self.db.process( steps )) as dbview:

                if not dbview.record_count:
                    warning( 'Events(%s): No records %s' % (name,path) )
                    return

                for temp in dbview.iter_record():

                    (evid,orid,time,lat,lon,depth,auth,nass,ndef,review) = \
                            temp.getv('evid','orid','time','lat','lon','depth',
                                    'auth','nass','ndef','review')

                    debug( "Events(): new evid #%s" % evid )

                    allmags = []
                    magnitude = '-'
                    maglddate = 0
                    time = parse_time(time)
                    strtime = stock.epoch2str(time, self.timeformat, self.timezone)

                    try:
                        srname = stock.srname(lat,lon)
                        grname = stock.grname(lat,lon)
                    except Exception,e:
                        warninig('Problems with (s/g)rname for orid %s: %s' % (orid,lat,lon,e) )
                        srname = '-'
                        grname = '-'

                    if orid in self.mags:
                        for o in self.mags[orid]:
                            allmags.append(self.mags[orid][o])
                            if self.mags[orid][o]['lddate'] > maglddate:
                                magnitude = self.mags[orid][o]['printmag']
                                maglddate = self.mags[orid][o]['lddate']


                    self.cache.append({'time':time, 'lat':lat, 'srname':srname,
                            'evid':evid, 'orid':orid, 'lon':lon, 'magnitude':magnitude,
                            'grname': grname, 'review': review, 'strtime':strtime,
                            'allmags': allmags, 'depth':depth, 'auth':auth,
                            'ndef': ndef, 'nass':nass})

            debug( "Completed updating db." )


    def _dump_cache(self):

        currCollection = self.mongo_db["events"]
        for entry in self.cache:
            # Convert to JSON then back to dict to stringify numeric keys
            entry = json.loads( json.dumps( entry ) )

            currCollection.update({'_id': entry['evid']}, {'$set':entry}, upsert=True)

        index_db(currCollection, self.event_mongo_index)
