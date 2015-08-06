from __main__ import *


class Dlevent():
    def __init__(self, pf, clean=False):
        """
        Load class and get the data from dlevent table to MongoDB
        """

        notify( "Dlevent(): init()" )

        self.db = False
        self.cache = {}

        self.tables = ['deployment','dlevent']
        self.dbs_tables = {}

        # not implementing type for now.
        self.pf_keys = {
                'timezone':{'type':'str','default':'utc'},
                'db_subset':{'type':'str','default':False},
                'database':{'type':'str','default':False},
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
                self.mongo_db.drop_collection("dlevent")

        except Exception,e:
            sys.exit("Problem with MongoDB Configuration. %s(%s)\n" % (Exception,e) )

        # Check DBs
        self._init_db()


    def _verify_cache(self,snet,sta):
        if not snet in self.cache:
            self.cache[snet] = {}

        if not sta in self.cache[snet]:
            self.cache[snet][sta] = {}

        if not 'dlevent' in self.cache[snet][sta]:
            self.cache[snet][sta]['dlevent'] = defaultdict(lambda: defaultdict(defaultdict))

    def dump(self):
        """
        Call this method 'dump' from parent to trigger an update
        to the MongoDB instance.
        """
        if self._get_sta_cache():
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


    def _get_dlevents(self):

        debug( "_get_dlevents()")

        steps = [ 'dbopen dlevent']

        debug( ', '.join(steps) )

        fields = ['dlevtype','dlcomment','time']

        with datascope.freeing(self.db.process( steps )) as dbview:
            if not dbview.record_count:
                warning( 'No records in %s ' % \
                        dbview.query(datascope.dbDATABASE_NAME) )
                return

            for temp in dbview.iter_record():
                snet,sta = temp.getv('dlname')[0].split('_',1)

                results = dict( zip(fields, temp.getv(*fields)) )

                year = stock.epoch2str(results['time'], '%Y', 'UTC')
                month = stock.epoch2str(results['time'], '%L', 'UTC')

                self._verify_cache(snet,sta)

                debug('dlevent(%s_%s)' % (snet,sta) )

                try:
                    if not len(self.cache[snet][sta]['dlevent'][year][month]): raise
                except:
                    self.cache[snet][sta]['dlevent'][year][month] = [ results ]
                else:
                    self.cache[snet][sta]['dlevent'][year][month].append( results )



    def _get_deployment_list(self):

        steps = [ 'dbopen deployment', 'dbjoin -o site']

        if self.db_subset:
            steps.extend(["dbsubset %s" % self.db_subset])

        steps.extend(['dbsort snet sta'])

        debug( ', '.join(steps) )

        with datascope.freeing(self.db.process( steps )) as dbview:
            if not dbview.record_count:
                warning( 'No records after deployment-site join %s' % \
                        dbview.query(datascope.dbDATABASE_NAME) )
                return

            for temp in dbview.iter_record():

                fields = ['vnet','snet','sta','time','endtime','staname']

                db_v = dict( zip(fields, temp.getv(*fields)) )

                sta = db_v['sta']
                snet = db_v['snet']

                debug( "_get_deployment_list(%s_%s)" % (snet,sta) )

                # fix values of time
                for f in ['time', 'endtime']:
                    db_v[f] = parse_time( db_v[f] )


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
        debug( "Dlevent._get_sta_cache(%s)" % (self.database) )


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
                self._get_dlevents()
            except Exception,e:
                warning('Exception %s' % e)
                self.db = False
                return False

            debug( "Completed updating db. (%s)" % self.database )
            return True
        else:
            return False

    def _dump_cache(self):

        currCollection = self.mongo_db["dlevent"]
        for entry in flatten_cache( self.cache ):
            # Convert to JSON then back to dict to stringify numeric keys
            entry = json.loads( json.dumps( entry ) )

            currCollection.update({'_id': entry['dlname']}, {'$set':entry}, upsert=True)

        index_db(currCollection, self.db_mongo_index)
