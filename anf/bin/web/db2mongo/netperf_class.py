class NetPerfException(Exception):
    """
    Local class to raise Exceptions to the
    rtwebserver framework.
    """
    def __init__(self, message):
        super(NetPerfException, self).__init__(message)
        self.message = message


try:
    import inspect
    import sys
    import json
    from datetime import datetime, timedelta
    from collections import defaultdict
except Exception, e:
    raise NetPerfException("Problems importing libraries.%s %s" % (Exception, e))

try:
    import antelope.datascope as datascope
    import antelope.stock as stock
except Exception, e:
    raise NetPerfException("Problems loading ANTELOPE libraries. %s(%s)" % (Exception, e))


try:
    from db2mongo.logging_class import getLogger
except Exception, e:
    raise NetPerfException("Problem loading logging_class. %s(%s)" % (Exception, e))

try:
    from db2mongo.db2mongo_libs import *
except Exception, e:
    raise NetPerfException("Problem loading db2mongo_libs.py file. %s(%s)" % (Exception, e))




class NetPerf():
    def __init__(self, db_list=[], subset=False):
        """
        Load class and get the data from netperf table to MongoDB

        Usage:
            netperf = NetPerf(db,subset=False)

            netperf.validate()

            while True:
                if netperf.need_update():
                    netperf.update()
                    data,error = netperf.data()
                sleep(time)

        """

        self.logging = getLogger(self.__class__.__name__)

        self.logging.debug( "Dlevent.init()" )

        self.db = {}
        self.database_list = db_list
        self.db_subset = subset
        self.cache = []
        self.error_cache = []

        self.tables = ['netperf']


    def data(self,refresh=False):
        """
        Export all values stored in memory.
        """

        if refresh: self.update()

        return (clean_cache_object(self.cache, 'id'),
                clean_cache_object(self.error_cache, 'id'))


    def need_update(self):
        """
        Verify if the md5 checksum changed on any table
        """
        self.logging.debug( "need_update()" )

        for db in self.db:
            for table in self.tables:

                md5 = self.db[db][table]['md5']
                test = get_md5( self.db[db][table]['path'] )

                self.logging.debug('(%s) table:%s md5:[old: %s new: %s]' % \
                            (db,table,md5,test) )

                if test != md5: return db

        return False

    def update(self):
        """
        function to update the data from the tables
        """
        if not self.db: self.validate()

        self.logging.debug( "refresh(%s)" % (self.db) )

        self._get_dlevents()

        for db in self.db:
            for table in self.tables:
                self.db[db][table]['md5'] = get_md5( self.db[db][table]['path'] )



    def validate(self):
        self.logging.debug( 'validate()' )

        if self.db: return True

        # Verify database files
        for test_db in self.database_list:
            name = verify_db( test_db )
            if name:
                self.db[name] = {}
            else:
                raise NetPerfException("Not a valid database: %s" % (self.database))

        if not len(self.db):
            raise NetPerfException("Missing value for database" )

        # Verify tables
        for db in self.db:
            for table in self.tables:
                path = test_table(db,table)
                if not path:
                    raise NetPerfException("Empty or missing: %s %s" % (self.db, table))

                self.db[db][table] = { 'path':path, 'md5':False }
                self.logging.debug( 'run validate(%s) => %s' % (table, path) )

        return True


    def _get_dlevents(self):

        self.logging.debug( "_get_dlevents()")
        self.cache = []
        self.error_cache = []

        steps = [ 'dbopen netperf']

        fields = ['snet','time','npsta','perf']

        for db in self.db:
            for v in extract_from_db( db, steps, fields, self.db_subset):

                try:
                    v['perf'] = int( v['perf'] )
                    v['time'] = int( v['time'] )

                    v['year'] = int( stock.epoch2str(v['time'], '%Y', 'UTC') )
                    v['jday'] = int( stock.epoch2str(v['time'], '%j', 'UTC') )

                    v['id'] = '%s_%s_%s' % (v['snet'], v['jday'], v['year'])

                    self.logging.debug('netperf() => %s, %s)' % (v['id'], v['perf']) )

                    self.cache.append( v )
                except Exception, e:
                    self.logging.complain('netperf() => parse exception)' )
                    v['exception'] = Exception
                    v['error'] = e

                    self.logging.complain( v )

                    self.error_cache.append( v )
