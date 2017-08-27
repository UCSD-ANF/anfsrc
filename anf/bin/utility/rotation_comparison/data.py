from __main__ import *

class Waveforms():
    def __init__(self, db):

        self.logging = getLogger('Waveforms')

        self.db = db

        self.trdata = {}
        
        # Get db ready

        try:
            self.wftable = self.db.lookup(table='wfdisc')
        except Exception,e:
            self.logging.error('Problems opening wfdisc: %s %s' % (self.db,e) )

        if not self.wftable.record_count:
            self.logging.error( 'No data in wfdisc %s' % self.db )
 
    def get_waveforms(self, sta, chan, start, tw,
                    bw_filter=None, debug_plot=False):

        self.logging.debug('Start data extraction for %s' % sta )
        results = False

        self.start = start - tw
        self.end = start + 2*tw
        self.tw = tw
 
        self.logging.debug('Get %s data' % (sta) )
        self.logging.debug('self.start: %s self.end:%s' % (self.start,self.end) )

        steps = ['dbopen wfdisc']
        
        steps.extend(['dbsubset sta=~/%s/ && endtime > %s && time < %s && chan=~/%s./'  % \
                ( sta, self.start, self.end, chan) ])
        steps.extend(['dbjoin sensor'])
        steps.extend(['dbjoin instrument'])
        steps.extend(['dbsort sta chan'])

        self.logging.debug( 'Database query for waveforms:' )
        self.logging.debug( ', '.join(steps) )

        dbview = self.db.process( steps )
        
        if not dbview.record_count:
            # This failed.
            self.logging.info( 'No traces after subset for sta =~ [%s]' % sta )
            dbview.free()
            tr = None
            #self.trdata[sta] = None

        else:
            self.logging.info( '%s traces after subset for sta =~ [%s]' % (dbview.record_count,sta) )
            results = self._extract_waveforms(dbview, sta, chan, bw_filter, debug_plot)
           
            return results
            dbview.free()

    def _extract_waveforms(self, dbview, sta, chan, bw_filter, debug_plot=False):

        results = 0

        # Look for information in the first record
        dbview.record = 0

        # Extract some parameters from instrument and wfdsic table
        ( samprate, segtype, dfile ) = \
                dbview.getv( 'wfdisc.samprate', 'instrument.rsptype', 'wfdisc.dfile')

        # Return view to all traces
        dbview.record = datascope.dbALL

        # Segtypes are set in the parameter file. Need to know what
        # we get from the wfdisc so we can match GreensFunctions units.
        #if not segtype in self.allowed_segtype:
        #    # SKIP THIS SITE
        #    self.logging.warning( 'Skipping station: %s Wrong type: %s' % (sta,segtype) )
        #    return False

        # Bring the data into memory. Join segments if fragmented.
        try:
            tr = dbview.trload_cssgrp( self.start, self.end )
            #tr.trsplice()
        except Exception, e:
            self.logging.error('Could not prepare data for %s:%s [%s]' % (sta,chan, e))

        # Stop here if we don't have something to work with.
        if not tr.record_count:
            self.logging.warning( 'No data after trload for %s' % sta )
            self.set_trdata(sta, None)

        if (tr.record_count > 3 or tr.record_count < 3):
            # Recursive call to a new subset
            self.logging.warning( 'Not 3 traces after trload_cssgrp for [%s]. Now %s' % \
                    (sta, tr.record_count) )
            self.set_trdata(sta, None)

        if tr.record_count == 3:
            # Demean the trace

            # Need real units, not counts.
            if debug_plot:
                self.logging.info(" Plotting raw waveforms: %s %s" % (sta, chan))
                fig = plot_tr(tr, sta, chan, style='r', label='raw', fig=False)

            tr.trapply_calib()
           
            if debug_plot:
                self.logging.info(" Plotting calibrated waveforms: %s %s" % (sta, chan))
                plot_tr(tr, sta, chan, style='g', label='calib', fig=fig)
            
            # Integrate if needed to get displacement
            if segtype == 'A':
                tr.trfilter('INT2')
                # Need to bring the data from nm to cm and match the gf's
                tr.trfilter( "G 0.0000001" )
                segtype = 'D'
            elif segtype == 'V':
                tr.trfilter('INT')
                # Need to bring the data from nm to cm and match the gf's
                tr.trfilter( "G 0.0000001" )
                segtype = 'D'
            elif segtype == 'D':
                # Need to bring the data from nm to cm and match the gf's
                tr.trfilter( "G 0.0000001" )

            if debug_plot:
                self.logging.info(" Plotting integrated waveforms: %s %s" % (sta, chan))
                #plot_tr(tr, sta, chan, style='b', label='integrated', fig=fig)
            
            tr.trfilter('BW 0 0 2 4')
            tr.trfilter('DEMEAN')

            if debug_plot:
                self.logging.info(" Plotting calibrated, integrated, and demeaned waveforms: %s %s" % (sta, chan))
                #plot_tr(tr, sta, chan, style='y', label='demeaned')
 
            # FILTERING
            #
            self.logging.debug('Filter data from %s with [%s]' % (sta, bw_filter))
            try:
                tr.trfilter( bw_filter )
            except Exception,e:
                self.logging.warning('Problems with the filter %s => %s' % (bw_filter,e))
                return False
            # instead of this just return tr
            return tr
            #self.set_trdata(sta, tr)

    # wont need this
    def set_trdata(self, sta, trdata):
        self.trdata[sta] = trdata

    #def set_refsta_data(self, ref_sta):
    #    tr = self.get_tr(ref_sta)
    #    results = {} 
    #    for i,chan in enumerate(['T', 'R', 'Z']):
    #        original = tr2vec(tr, i)
    #        results[chan] = Records()
    #        results[chan].set_data(original=original, rotated=original, azimuth=0, xcorr=1.0)    
    #    return results

    def get_tr(self, sta):
        tr = self.trdata[sta]
        return tr
    
    def set_ref_data(self, sta, tr):
        #tr_ref.trrotate(ref_esaz, 0, ['T', 'R', 'Z'])
        #tr_ref = tr_ref.subset("chan=~/T|R|Z/")
        
        self.ref_data = {}
        for i,chan in enumerate(['T', 'R', 'Z']):
            ref_data = tr2vec(tr, i)
            samplerate = len(ref_data)/(self.end-self.start)
            step = samplerate/10
            data = []
            for x in range(0,len(ref_data), int(step)):
                data.append( ref_data[x] )
     
            ref_data = data[int(self.tw*10):int((2*self.tw*10))]
            self.ref_data[chan] = ref_data
            #self.ref_data[chan] = [x / 4000 for x in ref_data]
        
    def get_azimuth(self, sta, tr):
        tr_orig = tr
        #tr_orig = self.get_tr(sta)
#            tr_orig = tr_orig.subset("chan=~/T|R|Z/")
                     
        azimuths  = get_range(start=0, stop=360, step=0.5)
        results = {}
        for i,chan in enumerate(['T', 'R', 'Z']):
            ref_data = self.ref_data[chan] 
    
            time_shifts = []
            correlations = []
            for az in azimuths:
                tr = tr_orig.trcopy()

                tr.trrotate(az, 0, ['T', 'R', 'Z'])
                
                sta_data = tr2vec(tr, i+3)
                
                samplerate = len(sta_data)/(self.end-self.start)
                step = samplerate/10
               
                data = []
                for x in range(0,len(sta_data), int(step)):
                    data.append( sta_data[x] )
                sta_data = data[int(self.tw*10):int((2*self.tw*10))]
              
                #if len(ref_data) > len(sta_data):
#               #     ref_data = resample(ref_data, len(sta_data))
                #    samprate = len(sta_data)/float(self.end-self.start)
                #    data = []
                #    for x in range(0,len(ref_data),int(samprate)):
                #        data.append( ref_data[x] )
                #    ref_data = data

                #if len(sta_data) > len(ref_data):
#               #     sta_data = resample(ref_data, len(sta_data))
                #    samprate = len(ref_data)/float(self.end-self.start)
                #    data = []
                #    for x in range(0,len(sta_data),int(samprate)):
                #        data.append( sta_data[x] )
                #    sta_data = data
                
                if len(sta_data) == len(ref_data):
                    #need if statement if these are different sizes 
                    time_shift, xcorr_value, cross_corr = cross_correlation(ref_data, sta_data)
                    #print("az %s, xcorr %s" % (az, xcorr_value))
                    time_shifts.append(time_shift)
                    correlations.append(xcorr_value)
                else:
                    time_shifts.append(float('NaN'))
                    correlations.append(float('NaN'))
                free_tr(tr)

            correlations = np.array(correlations)
            max_corr = np.nanmax(correlations)
            max_ind  = np.where(correlations == max_corr)[0][0]
            azimuth = azimuths[max_ind]
 
            # make 2 copies
            tr1 = tr_orig.trcopy()
            tr2 = tr_orig.trcopy()

            # rotate to station-event azimuth for plot
            tr1.trrotate(0, 0, ['T', 'R', 'Z']) 
            original = tr2vec(tr1, i+3)
            samplerate = len(original)/(self.end-self.start)
            step = samplerate/10
            
            data = []
            for x in range(0,len(original), int(step)):
                data.append( original[x] )
            original = data[int(self.tw*10):int((2*self.tw*10))]

            # rotate to station-event + rotation angle relative to reference sta
            tr2.trrotate(azimuth, 0, ['T', 'R', 'Z'])
            rotated = tr2vec(tr2, i+3)
            samplerate = len(rotated)/(self.end-self.start)
            step = samplerate/10
            
            data = []
            for x in range(0,len(rotated), int(step)):
                data.append( rotated[x] )
            rotated = data[int(self.tw*10):int((2*self.tw*10))]
 
            xcorr = max_corr
            if azimuth > 5 and azimuth < 355:
                logging.warning("ROTATION PROBLEM:  Station: %s Channel: %s Azimuth: %s XCorr: %s" \
                                    % (sta, chan, azimuth, xcorr))       
            logging.info( " Station: %s Channel: %s Azimuth: %s XCorr: %s" % (sta, chan, azimuth, xcorr))
            results[chan] = Results()
            results[chan].set_data(original=original, rotated=rotated, azimuth=azimuth, xcorr=xcorr)    

            free_tr(tr1)
            free_tr(tr2)
                
        return results

    def azimuth_correction(self, tr, esaz):
        try:
            tr.trrotate(float(esaz), 0, ['T', 'R', 'Z'])
            tr.subset('chan =~ /T|R|Z/')
        except Exception, e:
            self.logging.error('Problem with trrotate %s => %s' % (Exception, e))
         
        return tr
