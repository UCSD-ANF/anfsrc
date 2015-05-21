import re,os,sys
import json
import socket
import pprint
from collections import defaultdict
from datetime import datetime, timedelta

# safe to import * here
from db2web.db2json_libs import *

try:
    import antelope.elog as elog
    import antelope.stock as stock
    import antelope.datascope as datascope
except Exception,e:
    raise event2jsonException( 'Problems loading Antelope libs: %s' % e )

try:
    from pymongo import MongoClient
except Exception,e:
    sys.exit("Problem loading Pymongo library. %s(%s)\n" % (Exception,e) )

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
                'time_limit':{'type':'int','default':3600},
                'refresh':{'type':'int','default':60},
                'databases':{'type':'dict','default':{}},
                'readableJSON':{'type':'int','default':0},
                'mongo_host':{'type':'str','default':None},
                'mongo_db':{'type':'str','default':None},
                'mongo_user':{'type':'str','default':None},
                'mongo_password':{'type':'str','default':None},
                }

        self._read_pf(pfname)

        try:
            self.mongo_instance = MongoClient(self.mongo_host)
            self.mongo_db_instance = self.mongo_instance[self.mongo_db]
            self.mongo_db_instance.authenticate(self.mongo_user, self.mongo_password)
        except Exception,e:
            sys.exit("Problem with MongoDB Configuration. %s(%s)\n" % (Exception,e) )

        self.event_cache = {}

        self.loading = True

        self._log( "Events(): init()" )

        self._log( '\t' + '#'*20 )
        self._log( '\tLoading Events!' )
        self._log( '\t' + '#'*20 )

        for name,path in self.databases.iteritems():
            self._log( "Test %s db: %s" % (name,path) )

            for table in ['event','origin','netmag']:
                present = test_table(path,table)
                if not present:
                    self._complain('Empty or missing %s.%s' % (path,table) )

                if table is 'event': event = present
                if table is 'origin': origin = present
                if table is 'netmag': netmag = present

            if not origin:
                self._complain( 'Cannot work without origin table.')
                continue

            #db = datascope.dbopen( path , 'r' )
            self.dbs[name] = { 'db':path, 'path':path, 'mags':{},
                    'md5event':False, 'md5origin':False, 'md5netmag':False,
                    'origin': origin, 'event':event, 'netmag':netmag }

        self._get_event_cache()


    def _log(self,msg):
        if self.verbose:
            elog.notify( 'event2json: %s' % msg )

    def _complain(self,msg):
        elog.complain( 'event2json: PROBLEM: %s' % msg )

    def _read_pf(self, pfname):
        """
        Read configuration parameters from rtwebserver pf file.
        """

        elog.notify( 'Read parameters from pf file: ' + pfname)

        pf = stock.pfread(pfname)

        for attr in self.pf_keys:
            setattr(self, attr, pf.get(attr))
            elog.notify( "%s: read_pf[%s]: %s" % (pfname, attr, getattr(self,attr) ) )

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
            self._complain('Cannot find self.table(%s) => %s' % (db,e) )
            return False

    def _get_magnitudes(self,db):

        mags = {}

        self._log('Get magnitudes ' )

        steps = ['dbopen netmag', 'dbsubset orid!=NULL']

        if self.time_limit:
            steps.extend(["dbsubset lddate > %d" % (stock.now() - float(self.time_limit))] )

        with datascope.freeing(db.process( steps )) as dbview:

            self._log('Got %s mags from file' % dbview.record_count )

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



    def _get_event_cache(self):
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

                self._log( "Events(%s): db: %s" % (name,path) )


                testorigin =get_md5(origin)
                testevent = get_md5(event) if event else False
                testnetmag = get_md5(netmag) if netmag else False


                self._log('event [old: %s new: %s]' %(md5event,testevent) )
                self._log('origin [old: %s new: %s]' %(md5origin,testorigin) )
                self._log('netmag [old: %s new: %s]' %(md5netmag,testnetmag) )

                if testorigin == md5origin and testevent == md5event and testnetmag == md5netmag:
                    self._log('No update needed. Skipping.')
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
                    self._log( 'Events(%s): updating from %s' % (name,path) )

                self._log( ', '.join(steps) )


                with datascope.freeing(db.process( steps )) as dbview:

                    if not dbview.record_count:
                        self._complain( 'Events(%s): No records %s' % (name,path) )
                        continue

                    for temp in dbview.iter_record():

                        (orid,time,lat,lon,depth,auth,nass,ndef,review) = \
                                temp.getv('orid','time','lat','lon','depth',
                                        'auth','nass','ndef','review')

                        evid = orid
                        if event:
                            evid = temp.getv('evid')[0]


                        self._log( "Events(%s): new evid #%s" % (name,evid) )

                        allmags = []
                        magnitude = '-'
                        maglddate = 0
                        strtime = stock.epoch2str(time, self.timeformat, self.timezone)
                        try:
                            srname = stock.srname(lat,lon)
                            grname = stock.grname(lat,lon)
                        except Exception,e:
                            error = 'Problems with (s/g)rname for orid %s: %s' % (orid,lat,lon,e) 
                            self._complain(error)
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

                        self._log( "Events(): %s add (%s,%s)" % (name,evid,orid) )

                self.event_cache[name] = tempcache[name]
                self._log( "Completed updating db. (%s)" % name )


    def dump_cache(self, to_mongo=False, to_json=False, jsonPath="default.json"):
        if not hasattr(self, 'event_cache'):
            self._complain('No event cache loaded, cannot dump to MongoDB.')
            return;

        # USArray, CEUSN, etc.
        for project in self.event_cache:
            if to_mongo:
                currCollection = self.mongo_db_instance[project+'_events']
                
                # Clear old entries
                currCollection.remove()

                # Each individual event entry
                for entry in self.event_cache[project]:

                    # Convert to JSON then back to dict to stringify numeric keys
                    jsonEntry = json.dumps(entry)
                    revertedEntry = json.loads(jsonEntry)
                    currCollection.update({'evid': entry['evid']}, {'$set':revertedEntry}, upsert=True)

        if to_json:
            with open(jsonPath, 'w') as outfile:
                json.dump(self.event_cache, outfile)
