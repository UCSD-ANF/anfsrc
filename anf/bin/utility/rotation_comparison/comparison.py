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
        self.debug_plot = options.debug_plot 
        
        # parse parameter file 
        try:
            self._parse_pf(options)
        except Exception:
            self.logging.error('ERROR: problem during parsing of pf file (%s)' % options.pf)

    def _parse_pf(self, options):
        self.image_dir = safe_pf_get(self.pf, "image_dir")

        if options.tw: self.tw = options.tw
        else: self.tw = safe_pf_get(self.pf, 'time_window')
        self.tw = float(self.tw)
 
        if options.filter: self.filter = options.filter
        else: self.filter = safe_pf_get(self.pf, 'filter')
       
        if options.chan: self.chan = options.chan
        else: self.chan = safe_pf_get(self.pf, 'chan')

    def comp(self, arg):
        try:
            self.db = datascope.dbopen( self.databasename, "r+" )
        except Exception,e:
            self.logging.error('Problems opening database: %s %s' % (self.db,e) )


        if self.origin:
            event_data = Origin(self.db, arg)
            time = event_data.time
        else:   
             try:
                 time = arg
                 if isinstance(time, str): time = str2epoch(time)
             except Exception:
                 sys.exist(usage)
            
        # grab station info from select list that are active during this time
        site_data = Stations(self.select, self.ref_sta, self.db, time, logging, event_data)
        station_list = site_data.station_list()
        print station_list 
 
        if self.ref_sta not in station_list:
            station_list.insert(0, self.ref_sta)
        else: 
            old_ind = station_list.index(self.ref_sta)
            station_list.insert(0, station_list.pop(old_ind))

        #  Inititiate waveform data class
        data = Waveforms(self.db)

        results = {}
        for sta in station_list:
            if site_data.stations[sta]['ptime']: start = site_data.stations[sta]['ptime'] - 2
            else: start = time

            data.get_waveforms(sta=sta, chan=self.chan, start=start, tw=self.tw, bw_filter=self.filter)
            
            if data.trdata[sta]:
                if sta == self.ref_sta: 
                    results[sta] = data.set_refsta_data(sta)
                else:   
                    results[sta] = data.get_azimuth(self.ref_sta, sta, site_data.stations, noplot=self.noplot, image_dir = self.image_dir, debug_plot=self.debug_plot) 

        return results


