"""Cross-correlation comparison routines and classes."""
import types

from anf.logutil import fullname, getLogger
import antelope.datascope as datascope
from antelope.stock import str2epoch
from rotation_comparison.data import Waveforms
from rotation_comparison.util import (
    Origin,
    Plot,
    Site,
    open_verify_pf,
    safe_pf_get,
    save_results,
)

logger = getLogger(__name__)


class Comparison:
    """Class to run cross-correlation comparison."""

    def __init__(self, options, databasename):
        """Initialize the Comparison object.

        Args:
            options (dict): dictionary containing required options
            databasename(string): path to Datascope database.

        Options dict format:
            origin (int): origin id of an event
            noplot (bool): do not make a plot at the end
            nosave (bool): do not save results
            debug_plot (bool): run plotting routines with debug option

        """
        self.databasename = databasename
        self.logger = getLogger(fullname(self))
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
            self.logger.error(
                "ERROR: problem during parsing of pf file (%s)" % options.pf
            )

    def _parse_pf(self, options):
        """Parse parameter file."""
        self.ref_regex = safe_pf_get(self.pf, "reference")
        if options.reference:
            self.ref_regex = self.options.ref

        self.comp_regex = safe_pf_get(self.pf, "compare")
        if options.compare:
            self.comp_regex = options.select

        self.result_dir = safe_pf_get(self.pf, "result_dir")

    def _parse_sta_params(self, distance, options):
        """Parse station parameters."""
        self.dist_info = safe_pf_get(self.pf, "dist_%s" % distance)

        try:
            self.filter = getattr(options, "filter", None) or self.dist_info["filter"]

            self.tw = getattr(options, "tw", None) or float(self.dist_info["tw"])

            self.dist_min = float(self.dist_info["ssdist_min"])
            self.dist_max = float(self.dist_info["ssdist_max"])
        except KeyError:
            self.logger.exception("Missing a required parameter file key.")
            raise

    def comp(self, arg):
        """Run cross-correlation and select rotation azimuth."""
        # Load main database
        try:
            self.db = datascope.dbopen(self.databasename, "r+")

        except Exception as e:
            self.logger.error("Problems opening database: %s %s" % (self.db, e))

        # If origin mode, get origin data
        if self.origin:
            event_data = Origin(self.db, arg)
            time = event_data.time
            orid = event_data.orid

        else:
            time = arg
            if isinstance(time, str):
                time = str2epoch(time)
            event_data = None
            orid = None

        # Grab station info from select list that are active during this time
        site_table = Site(self.db)
        site_table.get_stations(self.ref_regex, time, event_data=event_data)
        try:
            reference = list(site_table.stations.keys())[0]
        except IndexError:
            self.logger.error("No stations found in site table.")
            return None

        stations = site_table.get_stations(self.comp_regex, time, reference, event_data)
        ref_chan = stations[reference].chans[0]

        options = types.SimpleNamespace()
        # Get station parameters based on station-event distance
        if stations[reference].delta:
            delta = stations[reference].delta
            if delta >= 0 and delta < 5:
                distance = 5
            elif delta >= 5 and delta < 20:
                distance = 20
            elif delta >= 20 and delta < 50:
                distance = 50
            elif delta >= 50 and delta < 100:
                distance = 100
            elif delta >= 100 and delta < 180:
                distance = 180
            self._parse_sta_params(distance, options)

        #  Inititiate waveform data class
        data = Waveforms(self.db)

        results = {}
        if stations[reference].ptime:
            start = stations[reference].ptime - 2
        else:
            start = time

        # Get reference sensor data
        ref_tr = data.get_waveforms(
            sta=reference,
            chan=ref_chan,
            start=start,
            tw=self.tw,
            bw_filter=self.filter,
            debug_plot=self.debug_plot,
        )
        if ref_tr:
            data.set_ref_data(reference, ref_tr)
        else:
            self.logger.notify("No data for reference station %s available" % reference)

        for sta in stations:
            results[sta] = {}

            # for each comparison, get trace
            for chan in stations[sta].chans:
                if chan == ref_chan and sta == reference:
                    pass
                else:
                    tr = data.get_waveforms(
                        sta=sta,
                        chan=chan,
                        start=start,
                        tw=self.tw,
                        bw_filter=self.filter,
                        debug_plot=self.debug_plot,
                    )
                    if tr:
                        if event_data:
                            diff_esaz = stations[sta].esaz - stations[reference].esaz

                            # Do not run if station-station azimuth is too far
                            if diff_esaz > 45 and diff_esaz < 315:
                                self.logger.info(
                                    "Event-station azimuth difference %s > \
                                        45 degrees. Station %s thrown out."
                                    % (diff_esaz, sta)
                                )
                                if not self.nosave:
                                    save_results(
                                        ref_sta=self.reference,
                                        ref_chan=stations[reference].chans[0],
                                        sta=sta,
                                        chan=chan,
                                        result_dir=self.result_dir,
                                        ref_esaz=stations[reference].esaz,
                                        ssaz=stations[sta].ssaz,
                                        distance=stations[sta].ssdistance,
                                        esaz=stations[sta].esaz,
                                        azimuth1="NULL",
                                        azimuth2="NULL",
                                    )

                            # Otherwise, calculate rotation azimuth
                            else:
                                results[sta][chan] = data.get_azimuth(sta, tr)

                                if not self.nosave:
                                    save_results(
                                        ref_sta=reference,
                                        ref_chan=stations[reference].chans[0],
                                        sta=sta,
                                        chan=chan,
                                        result_dir=self.result_dir,
                                        ref_esaz=stations[reference].esaz,
                                        ssaz=stations[sta].ssaz,
                                        distance=stations[sta].ssdistance,
                                        esaz=stations[sta].esaz,
                                        azimuth1=results[sta][chan]["T"].azimuth,
                                        azimuth2=results[sta][chan]["R"].azimuth,
                                    )

                        else:
                            results[sta][chan] = data.get_azimuth(sta, tr)

                if len(results[sta]) > 0 and not self.noplot:
                    Plot(
                        width=16,
                        height=6,
                        result=results[sta],
                        reference=data.ref_data,
                        ref_sta=reference,
                        ref_chan=ref_chan,
                        sta=sta,
                        start=start,
                        end=start + self.tw,
                        result_dir=self.result_dir,
                        debug_plot=self.debug_plot,
                        orid=orid,
                    )

        return results
