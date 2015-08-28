class DleventException(Exception):
    """
    Local class to raise Exceptions to the
    rtwebserver framework.
    """
    def __init__(self, message):
        super(dleventException, self).__init__(message)
        self.message = message


try:
    import inspect
    import sys
    import json
    from datetime import datetime, timedelta
    from collections import defaultdict
except Exception, e:
    raise dleventException("Problems importing libraries.%s %s" % (Exception, e))

try:
    import antelope.datascope as datascope
    import antelope.orb as orb
    import antelope.Pkt as Pkt
    import antelope.stock as stock
except Exception, e:
    raise dleventException("Problems loading ANTELOPE libraries. %s(%s)" % (Exception, e))


try:
    from db2mongo.logging_class import getLogger
except Exception, e:
    raise dleventException("Problem loading logging_class. %s(%s)" % (Exception, e))

try:
    from db2mongo.db2mongo_libs import *
except Exception, e:
    raise dleventException("Problem loading db2mongo_libs.py file. %s(%s)" % (Exception, e))




class Dlevent():
    def __init__(self, db=False, subset=False):
        """
        Load class and get the data from dlevent table to MongoDB
        Class to query a Datascope dlevent database and cache
        values in memory.

        Usage:
            dlevent = Dlevent(db,subset=False)

            dlevent.validate()

            while True:
                if dlevent.need_update():
                    dlevent.update()
                    data,error = dlevent.data()
                sleep(time)

        """

        self.logging = getLogger(self.__class__.__name__)

        self.logging.debug( "Dlevent.init()" )

        self.db = False
        self.database = db
        self.db_subset = subset
        self.cache = []
        self.error_cache = []

        self.tables = ['dlevent']
        self.dbs_tables = {}


    def data(self,refresh=False):
        """
        Export all values stored in memory.
        """

        if refresh: self.update()

        return (self._clean_cache(self.cache), self._clean_cache(self.error_cache))


    def need_update(self):
        """
        Verify if the md5 checksum changed on any table
        """
        self.logging.debug( "need_update()" )

        for name in self.tables:

            md5 = self.dbs_tables[name]['md5']
            test = get_md5(self.dbs_tables[name]['path'])

            self.logging.debug('(%s) table:%s md5:[old: %s new: %s]' % \
                        (self.database,name,md5,test) )

            if test != md5: return True

        return False

    def update(self):
        """
        function to update the data from the tables
        """
        if not self.db: self.validate()

        self.logging.debug( "refresh(%s)" % (self.db) )

        for name in self.tables:
            self.dbs_tables[name]['md5'] = get_md5( self.dbs_tables[name]['path'] )

        self._get_dlevents()


    def validate(self):
        self.logging.debug( 'validate()' )

        if self.db: return True

        # Vefiry database files
        if self.database:
            if verify_db(self.database):
                self.db = self.database
            else:
                raise dleventException("Not a vaild database: %s" % (self.database))
        else:
            raise dleventtException("Missing value for database" )

        # Verify tables
        for table in self.tables:
            path = test_table(self.db,table)
            if not path:
                raise dleventException("Empty or missing: %s %s" % (self.db, table))

            self.dbs_tables[table] = { 'path':path, 'md5':False }
            self.logging.debug( 'run validate(%s) => %s' % (table, path) )

        return True


    def _get_dlevents(self):

        self.logging.debug( "_get_dlevents()")
        self.cache = []
        self.error_cache = []

        steps = [ 'dbopen dlevent']

        fields = ['dlname','dlevtype','dlcomment','time']

        for v in extract_from_db(self.db, steps, fields, self.db_subset):

            self.logging.debug('dlevent(%s)' % (v['dlname']) )
            snet,sta = v['dlname'].split('_',1)
            v['snet'] = snet
            v['sta'] = sta

            v['year'] = stock.epoch2str(v['time'], '%Y', 'UTC')
            v['month'] = stock.epoch2str(v['time'], '%L', 'UTC')

            self.cache.append( v )


    def _clean_cache(self, cache):

        results = []

        for entry in cache:
            if not 'dlname' in entry: continue

            # Convert to JSON then back to dict to stringify numeric keys
            entry = json.loads( json.dumps( entry ) )

            # Generic id for this entry
            entry['id'] = len(results)

            # add entry for autoflush index
            entry['time_obj'] = datetime.fromtimestamp( entry['time'] )

            # add entry for last load of entry
            entry['lddate'] = datetime.fromtimestamp( stock.now() )

            results.append( entry )

        return results
