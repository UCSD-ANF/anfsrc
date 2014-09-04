"""
Antelope Datascope output to JSON files
Summary & individual stations

@package  Datascope
@author   Rob Newman <robertlnewman@gmail.com> 858.822.1333
@version  2.2
@license  MIT style license
@modified 2012-03-08
@notes    1. Rewrite to only have dbpointers open for a short
          while - Datascope does not like realtime dbs being
          open when edits can happen (dbpointers all become
          invalid and the script crashes)
          2. Datascope does not correctly free up memory. Triage
          this by forcing memory cleanup with datascope.dbfree()
          and datascope.dbclose(). This goes against Pythonic
          Principles (Python has dynamic garbage collection) but
          until underlying Datascope memory leaks are fixed, this
          is a stop-gap.
          3. Polaris, Canada (snet PO) stations only have HH.*
          channels. This means some additional exceptions code to
          account for this (we don't want to include BK or CI
          stations that use HH.* channels)
          4. Create and use a parameter file (db2json.pf) that has
          the specific network and channel subsets to account for
          (3) above (look for 'override_subset' in code).
          5. Account for stations that have more than one sensor
          installed, such as an STS-2 (broadband) and Episensor
          (strong-motion).
"""

import sys
import os
import json
import string
import tempfile
import re
import gzip
# Load datascope functions
from antelope import datascope
from antelope import orb
from antelope import stock
from optparse import OptionParser
from time import time, gmtime, strftime
from pprint import pprint
from collections import defaultdict

subtype_list = ['all']
station_dict = {'decom':{}, 'adopt':{}, 'active':{}}
for k in station_dict.iterkeys():
    subtype_list.append(k)
core_fields = ["snet", "vnet", "lat", "lon", "staname", "time"]
active_fields = core_fields + [
    "commtype",
    "provider",
    "insname",
    "elev",
    "equip_install",
    "cert_time"
]
decom_fields = core_fields + [
    "decert_time",
    "insname",
    "endtime",
    "cert_time"
]
adopt_fields = core_fields + [
    "decert_time",
    "newsnet",
    "newsta",
    "atype",
    "auth"
]
# For station detail pages (individual station JSON files)
detail_dbmaster_fields = core_fields + [
    "sta",
    "ondate",
    "offdate",
    "elev",
    "endtime",
    "equip_install",
    "equip_remove",
    "cert_time",
    "decert_time",
    "commtype",
    "provider",
    "power",
    "dutycycle",
    "insname"
]
detail_dbmaster_adopt_fields  = adopt_fields + [
    "sta",
    "ondate",
    "offdate",
    "elev",
    "endtime",
    "equip_install",
    "equip_remove",
    "cert_time",
    "commtype",
    "provider",
    "power",
    "dutycycle",
    "insname"
]
detail_inst_hist_fields = [
    "insname",
    "instype",
    "ssident",
    "chan",
    "hang",
    "vang",
    "sitechan.ondate",
    "sitechan.offdate",
    "gtype",
    "idtag"
]
detail_deployment_hist_fields = [
    "time",
    "endtime",
    "vnet",
    "cert_time",
    "decert_time"
]
detail_comms_hist_fields = [
    "time",
    "endtime",
    "commtype",
    "provider",
    "power",
    "dutycycle"
]
detail_baler_fields = [
    "model",
    "firm",
    "nreboot",
    "last_reboot",
    "ssident"
]
detail_dlevents = ["dlevtype", "dlcomment"]

def configure():
    """Parse command 
    line args
    """
    # configure
    usage = "Usage: %prog [options]"
    parser = OptionParser(usage=usage)
    parser.add_option("-v", action="store_true", dest="verbose",
        help="verbose output", default=False)
    parser.add_option("-d", action="store_true", dest="debug",
        help="debug output", default=False)
    parser.add_option("-t", "--type", action="store", type="string",
        dest="subtype", help="type of station to process", default=False)
    parser.add_option("-z", action="store_true", dest="zipper",
        help="create a gzipped version of the file", default=False)
    parser.add_option("-p", "--pf", action="store", dest="pf", type="string",
        help="parameter file path", default="db2json")
    (options, args) = parser.parse_args()

    if options.debug:
        options.verbose = True

    if options.subtype:
        subtype = options.subtype
        if subtype not in subtype_list:
            logfmt("Subtype '%s' not recognized" % subtype)
            logfmt("\tEither don't define it or use: %s" % ', '.join(subtype_list))
            sys.exit(-1)

    return options.verbose, options.debug, options.zipper, options.subtype, options.pf
    # 

def nfs_test(db):
    """Test that the disk
    mount point is visible
    """
    # nfs_test
    if not os.path.isfile(db):
        logfmt("Error: Cannot read the dbmaster file (%s)" % db)
        logfmt("NFS or permissions problems? Check file exists...")
        sys.exit(-1)
    return True
    # 

def zip_me_up(myfile):
    """Create a gzipped 
    JSON file
    """
    # zip_me_up
    fzip_in = open(myfile, 'rb')
    try:
        fzip_out = gzip.open('%s.gz' % myfile, 'wb' )
    except IOError,e:
        logfmt("Error: %s - %s" % (IOError, e))
    else:
        fzip_out.writelines(fzip_in)
        fzip_out.close()
        fzip_in.close()
        return True
    # 

def logfmt(message):
    """Output a log
    message with a
    timestamp"""
    # logfmt
    curtime = stock.strtime(time())
    print curtime, message
    # 

def print_select_statement(statement):
    """Output a log
    message for the 
    orb select statement
    """
    # print_select_statement
    logfmt("Orbselect statement parts (split on '|'):")
    parts = statement.strip('()').split('|')
    for p in parts:
        print "\t%s" % p
    # 

class ParseOrb:
    """Methods for grabbing the
    useful packet values out
    of the specified orb
    """
    # ParseOrb

    def __init__(self, alerts, verbose=False, debug=False):
        """Default args"""
        # __init__
        self.alerts = alerts
        self.verbose = verbose
        self.debug = debug
        # 

    def orb_interaction(self, orbptr, selection_string=False):
        """Open & select orb
        """
        # orb_interaction
        if self.verbose or self.debug:
            logfmt("Orb (%s) operations" % orbptr)
        try:
            myorb = orb.Orb(orbptr, 'r')
            myorb.connect()
        except Exception, e:
            logfmt("\tException: %s" % e)
            sys.exit(-1)

        myorb.select(selection_string)

        when, sources = myorb.sources()
        orb_dict = self.parse_orb_sources(sources)

        myorb.close()

        if self.verbose or self.debug:
            [ logfmt("sources:[%s]" % x) for x in sources]

        return orb_dict

    def parse_orb_sources(self, sources):
        """Parse the sources
        and return a dictionary
        """
        # parse_orb_sources
        # source_dict = {}
        source_dict = defaultdict(dict)
        for s in sources:
            srcname = s['srcname']
            parts = srcname.split('/')
            snet_sta = parts[0].split('_')
            snet = snet_sta[0]
            sta = snet_sta[1]
            latency = time() - s['slatest_time']
            alert, off_on = self.orbstat_alert_level(latency)
            source_dict[sta].update(latency=latency)
            source_dict[sta].update(latency_readable=self.humanize_time(latency))
            source_dict[sta].update(snet=snet)
            source_dict[sta].update(alert=alert)
            source_dict[sta].update(offon=off_on)
            source_dict[sta].update(soldest_time=stock.epoch2str(s['soldest_time'], "%Y-%m-%d %H:%M:%S"))
            source_dict[sta].update(slatest_time=stock.epoch2str(s['slatest_time'], "%Y-%m-%d %H:%M:%S"))
        return source_dict
        # 

    def orbstat_alert_level(self, secs):
        """Determine the alert level
        """
        # orbstat_alert_level
        if secs >= int(self.alerts['offline']):
            return 'down', 0
        elif secs >= int(self.alerts['warning']):
            return 'warning', 1
        else:
            return 'ok', 1
        # 

    def humanize_time(self, secs):
        """Create human readable
        timestamp
        """
        # humanize_time
        secs = round(secs)
        if secs < 60:
            return '%02ds' % (secs)
        else:
            mins,secs = divmod(secs,60)
            if mins < 60:
                return '%02dm:%02ds' % (mins, secs)
            else:
                hours,mins = divmod(mins,60)
                return '%02dh:%02dm:%02ds' % (hours, mins, secs)
        # 

    def add_orbstat(self, orbstat, sta, qtype=False):
        """Return station specific 
        orbstat values
        """
        # add_orbstat
        orbstat_dict = defaultdict(dict)
        if sta in orbstat:
            orbstat_dict.update(latency = orbstat[sta]['latency'])
            orbstat_dict.update(latency_readable = self.humanize_time(orbstat[sta]['latency']))
            orbstat_dict.update(alert = orbstat[sta]['alert'])
            orbstat_dict.update(status = orbstat[sta]['offon'])
            if qtype == 'detail':
                orbstat_dict.update(slatest_time = orbstat[sta]['slatest_time'])
                orbstat_dict.update(soldest_time = orbstat[sta]['soldest_time'])
        else:
            orbstat_dict.update(latency = -1)
            orbstat_dict.update(alert = 'down')
            orbstat_dict.update(status = 0)
        return orbstat_dict
        # 

    # 

class NetworkSummary:
    """Methods for determining
    values of network and stations
    for JSON file(s)
    """
    # NetworkSummary

    def __init__(self, dbptr, pf, verbose=False, debug=False):
        """Initialize database pointers
        """
        # __init__
        self.db = dbptr
        self.dbptr = dbptr
        self.pf = pf
        self.verbose = verbose
        self.debug = debug
        # 

    def open_db(self):
        """Test that the database
        pointer is valid
        """
        # open_db
        try:
            db = datascope.dbopen(self.dbptr, 'r')
        except Exception,e:
            logfmt("Cannot open database '%s'. Caught exception %s" % (self.dbptr, e))
            sys.exit(-1)
        else:
            self.dbptr = db
            self.db = db
        # 

    def close_db(self):
        """Close the open database 
        pointer. This will free() all
        dbpointers in memory
        """
        # close_db
        try: 
            self.db.close()
        except:
            pass
        # 

    def table_test(self, tables_to_check, json_file):
        """Test modification time 
        for database tables to see 
        if we need to run script"""
        # table_test
        if self.verbose:
            logfmt("Test for modification time of tables:")
        table_modification_times = []
        for table in tables_to_check:
            table_ptr = self.db.lookup(table=table)
            table_stats = os.stat(table_ptr.query('dbTABLE_FILENAME'))
            table_age = table_stats.st_mtime
            if self.verbose:
                logfmt("\tFile modification time of '%s' table: %s" % (table, stock.epoch2str(table_age, "%Y-%m-%d %H:%M:%S")))
            table_modification_times.append(table_age)
        try:
            json_stats = os.stat(json_file)
        except OSError, e:
            logfmt("OSError: %s. Recreate!" % e)
            return True
        else:
            if self.verbose:
                logfmt("\tFile modification time of '%s': %s" % (json_file, stock.epoch2str(json_stats.st_mtime, "%Y-%m-%d %H:%M:%S")))
            if max(table_modification_times) > json_stats.st_mtime:
                return True
            else:
                return False
        # 
 
    def idtag_determiner(self, dlogger_id):
        """The idtag field is only
        in dlsite, staq330 and q330comm
        tables. Dlsite is depreciated,
        q330comm first used 2006.
        Try q330comm first.
        """
        # idtag_determiner
        dbptr = self.db.lookup(table='q330comm')
        dbptr = dbptr.sort('ssident', unique=True)
        dbptr = dbptr.subset('ssident=~/%s/' % dlogger_id)
        if dbptr.query('dbRECORD_COUNT') > 0:
            dbptr.record = 0
            idtag = dbptr.getv('idtag')[0]
        else:
            idtag = 'N/A'
        dbptr.free()
        return idtag
        # 

    def create_instrument_history(self, override_subset=False):
        """Open the snetsta table then
        join on stage, dlsensor and sitechan
        using very specific join keys (including
        time ranges). Then get histories for
        all stations, returning dictionary

        Gets complicated for stations with more
        than one station installed, such as sites
        with broadband seismometer and strong
        motion sensor, or TOLK which has two
        sensors installed
        """
        # create_instrument_history
        if self.verbose or self.debug:
            logfmt("create_instrument_history(): Use override_subset if def")
            logfmt("create_instrument_history(): Parse dlsensor tbl into dict")

        # Get dlsensor table into simple per snident_dlident keyed dict
        dlsensor_history = defaultdict(lambda: defaultdict(dict))
        dlsensor_hist_dbptr = self.db.lookup(table='dlsensor')
        for i in range(dlsensor_hist_dbptr.query('dbRECORD_COUNT')):
            dlsensor_hist_dbptr.record = i
            (dlsen_dlmodel,
             dlsen_dlident,
             dlsen_chident,
             dlsen_time,
             dlsen_endtime,
             dlsen_snmodel,
             dlsen_snident) = dlsensor_hist_dbptr.getv('dlmodel',
                                                       'dlident',
                                                       'chident',
                                                       'time',
                                                       'endtime',
                                                       'snmodel',
                                                       'snident')
            new_key = '%s %s' % (dlsen_snident, dlsen_dlident)
            dlsensor_history[new_key] = {
                'dlmodel':dlsen_dlmodel,
                'dlident':dlsen_dlident,
                'chident':dlsen_chident,
                'time':dlsen_time,
                'endtime':dlsen_endtime,
                'snmodel':dlsen_snmodel,
                'snident':dlsen_snident
            }

        '''
        Get whole sitechan table
        into simple per station list
        '''

        if self.verbose or self.debug:
            logfmt("create_instrument_history(): Parse sitechan, snetsta")

        instrument_history = defaultdict(list)

        sitechan_hist_dbptr = self.dbptr.lookup(table='sitechan')
        sitechan_hist_dbptr = sitechan_hist_dbptr.join('snetsta')
        sitechan_hist_dbptr = sitechan_hist_dbptr.join('sensor')
        sitechan_hist_dbptr = sitechan_hist_dbptr.join('instrument')

        if override_subset:
            logfmt('create_instrument_history(): Apply override_subset(s)')
            for o in override_subset:
                if self.verbose or self.debug:
                    logfmt("\t'%s'" % o)
                try:
                    sitechan_hist_dbptr = sitechan_hist_dbptr.subset(o)
                except Exception, e:
                    logfmt("\tError with subset (%s) encountered: %s" % (o, e))

        sitechan_hist_dbpt = sitechan_hist_dbptr.sort(('sta', 'ondate', 'chan'))

        # Handle multiple sensors here
        sitechan_hist_grp_dbptr = sitechan_hist_dbptr.group('sta')
        for i in range(sitechan_hist_grp_dbptr.query('dbRECORD_COUNT')):
            sitechan_hist_grp_dbptr.record = i
            (sta, [db,
                   view,
                   end_rec,
                   start_rec]) = sitechan_hist_grp_dbptr.getv('sta', 'bundle')
            if self.verbose:
                logfmt("\tcreate_instrument_history(): %s" % sta)
            for j in range(start_rec, end_rec):
                sitechan_hist_dbptr.record = j
                (site_chan,
                 site_ondate,
                 site_offdate,
                 site_descrip,
                 site_hang,
                 site_vang,
                 site_insname) = sitechan_hist_dbptr.getv('chan',
                                                          'ondate',
                                                          'offdate',
                                                          'descrip',
                                                          'hang',
                                                          'vang',
                                                          'insname')
                # At a minimum we get the following:
                ins_hist_obj = {
                    'channel':site_chan,
                    'ondate':site_ondate,
                    'offdate':site_offdate,
                    'descrip':site_descrip,
                    'hang':site_hang,
                    'vang':site_vang
                }
                # Augment with extra info if available
                if site_descrip != '' and len(site_descrip) > 1:
                    site_sensorid, site_dloggerid = site_descrip.split()
                    if site_descrip in dlsensor_history:
                        this_sensor = self.sensor_readable(
                            dlsensor_history[site_descrip]['snmodel'])
                        this_datalogger = self.datalogger_readable(
                            dlsensor_history[site_descrip]['dlmodel'])
                        datalogger_idtag = self.idtag_determiner(
                            dlsensor_history[site_descrip]['dlident'])
                        sensor = {
                            'model':this_sensor[0],
                            'css':this_sensor[1],
                            'ssident':dlsensor_history[site_descrip]['snident']
                        }
                        datalogger = {
                            'model':this_datalogger[0],
                            'css':this_datalogger[1],
                            'ssident':dlsensor_history[site_descrip]['dlident'],
                            'idtag':datalogger_idtag
                        }
                        ins_hist_obj.update(snmodel=dlsensor_history[site_descrip]['snmodel'])
                        ins_hist_obj.update(sensor_id=dlsensor_history[site_descrip]['snident'])
                        ins_hist_obj.update(dlmodel=dlsensor_history[site_descrip]['dlmodel'])
                        ins_hist_obj.update(dlogger_id=dlsensor_history[site_descrip]['dlident'])
                        ins_hist_obj.update(snident=dlsensor_history[site_descrip]['snident'])
                        ins_hist_obj.update(chident=dlsensor_history[site_descrip]['chident'])
                        ins_hist_obj.update(datalogger=datalogger)
                        ins_hist_obj.update(sensor=sensor)
                    else:
                        # Alternatively try the insname field
                        this_sensor = self.sensor_readable(site_insname)
                        this_datalogger = self.datalogger_readable(site_insname)
                        sensor = {
                            'model':this_sensor[0],
                            'css':this_sensor[1],
                            'ssident':'Unknown'
                        }
                        datalogger = {
                            'model':this_datalogger[0],
                            'css':this_datalogger[1],
                            'idtag':'Unknown'
                        }
                        ins_hist_obj.update(sensor_id=site_sensorid)
                        ins_hist_obj.update(dlogger_id=site_dloggerid)
                        ins_hist_obj.update(datalogger=datalogger)
                        ins_hist_obj.update(sensor=sensor)
                instrument_history[sta].append(ins_hist_obj)
        sitechan_hist_grp_dbptr.free()
        sitechan_hist_dbptr.free()
        return instrument_history
        # 

    def create_deploy_pointer(self, override_subset=False):
        """Create a pointer to the
        simple joined view of deployment
        Add ability to define an override
        subset to just get certain stations 
        of interest
        """
        # create_deploy_pointer
        dbptr = self.db.lookup(table='deployment')
        dbptr = dbptr.join('site', outer=True)
        dbptr = dbptr.join('snetsta', outer=True)
        dbptr = dbptr.join('sitechan', outer=True)
        dbptr = dbptr.join('comm', outer=True)
        dbptr = dbptr.join('sensor', outer=True)
        dbptr = dbptr.join('instrument', outer=True)
        if override_subset:
            logfmt('create_deploy_pointer(): Apply override_subset(s)')
            for o in override_subset:
                if self.verbose or self.debug:
                    logfmt("\t'%s'" % o)
                try:
                    dbptr = dbptr.subset(o)
                except Error, e:
                    logfmt("\tError with subset (%s) encountered: %s" % (o, e))
        if self.debug or self.verbose:
            logfmt('Number of records: %d' % dbptr.query('dbRECORD_COUNT'))
        self.deploy_dbptr = dbptr
        # 

    def get_metadata(self):
        """Get all the meta data values for
        all fields of a database pointer, 
        including dbNULL, dbFIELD_DETAIL,
        dbFIELD_DESCRIPTION, dbFIELD_TYPE
        """
        # get_metadata
        if self.verbose:
            logfmt("Determine field nulls, detail, desc and types for schema")
        self.dbmeta = defaultdict(dict)
        dbmeta = self.db
        for table in dbmeta.query('dbSCHEMA_TABLES'):
            dbmeta = self.db.lookup(table=table)
            try:
                dbmeta.query('dbTABLE_FIELDS')
            except:
                pass
            else:
                for field in dbmeta.query('dbTABLE_FIELDS'):
                    if field not in self.dbmeta:
                        #dbmeta = dbmeta.lookup(table=field, record='dbNULL')
                        dbmeta = dbmeta.lookup(field=field)
                        self.dbmeta[field] = {'null':'',
                                              'detail':'',
                                              'description':'',
                                              'field_type':''}
                        try:
                            dbmeta.getv(field)
                        except:
                            pass
                        else:
                            self.dbmeta[field]['null'] = dbmeta.getv(field)[0]
                            self.dbmeta[field]['detail'] = dbmeta.query('dbFIELD_DETAIL')
                            self.dbmeta[field]['description'] = dbmeta.query('dbFIELD_DESCRIPTION')
                            self.dbmeta[field]['field_type'] = dbmeta.query('dbFIELD_TYPE')
        dbmeta.free()
        if self.debug:
            logfmt("Metadata dictionary:")
            logfmt(self.dbmeta)
        return self.dbmeta
        # 

    def field_definitions(self, dbptr, field):
        """Define what each field key
        should be and what it should return
        """
        # field_definitions
        field_object = defaultdict(dict)
        if field in self.dbmeta:
            detail = self.dbmeta[field]['detail']
            description = self.dbmeta[field]['description']
            field_type = self.dbmeta[field]['field_type']
            null = self.dbmeta[field]['null']
        value = dbptr.getv(field)[0]
        field_readable = '%s_readable' % field
        if value == null:
            if field == 'commtype':
                field_object['readable'] = 'unknown'
                field_object['css'] = 'unknown'
            elif field == 'provider':
                field_object['readable'] = 'unknown'
                field_object['css'] = 'unknown'
            else:
                field_object[field_readable] = "N/A"
        else:
            if field_type == datascope.dbREAL:
                field_object[field_readable] = round(value, 3)
            elif field_type == datascope.dbTIME:
                field_object[field_readable] = stock.epoch2str(value, "%Y-%m-%d %H:%M:%S")
            elif field_type == datascope.dbYEARDAY:
                field_object[field_readable] = stock.epoch2str(value, "%Y-%m-%d")
            else:
                field_object[field_readable] = value
            # Deal with specialized fields that have their own CSS
            if field == 'commtype':
                field_format = value.lower()
                field_format = field_format.replace(' ','_')
                if field_format not in self.pf['comms']:
                    logfmt("Commtype '%s' not in pf_comms_list!" % field_format)
                    field_object['readable'] = 'unknown'
                    field_object['css'] = 'unknown'
                else:
                    pf_field_readable = self.pf['comms'][field_format]['name']
                    field_object['readable'] = pf_field_readable
                    field_object['css'] = field_format
            elif field == 'provider':
                field_format = value.lower()
                field_format = field_format.replace(' ','_')
                field_format = field_format.replace('/','_')
                field_format = field_format.strip("'")
                if field_format not in self.pf['provider']:
                    logfmt("Provider '%s' not in pf_provider_list!" % field_format)
                    field_object['readable'] = 'unknown'
                    field_object['css'] = 'unknown'
                else:
                    pf_field_readable = self.pf['provider'][field_format]['name']
                    field_object['readable'] = pf_field_readable
                    field_object['css'] = field_format
        if self.debug:
            field_object['field'] = field
            field_object['detail'] = detail
            field_object['description'] = description
            field_object['type'] = field_type
            field_object['null'] = null
        field_object['value'] = value
        if self.debug:
            logfmt(field_object)
        return field_object
        # 

    def process_decom_stations(self, field_list, adoptions=False):
        """Process just decommissioned stations
        """
        # process_decom_stations
        all_snets = self.pf['network']
        all_colors = self.pf['colors']
        if field_list == 'detail':
            fields = detail_dbmaster_fields
        elif field_list == 'summary':
            fields = decom_fields
        decom_list = []
        db_decom = self.deploy_dbptr.subset('offdate != NULL || offdate < now()')
        db_decom = db_decom.subset('endtime < now()')
        if adoptions:
            db_decom = db_decom.join('adoption', pattern1=('sta'), outer=True)
            db_decom = db_decom.subset('atype == NULL')
        db_decom = db_decom.sort(['snet','sta'], unique=True)
        if self.verbose:
            logfmt("process_decom_stations(): Process %d stations" % db_decom.query('dbRECORD_COUNT'))
        for i in range(db_decom.query('dbRECORD_COUNT')):
            db_decom.record = i
            sta = db_decom.getv('sta')[0]
            this_sta_dict = {}
            this_sta_dict['type'] = "Feature" # GEOJSON
            this_sta_dict['id'] = sta # GEOJSON
            this_sta_dict['properties'] = {} # GEOJSON
            this_sta_dict['geometry'] = { "type": "Point", "coordinates":[] } # GEOJSON
            for df in fields:
                df_obj = self.field_definitions(db_decom, df)
                df_readable_field = '%s_readable' % df
                if df == 'provider' or df == 'commtype':
                    this_sta_dict['properties'][df] = {}
                    this_sta_dict['properties'][df]['value'] = df_obj['readable']
                    this_sta_dict['properties'][df]['css'] = df_obj['css']
                elif df == 'snet':
                    this_color = all_snets[df_obj[df_readable_field]]['color']
                    this_sta_dict['properties']['snethexi'] = all_colors[this_color]['hexidecimal']
                    this_sta_dict['properties'][df] = df_obj[df_readable_field]
                else:
                    this_sta_dict['properties'][df] = df_obj[df_readable_field]
            this_sta_dict['geometry']['coordinates'].append(this_sta_dict['properties']['lon']) # GEOJSON
            this_sta_dict['geometry']['coordinates'].append(this_sta_dict['properties']['lat']) # GEOJSON
            decom_list.append(this_sta_dict)
        db_decom.free()
        return decom_list
        # 

    def process_adopted_stations(self, field_list):
        """Process just adopted stations
        """
        # process_adopted_stations
        all_snets = self.pf['network']
        all_colors = self.pf['colors']
        if field_list == 'detail':
            fields = detail_dbmaster_adopt_fields
        elif field_list == 'summary':
            fields = adopt_fields
        adopt_list = []
        db_adopt = self.deploy_dbptr.subset('offdate != NULL || offdate < now()')
        db_adopt = db_adopt.subset('endtime < now()')
        db_adopt = db_adopt.sort(['snet', 'sta'])
        db_adopt = db_adopt.join('adoption', pattern1=('sta'), outer=True)
        db_adopt = db_adopt.subset('atype != NULL')
        db_adopt = db_adopt.sort(['snet', 'sta'])
        db_adopt = db_adopt.group('sta')
        if self.verbose:
            logfmt("process_adopted_stations(): Process %d stations" % db_adopt.query('dbRECORD_COUNT'))
        for i in range(db_adopt.query('dbRECORD_COUNT')):
            db_adopt.record = i
            sta = db_adopt.getv('sta')[0]
            this_sta_dict = {}
            dbptr_sub = db_adopt.subset('sta =~ /%s/' % sta)
            dbptr_sub = dbptr_sub.ungroup()
            dbptr_sub = dbptr_sub.sort(["adoption.time"], reverse=True)
            dbptr_sub.record = 0 # Only get the most recent deployment

            sta = dbptr_sub.getv('sta')[0]

            this_sta_dict = {}
            this_sta_dict['type'] = "Feature" # GEOJSON
            this_sta_dict['id'] = sta # GEOJSON
            this_sta_dict['properties'] = {} # GEOJSON
            this_sta_dict['geometry'] = { "type": "Point", "coordinates":[] } # GEOJSON
            for adf in fields:
                adf_obj = self.field_definitions(dbptr_sub, adf)
                adf_readable_field = '%s_readable' % adf
                if adf == 'provider' or adf == 'commtype':
                    this_sta_dict['properties'][adf] = {}
                    this_sta_dict['properties'][adf]['value'] = adf_obj['readable']
                    this_sta_dict['properties'][adf]['css'] = adf_obj['css']
                elif adf == 'snet':
                    this_color = all_snets[adf_obj[adf_readable_field]]['color']
                    this_sta_dict['properties']['snethexi'] = all_colors[this_color]['hexidecimal']
                    this_sta_dict['properties'][adf] = adf_obj[adf_readable_field]
                else:
                    this_sta_dict['properties'][adf] = adf_obj[adf_readable_field]
            this_sta_dict['geometry']['coordinates'].append(this_sta_dict['properties']['lon']) # GEOJSON
            this_sta_dict['geometry']['coordinates'].append(this_sta_dict['properties']['lat']) # GEOJSON
            adopt_list.append(this_sta_dict)
        db_adopt.free()
        return adopt_list
        # 

    def process_active_stations(self, field_list):
        """Process currently active
        stations
        """
        # process_active_stations
        all_snets = self.pf['network']
        all_colors = self.pf['colors']
        if field_list == 'detail':
            fields = detail_dbmaster_fields
        elif field_list == 'summary':
            fields = active_fields
        active_list = []
        db_active = self.deploy_dbptr.subset('offdate == NULL || offdate >= now()')
        db_active = db_active.subset('offdate == NULL || offdate >= now()')
        db_active = db_active.subset('endtime >= now()')
        db_active = db_active.subset('time <= now()')
        db_active = db_active.subset('comm.endtime == NULL || comm.endtime >= now()')
        db_active = db_active.subset('sensor.endtime == NULL || sensor.endtime >= now()')
        db_active = db_active.subset('insname != NULL')
        db_active = db_active.sort(("sta"), unique=True)
        if self.verbose:
            logfmt("process_active_stations(): Process %d stations" % db_active.query('dbRECORD_COUNT'))
        for i in range(db_active.query('dbRECORD_COUNT')):
            db_active.record = i
            sta = db_active.getv('sta')[0]
            this_sta_dict = {}
            this_sta_dict['type'] = "Feature" # GEOJSON
            this_sta_dict['id'] = sta # GEOJSON
            this_sta_dict['properties'] = {} # GEOJSON
            this_sta_dict['geometry'] = { "type": "Point", "coordinates":[] } # GEOJSON
            for af in fields:
                af_obj = self.field_definitions(db_active, af)
                af_readable_field = af + '_readable'
                if af == 'provider' or af == 'commtype':
                    this_sta_dict['properties'][af] = {}
                    this_sta_dict['properties'][af]['value'] = af_obj['readable']
                    this_sta_dict['properties'][af]['css'] = af_obj['css']
                elif af == 'snet':
                    this_color = all_snets[af_obj[af_readable_field]]['color']
                    this_sta_dict['properties']['snethexi'] = all_colors[this_color]['hexidecimal']
                    this_sta_dict['properties'][af] = af_obj[af_readable_field]
                else:
                    this_sta_dict['properties'][af] = af_obj[af_readable_field]
            this_sta_dict['geometry']['coordinates'].append(this_sta_dict['properties']['lon']) # GEOJSON
            this_sta_dict['geometry']['coordinates'].append(this_sta_dict['properties']['lat']) # GEOJSON
            active_list.append(this_sta_dict)
        db_active.free()
        return active_list
        # 

    def baler_history(self):
        """Retrieve and return
        baler history depending
        on query type
        """
        # baler_history
        if self.verbose:
            logfmt("baler_history(): Working on all stations")
        baler_dict = defaultdict(lambda: defaultdict(dict))
        stabaler_ptr = self.db.lookup(table='stabaler')
        stabaler_ptr = stabaler_ptr.sort(('dlsta','time'))
        try:
            baler_dict = self.process_grouped_records(stabaler_ptr,
                                                      'dlsta',
                                                      detail_baler_fields)
        except LookupError,e:
            logfmt('baler_history(): LookupError: %s' % (e))
        stabaler_ptr.free()
        return baler_dict
        # 

    def process_grouped_records(self, dbpt, dict_key, my_fields):
        """Process groups of records
        Use a list - simplest to sort
        """
        # process_grouped_records
        my_dict = defaultdict(list)
        my_group = dbpt.group(dict_key)
        if my_group.query('dbRECORD_COUNT') > 0:
            for i in range(my_group.query('dbRECORD_COUNT')):
                my_group.record = i
                my_dict_key, [db, view, end_rec, start_rec] = my_group.getv(dict_key, 'bundle')
                # my_bundle is a list describing a view where
                # [db, view, end_rec, start_rec]
                for j in range(start_rec, end_rec):
                    dbpt.record = j
                    my_sub_dict = defaultdict()
                    for f in my_fields:
                        my_f_obj = self.field_definitions(dbpt, f)
                        readable_field = '%s_readable' % f
                        my_sub_dict[f] = my_f_obj[readable_field]
                    my_dict[my_dict_key].append(my_sub_dict)
            return my_dict
        else:
            raise LookupError('No groupable records for this station')
        # 

    def infrasound_sensors(self, imap):
        """Determine what infrasound sensors are installed for both
        summary JSON and detailed station JSON files
        Kind of a mess right now due to how the channels map to one
        or more sensors, so we have to have a 'holder' list 
        and then get unique values of that list to append and return
        This is a little more complex than the usual grouped
        records, so cannot use utility function process_grouped_records()
        """
        # infrasound_sensors
        # Build the Datascope query str
        qstr = '|'.join([ '|'.join(v) for k,v in imap.iteritems()])
        if self.verbose:
            logfmt("\tinfrasound_sensors(): Sitechan subset w/ regex: %s" % qstr)
        infrasound_history = defaultdict(lambda: defaultdict(dict))
        infra_hist_dbptr = self.db.lookup(table='sitechan')
        try:
            infra_hist_dbptr = infra_hist_dbptr.subset('chan=~/(%s)/' % qstr)
        except Exception,e:
            logfmt("\tinfrasound_sensors(): Exception %s" % e)
        else:
            if self.debug:
                logfmt("\tinfrasound_sensors(): Process %d records" % infra_hist_dbptr.query('dbRECORD_COUNT'))
            infra_hist_dbptr = infra_hist_dbptr.sort(('sta', 'ondate', 'chan'))
            infra_hist_grp_dbptr = infra_hist_dbptr.group('sta')
            for i in range(infra_hist_grp_dbptr.query('dbRECORD_COUNT')):
                infra_hist_grp_dbptr.record = i
                sta, [db, view, end_rec, start_rec] = infra_hist_grp_dbptr.getv('sta', 'bundle')
                # Generate all keys for the dictionary
                if self.verbose:
                    logfmt("\tinfrasound_sensors(): Processing station %s" % sta)
                infrasound_history[sta] = {'current':[], 'history':{}}
                infrachans_history_holder = []
                # Process all records per station
                for j in range(start_rec, end_rec):
                    infra_hist_dbptr.record = j
                    my_sub_dict = defaultdict()
                    ondate, offdate, chan = infra_hist_dbptr.getv('ondate', 'offdate', 'chan')
                    my_sub_dict['ondate'] = ondate
                    my_sub_dict['chan'] = chan
                    for sentype, senchans in imap.iteritems():
                        if chan in senchans:
                            infra_sensor = sentype
                    my_sub_dict['sensor'] = infra_sensor
                    if self.debug and (sta == '442A' or sta == '214A' or sta == 'MDND'):
                        logfmt('infrasound_sensors(): Debugging using 442A, 214A, MDND')
                        logfmt(infrasound_history[sta]['current'])
                    if offdate == self.dbmeta['offdate']['null']:
                        offdate = 'N/A'
                        if not infra_sensor in infrasound_history[sta]['current']:
                            infrasound_history[sta]['current'].append(infra_sensor)
                    else:
                        if infra_sensor in infrasound_history[sta]['current']:
                            infrasound_history[sta]['current'].remove(infra_sensor)
                    my_sub_dict['offdate'] = offdate
                    infrachans_history_holder.append(my_sub_dict)

                infrasound_history[sta]['history'] = infrachans_history_holder

                if ('MEMS' in infrasound_history[sta]['current']) and ('SETRA' in
                    infrasound_history[sta]['current']) and ('NCPA' in
                    infrasound_history[sta]['current']):
                    infrasound_history[sta]['current'] = 'complete'
                elif 'MEMS' in infrasound_history[sta]['current']:
                    infrasound_history[sta]['current'] = 'mems'
                else:
                    infrasound_history[sta]['current'] = 'none'
            infra_hist_grp_dbptr.free()
            infra_hist_dbptr.free()
            return infrasound_history
            # 

    def deployment_history(self):
        """Return the deployment
        history as a dictionary
        """
        # deployment_history
        if self.verbose:
            logfmt("deployment_history(): Working on all stations")
        deploy_hist_dict = defaultdict(list)
        # This ensures only one entry per time period
        deploy_ptr = self.deploy_dbptr.sort(('sta', 'time'),
                                      unique=True)
        deploy_grp_ptr = deploy_ptr.group('sta')
        for i in range(deploy_grp_ptr.query('dbRECORD_COUNT')):
            deploy_grp_ptr.record = i
            sta, [db, view, end_rec, start_rec] = deploy_grp_ptr.getv('sta',
                                                                      'bundle')
            # Only create dictionary entry if more than one deployment
            if (end_rec - start_rec) > 1:
                for j in range(start_rec, end_rec):
                    per_deploy_dict = defaultdict()
                    deploy_ptr.record = j
                    for ddhf in detail_deployment_hist_fields:
                        ddhf_obj = self.field_definitions(deploy_ptr, ddhf)
                        ddhf_readable_field = '%s_readable' % ddhf
                        per_deploy_dict[ddhf] = ddhf_obj[ddhf_readable_field]
                    deploy_hist_dict[sta].append(per_deploy_dict)
        deploy_grp_ptr.free()
        deploy_ptr.free()
        return deploy_hist_dict
        # 

    def comms_history(self):
        """Return the communications
        history as a dictionary
        """
        # comms_history
        if self.verbose:
            logfmt("comms_history(): Working on all stations")
        comms_dict = defaultdict(list)
        comms_ptr = self.db.lookup(table='comm')
        comms_ptr = comms_ptr.sort(('sta','time'))
        comms_grp_ptr = comms_ptr.group('sta')
        for i in range(comms_grp_ptr.query('dbRECORD_COUNT')):
            comms_grp_ptr.record = i
            sta, [db, view, end_rec, start_rec] = comms_grp_ptr.getv('sta',
                                                                     'bundle')
            for j in range(start_rec, end_rec):
                per_sta_comms_dict = defaultdict(dict)
                comms_ptr.record = j
                for dchf in detail_comms_hist_fields:
                    dchf_obj = self.field_definitions(comms_ptr, dchf)
                    dchf_readable_field = '%s_readable' % dchf
                    if dchf == 'provider' or dchf == 'commtype':
                        per_sta_comms_dict[dchf]['value'] = dchf_obj['readable']
                        per_sta_comms_dict[dchf]['css'] = dchf_obj['css']
                    else:
                        per_sta_comms_dict[dchf] = dchf_obj[dchf_readable_field]
                comms_dict[sta].append(per_sta_comms_dict)
        comms_grp_ptr.free()
        comms_ptr.free()
        return comms_dict
        # 

    def calibration_history(self, dbpath):
        """Return calibration history
        This is a little more complex than the usual grouped
        records, so cannot use utility function process_grouped_records()
        """
        # calibration_history
        calibration_dict = defaultdict(list)
        calib_ptr = datascope.dbopen(dbpath, 'r')
        calib_ptr = calib_ptr.lookup(table='calplot')
        calib_ptr = calib_ptr.sort(('sta', 'time'))
        calib_grp_ptr = calib_ptr.group('sta')
        if self.debug:
            logfmt("\tcalibration_history(): Process %d grouped records" % calib_grp_ptr.query('dbRECORD_COUNT'))
        for i in range(calib_grp_ptr.query('dbRECORD_COUNT')):
            calib_grp_ptr.record = i
            sta, [db, view, end_rec, start_rec] = calib_grp_ptr.getv('sta',
                                                                     'bundle')
            if self.debug:
                logfmt("\tcalibration_history(): Processing station %s" % sta)
            # Temporaray holder dictionary
            calib_holder = defaultdict(list)
            for j in range(start_rec, end_rec):
                calib_ptr.record = j
                chan, time = calib_ptr.getv('chan', 'time')
                time_int = int(time)
                if not time_int in calib_holder:
                    calib_holder[time_int] = []
                calib_holder[time_int].append({'chan':chan, 'file':calib_ptr.extfile()})
            # Sort the dictionary and append to list
            for key in sorted(calib_holder.iterkeys()):
                calibration_dict[sta].append({'time':key,'chanfiles':calib_holder[key]})
        calib_grp_ptr.free()
        calib_ptr.close()
        return calibration_dict
        # 

    def dlevents_history(self, dbpath):
        """Return all datalogger
        events for all stations
        as a dictionary
        """
        # dlevents_history
        if self.verbose:
            logfmt("dlevents_history(): Working on all stations")
        dlevents_dict = defaultdict(lambda: defaultdict(dict))
        dlevs_ptr = datascope.dbopen(dbpath, 'r')
        dlevs_ptr = dlevs_ptr.lookup(table='dlevent')
        dlevs_ptr = dlevs_ptr.sort(('dlname','time'))
        dlevs_grp_ptr = dlevs_ptr.group('dlname')
        for i in range(dlevs_grp_ptr.query('dbRECORD_COUNT')):
            dlevs_grp_ptr.record = i
            dlname, [db, view, end_rec, start_rec] = dlevs_grp_ptr.getv('dlname',
                                                                        'bundle')
            for j in range(start_rec, end_rec):
                dlevs_ptr.record = j
                time = dlevs_ptr.getv('time')[0]
                time_int = int(time)
                year, month = stock.epoch2str(time,"%Y_%L").split('_')
                month = month.strip()
                '''
                This deep a structure
                appears to kill defaultdict
                so revert to hand creation
                '''
                if year not in dlevents_dict[dlname]:
                    dlevents_dict[dlname][year] = {}
                if month not in dlevents_dict[dlname][year]:
                    dlevents_dict[dlname][year][month] = {}
                dlevents_dict[dlname][year][month][time_int] = {}
                for ddle in detail_dlevents:
                    my_ddle_obj = self.field_definitions(dlevs_ptr, ddle)
                    readable_field = '%s_readable' % ddle
                    try:
                        dlevents_dict[dlname][year][month][time_int][ddle] = my_ddle_obj[readable_field]
                    except Exception,e:
                        logfmt("dlevents_history(): Error: %s" % e)
                        pprint(dlevents_dict[dlname])
        dlevs_grp_ptr.free()
        dlevs_ptr.close()
        return dlevents_dict
        # 

    def sensor_readable(self, insname):
        """Use pf values to determine sensor values
        Force match to be a string in case of just int
        values in the regex
        """
        # sensor_readable
        smodel = False
        sclass = False
        l_insname = insname.lower()
        for k in self.pf['sensors']:
            for match in self.pf['sensors'][k]['regex']:
                if str(match) in l_insname:
                    smodel = self.pf['sensors'][k]['name']
                    sclass = k
        if not smodel:
            logfmt("sensor_readable(): Error: instrument %s is not one of the options!" % insname)
            smodel = 'unknown'
        if not sclass:
            sclass = 'unknown'
        return smodel, sclass
        # 

    def datalogger_readable(self, insname):
        """Use pf values to determine datalogger values
        Force match to be a string in case of just int
        values in the regex
        """
        # datalogger_readable
        dmodel = False
        dclass = False
        l_insname = insname.lower()
        for k in self.pf['dataloggers']:
            for match in self.pf['dataloggers'][k]['regex']:
                if str(match) in l_insname:
                    dmodel = self.pf['dataloggers'][k]['name']
                    dclass = k
        if not dmodel:
            logfmt("datalogger_readable(): Error: instrument %s is not one of the options!" % insname)
            dmodel = 'unknown'
        if not dclass:
            dclass = 'unknown'
        return dmodel, dclass
        # 

    def summary_instrument_history(self, sta_ins_hist, sta=False):
        """Parse and return the
        summary instrument
        history. There should always
        be at least one vertical (Z)
        channel. This will return
        something like the following:
        { 'datalogger': [
            [
                {'css': 'q330', 'idtag': '1532', 'model': 'Quanterra Q330', 'ssident': '0100000B69C47486'}
            ]
        ],
        'sensor': [
            [
                {'css': 'cmg', 'model': 'Guralp CMG-3T', 'ssident': 'T3K70'}
            ]
        ] }
        """
        # summary_instrument_history
        summary_grp = {'datalogger':[], 'sensor':[]}
        # Temporary holding dicts
        datalogger_hist = defaultdict(list)
        sensor_hist = defaultdict(list)

        for i in range(len(sta_ins_hist)):
            if 'Z' in sta_ins_hist[i]['channel']:
                ondate = sta_ins_hist[i]['ondate']
                if 'datalogger' in sta_ins_hist[i]:
                    datalogger_hist[ondate].append(sta_ins_hist[i]['datalogger'])
                if 'sensor' in sta_ins_hist[i]:
                    sensor_hist[ondate].append(sta_ins_hist[i]['sensor'])

        # Now loop over dicts and return a (ordered) list
        for key in sorted(datalogger_hist.iterkeys()):
            summary_grp['datalogger'].append(datalogger_hist[key])
        for key in sorted(sensor_hist.iterkeys()):
            summary_grp['sensor'].append(sensor_hist[key])

        if self.debug:
            pprint(summary_grp)

        if len(summary_grp['datalogger']) == 0:
            raise LookupError('No datalogger summary available')
        else:
            return summary_grp
        # 

    #  NetworkSummary

def main():
    """Main processing script
    for all JSON summary & individual
    files
    """
    # main
    verbose, debug, zipper, subtype, db2jsonpf = configure()

    if debug:
        logfmt("*** DEBUGGING MODE")

    stations_pf = 'stations.pf'

    if verbose or debug:
        logfmt("Parse stations configuration parameter file (%s)" % stations_pf)

    pf = stock.pfupdate(stations_pf)
    stapf = defaultdict()
    stapf['network'] = pf['network']
    stapf['provider'] = pf['comms_provider']
    stapf['comms'] = pf['comms_type']
    stapf['dataloggers'] = pf['datalogger']
    stapf['sensors'] = pf['sensor']
    stapf['colors'] = pf['colors']

    common_pf = 'common.pf'

    if verbose or debug:
        logfmt("Parse configuration parameter file (%s)" % common_pf)

    pf = stock.pfupdate(common_pf)
    json_path = '%s/stations' % pf['CACHEJSON']
    all_stations_json_file = '%s/stations_geo.json' % json_path
    dbmaster = pf['USARRAY_DBMASTER']
    tables_to_check = pf['USARRAY_CHECK_TABLES']
    q330comms = pf['USARRAY_Q330COMMS']
    orb = pf['USARRAY_ORB']
    orb_stations_select  = pf['USARRAY_ORB_STATIONS_SELECT']
    cascadia_orb = pf['CASCADIA_ORB']
    cascadia_orb_stations_select = pf['CASCADIA_ORB_STATIONS_SELECT']
    orbstat_alerts = pf['ORBSTAT_ALERTS']
    infrasound_mapping = pf['INFRASOUND_MAPPING']
    if verbose or debug:
        logfmt("Infrasound mapping:")
        print "\t", infrasound_mapping
    dbcalibrations = pf['DBCALIB']
    dbops_q330 = pf['DBOPS_Q330']
    landowner_dir = "%s_local" % pf['CACHE_REPORTS_LANDOWNER']
    station_digest_dir = "%s_local" % pf['CACHE_REPORTS_STATION_DIGEST']

    # Parse deployment specific option from db2json
    override_subset = False
    auth_snet = False
    adoptions = False
    balers = False
    infrasound = False
    calibrations = False
    dlevents = False
    encoding = False

    if verbose or debug:
        logfmt("Parse configuration parameter file (%s)" % db2jsonpf)

    pf = stock.pfupdate(db2jsonpf)
    try:
        override_subset = pf['override_subset']
    except Exception, e:
        logfmt("No 'override_subset' defined in pf '%s'" % db2jsonpf)

    try:
        auth_snet = pf['auth_snet']
    except Exception, e:
        logfmt("No 'auth_snet' defined in pf '%s'" % db2jsonpf)

    try:
        adoptions = pf['adoptions']
    except Exception, e:
        logfmt("No 'adoptions' defined in pf '%s'" % db2jsonpf)

    try:
        balers = pf['balers']
    except Exception, e:
        logfmt("No 'balers' defined in pf '%s'" % db2jsonpf)

    try:
        infrasound = pf['infrasound']
    except Exception, e:
        logfmt("No 'infrasound' defined in pf '%s'" % db2jsonpf)

    try:
        calibrations = pf['calibrations']
    except Exception, e:
        logfmt("No 'calibrations' defined in pf '%s'" % db2jsonpf)

    try:
        dlevents = pf['dlevents']
    except Exception, e:
        logfmt("No 'dlevents' defined in pf '%s'" % db2jsonpf)

    try:
        all_stations_json_file = pf['json_out']
    except Exception, e:
        logfmt("No 'json_out' defined in pf '%s'" % db2jsonpf)

    try:
        encoding = pf['encoding']
    except Exception, e:
        logfmt("No 'encoding' defined in pf '%s'. Using default (UTF-8)" % db2jsonpf)

    if verbose or debug:
        logfmt("Dbmaster path '%s'" % dbmaster)
        logfmt("Orb path '%s'" % orb)
        if auth_snet:
            logfmt("Authoritative network: '%s'" % auth_snet)
        print_select_statement(orb_stations_select)

    nfs_test(dbmaster)

    myorb = ParseOrb(orbstat_alerts, verbose, debug)
    orbstatus = defaultdict()
    orbstatus.update(myorb.orb_interaction(orb, orb_stations_select))
    orbstatus.update(myorb.orb_interaction(cascadia_orb, cascadia_orb_stations_select))

    db = NetworkSummary(dbmaster, stapf, verbose, debug)

    db.open_db()

    if not db.table_test(tables_to_check, all_stations_json_file):
        db.close_db()
        if verbose or debug:
             logfmt("**** Database tables not updated since JSON files last created. Aborting.")
    else:

        logfmt("Summary JSON file processing")
        db.get_metadata()

        db.create_deploy_pointer(override_subset)
        station_dict['decom'] = db.process_decom_stations('summary', adoptions)
        if adoptions:
            station_dict['adopt'] = db.process_adopted_stations('summary')
        station_dict['active'] = db.process_active_stations('summary')
        instrument_history = db.create_instrument_history(override_subset)
        if balers:
            baler_history = db.baler_history()
        if infrasound:
            infrasound_history = db.infrasound_sensors(infrasound_mapping)

        logfmt("Decom stations: Add most recent instrument & baler history")
        for i, item in enumerate(station_dict['decom']):
            sta = station_dict['decom'][i]['id']
            snet = station_dict['decom'][i]['properties']['snet']
            dlsta = '%s_%s' % (snet, sta)
            if verbose or debug:
                logfmt("\tProcessing decom station: %s" % sta)
            if snet == auth_snet:

                try:
                    summary_instrument = db.summary_instrument_history(instrument_history[sta], sta)
                except LookupError,e:
                    logfmt("\tsummary_instrument_history(): LookupError: %s" % e)
                else:
                    # More than one sensor allowed. Only one datalogger allowed
                    station_dict['decom'][i]['properties']['sensor'] = []
                    station_dict['decom'][i]['properties']['datalogger'] = {}
                    pprint(station_dict['decom'][i])
                    for j in range(len(summary_instrument['sensor'][-1])):
                        station_dict['decom'][i]['properties']['sensor'].append({
                            'value':summary_instrument['sensor'][-1][j]['model'], 
                            'css':summary_instrument['sensor'][-1][j]['css'],
                            'ssident':summary_instrument['sensor'][-1][j]['ssident']
                        })

                    station_dict['decom'][i]['properties']['datalogger']['value'] = summary_instrument['datalogger'][-1][-1]['model']
                    station_dict['decom'][i]['properties']['datalogger']['css'] = summary_instrument['datalogger'][-1][-1]['css']
                    station_dict['decom'][i]['properties']['datalogger']['idtag'] = summary_instrument['datalogger'][-1][-1]['idtag']

                if balers and dlsta in baler_history:
                    station_dict['decom'][i]['properties']['baler'] = baler_history[dlsta][-1]
                # Need this for most recent sensor in top right
                if infrasound and sta in infrasound_history:
                    if 'current' in infrasound_history[sta]:
                        station_dict['decom'][i]['properties']['infrasound'] = infrasound_history[sta]['current']
                    else:
                        station_dict['decom'][i]['properties']['infrasound'] = infrasound_history[sta]['history'][-1]
                else:
                    station_dict['decom'][i]['properties']['infrasound'] = 'unknown'

        logfmt("Active stations: Add most recent instrument & baler history")
        for i, item in enumerate(station_dict['active']):
            sta = station_dict['active'][i]['id']
            snet = station_dict['active'][i]['properties']['snet']
            dlsta = '%s_%s' % (snet, sta)
            if verbose:
                logfmt("\tProcessing active station: %s" % sta)
            station_dict['active'][i]['properties']['orbstat'] = myorb.add_orbstat(orbstatus, sta)
            if snet == auth_snet:
                try:
                    summary_instrument = db.summary_instrument_history(instrument_history[sta], sta)
                except LookupError,e:
                    logfmt("\tsummary_instrument_history(): LookupError: %s" % e)
                else:
                    # More than one sensor allowed. Only one datalogger allowed
                    station_dict['active'][i]['properties']['sensor'] = []
                    station_dict['active'][i]['properties']['datalogger'] = {}
                    for j in range(len(summary_instrument['sensor'][-1])):
                        station_dict['active'][i]['properties']['sensor'].append({
                            'value':summary_instrument['sensor'][-1][j]['model'], 
                            'css':summary_instrument['sensor'][-1][j]['css'],
                            'ssident':summary_instrument['sensor'][-1][j]['ssident']
                    })

                    station_dict['active'][i]['properties']['datalogger']['value'] = summary_instrument['datalogger'][-1][-1]['model']
                    station_dict['active'][i]['properties']['datalogger']['css'] = summary_instrument['datalogger'][-1][-1]['css']
                    station_dict['active'][i]['properties']['datalogger']['idtag'] = summary_instrument['datalogger'][-1][-1]['idtag']

                if infrasound and sta in infrasound_history:
                    station_dict['active'][i]['properties']['infrasound'] = infrasound_history[sta]['current']
                else:
                    station_dict['active'][i]['properties']['infrasound'] = 'unknown'
                if balers and dlsta in baler_history:
                    station_dict['active'][i]['properties']['baler'] = baler_history[dlsta][-1]
            else:
                station_dict['active'][i]['properties']['infrasound'] = 'unknown'
                station_dict['active'][i]['properties']['baler'] = 'unknown'
        db.close_db()


        geodict = {
            "type": "FeatureCollection",
            "id": "Active",
            "features": station_dict['active'],
        }

        if verbose or debug:
            logfmt("Dump summary JSON file for all stations")
        f = open(all_stations_json_file+'+', 'w') 

        if encoding:
            try:
                # json.dump(station_dict, f, sort_keys=True, indent=2, encoding=encoding)
                json.dump(geodict, f, sort_keys=True, indent=2, encoding=encoding)
            except Exception, e: 
                logfmt("JSON encoding error for '%s': %s -, %s" % (encoding, Exception, e))
        else:
            # json.dump(station_dict, f, sort_keys=True, indent=2)
            json.dump(geodict, f, sort_keys=True, indent=2)

        f.flush()

        try:
            os.rename(all_stations_json_file+'+', all_stations_json_file)
        except OSError,e:
            logfmt("\tCannot rename summary JSON file. Error: %s-%s" % (OSError, e))

        if zipper:
            if verbose or debug:
                logfmt("\tCreate gzip file: %s.gz" % all_stations_json_file)
            zip_me_up(all_stations_json_file)

    return 0
    # 

if __name__ == '__main__':
    status = main()
    sys.exit(status)
