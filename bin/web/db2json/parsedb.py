"""
Class ParseDB from db2json script.

Will be loaded into script and 
not called directly.

Juan Reyes
reyes@ucsd.edu

"""

from __main__ import *

def log(message):
    """Format our print commands

    Prepend  a timestamp and the name of the
    script to the log msg.

    """
    curtime = stock.epoch2str(stock.now(),"%d(%j)%H:%M:%S")
    print "%s db2json: %s" % (curtime, message)

class ParseDB:
    """Methods for determining
    values of network and stations
    for JSON file(s)
    """

    def __init__(self, dbname, config, db_subset, verbose=False):
        """Initialize database pointers
        """
        log("ParseDB(%s)" % dbname)
        self.db = False
        self.dbname = dbname
        self.q330comm_ptr = dbname
        self.config = config
        self.verbose = verbose
        self.deploy_dbptr = False
        self.db_subset = db_subset

        try:
            self.db = datascope.dbopen(dbname, 'r')
        except Exception,e:
            sys.exit("Cannot open database '%s'. Exception %s" % (dbname, e))

        if not self.db:
            sys.exit("Cannot open database '%s'. Empty pointer %s" % (dbname, self.db))

        try:
            self.q330comm_ptr = datascope.dblookup(self.db, '', 'q330comm', '', '')
        except Exception,e:
            sys.exit("Cannot open table q330comm '%s'. Exception %s" % (dbname, e))

        self.get_css_metadata()
        #self.create_deploy_pointer()


    #def open(self):
    #    """Test that the database
    #    pointer is valid
    #    """
    #    log("Start open_db [%s]" % self.dbname)

    #    try:
    #        self.db = datascope.dbopen(self.dbname, 'r')
    #        log("done opening db %s" % self.db)
    #    except Exception,e:
    #        sys.exit("Cannot open database '%s'. Caught exception %s" % (self.db, e))

    #    log("Success at open_db")

    #def free(self):
    #    """Free the open database pointer.
    #    """

    #    log("free(%s) %s" % (self.dbname,self.db))

    #    if self.db:
    #        try:
    #            self.db.free()
    #            #datascope.dbclose(self.db)
    #        except Exception,e:
    #            log("Cannot free database '%s'. Caught exception %s" % (self.db, e))

    #def close_db(self):
    #    """Close the open database 
    #    pointer. This will free() all
    #    dbpointers in memory
    #    """

    #    log("close_db(%s) %s" % (self.dbname,self.db))

    #    if self.db:
    #        try:
    #            self.db.close()
    #            #datascope.dbclose(self.db)
    #        except Exception,e:
    #            log("Cannot close database '%s'. Caught exception %s" % (self.db, e))

    def table_test(self, tables_to_check, json_file):
        """Test modification time

        Verify if database tables need an update.

        """

        if self.verbose:
            log("Test for modification time of tables:")

        #try:
        #    db = datascope.dbopen(self.dbname, 'r')
        #except Exception,e:
        #    sys.exit("Cannot open database '%s'. Caught exception %s" % (self.dbname, e))

        table_modification_times = []
        for table in tables_to_check:
            table_ptr = datascope.dblookup(self.db, '', table, '', '')
            table_stats = os.stat(table_ptr.query('dbTABLE_FILENAME'))
            table_age = table_stats.st_mtime

            log("\tFile modification time of '%s' table: %s" % (table, stock.epoch2str(table_age, "%Y-%m-%d %H:%M:%S")))

            table_modification_times.append(table_age)
            datascope.dbfree(table_ptr)


        try:
            json_stats = os.stat(json_file)
        except Exception, e:
            log("Exception: %s. Recreate!" % e)
            return True

        log("\tJSON time of '%s': %s" % (json_file, stock.epoch2str(json_stats.st_mtime, "%Y-%m-%d %H:%M:%S")))

        if max(table_modification_times) > json_stats.st_mtime:
            return True

        return False


    def idtag_determiner(self, dlogger_id):
        """The idtag field is only
        in dlsite, staq330 and q330comm
        tables. Dlsite is depreciated,
        q330comm first used 2006.
        Try q330comm first.
        """

        #self.q330cmm_ptr = datascope.dblookup(self.db, '', 'q330comm', '', '')
        #dbptr = datascope.dblookup(self.db, '', 'q330comm', '', '')
        #dbptr[3] = dbptr.find('ssident=~/%s/' % dlogger_id)

        self.q330comm_ptr[3] = self.q330comm_ptr.find('ssident=~/%s/' % dlogger_id)

        if self.q330comm_ptr[3] > -1:
            idtag = self.q330comm_ptr.getv('idtag')[0]
        else:
            log("Cannot find ssident=~/%s/ in q330comm table" % dlogger_id)
            idtag = 'N/A'

        #dbptr.free()

        return idtag


    def create_instrument_history(self, db_subset=False):
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
        log("create_instrument_history(): start")
        #  create_instrument_history
        if self.verbose:
            log("create_instrument_history(): Use db_subset if def")
            log("create_instrument_history(): Parse dlsensor tbl into dict")

        #try:
        #    db = datascope.dbopen(self.dbname, 'r')
        #except Exception,e:
        #    sys.exit("Cannot open database '%s'. Caught exception %s" % (self.dbname, e))

        # Get dlsensor table into simple per snident_dlident keyed dict
        dlsensor_history = defaultdict(lambda: defaultdict(dict))
        dlsensor_hist_dbptr = datascope.dblookup(self.db, '', 'dlsensor', '', '')

        for i in range(dlsensor_hist_dbptr.query('dbRECORD_COUNT')):
            dlsensor_hist_dbptr[3] = i
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

        if self.verbose:
            log("create_instrument_history(): Parse sitechan, snetsta")

        instrument_history = defaultdict(list)

        sitechan_hist_dbptr = datascope.dblookup(self.db, '', 'sitechan', '', '')
        sitechan_hist_dbptr = sitechan_hist_dbptr.join('snetsta')
        sitechan_hist_dbptr = sitechan_hist_dbptr.join('sensor')
        sitechan_hist_dbptr = sitechan_hist_dbptr.join('instrument')

        if db_subset:
            log('create_instrument_history(): Apply db_subset(%s)' % db_subset)
            sitechan_hist_dbptr = sitechan_hist_dbptr.subset(db_subset)

        sitechan_hist_dbptr = sitechan_hist_dbptr.sort(('sta', 'ondate', 'chan'))

        log("\t\tRECORDS %s" % sitechan_hist_dbptr.query('dbRECORD_COUNT'))


        # Handle multiple sensors here
        sitechan_hist_grp_dbptr = datascope.dbgroup(sitechan_hist_dbptr, 'sta')

        for i in range(sitechan_hist_grp_dbptr.query('dbRECORD_COUNT')):

            sitechan_hist_grp_dbptr[3] = i
            (sta, [dbbundle, view, end_rec, start_rec]) = sitechan_hist_grp_dbptr.getv('sta', 'bundle')

            if self.verbose:
                log("\tcreate_instrument_history(): %s" % sta)

            #log("\tcreate_instrument_history(): %s [%s,%s]" % (sta,start_rec,end_rec))
            for j in range(start_rec, end_rec):
                sitechan_hist_dbptr[3] = j
                #log("\t\t%s" % j)
                #log("\t\ttable %s" % sitechan_hist_dbptr.query('dbTABLE_PRESENT'))
                #log("\t\t%s" % sitechan_hist_dbptr)
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
                #log("\t\t%s %s %s %s %s %s %s" % (site_chan, site_ondate, 
                #        site_offdate, site_descrip,
                #        site_hang, site_vang, site_insname))
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
                #log("\t\ttable %s" % sitechan_hist_dbptr.query('dbTABLE_PRESENT'))
                if site_descrip != '' and len(site_descrip) > 1:
                    #log("\t\tsite_descrip")
                    site_sensorid, site_dloggerid = site_descrip.split()
                    if site_descrip in dlsensor_history:
                        #log("\t\tsite_descrip in dlsensor_history")
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
                        #log("\t\tsite_descrip NOT in dlsensor_history")
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
                #log("\t\ttable %s" % sitechan_hist_dbptr.query('dbTABLE_PRESENT'))
                instrument_history[sta].append(ins_hist_obj)
                #log("\t\t\t %s" % ins_hist_obj)

        #sitechan_hist_grp_dbptr.free()
        #sitechan_hist_dbptr.free()

        #db.free()
        log("create_instrument_history(): done")

        return instrument_history
        # 

    def close_deploy_pointer(self):
        """Clean memory of pointer

        """
        log("close_deploy_pointer(): start")

        try:
            datascope.dbfree(self.deploy_dbptr)
        except Exception,e:
            sys.exit("Cannot close database '%s'. Caught exception %s" % (self.dbname, e))


        log("close_deploy_pointer(): done")

        return

    def create_deploy_pointer(self, db_subset=False):
        """Create a pointer to the
        simple joined view of deployment
        Add ability to define an override
        subset to just get certain stations 
        of interest
        """

        #try:
        #    db = datascope.dbopen(self.dbname, 'r')
        #except Exception,e:
        #    sys.exit("Cannot open database '%s'. Caught exception %s" % (self.dbname, e))

        log("create_deploy_pointer(): start")
        log("self.db(): %s" % self.db )

        self.deploy_dbptr = datascope.dblookup(self.db, '', 'deployment', '', '')
        self.deploy_dbptr = self.deploy_dbptr.join('site', outer=True)
        self.deploy_dbptr = self.deploy_dbptr.join('snetsta', outer=True)
        self.deploy_dbptr = self.deploy_dbptr.join('sitechan', outer=True)
        self.deploy_dbptr = self.deploy_dbptr.join('comm', outer=True)
        self.deploy_dbptr = self.deploy_dbptr.join('sensor', outer=True)
        self.deploy_dbptr = self.deploy_dbptr.join('instrument', outer=True)

        if db_subset:
            log('create_deploy_pointer(): Apply db_subset(%s)' % db_subset)
            self.deploy_dbptr = self.deploy_dbptr.subset(db_subset)

        #if self.verbose:
        if True:
            log('Number of records: %d' % self.deploy_dbptr.query('dbRECORD_COUNT'))

        log("self.deploy_dbptr(): %s" % self.deploy_dbptr )
        log("create_deploy_pointer(): done")

        return


    def get_css_metadata(self):
        """Get all the meta data values for
        all fields of a database pointer, 
        including dbNULL, dbFIELD_DETAIL,
        dbFIELD_DESCRIPTION, dbFIELD_TYPE
        """

        if self.verbose:
            log("Determine field nulls, detail, desc and types for schema")

        self.dbmeta = defaultdict(dict)

        #try:
        #    db = datascope.dbopen(self.dbname, 'r')
        #except Exception,e:
        #    sys.exit("Cannot open database '%s'. Caught exception %s" % (self.dbname, e))

        for table in self.db.query('dbSCHEMA_TABLES'):
            #log('table: %s' % table)
            dbtable = self.db.lookup('',table,'','dbNULL')
            for field in dbtable.query('dbTABLE_FIELDS'):
                #log('\tfield: %s' % field)
                if field not in self.dbmeta:
                    self.dbmeta[field] = {  'null':'',
                                            'detail':'',
                                            'description':'',
                                            'field_type':''  }

                    #log('\t\t%s %s %s %s' % (dbtable[0],dbtable[1],dbtable[2],dbtable[3]))
                    try:
                        #log('\t\tgetv: %s' % dbtable.getv(field))

                        self.dbmeta[field]['null'] = dbtable.getv(field)[0]
                        self.dbmeta[field]['detail'] = dbtable.query('dbFIELD_DETAIL')
                        self.dbmeta[field]['description'] = dbtable.query('dbFIELD_DESCRIPTION')
                        self.dbmeta[field]['field_type'] = dbtable.query('dbFIELD_TYPE')
                    except:
                        self.dbmeta[field]['null'] = '-' 
                        self.dbmeta[field]['detail'] = '-'
                        self.dbmeta[field]['description'] = '-'
                        self.dbmeta[field]['field_type'] = '-'

            #dbtable.free()

        #db.free()

        return


    def field_definitions(self, dbptr, field):
        """Define what each field key
        should be and what it should return
        """
        #  field_definitions
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
                field_object[field_readable] = stock.epoch2str(stock.epoch(value), "%Y-%m-%d")
            else:
                field_object[field_readable] = value
            # Deal with specialized fields that have their own CSS
            if field == 'commtype':
                field_format = value.lower()
                field_format = field_format.replace(' ','_')
                if field_format not in self.config['comms']:
                    log("Commtype '%s' not in pf_comms_list!" % field_format)
                    field_object['readable'] = 'unknown'
                    field_object['css'] = 'unknown'
                else:
                    pf_field_readable = self.config['comms'][field_format]['name']
                    field_object['readable'] = pf_field_readable
                    field_object['css'] = field_format
            elif field == 'provider':
                field_format = value.lower()
                field_format = field_format.replace(' ','_')
                field_format = field_format.replace('/','_')
                field_format = field_format.strip("'")
                if field_format not in self.config['provider']:
                    log("Provider '%s' not in pf_provider_list!" % field_format)
                    field_object['readable'] = 'unknown'
                    field_object['css'] = 'unknown'
                else:
                    pf_field_readable = self.config['provider'][field_format]['name']
                    field_object['readable'] = pf_field_readable
                    field_object['css'] = field_format

        field_object['field'] = field
        field_object['detail'] = detail
        field_object['description'] = description
        field_object['type'] = field_type
        field_object['null'] = null
        field_object['value'] = value
        if self.verbose:
            log(field_object)

        return field_object

    def process_decom_stations(self, field_list, adoptions=False):
        """Process just decommissioned stations
        """
        self.create_deploy_pointer()

        log("process_decom_stations(): start %s " % field_list)

        if field_list == 'detail':
            fields = detail_dbmaster_fields
        elif field_list == 'summary':
            fields = decom_fields

        decom_dict = defaultdict(lambda: defaultdict(dict))

        log("process_decom_stations(): subset  self.deploy_dbptr %s " % self.deploy_dbptr)
        db_decom = self.deploy_dbptr.subset('offdate != NULL || offdate < now()')
        db_decom = db_decom.subset('endtime < now()')

        if adoptions:
            db_decom = db_decom.join('adoption', pattern1=('sta'), outer=True)
            db_decom = db_decom.subset('atype == NULL')

        log("process_decom_stations(): sort (snet,sta)" )
        db_decom = db_decom.sort(['snet','sta'], unique=True)

        if self.verbose:
            log("process_decom_stations(): Process %d stations" % db_decom.query('dbRECORD_COUNT'))
        for i in range(db_decom.query('dbRECORD_COUNT')):
            db_decom[3] = i
            sta = db_decom.getv('sta')[0]
            log("process_decom_stations(): sta %s" % sta )
            for df in fields:
                df_obj = self.field_definitions(db_decom, df)
                df_readable_field = '%s_readable' % df
                if df == 'provider' or df == 'commtype':
                    decom_dict[sta][df]['value'] = df_obj['readable']
                    decom_dict[sta][df]['css'] = df_obj['css']
                else:
                    decom_dict[sta][df] = df_obj[df_readable_field]

        #db_decom.free()

        return decom_dict


    def process_adopted_stations(self, field_list):
        """Process just adopted stations
        """
        self.create_deploy_pointer()

        #  process_adopted_stations
        if field_list == 'detail':
            fields = detail_dbmaster_adopt_fields
        elif field_list == 'summary':
            fields = adopt_fields
        adopt_dict = defaultdict(lambda: defaultdict(dict))
        db_adopt = datascope.dbsubset(self.deploy_dbptr,
                                      'offdate != NULL || offdate < now()')
        db_adopt = db_adopt.subset('endtime < now()')
        db_adopt = db_adopt.sort(['snet', 'sta'])
        db_adopt = db_adopt.join('adoption', pattern1=('sta'), outer=True)
        db_adopt = db_adopt.subset('atype != NULL')
        db_adopt = db_adopt.sort(['snet', 'sta'])
        db_adopt = db_adopt.group('sta')
        if self.verbose:
            log("process_adopted_stations(): Process %d stations" % db_adopt.query('dbRECORD_COUNT'))
        for i in range(db_adopt.query('dbRECORD_COUNT')):
            db_adopt[3] = i
            sta = db_adopt.getv('sta')[0]
            dbptr_sub = datascope.dbsubset(db_adopt, 'sta =~ /%s/' % sta)
            dbptr_sub = dbptr_sub.ungroup()
            dbptr_sub = dbptr_sub.sort(["adoption.time"], reverse=True)
            dbptr_sub[3] = 0 # Only get the most recent deployment
            sta = dbptr_sub.getv('sta')[0]
            for adf in fields:
                adf_obj = self.field_definitions(dbptr_sub, adf)
                adf_readable_field = '%s_readable' % adf
                if adf == 'provider' or adf == 'commtype':
                    adopt_dict[sta][adf]['value'] = adf_obj['readable']
                    adopt_dict[sta][adf]['css'] = adf_obj['css']
                else:
                    adopt_dict[sta][adf] = adf_obj[adf_readable_field]

        #db_adopt.free()
        return adopt_dict
        # 

    def process_active_stations(self, field_list):
        """Process currently active
        stations
        """
        self.create_deploy_pointer()

        #  process_active_stations
        if field_list == 'detail':
            fields = detail_dbmaster_fields
        elif field_list == 'summary':
            fields = active_fields
        active_dict = defaultdict(lambda: defaultdict(dict))
        db_active = datascope.dbsubset(self.deploy_dbptr,
                                       'offdate == NULL || offdate >= now()')
        db_active = db_active.subset('offdate == NULL || offdate >= now()')
        db_active = db_active.subset('endtime >= now()')
        db_active = db_active.subset('time <= now()')
        db_active = db_active.subset('comm.endtime == NULL || comm.endtime >= now()')
        db_active = db_active.subset('sensor.endtime == NULL || sensor.endtime >= now()')
        db_active = db_active.subset('insname != NULL')
        db_active = db_active.sort(("sta"), unique=True)
        if self.verbose:
            log("process_active_stations(): Process %d stations" % db_active.query('dbRECORD_COUNT'))
        for i in range(db_active.query('dbRECORD_COUNT')):
            db_active[3] = i
            sta = db_active.getv('sta')[0]
            for af in fields:
                af_obj = self.field_definitions(db_active, af)
                af_readable_field = af + '_readable'
                if af == 'provider' or af == 'commtype':
                    active_dict[sta][af]['value'] = af_obj['readable']
                    active_dict[sta][af]['css'] = af_obj['css']
                else:
                    active_dict[sta][af] = af_obj[af_readable_field]

        #db_active.free()
        return active_dict
        # 

    def baler_history(self):
        """Retrieve and return
        baler history depending
        on query type
        """
        #try:
        #    db = datascope.dbopen(self.db, 'r')
        #except Exception,e:
        #    sys.exit("Cannot open database '%s'. Caught exception %s" % (self.db, e))

        #  baler_history
        log("baler_history(): start")
        if self.verbose:
            log("baler_history(): Working on all stations")
        baler_dict = defaultdict(lambda: defaultdict(dict))
        stabaler_ptr = datascope.dblookup(self.db,
                                          '', 'stabaler', '', '')
        stabaler_ptr = stabaler_ptr.sort(('dlsta','time'))
        try:
            baler_dict = self.process_grouped_records(stabaler_ptr,
                                                      'dlsta',
                                                      detail_baler_fields)
        except LookupError,e:
            log('baler_history(): LookupError: %s' % (e))
        log("baler_history(): done")

        #stabaler_ptr.free()

        return baler_dict


    def process_grouped_records(self, dbpt, dict_key, my_fields):
        """Process groups of records
        Use a list - simplest to sort
        """
        log("process_rouped_records(): start")
        #  process_grouped_records
        my_dict = defaultdict(list)
        my_group = datascope.dbgroup(dbpt, dict_key)
        if my_group.query('dbRECORD_COUNT') > 0:
            for i in range(my_group.query('dbRECORD_COUNT')):
                my_group[3] = i
                my_dict_key, [db, view, end_rec, start_rec] = my_group.getv(dict_key, 'bundle')
                # my_bundle is a list describing a view where
                # [db, view, end_rec, start_rec]
                for j in range(start_rec, end_rec):
                    dbpt[3] = j
                    my_sub_dict = defaultdict()
                    for f in my_fields:
                        my_f_obj = self.field_definitions(dbpt, f)
                        readable_field = '%s_readable' % f
                        my_sub_dict[f] = my_f_obj[readable_field]
                    my_dict[my_dict_key].append(my_sub_dict)
            return my_dict
        else:
            raise LookupError('No groupable records for this station')
        log("process_rouped_records(): done")
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
        log("infrasound_sensors(): start")

        #try:
        #    db = datascope.dbopen(self.db, 'r')
        #except Exception,e:
        #    sys.exit("Cannot open database '%s'. Caught exception %s" % (self.db, e))

        #  infrasound_sensors
        # Build the Datascope query str
        qstr = '|'.join([ '|'.join(v) for k,v in imap.iteritems()])
        if self.verbose:
            log("\tinfrasound_sensors(): Sitechan subset w/ regex: %s" % qstr)
        infrasound_history = defaultdict(lambda: defaultdict(dict))
        infra_hist_dbptr = datascope.dblookup(self.db, 
                                              '', 'sitechan', '', '')
        try:
            infra_hist_dbptr = infra_hist_dbptr.subset('chan=~/(%s)/' % qstr)
        except Exception,e:
            log("\tinfrasound_sensors(): Exception %s" % e)
            return
        if self.verbose:
            log("\tinfrasound_sensors(): Process %d records" % infra_hist_dbptr.query('dbRECORD_COUNT'))
        infra_hist_dbptr = infra_hist_dbptr.sort(('sta', 'ondate', 'chan'))
        infra_hist_grp_dbptr = datascope.dbgroup(infra_hist_dbptr, 'sta')
        for i in range(infra_hist_grp_dbptr.query('dbRECORD_COUNT')):
            infra_hist_grp_dbptr[3] = i
            sta, [db, view, end_rec, start_rec] = infra_hist_grp_dbptr.getv('sta', 'bundle')
            # Generate all keys for the dictionary
            if self.verbose:
                log("\tinfrasound_sensors(): Processing station %s" % sta)
            infrasound_history[sta] = {'current':[], 'history':{}}
            infrachans_history_holder = []
            # Process all records per station
            for j in range(start_rec, end_rec):
                infra_hist_dbptr[3] = j
                my_sub_dict = defaultdict()
                ondate, offdate, chan = infra_hist_dbptr.getv('ondate', 'offdate', 'chan')
                my_sub_dict['ondate'] = ondate
                my_sub_dict['chan'] = chan
                for sentype, senchans in imap.iteritems():
                    if chan in senchans:
                        infra_sensor = sentype
                my_sub_dict['sensor'] = infra_sensor
                if self.verbose and (sta == '442A' or sta == '214A' or sta == 'MDND'):
                    log('infrasound_sensors(): Debugging using 442A, 214A, MDND')
                    log(infrasound_history[sta]['current'])
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

        log("infrasound_sensors(): done")
        return infrasound_history

    def deployment_history(self):
        """Return the deployment
        history as a dictionary
        """
        log("deployment_history(): start")
        #  deployment_history
        if self.verbose:
            log("deployment_history(): Working on all stations")
        # This ensures only one entry per time period

        try:
            log("deployment_history(): build dict")
            deploy_hist_dict = defaultdict(list)
            log("deployment_history(): lookup calplot")
            deploy_ptr = self.db.lookup(table='deployment')
            log("deployment_history(): sort (sta,time) unique")
            deploy_ptr = deploy_ptr.sort(('sta', 'time'), unique=True)
        except Exception,e:
            log("\tdeployment_history(): Exception %s" % e)

        if self.verbose: log("deployment_history(): Group for stations")
        deploy_grp_ptr = datascope.dbgroup(deploy_ptr, 'sta')
        for i in range(deploy_grp_ptr.query('dbRECORD_COUNT')):
            deploy_grp_ptr[3] = i
            sta, [db, view, end_rec, start_rec] = deploy_grp_ptr.getv('sta',
                                                                      'bundle')
            if self.verbose: log("deployment_history(): For %s" % sta)
            # Only create dictionary entry if more than one deployment
            if (end_rec - start_rec) > 1:
                for j in range(start_rec, end_rec):
                    per_deploy_dict = defaultdict()
                    deploy_ptr[3] = j
                    for ddhf in detail_deployment_hist_fields:
                        ddhf_obj = self.field_definitions(deploy_ptr, ddhf)
                        ddhf_readable_field = '%s_readable' % ddhf
                        per_deploy_dict[ddhf] = ddhf_obj[ddhf_readable_field]
                    deploy_hist_dict[sta].append(per_deploy_dict)

        #deploy_grp_ptr.free()
        #deploy_ptr.free()
        log("deployment_history(): done")

        return deploy_hist_dict


    def comms_history(self):
        """Return the communications
        history as a dictionary
        """
        log("comms_history(): start")

        #try:
        #    db = datascope.dbopen(self.db, 'r')
        #except Exception,e:
        #    sys.exit("Cannot open database '%s'. Caught exception %s" % (self.db, e))

        #  comms_history
        if self.verbose:
            log("comms_history(): Working on all stations")
        comms_dict = defaultdict(list)
        comms_ptr = datascope.dblookup(self.db, '', 'comm', '', '')
        comms_ptr.sort(('sta','time'))
        comms_grp_ptr = datascope.dbgroup(comms_ptr, 'sta')
        for i in range(comms_grp_ptr.query('dbRECORD_COUNT')):
            comms_grp_ptr[3] = i
            sta, [db, view, end_rec, start_rec] = comms_grp_ptr.getv('sta',
                                                                     'bundle')
            for j in range(start_rec, end_rec):
                per_sta_comms_dict = defaultdict(dict)
                comms_ptr[3] = j
                for dchf in detail_comms_hist_fields:
                    dchf_obj = self.field_definitions(comms_ptr, dchf)
                    dchf_readable_field = '%s_readable' % dchf
                    if dchf == 'provider' or dchf == 'commtype':
                        per_sta_comms_dict[dchf]['value'] = dchf_obj['readable']
                        per_sta_comms_dict[dchf]['css'] = dchf_obj['css']
                    else:
                        per_sta_comms_dict[dchf] = dchf_obj[dchf_readable_field]
                comms_dict[sta].append(per_sta_comms_dict)

        #comms_grp_ptr.free()
        #comms_ptr.free()

        log("comms_history(): done")
        return comms_dict


    def calibration_history(self, dbpath):
        """Return calibration history
        This is a little more complex than the usual grouped
        records, so cannot use utility function process_grouped_records()
        """
        log("calibration_history(): start")
        #  calibration_history
        calibration_dict = defaultdict(list)
        try:
            log("calibration_history(): open db %s " % dbpath)
            calib_ptr = datascope.dbopen(dbpath, 'r')
            log("calibration_history(): lookup calplot")
            calib_ptr = calib_ptr.lookup(table='calplot')
            log("calibration_history(): sort ")
            calib_ptr = calib_ptr.sort(('sta', 'time'))
            log("calibration_history(): group ")
            calib_grp_ptr = datascope.dbgroup(calib_ptr, 'sta')
        except Exception, e:
            log("\tcalibration_history(): error %" % e)

        if self.verbose:
            log("\tcalibration_history(): Process %d grouped records" % calib_grp_ptr.query('dbRECORD_COUNT'))

        log("calibration_history(): dbREcord_COUNT %s" % calib_grp_ptr.query('dbRECORD_COUNT'))
        for i in range(calib_grp_ptr.query('dbRECORD_COUNT')):
            calib_grp_ptr[3] = i
            sta, [db, view, end_rec, start_rec] = calib_grp_ptr.getv('sta',
                                                                     'bundle')
            #if self.verbose:
            #    log("\tcalibration_history(): Processing station %s" % sta)
            log("\tcalibration_history(): Processing station %s" % sta)
            # Temporaray holder dictionary
            calib_holder = defaultdict(list)
            for j in range(start_rec, end_rec):
                calib_ptr[3] = j
                chan, time = calib_ptr.getv('chan', 'time')
                time_int = int(time)
                if not time_int in calib_holder:
                    calib_holder[time_int] = []
                calib_holder[time_int].append({'chan':chan, 'file':calib_ptr.extfile()})
            # Sort the dictionary and append to list
            for key in sorted(calib_holder.iterkeys()):
                calibration_dict[sta].append({'time':key,'chanfiles':calib_holder[key]})

        #calib_grp_ptr.free()
        #calib_ptr.free()

        log("calibration_history(): done")
        return calibration_dict
        # 

    def dlevents_history(self, dbpath):
        """Return all datalogger
        events for all stations
        as a dictionary
        """
        log("dlevents_history(): start")
        #  dlevents_history
        if self.verbose:
            log("dlevents_history(): Working on all stations")
        dlevents_dict = defaultdict(lambda: defaultdict(dict))
        log("dlevents_history(): open db %s " % dbpath)
        dlevs_ptr = datascope.dbopen(dbpath, 'r')
        log("dlevents_history():lookup dlevent ")
        dlevs_ptr = dlevs_ptr.lookup(table='dlevent')
        log("dlevents_history():sort time ")
        dlevs_ptr = dlevs_ptr.sort(('dlname','time'))
        log("dlevents_history(): dbgroup")
        dlevs_grp_ptr = datascope.dbgroup(dlevs_ptr, 'dlname')
        for i in range(dlevs_grp_ptr.query('dbRECORD_COUNT')):
            dlevs_grp_ptr[3] = i
            dlname, [db, view, end_rec, start_rec] = dlevs_grp_ptr.getv('dlname',
                                                                        'bundle')
            for j in range(start_rec, end_rec):
                dlevs_ptr[3] = j
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
                        log("dlevents_history(): Error: %s" % e)
                        pprint(dlevents_dict[dlname])

        #dlevs_grp_ptr.free()
        #dlevs_ptr.free()

        log("dlevents_history(): done")

        return dlevents_dict
        # 

    def sensor_readable(self, insname):
        """Use pf values to determine sensor values
        Force match to be a string in case of just int
        values in the regex
        """
        #  sensor_readable
        #smodel = False
        #sclass = False
        smodel = 'unknown'
        sclass = 'unknown'
        l_insname = insname.lower()

        try:
            for k in self.config['sensors']:
                #log("sensor_readable(): Looking inot pf[sensors][%s][regex] for %s" % (k,l_insname))
                for match in self.config['sensors'][k]['regex']:
                    #log("sensor_readable(): Looking inot %s ?= %s" % (match,l_insname))
                    if str(match) in l_insname:
                        smodel = self.config['sensors'][k]['name']
                        sclass = k
        except:
            smodel = 'unknown'
            sclass = 'unknown'

        if not smodel:
            #log("sensor_readable(): Error: instrument %s is not one of the options!" % insname)
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
        #  datalogger_readable

        dmodel = False
        dclass = False
        l_insname = insname.lower()
        for k in self.config['dataloggers']:
            for match in self.config['dataloggers'][k]['regex']:
                if str(match) in l_insname:
                    dmodel = self.config['dataloggers'][k]['name']
                    dclass = k
        if not dmodel:
            #log("datalogger_readable(): Error: instrument %s is not one of the options!" % insname)
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
        #  summary_instrument_history
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

        if self.verbose:
            pprint(summary_grp)

        if len(summary_grp['datalogger']) == 0:
            #raise LookupError('No datalogger summary available')
            log('No datalogger summary available')

        return summary_grp

