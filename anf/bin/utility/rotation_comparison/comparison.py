from __main__ import *

class Comparison():
    def __init__(self, options, databasename, logging):
        self.databasename = databasename
        self.logging = logging
        # verify adequate parameter file
        self.pf = open_verify_pf(options.pf)

        self.origin = options.origin
        self.noplot = options.noplot
        self.nosave = options.nosave
        self.debug_plot = options.debug_plot 

        # parse parameter file 
        try:
            self._parse_pf(options)
        except Exception:
            self.logging.error('ERROR: problem during parsing of pf file (%s)' % options.pf)

    def _parse_pf(self, options):
        self.ref_regex = safe_pf_get(self.pf, 'reference')
        if options.reference: self.ref_regex = self.options.ref        
#        self.ref_sta_regex = self.ref_regex.split('&&')[0]

        self.comp_regex = safe_pf_get(self.pf, 'compare')
        if options.compare: self.comp_regex = options.select
#        self.comp_sta_regex = self.comp_regex('&&')[0]

        self.result_dir = safe_pf_get(self.pf, "result_dir")
    
    # sta refers to the reference station, the filter and tw used depends on that
    # will write in if statement to not run if ssdist is not within specified range or diff_esaz is too high
    def _parse_sta_params(self, distance, options):
        self.dist_info = safe_pf_get(self.pf, 'dist_%s' % distance)
        
        if options.filter: self.filter = options.filter
        else: self.filter = self.dist_info[ 'filter' ]
        
        if options.tw: self.tw = options.tw
        else: self.tw = float(self.dist_info [ 'tw' ])
        self.dist_min = float(self.dist_info['ssdist_min'])
        self.dist_max = float(self.dist_info['ssdist_max'])
    
    def comp(self, arg):

        # Load main database
        try:
            self.db = datascope.dbopen( self.databasename, "r+" )
            
        except Exception,e:
            self.logging.error('Problems opening database: %s %s' % (self.db,e) )

        # If origin mode, get origin data
        if self.origin:
            event_data = Origin(self.db, arg)
            time = event_data.time
            orid = event_data.orid
        
        else:
            try:
                time = arg
                if isinstance(time, str): time = str2epoch(time)
                event_data = None
                orid = None
                 
            except Exception:
                sys.exist(usage)
            
        # grab station info from select list that are active during this time
        site_table = Site(self.db, logging)
        site_table.get_stations(self.ref_regex, time, event_data=event_data)
        reference = site_table.stations.keys()[0]
        
        stations = site_table.get_stations(self.comp_regex, time, reference, event_data)
        stas = stations.keys()
        ref_chan = stations[reference].chans[0] 


        if stations[reference].delta:
            delta = stations[reference].delta
            if (delta >= 0 and delta < 5): distance = 5
            if (delta >= 5 and delta < 20): distance = 20
            if (delta >= 20 and delta < 50): distance = 50
            if (delta >= 50 and delta < 100): distance = 100
            if (delta >= 100 and delta < 180): distance = 180
            self._parse_sta_params(distance, options)
            
        
#        site_data = Stations(self.ref_sta_regex, self.comp_sta_regex, self.db, time, logging, event_data)
#        siteinfo = site_data.stations
#        station_list = site_data.station_list()
#        logging.info("Stations: %s" % station_list) 
# 
#        if self.ref_sta not in station_list:
#            station_list.insert(0, self.ref_sta)
#        else: 
#            old_ind = station_list.index(self.ref_sta)
#            station_list.insert(0, station_list.pop(old_ind))
#
#        if site_data.stations[self.ref_sta]['delta']:
#            delta = float(site_data.stations[self.ref_sta]['delta'])
#            if (delta >= 0 and delta < 5): distance = 5
#            if (delta >= 5 and delta < 20): distance = 20
#            if (delta >= 20 and delta < 50): distance = 50
#            if (delta >= 50 and delta < 100): distance = 100
#            if (delta >= 100 and delta < 180): distance = 180
#            self._parse_sta_params(distance, options)

        #  Inititiate waveform data class
        data = Waveforms(self.db)

        results = {}
        
        if stations[reference].ptime: start = stations[reference].ptime-2 
        else: start = time
       
        ref_tr = data.get_waveforms(sta=reference, chan=ref_chan, start=start, tw=self.tw, bw_filter=self.filter, debug_plot=self.debug_plot)
        if ref_tr: data.set_ref_data(reference, ref_tr)
        else: logging.notify("No data for reference station %s available" % reference)
        
        for sta in stations:
            results[sta] = {} 
            
            for chan in stations[sta].chans:
                if chan == ref_chan and sta==reference:
                    pass
                else:
                    tr = data.get_waveforms(sta=sta, chan=chan, start=start, tw=self.tw, bw_filter=self.filter, debug_plot=self.debug_plot)
                    if tr:
                        if event_data:
                            diff_esaz = stations[sta].esaz - stations[reference].esaz
                   
                            if (diff_esaz > 45 and diff_esaz < 315): 
                                logging.info("Event-station azimuth difference %s > 45 degrees. Station %s thrown out." \
                                            % (diff_esaz, sta))
                                if self.nosave==False:
                                    save_results(ref_sta=self.reference, ref_chan=stations[reference].chans[0], sta=sta, chan=chan, result_dir=self.result_dir, \
                                                 ref_esaz=stations[reference].esaz, ssaz=stations[sta].ssaz, distance=stations[sta].ssdistance, esaz=stations[sta].esaz, \
                                                 azimuth1="NULL", azimuth2="NULL")
                            else:
                                results[sta][chan] = data.get_azimuth(sta, tr) 
                                
                                if self.nosave==False: 
                                    save_results(ref_sta=reference, ref_chan=stations[reference].chans[0], sta=sta, chan=chan, result_dir=self.result_dir, \
                                                ref_esaz=stations[reference].esaz, ssaz=stations[sta].ssaz, distance=stations[sta].ssdistance, esaz=stations[sta].esaz, \
                                                azimuth1=results[sta][chan]['T'].azimuth, azimuth2=results[sta][chan]['R'].azimuth)
            
                        else:
                            results[sta][chan] = data.get_azimuth(sta, tr) 
                                
                if len(results[sta])>0 and self.noplot==False:
                    Plot(width=16, height=6, result=results[sta], reference=data.ref_data, ref_sta=reference, ref_chan=ref_chan, sta=sta, start=start, end=start+self.tw, result_dir=self.result_dir, debug_plot=self.debug_plot, orid=orid)

        return results


