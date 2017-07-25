from __main__ import *

class Comparison():
    def __init__(self, options, databasename, logging):
        self.databasename = databasename
        self.logging = logging
        # verify adequate parameter file
        self.pf = open_verify_pf(options.pf)

        self.origin = options.origin
        self.select = options.select
        self.ref_sta = options.ref_sta
        self.noplot = options.noplot
        self.nosave = options.nosave
        self.debug_plot = options.debug_plot 
        
        # parse parameter file 
        try:
            self._parse_pf(options)
        except Exception:
            self.logging.error('ERROR: problem during parsing of pf file (%s)' % options.pf)

    def _parse_pf(self, options):
        self.result_dir = safe_pf_get(self.pf, "result_dir")

        if options.tw: self.tw = options.tw
        else: self.tw = safe_pf_get(self.pf, 'time_window')
        self.tw = float(self.tw)
 
        if options.filter: self.filter = options.filter
        else: self.filter = safe_pf_get(self.pf, 'filter')
       
        if options.chan: self.chan = options.chan
        else: self.chan = safe_pf_get(self.pf, 'chan')

    # sta refers to the reference station, the filter and tw used depends on that
    # will write in if statement to not run if ssdist is not within specified range or diff_esaz is too high
    def _parse_sta_params(self, distance):
        self.dist_info = safe_pf_get(self.pf, 'dist_%s' % distance)
        self.filter = self.dist_info[ 'filter' ]
        self.tw = float(self.dist_info [ 'tw' ])
        self.dist_min = float(self.dist_info['ssdist_min'])
        self.dist_max = float(self.dist_info['ssdist_max'])
    
    def comp(self, arg):
        try:
            self.db = datascope.dbopen( self.databasename, "r+" )
            
        except Exception,e:
            self.logging.error('Problems opening database: %s %s' % (self.db,e) )

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
        site_data = Stations(self.select, self.ref_sta, self.db, time, logging, event_data)
        siteinfo = site_data.stations
        station_list = site_data.station_list()
        logging.info("Stations: %s" % station_list) 
 
        if self.ref_sta not in station_list:
            station_list.insert(0, self.ref_sta)
        else: 
            old_ind = station_list.index(self.ref_sta)
            station_list.insert(0, station_list.pop(old_ind))

        if site_data.stations[self.ref_sta]['delta']:
            delta = float(site_data.stations[self.ref_sta]['delta'])
            if (delta >= 0 and delta < 5): distance = 5
            if (delta >= 5 and delta < 20): distance = 20
            if (delta >= 20 and delta < 50): distance = 50
            if (delta >= 50 and delta < 100): distance = 100
            if (delta >= 100 and delta < 180): distance = 180
            self._parse_sta_params(distance)

        #  Inititiate waveform data class
        data = Waveforms(self.db)

        results = {}
        for sta in station_list:
            if siteinfo[sta]['ptime']: start = siteinfo[sta]['ptime'] - 2
            else: start = time

            data.get_waveforms(sta=sta, chan=self.chan, start=start, tw=self.tw, bw_filter=self.filter)
             
            if (data.trdata[sta] and data.trdata[self.ref_sta]):
                if sta == self.ref_sta: data.set_ref_data(sta)
                else:   
           
                    if event_data: 
                        ref_esaz = float(siteinfo[self.ref_sta]['esaz'])
                        sta_esaz = float(siteinfo[sta]['esaz'])
                        diff_esaz  = sta_esaz - ref_esaz
               
                        if (diff_esaz > 45 and diff_esaz < 315): 
                            logging.info("Event-station azimuth difference %s > 45 degrees. Station %s thrown out." \
                                        % (diff_esaz, sta))
                            if self.nosave==False:
                                save_results(ref_sta=self.ref_sta, sta=sta, result_dir=self.result_dir, ref_esaz=siteinfo[self.ref_sta]['esaz'], \
                                                 ssaz=siteinfo[sta]['ssaz'], distance=siteinfo[sta]['ssdistance'], esaz=siteinfo[sta]['esaz'], \
                                                    azimuth1="NULL", azimuth2="NULL")
                        else:
                            results[sta] = data.get_azimuth(sta, ref_sta=self.ref_sta, siteinfo=siteinfo) 
                            
                            if self.nosave==False: 
                                save_results(ref_sta=self.ref_sta, sta=sta, result_dir=self.result_dir, ref_esaz=siteinfo[self.ref_sta]['esaz'], \
                                                 ssaz=siteinfo[sta]['ssaz'], distance=siteinfo[sta]['ssdistance'], esaz=siteinfo[sta]['esaz'], \
                                                    azimuth1=results[sta]['T'].azimuth, azimuth2=results[sta]['R'].azimuth)
                                
                            if self.noplot==False:
                                Plot(width=24, height=8, result=results[sta], reference=data.ref_data, ref_sta=self.ref_sta, sta=sta, start=start, end=start+self.tw, result_dir=self.result_dir, debug_plot=self.debug_plot, orid=orid)
        
                    else:
                        results[sta] = data.get_azimuth(sta, ref_sta=self.ref_sta, siteinfo=siteinfo) 
                            
                        if self.noplot==False:
                            Plot(width=24, height=8, result=results[sta], reference=data.ref_data, ref_sta=self.ref_sta, sta=sta, start=start, end=start+self.tw, result_dir=self.result_dir, debug_plot=self.debug_plot, orid=orid)

        return results


