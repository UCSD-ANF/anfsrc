"""Data retrival functions and classes."""
from anf.logutil import fullname, getLogger
import antelope.datascope as datascope
import numpy

from .util import Results, cross_correlation, free_tr, get_range, plot_tr, tr2vec

logger = getLogger(__name__)


class Waveforms:
    """Manipulate Antelope Datascope waveforms."""

    def __init__(self, db):
        """Initialize Waveforms object.

        Args:
            db(antelope.datascope.Database): database pointer
        """
        self.logger = getLogger(fullname(self))
        self.db = db
        self.trdata = {}

        # Get db ready
        try:
            self.wftable = self.db.lookup(table="wfdisc")
        except Exception as e:
            self.logger.error("Problems opening wfdisc: %s %s" % (self.db, e))

        if not self.wftable.record_count:
            self.logger.error("No data in wfdisc %s" % self.db)

    def get_waveforms(self, sta, chan, start, tw, bw_filter=None, debug_plot=False):
        """Store waveforms."""
        self.logger.debug("Start data extraction for %s" % sta)
        results = False

        self.start = start - tw
        self.end = start + 2 * tw
        self.tw = tw

        self.logger.debug("Get %s data" % (sta))
        self.logger.debug("self.start: %s self.end:%s" % (self.start, self.end))

        # Open and subset wfdisc
        steps = ["dbopen wfdisc"]
        steps.extend(
            [
                "dbsubset sta=~/%s/ && endtime > %s && time < %s && chan=~/%s./"
                % (sta, self.start, self.end, chan)
            ]
        )
        steps.extend(["dbjoin sensor"])
        steps.extend(["dbjoin instrument"])
        steps.extend(["dbsort sta chan"])

        self.logger.debug("Database query for waveforms:")
        self.logger.debug(", ".join(steps))

        dbview = self.db.process(steps)

        if not dbview.record_count:
            self.logger.info("No traces after subset for sta =~ [%s]" % sta)
            results = None

        else:
            self.logger.info(
                "%s traces after subset for sta =~ [%s]" % (dbview.record_count, sta)
            )
            results = self._extract_waveforms(dbview, sta, chan, bw_filter, debug_plot)

        dbview.free()
        return results

    def _extract_waveforms(self, dbview, sta, chan, bw_filter, debug_plot=False):
        """Extract waveforms from database subset."""

        # Look for information in the first record
        dbview.record = 0

        # Extract some parameters from instrument and wfdsic table
        (samprate, segtype, dfile) = dbview.getv(
            "wfdisc.samprate", "instrument.rsptype", "wfdisc.dfile"
        )

        # Return view to all traces
        dbview.record = datascope.dbALL

        # Load data
        try:
            tr = dbview.trload_cssgrp(self.start, self.end)
        except Exception as e:
            self.logger.error("Could not prepare data for %s:%s [%s]" % (sta, chan, e))

        # Stop here if we don't have something to work with.
        if not tr.record_count:
            self.logger.warning("No data after trload for %s" % sta)
            self.set_trdata(sta, None)

        # Require only 3 traces
        if tr.record_count > 3 or tr.record_count < 3:
            self.logger.warning(
                "Not 3 traces after trload_cssgrp for [%s]. Now %s"
                % (sta, tr.record_count)
            )
            self.set_trdata(sta, None)

        # Good if 3 traces
        if tr.record_count == 3:
            if debug_plot:
                self.logger.info(" Plotting raw waveforms: %s %s" % (sta, chan))
                fig = plot_tr(tr, sta, chan, style="r", label="raw", fig=False)

            for t in tr.iter_record():
                calib = t.getv("calib")[0]
                if not float(calib):
                    self.logger.info("Calib %s" % calib)
                    t.putv(("calib", 1.0))

            # Get real units
            tr.trapply_calib()

            if debug_plot:
                self.logger.info(" Plotting calibrated waveforms: %s %s" % (sta, chan))
                plot_tr(tr, sta, chan, style="g", label="calib", fig=fig)

            # Integrate if needed to get displacement
            # Bring the data from nm to cm
            if segtype == "A":
                tr.trfilter("INT2")
                tr.trfilter("G 0.0000001")
                segtype = "D"
            elif segtype == "V":
                tr.trfilter("INT")
                tr.trfilter("G 0.0000001")
                segtype = "D"
            elif segtype == "D":
                tr.trfilter("G 0.0000001")

            if debug_plot:
                self.logger.info(" Plotting integrated waveforms: %s %s" % (sta, chan))
                plot_tr(tr, sta, chan, style="b", label="integrated", fig=fig)

            tr.trfilter("BW 0 0 2 4")
            tr.trfilter("DEMEAN")

            if debug_plot:
                self.logger.info(
                    " Plotting calibrated, integrated, \
                        and demeaned waveforms: %s %s"
                    % (sta, chan)
                )
                plot_tr(tr, sta, chan, style="y", label="demeaned")

            # Filter waveforms
            self.logger.debug("Filter data from %s with [%s]" % (sta, bw_filter))
            try:
                tr.trfilter(bw_filter)
            except Exception as e:
                self.logger.warning(
                    "Problems with the filter %s => %s" % (bw_filter, e)
                )
                return False

            return tr

    def set_trdata(self, sta, trdata):
        """Store trace data."""
        self.trdata[sta] = trdata

    def get_tr(self, sta):
        """Get trace data."""
        tr = self.trdata[sta]
        return tr

    def set_ref_data(self, sta, tr):
        """Set reference waveform data."""
        self.ref_data = {}
        for i, chan in enumerate(["T", "R", "Z"]):
            ref_data = tr2vec(tr, i)
            samplerate = len(ref_data) / (self.end - self.start)
            step = samplerate / 10
            data = []
            for x in range(0, len(ref_data), int(step)):
                data.append(ref_data[x])

            ref_data = data[int(self.tw * 10) : int((2 * self.tw * 10))]
            self.ref_data[chan] = ref_data

    def get_azimuth(self, sta, tr):
        """Calculate rotation angle."""
        tr_orig = tr
        azimuths = get_range(start=0, stop=360, step=0.5)
        results = {}
        for i, chan in enumerate(["T", "R", "Z"]):
            ref_data = self.ref_data[chan]

            time_shifts = []
            correlations = []
            for az in azimuths:
                tr = tr_orig.trcopy()

                tr.trrotate(az, 0, ["T", "R", "Z"])

                sta_data = tr2vec(tr, i + 3)

                samplerate = len(sta_data) / (self.end - self.start)
                step = samplerate / 10

                data = []
                for x in range(0, len(sta_data), int(step)):
                    data.append(sta_data[x])
                sta_data = data[int(self.tw * 10) : int((2 * self.tw * 10))]

                if len(sta_data) == len(ref_data):
                    time_shift, xcorr_value, cross_corr = cross_correlation(
                        ref_data, sta_data
                    )
                    time_shifts.append(time_shift)
                    correlations.append(xcorr_value)
                else:
                    time_shifts.append(float("NaN"))
                    correlations.append(float("NaN"))
                free_tr(tr)

            correlations = numpy.array(correlations)
            max_corr = numpy.nanmax(correlations)
            max_ind = numpy.where(correlations == max_corr)[0][0]
            azimuth = azimuths[max_ind]

            # make 2 copies
            tr1 = tr_orig.trcopy()
            tr2 = tr_orig.trcopy()

            # rotate to station-event azimuth for plot
            tr1.trrotate(0, 0, ["T", "R", "Z"])
            original = tr2vec(tr1, i + 3)
            samplerate = len(original) / (self.end - self.start)
            step = samplerate / 10

            data = []
            for x in range(0, len(original), int(step)):
                data.append(original[x])
            original = data[int(self.tw * 10) : int((2 * self.tw * 10))]

            # rotate to station-event + rotation angle relative to reference sta
            tr2.trrotate(azimuth, 0, ["T", "R", "Z"])
            rotated = tr2vec(tr2, i + 3)
            samplerate = len(rotated) / (self.end - self.start)
            step = samplerate / 10

            data = []
            for x in range(0, len(rotated), int(step)):
                data.append(rotated[x])
            rotated = data[int(self.tw * 10) : int((2 * self.tw * 10))]

            xcorr = max_corr
            if azimuth > 5 and azimuth < 355:
                self.logger.warning(
                    "ROTATION PROBLEM:  Station: %s Channel: \
                        %s Azimuth: %s XCorr: %s"
                    % (sta, chan, azimuth, xcorr)
                )
            self.logger.info(
                " Station: %s Channel: %s Azimuth: %s XCorr: %s"
                % (sta, chan, azimuth, xcorr)
            )
            results[chan] = Results()
            results[chan].set_data(
                original=original, rotated=rotated, azimuth=azimuth, xcorr=xcorr
            )

            free_tr(tr1)
            free_tr(tr2)

        return results

    def azimuth_correction(self, tr, esaz):
        """Perform an azimuth correction on a trace object."""

        try:
            tr.trrotate(float(esaz), 0, ["T", "R", "Z"])
            tr.subset("chan =~ /T|R|Z/")
        except Exception as e:
            self.logger.error("Problem with trrotate %s => %s" % (Exception, e))

        return tr
