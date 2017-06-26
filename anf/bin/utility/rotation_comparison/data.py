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
                    bw_filter=None):

        self.logging.debug('Start data extraction for %s' % sta )
        results = False

        self.start = start
        self.end = start + tw
       
        self.logging.debug('Get %s data' % (sta) )
        self.logging.debug('self.start: %s self.end:%s' % (self.start,self.end) )

        steps = ['dbopen wfdisc']
        
        steps.extend(['dbsubset sta=~/%s/ && endtime > %s && time < %s && chan=~/%s/'  % \
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
            self.trdata[sta] = None

        else:
            self.logging.info( '%s traces after subset for sta =~ [%s]' % (dbview.record_count,sta) )
            results = self._extract_waveforms(dbview, sta, chan, bw_filter)

            dbview.free()

    def _extract_waveforms(self, dbview, sta, chan, bw_filter):

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
            tr.trsplice()
        except Exception, e:
            self.logging.error('Could not prepare data for %s:%s [%s]' % (sta,chans, e))

        # Stop here if we don't have something to work with.
        if not tr.record_count:
            self.logging.warning( 'No data after trload for %s' % sta )
            self.set_trdata(sta, None)
            return False

        if tr.record_count > 3:
            # Recursive call to a new subset
            self.logging.warning( 'Too many traces after trload_cssgrp for [%s]. Now %s' % \
                    (sta, tr.record_count) )
            self.set_trdata(sta, None)
            return False

        # Demean the trace
        #tr.trfilter('BW 0 0 2 4')
        tr.trfilter('DEMEAN')

        # Need real units, not counts.
        tr.trapply_calib()

       #  Integrate if needed to get displacement
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

        # FILTERING
        #
        self.logging.debug('Filter data from %s with [%s]' % (sta, bw_filter))
        try:
            tr.trfilter( bw_filter )
        except Exception,e:
            self.logging.warning('Problems with the filter %s => %s' % (bw_filter,e))
            return False
        self.set_trdata(sta, tr)

    def set_trdata(self, sta, trdata):
        self.trdata[sta] = trdata

    def set_refsta_data(self, ref_sta):
        tr_ref = self.get_tr(ref_sta)
        results = {} 
        for i,chan in enumerate(['T', 'R', 'Z']):
            original = tr2vec(tr_ref, i)
            results[chan] = Records()
            results[chan].set_data(original=original, rotated=original, azimuth=0, xcorr=1.0)    
        return results

    def get_tr(self, sta):
        tr = self.trdata[sta]
        return tr
 
    def get_azimuth(self, ref_sta, sta, siteinfo, image_dir, debug_plot, noplot):
        if ref_sta!=sta:
            ref_esaz = float(siteinfo[ref_sta]['esaz'])
            sta_esaz = float(siteinfo[sta]['esaz'])
            diff_esaz  = sta_esaz - ref_esaz

            tr_ref = self.get_tr(sta).trcopy()
            tr_ref.trrotate(ref_esaz, 0, ['T', 'R', 'Z'])
            tr_ref = tr_ref.subset("chan=~/T|R|Z/")

            tr_orig = self.get_tr(sta)
#            tr_orig = tr_orig.subset("chan=~/T|R|Z/")
  
            azimuths  = get_range(start=0, stop=360, step=0.5)
            results = {}
            reference = {}
            for i,chan in enumerate(['T', 'R', 'Z']):
                #print " Station: %s Channel: %s" % (sta, chan)
                time_shifts = []
                correlations = []
                ref_data = tr2vec(tr_ref, i)
                reference[chan] =ref_data
                for az in azimuths:
                    tr = tr_orig.trcopy()

                    #print az, "before", tr.record_count
                    tr.trrotate(az+sta_esaz, 0, ['T', 'R', 'Z'])
                    #print "after", tr.record_count
                    
                    sta_data = tr2vec(tr, i+3)
                    if len(ref_data) > len(sta_data):
                        ref_data = resample(ref_data, len(sta_data))
                    if len(sta_data) > len(ref_data):
                        sta_data = resample(ref_data, len(sta_data))

                    time_shift, xcorr_value, cross_corr = cross_correlation(ref_data, sta_data)
                    time_shifts.append(time_shift)
                    correlations.append(xcorr_value)

                    #free_tr(tr_ref)
                    free_tr(tr)

                max_corr = max(correlations)
                max_ind  = correlations.index(max_corr)

                # make 2 copies
                tr1 = tr_orig.trcopy()
                tr2 = tr_orig.trcopy()

                # rotate to station-event azimuth for plot
                tr1.trrotate(sta_esaz, 0, ['T', 'R', 'Z']) 
                original = tr2vec(tr1, i+3)

                # rotate to station-event + rotation angle relative to reference sta
                tr2.trrotate(azimuths[max_ind]+sta_esaz, 0, ['T', 'R', 'Z'])
                rotated = tr2vec(tr2, i+3)
       
                azimuth = azimuths[max_ind]
                xcorr = max_corr       
                if azimuth > 5:
                    print "PROBLEM: Station: %s Channel: %s Azimuth: %s XCorr: %s" % (sta, chan, azimuth, xcorr) 
                self.logging.info(" Station: %s Channel: %s Azimuth: %s XCorr: %s" % (sta, chan, azimuth, xcorr))
                results[chan] = Records()
                results[chan].set_data(original=original, rotated=rotated, azimuth=azimuth, xcorr=xcorr)    

            if noplot==False: 
                Plot(width=24, height=8, result=results, reference=reference, ref_sta=ref_sta, sta=sta, start=self.start, end=self.end, image_dir=image_dir, debug_plot=debug_plot)       
                
        return results

    def azimuth_correction(self, tr, esaz):
        try:
            tr.trrotate(float(esaz), 0, ['T', 'R', 'Z'])
            tr.subset('chan =~ /T|R|Z/')
        except Exception, e:
            self.logging.error('Problem with trrotate %s => %s' % (Exception, e))
         
        return tr
