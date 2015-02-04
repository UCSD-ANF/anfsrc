# Dbcentral will load the database and test for
# the existence of the 'clusters' table first. If missing
# the class will assume that the intention of the user
# is to load a regular database and use the class
# functionality to store the pointer. This will trigger
# the self.type value to be "masquerade". Regular
# dbcentral tables will load normally and set
# self.type to "dbcentral".

#
# @author: Juan Reyes <reyes@ucsd.edu>
#
# @usage:
#   Create:
#      element = dbcentral(path)
#      element = dbcentral(path,nickname)
#      element = dbcentral(path,nickname,True) # Enable Debug mode. Verbose output
#   Access:
#      print element                           # Nice print of values
#      element.type                            # return string value for mode [dbcentral,masquerade]
#      element.path                            # return string value for path
#      element.nickname                        # return string value for nickname
#      element.list()                          # return list of databases
#      element(epoch)                          # return database matching the epoch time
#      element.purge(db)                       # remove database from class.
#

from __main__ import *

if __name__ == '__main__':
    """
    This will run if the file is called directly.
    """
    import sys, os, signal

    signal.signal(signal.SIGINT, signal.SIG_DFL)

    sys.path.append(os.environ['ANTELOPE'] + "/data/python")
    try:
        import antelope.datascope as datascope
        import antelope.stock as stock
    except Exception,e:
        sys.exit( "\n\tProblems with Antelope libraries.%s %s\n" % (Exception,e) )

    try:
        import logging
        from anf.eloghandler import ElogHandler
    except Exception,e:
        sys.exit( "\n\tProblems loading ANF logging libs. %s(%s)\n"  % (Exception,e))



class dbcentralException(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __repr__(self):
        return 'dbcentralException: %s' % (self.msg)
    def __str__(self):
        return repr(self)

class dbcentral:

    def __init__(self, path, nickname=False, debug=False):
        self.type = False
        self.path = os.path.abspath(path)
        self.nickname = nickname
        self.debug = debug

        import glob
        self.glob = glob.glob
        import logging

        self.logger = logging.getLogger().getChild('dbcentral')

        if self.debug:
            self.logger.setLevel( logging.DEBUG )
        else:
            self.logger.setLevel( logging.WARNING )

        # Create dictionary to hold all the values
        self.logger.debug( 'init(): path:%s nickname:%s debug:%s' \
                % (self.path,self.nickname,self.debug) )
        self.dbs = {}

        # Load the dbs
        self.logger.debug( '_get_list(): ' )
        self._get_list()


    def __str__(self):
        """
        end-user/application display of content using print() or log.msg()
        """
        return ''.join(["\ndbcentral:\t%s: %s" % \
                (value,self.dbs[value]) for value in sorted(self.dbs.keys())])


    def info(self):
        self.logger.info( "dbcentral.nickname() => %s" % self.nickname )
        self.logger.info( "dbcentral.type() => %s" % self.type )
        self.logger.info( "dbcentral.path() => %s" % self.path )
        self.logger.info( "dbcentral.list() => %s" % self.list() )
        for element in sorted(self.dbs):
            self.logger.info( "%s => %s" % (element,self.dbs[element]['times']) )


    def __call__(self, time=stock.now()):
        """
        method to intercepts data requests.
            time default is "now"
        """

        try:
            time = float(time)
        except Exception,e:
            raise dbcentralException( "wrong time=>[%s] %s" % (time,time.__class__) )
        else:
            for element in sorted(self.dbs):
                start = self.dbs[element]['times'][0]
                end = self.dbs[element]['times'][1]
                if start < time and time < end:
                    return element

        raise dbcentralException( "No db match for time=>[%s]" % time )


    def __dell__(self):
        """
        method to cleanup dict.
        """

        self.dbs = {}


    def _raise(self, log):
        """
        method to print problems and raise exceptions
        """
        raise dbcentralException('*dbcentral*: ERROR=> %s' % log)


    def _get_list(self):

        self.logger.debug( 'dbopen(%s)' % self.path  )
        try:
            db = datascope.dbopen(self.path, "r")
        except Exception,e:
            self._raise("Cannot open database %s (%s)" % (self.path,e))


        self.logger.debug( 'lookup(table=clusters)' )
        try:
            db = db.lookup(table='clusters')
            if not db.query(datascope.dbTABLE_PRESENT): raise
        except:
            self.type = 'masquerade'
            self.nickname = None
            self.dbs[self.path] = {'times': [-10000000000.0,10000000000.0]}
            self.logger.debug( "Not a dbcentral database. Set single database." )
            return


        self.type = 'dbcentral'
        if self.nickname is None:
            self._raise("Need nickname for dbcentral clustername regex.")


        try:
            db = db.lookup('','clusters','','dbNULL')
            null_time,null_endtime = db.getv('time','endtime')
        except Exception,e:
            self._raise("Cannot look up null values in clusters table. (%s)" % e)


        db = db.subset("clustername =~ /%s/" % self.nickname)
        db = db.sort('time')

        nclusters = db.record_count
        self.logger.debug( "Records=%s" % nclusters )
        if nclusters < 1:
            self._raise("No matches for nickname.")


        for record in db.iter_record():
            try:
                dbname_template = record.extfile()[-1]
            except Exception, e:
                self._raise("Cannot run db.extfile(). %s" % e)

            self.logger.debug( "dbname_template=%s" % dbname_template )

            try:
                self.volumes,self.net,time,endtime = record.getv("volumes","net","time","endtime")
            except Exception,e:
                self._raise("Problems with record.getv('volumes','net','time','endtime'). (%s)\n" % e)

            self.logger.debug( "volumes=%s" % self.volumes )
            self.logger.debug( "net=%s" % self.net )
            self.logger.debug( "time=%s" % time )

            if endtime == null_endtime:
                # This will be problematic with realtime systems
                endtime = stock.now()

            self.logger.debug( "endtime=%s" % endtime )

            if self.volumes == 'single':

                self._test_db(time,endtime,dbname_template)

            elif self.volumes == 'year':

                start_year = int(stock.epoch2str(time,"%Y"))
                end_year   = int(stock.epoch2str(endtime,"%Y"))

                for y in range(start_year,end_year+1):

                    voltime    = stock.str2epoch("1/1/%s 00:00:00" % y)
                    volendtime = stock.str2epoch("12/31/%s 23:59:59" % y)
                    dbname     = stock.epoch2str(voltime,dbname_template)

                    self._test_db(voltime,volendtime,dbname)

            elif self.volumes == 'month':

                start_month = int(stock.epoch2str(time,"%L"))
                start_year  = int(stock.epoch2str(time,"%Y"))
                end_month   = int(stock.epoch2str(endtime,"%L"))
                end_year    = int(stock.epoch2str(endtime,"%Y"))

                vol_month   = start_month
                vol_year    = start_year

                while vol_year < end_year or ( vol_year == end_year and vol_month <= end_month ):

                    voltime           = stock.str2epoch("%d/1/%d" % (vol_month,vol_year) )

                    if vol_month < 12:
                        temp_vol_endmonth = vol_month + 1
                        temp_vol_endyear  = vol_year
                    else:
                        temp_vol_endmonth = 1
                        temp_vol_endyear  = vol_year + 1

                    volendtime = stock.str2epoch("%d/1/%d" % (temp_vol_endmonth,temp_vol_endyear) ) - 1
                    dbname     = stock.epoch2str(int(voltime), dbname_template)

                    self._test_db(voltime,volendtime,dbname)


                    if vol_month < 12:
                        vol_month = vol_month + 1
                    else:
                        vol_year = vol_year + 1
                        vol_month = 1


            elif self.volumes == 'day':

                start_day = int(stock.yearday(time))
                end_day   = int(stock.yearday(endtime))

                vol_day   = start_day

                while vol_day <= end_day:

                    voltime    = stock.epoch(vol_day)
                    volendtime = voltime + 86399 # one second less than a full day
                    dbname     = stock.epoch2str(voltime, dbname_template)

                    self._test_db(voltime,volendtime,dbname)

                    vol_day = stock.yearday((stock.epoch(vol_day)+86400))

            else:
                self._raise( "Volumes type '%s' in cluster database not understood" % volumes )

        self.logger.debug( "DBS=%s" % self.dbs.keys() )


    def _test_db(self,time,endtime,dbname):
        """
        Method to verify that the db is valid before saving the value.
        """

        self.logger.debug( "Test for time=%s =>> %s" % (time,dbname) )

        if os.path.isfile(dbname):
            self.dbs[dbname] = {'times': [time,endtime]}
            return

        if self.glob("%s.*" % dbname):
            self.dbs[dbname] = {'times': [time,endtime]}
            self.logger.error( "No descriptor file for (%s)." % dbname )
            return

        self.logger.error( "Cannont find dbname=%s" % dbname )


    def after(self,time):
        """
        Method to get the rest of the
        databases after the designated
        for the timestamp.
        """

        temp = []

        try:
            time = float(time)
        except Exception,e:
            print "\n*dbcentral*: dbcentral() => error in time=>[%s] %s" % \
                    (time,time.__class__)
        else:
            for element in sorted(self.dbs):
                start = self.dbs[element]['times'][0]
                end = self.dbs[element]['times'][1]
                if time < start:
                    temp.extend([element])

        return temp

    def clean_before(self,time):
        """
        Method to clean the list of dbs
        for times earlier than the provided
        epoch.
        """

        temp = []

        try:
            time = float(time)
        except Exception,e:
            print "\n*dbcentral*: dbcentral() => error in time=>[%s] %s" % \
                    (time,time.__class__)
        else:
            for element in sorted(self.dbs):
                start = self.dbs[element]['times'][0]
                end = self.dbs[element]['times'][1]
                if time > end:
                    temp.extend([element])

            for element in sorted(temp):
                self.purge(element)

        return self.list()


    def list(self):

        try:
            return sorted(self.dbs.keys())
        except:
            self._raise( 'Cannot check content of list!' )


    def purge(self,tbl=None):
        """
        Method to clean dbcentral object by removing a database
        """
        if not tbl:
            raise dbcentralException('*dbcentral*: dbcentral.purge() => No db')

        self.logger.debug( '*dbcentral*: dbcentral.purge() => %s' % tbl )

        try:
            del self.dbs[tbl]
        except :
            pass

        #self.info()


if __name__ == '__main__':
    """
    This will run if the file is called directly.
    """
    try:
        import logging
        from anf.eloghandler import ElogHandler
    except Exception,e:
        sys.exit( "\n\tProblems loading ANF logger libs. %s(%s)\n"  % (Exception,e)) 
    try:
        logging.basicConfig()
        logger = logging.getLogger()
        formatter = logging.Formatter('[%(name)s] %(message)s')
        handler = ElogHandler()
        handler.setFormatter(formatter)
        logger.handlers=[]
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
    except Exception, e:
        sys.exit("Problem building logging handler. %s(%s)\n" % (Exception,e) )


    time =  1262404000.00000

    dbcntl = dbcentral('/opt/antelope/data/db/demo/demo',debug=True)

    logger.info( 'dbcntl = dbcentral("%s","%s")' % (dbcntl.path,dbcntl.nickname) )
    logger.info( 'dbcntl.type => %s' % dbcntl.type )
    logger.info( 'dbcntl.nickname => %s' % dbcntl.nickname )
    logger.info( '%s' % dbcntl )
    logger.info( 'dbcntl.list() => %s' % dbcntl.list() )
    logger.info( 'dbcntl(%s) => %s' % (time,dbcntl(time)) )
    try:
        dbcntl.purge('test')
    except Exception, e:
        logger.info('dbcntl.purge(%s) => %s' % ('test',e) )

    logger.info( 'Done with dbcentral demo.' )


