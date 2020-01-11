import json
from datetime import datetime
import antelope.datascope as datascope
import antelope.stock as stock
from db2mongo.logging_class import getLogger
from db2mongo.db2mongo_libs import parse_sta_time,\
                                   readable_time,\
                                   verify_db,\
                                   test_table,\
                                   get_md5,\
                                   extract_from_db,\
                                   warning

class eventException(Exception):
    """
    Local class to raise Exceptions to the
    rtwebserver framework.
    """
    def __init__(self, message):
        super(eventException, self).__init__(message)
        self.message = message



class Events():

    def __init__(self, db=False, subset=False):
        """
        Class to query a Datascope event database and cache
        them in memory. The origin table is the main source
        of information. The system will try to join with the
        event table if present. The netmag table will be imported
        into memory and used to expand the events.

        Usage:
            events = Events(db,subset=False)

            events.validate()

            while True:
                if events.need_update():
                    events.update()
                    data,error = events.data()
                sleep(time)

        """
        self.logging = getLogger(self.__class__.__name__)

        self.logging.debug( "Events.init()" )

        self.db = False
        self.database = False
        self.db_subset = False
        self.cache = []
        self.cache_error = []
        self.mags = {}

        # event table is not tested here.
        self.tables = ['origin','netmag']
        self.dbs_tables = {}

        self.timeformat = False
        self.timezone = False

    def validate(self):
        self.logging.debug( 'validate()' )

        if self.db: return True

        # Vefiry database files
        if self.database:
            if verify_db(self.database):
                self.db = self.database
            else:
                raise eventException("Not a vaild database: %s" % (self.database))
        else:
            raise eventException("Missing value for database" )

        # Verify tables
        for table in self.tables:
            path = test_table(self.db,table)
            if not path:
                raise eventException("Empty or missing: %s %s" % (self.db, table))

            self.dbs_tables[table] = { 'path':path, 'md5':False }
            self.logging.debug( 'run validate(%s) => %s' % (table, path) )

        return True


    def need_update(self):
        """
        Verify if the md5 checksum changed on any table
        """
        self.logging.debug( "need_update()" )

        for name in self.tables:

            md5 = self.dbs_tables[name]['md5']
            test = get_md5(self.dbs_tables[name]['path'])

            self.logging.debug('(%s) table:%s md5:[old: %s new: %s]' % \
                        (self.db,name,md5,test) )

            if test != md5: return True

        return False

    def update(self):
        """
        function to update the data from the tables
        """

        if not self.db: self.validate()

        self.logging.debug( "update(%s)" % (self.db) )

        for name in self.tables:
            self.dbs_tables[name]['md5'] = get_md5( self.dbs_tables[name]['path'] )

        self._get_magnitudes()
        self._get_events()

    def data(self, refresh=False):
        """
        function to export the data from the tables
            refresh:    Maybe we want to force an update to the cache.
                        This is False by default.
        """
        self.logging.debug( "data(%s)" % (self.db) )

        if not self.db: self.validate()

        if refresh: self.update()

        return (self._clean_cache(self.cache), self._clean_cache(self.cache_error))


    def _get_magnitudes(self):
        """
        Get all mags from the database into memory
        """

        self.logging.debug('Get magnitudes ' )

        self.mags = {}

        steps = ['dbopen netmag', 'dbsubset orid != NULL']

        fields = ['orid', 'magid', 'magnitude', 'magtype',
                'auth', 'uncertainty', 'lddate']

        for v in extract_from_db(self.db, steps, fields):
            orid = v.pop('orid')
            self.logging.debug('new mag for orid:%s' % orid)

            try:
                v['strmag'] = '%0.1f %s' % ( float(v['magnitude']), v['magtype'] )
            except:
                v['strmag'] = '-'

            if not orid in self.mags:
                self.mags[ orid ] = {}

            self.mags[ orid ][ v['magid'] ] = v


    def _get_events(self):
        """
        Read all orids/evids from the database and update
        local dict with the info.
        """
        self.cache = []

        # Test if we have event table
        with datascope.closing(datascope.dbopen(self.db, 'r')) as db:
            dbtable = db.lookup(table='event')
            if dbtable.query(datascope.dbTABLE_PRESENT):
                steps = ['dbopen event']
                steps.extend(['dbjoin origin'])
                steps.extend(['dbsubset origin.orid != NULL'])
                steps.extend(['dbsubset origin.orid == prefor'])
                fields = ['evid']
            else:
                steps = ['dbopen origin']
                steps.extend(['dbsubset orid != NULL'])
                fields = []

        fields.extend(['orid','time','lat','lon','depth','auth','nass',
                'ndef','review'])

        for v in extract_from_db(self.db, steps, fields, self.db_subset):
            if not 'evid' in v:
                v['evid'] = v['orid']

            self.logging.debug( "Events(): new event #%s" % v['evid'] )

            v['allmags'] = []
            v['magnitude'] = '-'
            v['maglddate'] = 0
            v['srname'] = '-'
            v['grname'] = '-'
            v['time'] = parse_sta_time(v['time'])
            v['strtime'] = readable_time(v['time'], self.timeformat, self.timezone)

            try:
                v['srname'] = stock.srname(v['lat'],v['lon'])
            except Exception as e:
                warning('Problems with srname for orid %s: %s' % (v['orid'],
                        v['lat'],v['lon'],e) )

            try:
                v['grname'] = stock.grname(v['lat'],v['lon'])
            except Exception as e:
                warning('Problems with grname for orid %s: %s' % (v['orid'],
                        v['lat'], v['lon'],e) )

            orid = v['orid']
            if orid in self.mags:
                for o in self.mags[orid]:
                    v['allmags'].append(self.mags[orid][o])
                    if self.mags[orid][o]['lddate'] > v['maglddate']:
                        v['magnitude'] = self.mags[orid][o]['strmag']
                        v['maglddate'] = self.mags[orid][o]['lddate']


            self.cache.append( v )


    def _clean_cache(self, cache):

        results = []

        for entry in cache:
            # Convert to JSON then back to dict to stringify numeric keys
            entry = json.loads( json.dumps( entry ) )

            # Generic id for this entry
            entry['id'] = entry['evid']

            # add entry for autoflush index
            entry['time_obj'] = datetime.fromtimestamp( entry['time'] )

            # add entry for last load of entry
            entry['lddate'] = datetime.fromtimestamp( stock.now() )

            results.append( entry )

        return results
