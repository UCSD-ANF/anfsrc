"""Generate a new map for the usarray website.

@author     Juan Reyes
@modified   25/07/2014 - Malcolm White
@notes      Updated to run under 5.4 of Antelope.
"""

import sys
import os
from shutil import move
import tempfile
from subprocess import check_call
import argparse

import antelope.datascope as antdb
import antelope.stock as stock
import collections

import datetime

from anf.logutil import getLogger, getAppLogger

logger = getLogger(__name__)

today = datetime.date.today()
MAP_TYPES = ["cumulative", "rolling"]
DEPLOYMENT_TYPES = ["seismic", "inframet"]

START_YEAR=2004
"""The first year that data is available for a given project."""

MAX_YEAR=today.year
"""The last year that data is available for."""

YearMonth = collections.namedtuple('YearMonth', ['year', 'month'])

WET_RGB = "202/255/255"

def getDefaultYearMonth():
    if today.month == 1:
        return YearMonth(today.year - 1, 12)
    else:
        return YearMonth(today.year, today.month -1)

class DeployMapError(Exception):
    """General Error for this script."""

class PfValidationError(DeployMapError):
    """The PF File failed validation."""
    def __init__(self, pfname, **args):
        msg="The PF File %s failed validation." % pfname
        super(PfValidationError, self).__init__(msg, args)


class ValidateYearMonth(argparse.Action):
    """Argparse validator for year and month."""
    def __call__(self, parser, args, values, option_string=None):
        valid_years = range(START_YEAR, MAX_YEAR)
        valid_months = range(1,12)
        (year, month) = values
        year = int(year)
        if year not in valid_years:
            raise ValueError("invalid year {s!r}".format(s=year))
        month = int(month)
        if month not in valid_months:
            raise ValueError("invalid month {s!r}".format(s=month))
        setattr(args, self.dest, YearMonth(year, month))

class StoreDeployType(argparse.Action):
    """Argparse action for handing the Deployment Type."""
    def __call__(self, parser, args, value, option_string=None):
        """Store the Deployment type.

        Expects values to contain a single element.

        If values[0] is both, then set the resulting attribute to DEPLOYMENT_TYPES
        """
        r = value
        if value not in DEPLOYMENT_TYPES+['both']:
            raise ValueError("invalid deployment type {s!r}".format(s=value))
        if value == 'both':
            r = DEPLOYMENT_TYPES
        setattr(args, self.dest, r)

class StoreMapType(argparse.Action):
    """Argparse action for handing the Map Type."""
    def __call__(self, parser, args, value, option_string=None):
        """Store the Map type.

        Expects values to contain a single element.

        If values[0] is both, then set the resulting attribute to MAP_TYPES
        """
        r = value
        if value not in MAP_TYPES+['both']:
            raise ValueError("invalid map type {s!r}".format(s=value))
        if value == 'both':
            r = MAP_TYPES
        setattr(args, self.dest, r)




class USArrayDeployMap():
    """The usarray_deploy_map application."""

    def _parse_args(self, args):
        """Parse our command-line arguments."""
        parser = argparse.ArgumentParser()
        parser.add_argument("deploytype", type=str,
                            help="type of deployment to plot",
                            choices=DEPLOYMENT_TYPES+['both'], default='both', action=StoreDeployType)
        parser.add_argument("maptype", type=str, help="type of map to plot",
                            choices=MAP_TYPES+['both'], default='both', action=StoreMapType)
        parser.add_argument("-v", "--verbose", action="store_true",
                            help="verbose output")
        parser.add_argument("-x", "--debug", action="store_true",
                            help="debug script")
        parser.add_argument("-s", "--size", type=str,
                            help="generate different sizes")
        parser.add_argument(
            "-t", "--time", type=int, nargs=2, help="year and month to plot",
            default=getDefaultYearMonth(), action=ValidateYearMonth
        )
        parser.add_argument("-p", "--pfname", type=str, help="parameter file", default="usarray_deploy_map")

        self.args = parser.parse_args(args)

    def _read_pf(self):
        parameter_file = stock.pfread(self.args.pfname)
        common_pf = stock.pfin(os.path.abspath(os.path.expanduser(parameter_file["common_pf"])))
        stations_pf = stock.pfin(os.path.abspath(os.path.expanduser(parameter_file["stations_pf"])))
        return common_pf, stations_pf, parameter_file


    def generate_times(year, month):
        """Generate start and end time unix timestamps for dbsubsets """

        logger.debug("month:%s" % month)
        logger.debug("year:%s " % year)
        month = int(month)
        year = int(year)
        next_year = year
        next_month = month + 1
        if next_month > 12:
            next_month = 1
            next_year = next_year + 1

        logger.debug("next_month: " + next_month)
        logger.debug("next_year: " + next_year)

        start_time = stock.str2epoch("%02d/01/%4d 00:00:00" % (month, year))
        end_time = stock.str2epoch("%02d/01/%4d 00:00:00" % (next_month, next_year))
        logger.info("START:%s => %s" % (start_time, stock.strdate(start_time)))
        logger.info("END:%s => %s" % (end_time, stock.strdate(end_time)))

        return start_time, end_time


    def generate_inframet_locations(db, mtype, deploytype, year, month,
                                    imap=False, verbose=False, debug=False):
        """Generate inframet locations for specific
        periods in time and write out to xy files
        suitable for GMT
        """
        # Build the Datascope query str.
        # For some reason this list comprehensions
        # has to be at the top of a function?
        # Cannot reproduce in independent tests?

        qstr = "|".join(["|".join(v) for k, v in imap.iteritems()])
        start_time, end_time = USArrayDeployMap.generate_times(year, month)

        logger.info("Infrasound: Searching sitechan table for chans that match: " + qstr)

        with antdb.closing(antdb.dbopen(db, "r")) as infraptr:
            process_list = [
                "dbopen sitechan",
                "dbjoin deployment",
                "dbjoin site",
                "dbsubset deployment.time <= %s" % end_time,
                "dbsubset chan=~/(%s)/" % qstr,
            ]
            #'dbsubset ondate <= %s' % end_time # Remove future deployed stations

            if mtype == "rolling":
                # process_list.append('dbsubset endtime >= %s' % start_time) # No decommissioned stations for rolling plot
                process_list.append(
                    "dbsubset deployment.endtime >= %s" % start_time
                )  # No decommissioned stations for rolling plot
            elif mtype != "cumulative":
                logger.error(
                    "generate_inframet_locations(): Inframet Error: Map type ('%s') is not recognized"
                    % mtype
                )
                return -1

            process_list.append("dbsort sta ondate chan time")

            try:
                infraptr = infraptr.process(process_list)
            except Exception:
                logger.exception("Dbprocessing failed.")
                return -1
            else:
                all_stations = {}

                infra_tmp_all = tempfile.mkstemp(
                    suffix=".xy", prefix="deployment_list_inframet_ALL_"
                )

                infra_tmp_ncpa = tempfile.mkstemp(
                    suffix=".xy", prefix="deployment_list_inframet_NCPA_"
                )

                infra_tmp_setra = tempfile.mkstemp(
                    suffix=".xy", prefix="deployment_list_inframet_SETRA_"
                )

                infra_tmp_mems = tempfile.mkstemp(
                    suffix=".xy", prefix="deployment_list_inframet_MEMS_"
                )

                file_list = {
                    "complete": infra_tmp_all[1],
                    "ncpa": infra_tmp_ncpa[1],
                    "setra": infra_tmp_setra[1],
                    "mems": infra_tmp_mems[1],
                }

                counter = {"complete": 0, "ncpa": 0, "setra": 0, "mems": 0}

                if mtype == "cumulative":
                    infra_tmp_decom = tempfile.mkstemp(
                        suffix=".xy", prefix="deployment_list_inframet_DECOM_"
                    )
                    # Add the DECOM by hand as it is a manufactured
                    # file, not a snet per se. Call it _DECOM to force
                    # it to plot first
                    file_list["1_DECOM"] = infra_tmp_decom[1]
                    counter["decom"] = 0
                try:
                    infraptr_grp = infraptr.group("sta")
                except Exception:
                    logger.exception("Dbgroup failed")
                    return -1
                else:
                    with antdb.freeing(infraptr_grp):
                        # Get values into a easily digestible dict
                        for record in infraptr_grp.iter_record():
                            sta, [db, view, end_rec, start_rec] = record.getv(
                                "sta", "bundle"
                            )
                            all_stations[sta] = {
                                "sensors": {"MEMS": False, "NCPA": False, "SETRA": False},
                                "location": {"lat": 0, "lon": 0},
                            }
                            for j in range(start_rec, end_rec):
                                infraptr.record = j
                                # Cannot use time or endtime as that applies to the station, not to the inframet sensor
                                ondate, offdate, chan, lat, lon = infraptr.getv(
                                    "ondate", "offdate", "chan", "lat", "lon"
                                )
                                all_stations[sta]["location"]["lat"] = lat
                                all_stations[sta]["location"]["lon"] = lon

                                ondate = stock.epoch(ondate)

                                if offdate > 0:
                                    offdate = stock.epoch(offdate)
                                else:
                                    offdate = "NULL"

                                if chan == "LDM_EP":
                                    if ondate <= end_time and (
                                        offdate == "NULL" or offdate >= start_time
                                    ):
                                        all_stations[sta]["sensors"]["MEMS"] = True
                                elif chan == "BDF_EP" or chan == "LDF_EP":
                                    if ondate <= end_time and (
                                        offdate == "NULL" or offdate >= start_time
                                    ):
                                        all_stations[sta]["sensors"]["NCPA"] = True
                                elif chan == "BDO_EP" or chan == "LDO_EP":
                                    if ondate <= end_time and (
                                        offdate == "NULL" or offdate > start_time
                                    ):
                                        all_stations[sta]["sensors"]["SETRA"] = True
                                else:
                                    logger.warning("Channel %s not recognized" % chan)
                        #
                        logger.debug(all_stations)

                        # Process dict
                        for sta in sorted(all_stations.iterkeys()):
                            logger.info("Working on station %s" % sta)
                            lat = all_stations[sta]["location"]["lat"]
                            lon = all_stations[sta]["location"]["lon"]
                            sensors = all_stations[sta]["sensors"]
                            if mtype == "rolling":
                                if sensors["MEMS"] and sensors["NCPA"] and sensors["SETRA"]:
                                    os.write(
                                        infra_tmp_all[0],
                                        "%s    %s    # %s \n" % (lat, lon, sta),
                                    )
                                    counter["complete"] += 1
                                elif sensors["MEMS"] and sensors["NCPA"]:
                                    os.write(
                                        infra_tmp_ncpa[0],
                                        "%s    %s    # %s \n" % (lat, lon, sta),
                                    )
                                    counter["ncpa"] += 1
                                elif sensors["MEMS"] and sensors["SETRA"]:
                                    os.write(
                                        infra_tmp_setra[0],
                                        "%s    %s    # %s \n" % (lat, lon, sta),
                                    )
                                    counter["setra"] += 1
                                elif sensors["MEMS"]:
                                    os.write(
                                        infra_tmp_mems[0],
                                        "%s    %s    # %s \n" % (lat, lon, sta),
                                    )
                                    counter["mems"] += 1
                            elif mtype == "cumulative":
                                if (
                                    not sensors["MEMS"]
                                    and not sensors["NCPA"]
                                    and not sensors["SETRA"]
                                ):
                                    os.write(
                                        infra_tmp_decom[0],
                                        "%s    %s    # DECOM %s \n" % (lat, lon, sta),
                                    )
                                    counter["decom"] += 1
                                else:
                                    if (
                                        sensors["MEMS"]
                                        and sensors["NCPA"]
                                        and sensors["SETRA"]
                                    ):
                                        os.write(
                                            infra_tmp_all[0],
                                            "%s    %s    # %s \n" % (lat, lon, sta),
                                        )
                                        counter["complete"] += 1
                                    elif sensors["MEMS"] and sensors["NCPA"]:
                                        os.write(
                                            infra_tmp_ncpa[0],
                                            "%s    %s    # %s \n" % (lat, lon, sta),
                                        )
                                        counter["ncpa"] += 1
                                    elif sensors["MEMS"] and sensors["SETRA"]:
                                        os.write(
                                            infra_tmp_setra[0],
                                            "%s    %s    # %s \n" % (lat, lon, sta),
                                        )
                                        counter["setra"] += 1
                                    elif sensors["MEMS"]:
                                        os.write(
                                            infra_tmp_mems[0],
                                            "%s    %s    # %s \n" % (lat, lon, sta),
                                        )
                                        counter["mems"] += 1
                        os.close(infra_tmp_all[0])
                        os.close(infra_tmp_mems[0])
                        if mtype == "cumulative":
                            os.close(infra_tmp_decom[0])
        return file_list, counter


    def generate_sta_locations(db, mtype, deploytype, year, month,
                               verbose=False, debug=False):
        """Generate station locations for specific
        periods in time and write out to xy files
        suitable for GMT
        """
        start_time, end_time = USArrayDeployMap.generate_times(year, month)

        # Define dbops
        process_list = [
            "dbopen site",
            "dbjoin snetsta",
            "dbjoin deployment",
            "dbsubset deployment.time <= %s" % end_time,
            "dbsort snet sta",
        ]
        with antdb.closing(antdb.dbopen(db, "r")) as dbptr:
            dbptr = dbptr.process(process_list)

            # Get networks
            snetptr = dbptr.sort("snet", unique=True)
            usnets = []
            try:
                with antdb.freeing(snetptr):
                    for record in snetptr.iter_record():
                        mysnet = record.getv("snet")[0]
                        usnets.append(mysnet)
                        logger.info("Adding snet:%s" % mysnet)
            except Exception:
                logger.exception()
                return -1

            # If we don't want to plot cumulative then remove old stations
            if mtype == "rolling":
                dbptr = dbptr.subset("deployment.endtime >= %s" % start_time)
            else:
                this_decom_counter = 0

            file_list = {}
            counter = {}

            dfile = tempfile.mkstemp(suffix=".xy", prefix="deployment_list_DECOM_")
            decom_ptr = dfile[0]
            decom_name = dfile[1]

            # Loop over unqiue snets
            for s in usnets:

                logger.info("generate_sta_locations(): Working on network: " + s)

                try:
                    dbptr_snet = dbptr.subset("snet=~/%s/" % s)
                except Exception:
                    logger.exception()
                    return -1

                if dbptr_snet.query("dbRECORD_COUNT") < 1:
                    continue

                stmp = tempfile.mkstemp(suffix=".xy", prefix="deployment_list_%s_" % s)
                file_ptr = stmp[0]
                file_name = stmp[1]

                this_counter = 0
                for record in dbptr_snet.iter_record():
                    if mtype == "rolling":
                        sta, lat, lon, snet = record.getv("sta", "lat", "lon", "snet")
                        os.write(file_ptr, "%s    %s    # %s %s\n" % (lat, lon, snet, sta))
                        this_counter = this_counter + 1
                    elif mtype == "cumulative":
                        sta, lat, lon, snet, sta_time, sta_endtime = record.getv(
                            "sta", "lat", "lon", "snet", "time", "endtime"
                        )
                        if sta_endtime >= start_time:
                            os.write(
                                file_ptr, "%s    %s    # %s %s\n" % (lat, lon, snet, sta)
                            )
                            this_counter = this_counter + 1
                        else:
                            os.write(
                                decom_ptr, "%s    %s    # DECOM %s\n" % (lat, lon, sta)
                            )
                            this_decom_counter = this_decom_counter + 1
                counter[s] = this_counter
                os.close(file_ptr)
                file_list[s] = file_name

            if mtype == "cumulative":
                counter["decom"] = this_decom_counter

        # Add the DECOM by hand as it is a manufactured
        # file, not a snet per se. Call it _DECOM to force
        # it plot first
        file_list["1_DECOM"] = decom_name
        os.close(decom_ptr)

        return file_list, counter


    def set_gmt_params(paper_orientation, paper_media):
        """ Calls gmtset to configure various GMT parameters just for this script """

        # Leaving on shell=True just in case Rob had some magic environment
        # set up that this script doesn't define explicily

        # Plot media
        check_call(
            " ".join(
                [
                    "gmt set",
                    "PS_PAGE_COLOR",
                    "255/255/255",
                    "PS_PAGE_ORIENTATION",
                    paper_orientation,
                    "PS_MEDIA",
                    paper_media,
                ]
            ),
            shell=True,
        )

        # Basemap Anotation Parameters
        check_call(
            " ".join(
                [
                    "gmt set",
                    "MAP_ANNOT_OFFSET_PRIMARY",
                    "0.2c",
                    "MAP_ANNOT_OFFSET_SECONDARY",
                    "0.2c",
                    "MAP_LABEL_OFFSET",
                    "0.2c",
                ]
            ),
            shell=True,
        )

        # Basemap Layout Parameters
        check_call(
            " ".join(
                [
                    "gmt set",
                    "MAP_FRAME_WIDTH",
                    "0.2c",
                    "MAP_SCALE_HEIGHT",
                    "0.2c",
                    "MAP_TICK_LENGTH",
                    "0.2c",
                    "X_AXIS_LENGTH",
                    "25c",
                    "Y_AXIS_LENGTH",
                    "15c",
                    "MAP_ORIGIN_X",
                    "2.5c",
                    "MAP_ORIGIN_Y",
                    "2.5c",
                    "MAP_LOGO_POS",
                    "BL/-0.2c/-0.2c",
                ]
            ),
            shell=True,
        )

        # Miscellaneous
        check_call(
            " ".join(["gmt set", "MAP_LINE_STEP", "0.025c", "PROJ_LENGTH_UNIT", "inch"]),
            shell=True,
        )
        # Miscellaneous
        check_call(
            " ".join(["gmt set", "DIR_GSHHG", "/usr/share/gshhg-gmt-nc4"]), shell=True
        )


    def gmt_fix_land_below_sealevel(
        regionname, description, region, center, outfile, wet_rgb
    ):
        """run psclip to fix coloring of dry areas that are below sea-level"""

        landfile = "land_only.cpt"
        grdfile = regionname + ".grd"
        gradientfile = regionname + ".grad"
        xyfile = regionname + ".xy"

        # Define a clip region
        try:
            check_call(
                "gmt psclip %s -R%s -JE%s -V -K -O >> %s"
                % (xyfile, region, center, outfile),
                shell=True,
            )
        except OSError:
            logger.exception(description + " gmt psclip execution failed")
            return -1

        # Make area 'land-only' and put into the clipping region
        try:
            check_call(
                "gmt grdimage %s -V -R%s -JE%s -C%s -I%s -O -K >> %s"
                % (grdfile, region, center, landfile, gradientfile, outfile),
                shell=True,
            )
        except OSError:
            logger.exception(description + " gmt grdimage execution failed")
            return -1

        # Color the actual water areas blue
        try:
            check_call(
                "gmt pscoast -V -R%s -JE%s -C%s -Df -O -K >> %s"
                % (region, center, wet_rgb, outfile),
                shell=True,
            )
        except OSError:
            logger.exception(description + " gmt pscoast execution failed")
            return -1

        # Close psclip
        try:
            check_call("gmt psclip -C -K -O >> %s" % outfile, shell=True)
        except OSError:
            logger.exception(description + " gmt psclip execution failed")
            return -1


    def gmt_plot_wet_and_coast(region, center, wet_rgb, outfile):
        """plot wet areas and coastline"""
        try:
            # Plot wet areas (not coast)
            check_call(
                "gmt pscoast"
                + " -V -R%s -JE%s -W0.5p,%s -S%s -A0/2/4 -Df -O -K >> %s"
                % (region, center, wet_rgb, wet_rgb, outfile),
                shell=True,
            )
            # Plot coastline in black
            check_call(
                "gmt pscoast"
                + " -V -R%s -JE%s -W0.5p,0/0/0 -Df -O -K >> %s" % (region, center, outfile),
                shell=True,
            )
            # Plot major rivers
            check_call(
                "gmt pscoast"
                + " -V -R%s -JE%s -Ir/0.5p,0/0/255 -Df -O -K >> %s"
                % (region, center, outfile),
                shell=True,
            )
            # Plot national (N1) and state (N2) boundaries
            # retcode = check_call("gmt pscoast"+" -V -R%s -JE%s -N1/5/0/0/0 -N2/1/0/0/0 -Df -O -K >> %s" % (region, center, outfile), shell=True)
            check_call(
                "gmt pscoast"
                + " -V -R%s -JE%s -N1/1 -N2/0.2 -Df -O -K >> %s"
                % (region, center, outfile),
                shell=True,
            )
        except OSError:
            logger.exception("A pscoast call failed.")
            return -2


    def gmt_overlay_grid(region, center, coords, legendloc, outfile):
        """Overlay the grid for a given region"""
        try:
            check_call(
                "gmt psbasemap -X0 -Y0 -R%s -JE%s -V -Bg%swesn -Lf%sk+l -O -K >> %s"
                % (region, center, coords, legendloc, outfile),
                shell=True,
            )
        except OSError:
            logger.exception("gmt psbasemap execution failed.")
            return -1


    def gmt_add_stations(station_loc_files, symsize, rgbs, outfile):
        """Overlay the station icons"""
        for key in sorted(station_loc_files.iterkeys()):
            if key == "IU" or key == "US":
                # Plots diamond symbols for US backbone stations
                symtype = "d"
            else:
                symtype = "t"

            try:
                check_call(
                    "gmt psxy %s -R -JE -V -S%s%s -G%s -W -L -O -K -: >> %s"
                    % (station_loc_files[key], symtype, symsize, rgbs[key], outfile),
                    shell=True,
                )
            except OSError:
                logger.exception("gmt psxy execution failed.")
                return -1


    def __init__(self, argv):
        """Main processing script for all maps """

        self.logger = getAppLogger(__name__)
        self.logger.info("Starting " + sys.argv[0])
        self._parse_args(argv[1:])
        (self.common_pf, self.stations_pf, self.parameter_file) = self._read_pf()
        if self.args.debug:
            logger.debug("*** DEBUGGING ON ***")
            logger.debug("*** No grd or grad files - just single color for speed ***")

        logger.debug(str(self.common_pf))
        logger.debug(str(self.stations_pf))

        self.dbmaster = self.common_pf.get("USARRAY_DBMASTER")
        self.networks = self.stations_pf.get("network")
        self.infrasound = self.stations_pf.get("infrasound")
        self.colors = self.stations_pf.get("colors")
        # Force the tmp dir environmental variable
        self.tmp = self.common_pf.get("TMP")
        self.gmtbindir = self.common_pf.get("GMT_BIN")
        self.usa_coords = self.common_pf.get("USACOORDS")
        self.ak_coords = self.common_pf.get("AKCOORDS")
        self.web_output_dir = self.common_pf.get("CACHE_MONTHLY_DEPLOYMENT")
        self.web_output_dir_infra = self.common_pf.get("CACHE_MONTHLY_DEPLOYMENT_INFRA")
        self.infrasound_mapping = self.common_pf.get("INFRASOUND_MAPPING")
        self.output_dir = self.parameter_file.get("output_dir")

        if self.args.size == "wario":
            self.paper_orientation = "landscape"
            self.paper_media = "b0"
            self.symsize = "0.3"
        else:
            self.paper_orientation = "portrait"
            self.paper_media = "a1"
            self.symsize = "0.15"


    def run(self):
        sys.path.append(self.gmtbindir)
        os.environ["TMPDIR"] = os.environ["TEMP"] = os.environ["TMP"] = self.tmp
        # Make sure execution occurs in the right directory
        #    cwd = os.getcwd()
        #    path_parts = cwd.split('/')
        #    if path_parts[-1] == 'deployment_history' and path_parts[-2] == 'bin':
        #        if verbose or debug:
        #            print ' - Already in the correct current working directory %s' % cwd
        #    else:
        #        cwd = os.getcwd() + '/data/deployment_history'
        #        if verbose or debug:
        #            print ' - Changed current working directory to %s' % cwd
        #        os.chdir(cwd)
        real_data_dir = os.path.abspath(os.path.expanduser(self.parameter_file["data_dir"]))
        real_cwd = os.path.abspath(os.getcwd())
        if real_cwd != real_data_dir:
            os.chdir(real_data_dir)
            logger.info(
                "Changed current working directory to " + real_data_dir
            )

        # Make sure we set some GMT parameters for just this script
        # GMTSET
        try:
            self.__class__.set_gmt_params(self.paper_orientation, self.paper_media)
        except Exception:
            logger.exception("An error occurred setting GMT params")
            return -1

        for m in self.args.maptype:
            if self.args.size == "wario":
                ps = tempfile.mkstemp(
                    suffix=".ps",
                    prefix="deployment_history_map_%s_%d_%02d_%s_WARIO_"
                    % (self.args.deploytype, self.args.time.year, self.args.time.month, m),
                )
                png = "PNG not created for tiled display wario. Create by hand in Photoshop"
            else:
                ps = tempfile.mkstemp(
                    suffix=".ps",
                    prefix="deployment_history_map_%s_%d_%02d_%s_"
                    % (self.args.deploytype, self.args.time.year, self.args.time.month, m),
                )
                if self.args.deploytype == "inframet":
                    finalfile = "deploymap_%s_%d_%02d.%s.png" % (self.args.deploytype, self.args.time.year, self.args.time.month, m)
                else:
                    finalfile = "deploymap_%d_%02d.%s.png" % (self.args.time.year, self.args.time.month, m)
                png = "%s/%s" % (self.output_dir, finalfile)

            logger.info("Working on maptype: " + m)
            logger.info("Temp postscript file: " + ps[1])
            logger.info("Output target: " + png)

            # Determine region of interest and center of plot
            # The lat and lon padding ensures we get full topo and bathy.
            minlon = int(self.usa_coords["MINLON"])
            maxlon = int(self.usa_coords["MAXLON"])
            minlat = int(self.usa_coords["MINLAT"])
            maxlat = int(self.usa_coords["MAXLAT"])
            region = "%s/%s/%s/%s" % (minlon, minlat, maxlon, maxlat) + "r"
            centerlat = (maxlat - minlat) / 2 + minlat
            centerlon = (maxlon - minlon) / 2 + minlon

            ak_minlon = int(self.ak_coords["MINLON"])
            ak_maxlon = int(self.ak_coords["MAXLON"])
            ak_minlat = int(self.ak_coords["MINLAT"])
            ak_maxlat = int(self.ak_coords["MAXLAT"])
            ak_region = "%s/%s/%s/%s" % (ak_minlon, ak_minlat, ak_maxlon, ak_maxlat) + "r"
            ak_centerlat = (ak_maxlat - ak_minlat) / 2 + ak_minlat
            ak_centerlon = (ak_maxlon - ak_minlon) / 2 + ak_minlon

            if self.args.size == "wario":
                center = "%s/%s/%s" % (centerlon, centerlat, "44") + "i"
                ak_center = "%s/%s/%s" % (ak_centerlon, ak_centerlat, "10") + "i"
            else:
                center = "%s/%s/%s" % (centerlon, centerlat, self.usa_coords["WIDTH"]) + "i"
                ak_center = (
                    "%s/%s/%s" % (ak_centerlon, ak_centerlat, self.ak_coords["WIDTH"]) + "i"
                )

            logger.info("GMT USA region string: " + region)
            logger.info("GMT USA center location string: " + center)
            logger.info("GMT AK region string: " + ak_region)
            logger.info("GMT AK center location string: " + ak_center)

            if self.args.deploytype == "seismic":
                station_loc_files, counter = self.generate_sta_locations(
                    self.dbmaster, m, self.args.deploytype, self.args.time.year, self.args.time.month, self.args.verbose, self.args.debug
                )
                rgbs = {
                    "1_DECOM": "77/77/77"
                }  # Init with the missing color and force to be first plotted
            elif self.args.deploytype == "inframet":
                station_loc_files, counter = self.generate_inframet_locations(
                    self.dbmaster, m, self.args.deploytype, self.args.time.year, self.args.time.month, self.infrasound_mapping, self.args.verbose, self.args.debug
                )
                rgbs = {
                    "1_DECOM": "255/255/255"
                }  # Init with the missing color and force to be first plotted

            snets_text = {}
            for key in sorted(station_loc_files.iterkeys()):
                if self.args.deploytype == "seismic":
                    if key in self.networks:
                        color = self.networks[key]["color"]
                        rgbs[key] = self.colors[color]["rgb"].replace(",", "/")
                        snets_text[key] = self.networks[key]["abbrev"].replace(" ", "\ ")
                elif self.args.deploytype == "inframet":
                    logger.debug("Working on inframet key: " + key)
                    if key in self.infrasound:
                        color = self.infrasound[key]["color"]
                        rgbs[key] = self.colors[color]["rgb"].replace(",", "/")
                        snets_text[key] = self.infrasound[key]["name"].replace(" ", "\ ")
            # Extra key for the decommissioned stations group
            if m == "cumulative":
                if self.args.deploytype == "seismic":
                    color = self.networks["DECOM"]["color"]
                    rgbs["decom"] = self.colors[color]["rgb"].replace(",", "/")
                elif self.args.deploytype == "inframet":
                    color = self.infrasound["decom"]["color"]
                    rgbs["decom"] = self.colors[color]["rgb"].replace(",", "/")

            # Create the contiguous United States topography basemap

            # {{{ Contiguous United States

            logger.info("Working on contiguous United States")

            if self.args.debug == True:
                try:
                    check_call(
                        "gmt pscoast -R%s -JE%s -Df -A5000 -S%s -G40/200/40 -V -X2 -Y2 -K >> %s"
                        % (region, center, WET_RGB, ps[1]),
                        shell=True,
                    )
                except OSError:
                    logger.exception(
                        "gmt pscoast for contiguous United States execution failed"
                    )
                    return -1
            else:
                try:
                    check_call(
                        "gmt grdimage usa.grd -R%s -JE%s -Cland_ocean.cpt -Iusa.grad -V -E100 -X2 -Y2 -K >> %s"
                        % (region, center, ps[1]),
                        shell=True,
                    )
                except OSError:
                    logger.exception("gmt grdimage for usa.grd execution failed")
                    return -1

            # Plot land areas below sea level correctly

            # Salton Sea co-ords -R-116.8/-115/32/34
            USArrayDeployMap.gmt_fix_land_below_sealevel(
                "saltonsea", "Salton Sea", region, center, ps[1], WET_RGB
            )

            # Death Valley co-ords -R
            USArrayDeployMap.gmt_fix_land_below_sealevel(
                "deathvalley", "Death Valley", region, center, ps[1], WET_RGB
            )

            # Plot wet areas and coastline
            self.gmt_plot_wet_and_coast(region, center, WET_RGB, ps[1])

            # Overlay the grid
            self.gmt_overlay_grid(
                region, center, self.usa_coords["GRIDLINES"], "-75/30/36/500", ps[1]
            )

            # Add stations from local text files
            self.gmt_add_stations(station_loc_files, self.symsize, rgbs, ps[1])

            # }}} Contiguous United States

            logger.info(" - Working on Alaska inset")

            # {{{ Alaska

            if self.args.debug == True:
                try:
                    check_call(
                        "gmt pscoast -R%s -JE%s -Df -A5000 -S%s -G40/200/40 -V -X0.1i -Y0.1i -O -K >> %s"
                        % (ak_region, ak_center, WET_RGB, ps[1]),
                        shell=True,
                    )
                except OSError:
                    logger.exception("gmt pscoast for Alaska execution failed")
                    return -4
            else:
                try:
                    check_call(
                        "gmt grdimage alaska.grd -R%s -JE%s -Cland_ocean.cpt -Ialaska.grad -V -E100 -X0.1i -Y0.1i -O -K >> %s"
                        % (ak_region, ak_center, ps[1]),
                        shell=True,
                    )
                except OSError:
                    logger.exception("gmt grdimage for alaska.grd execution failed")
                    return -5

            # Plot wet areas and coastline
            USArrayDeployMap.gmt_plot_wet_and_coast(ak_region, ak_center, WET_RGB, ps[1])

            # Overlay the grid
            USArrayDeployMap.gmt_overlay_grid(
                ak_region, ak_center, self.ak_coords["GRIDLINES"], "-145/57/60/500", ps[1]
            )

            # Add stations from local text files
            USArrayDeployMap.gmt_add_stations(station_loc_files, self.symsize, rgbs, ps[1])

            # }}} Alaska

            # Clean up station files
            for key in sorted(station_loc_files.iterkeys()):
                os.unlink(station_loc_files[key])

            logger.debug("Working on year and month timestamp")
            # Create the text files of year & month and legend
            time_file = tempfile.mkstemp(suffix=".txt", prefix="year_month_")
            # time_file = "%syear_month.txt" % tmp
            tf = open(time_file[1], "w")
            tf.write("-75.5    17    20    0    1    BR    %d\ %02d" % (self.args.time.year, self.args.time.month))
            tf.close()

            logger.debug("Working on copyright file")
            copyright_file = tempfile.mkstemp(suffix=".txt", prefix="copyright_")
            # copyright_file = "%scopyright.txt" % tmp
            cf = open(copyright_file[1], "w")
            cf.write(
                "-67    48.7    11    0    1    BR    (c)\ 2004\ -\ %s\ Array\ Network\ Facility,\ http://anf.ucsd.edu"
                % self.args.time.year
            )
            cf.close()

            logger.debug("Working on snet files")
            snets_file = tempfile.mkstemp(suffix=".txt", prefix="snets_")
            sf = open(snets_file[1], "w")
            if self.args.size == "wario":
                legend_symsize = "0.3"
            else:
                legend_symsize = "0.15"
            snet_file_txt = "G 0.06i\n"
            snet_file_txt += "H 14 Helvetica-Bold Network Legend\n"
            snet_file_txt += "D 0.06i 1p\n"  # A horizontal line
            snet_file_txt += "N 1\n"
            snet_file_txt += "V 0 1p\n"
            snet_symbol = "t"
            for key in sorted(snets_text.iterkeys()):
                snet_symbol = "t"
                logger.info("snets: " + key)
                if key == "IU" or key == "US":
                    snet_symbol = "d"
                snet_file_txt += "S 0.1i %s %s %s 0.25p 0.3i %s\ [%s]\n" % (
                    snet_symbol,
                    legend_symsize,
                    rgbs[key],
                    snets_text[key],
                    counter[key],
                )
            if m == "cumulative":
                snet_file_txt += "D 0.06i 1p\n"  # A horizontal line
                snet_file_txt += "S 0.1i %s %s %s 0.25p 0.3i Decommissioned\ [%s]\n" % (
                    snet_symbol,
                    legend_symsize,
                    rgbs["decom"],
                    counter["decom"],
                )
            sf.write(snet_file_txt)
            sf.close()

            # Overlay the copyright notice
            logger.info("Overlay the copyright notice")

            try:
                check_call(
                    "gmt pstext %s -R%s -JE%s -V -D0.25/0.25 -P -O -K >> %s"
                    % (copyright_file[1], region, center, ps[1]),
                    shell=True,
                )
            except OSError:
                logger.exception("Copyright msg plotting error: pstext execution failed")
                os.unlink(copyright_file[1])
                return -1
            else:
                os.unlink(copyright_file[1])

            # Overlay the date legend stamp
            logger.info("Overlay the date legend stamp")
            try:
                # " -W255/255/255o1p/0/0/0 -C50% -P -O -K >> " + ps[1],
                check_call(
                    "gmt pstext "
                    + time_file[1]
                    + " -R"
                    + region
                    + " -JE"
                    + center
                    + " -V -D0.25/0.25"
                    + " -G255 -C50% -P -O -K >> "
                    + ps[1],
                    shell=True,
                )
            except OSError:
                logger.exception("Time msg plotting error: pstext execution failed")
                return -1
            else:
                os.unlink(time_file[1])

            # Overlay the snet legend
            logger.info("Overlay the snet legend")

            if self.args.deploytype == "seismic":
                legend_width = "2.6"
                legend_height = "2.98"
            elif self.args.deploytype == "inframet":
                legend_width = "4.2"
                legend_height = "1.7"
            else:
                logger.error("unknown deploytype")
                return -1

            try:
                check_call(
                    "gmt pslegend %s -R%s -JE%s -V -Dg-90/26+w%si/%si+jTC -F+g255/255/255 -P -O >> %s"
                    % (snets_file[1], region, center, legend_width, legend_height, ps[1]),
                    shell=True,
                )
            except OSError:
                logger.exception(
                    "Network (snet) legend plotting error: pslegend execution failed"
                )
                return -2
            else:
                os.unlink(snets_file[1])

            # Run Imagemagick convert cmd on Postscript output
            if self.args.size == "wario":
                print("Your file for wario is ready for photoshop and is called " + ps[1])
            else:
                logger.info(
                    "Running Imagemagick's convert command on postscript file " + ps[1]
                )
                try:
                    check_call(
                        "convert -trim -depth 16 +repage %s %s" % (ps[1], png), shell=True
                    )
                except OSError:
                    logger.exception("convert Execution failed")
                    return -6
                else:
                    os.unlink(ps[1])

                if self.args.deploytype == "inframet":
                    web_output_dir = self.web_output_dir_infra

                logger.info("Going to move %s to %s/%s" % (png, web_output_dir, finalfile))
                try:
                    move(png, "%s/%s" % (web_output_dir, finalfile))
                except OSError:
                    logger.exception("move failed")
                    return -8
                else:
                    print(
                        "Your file is ready and is called %s/%s"
                        % (web_output_dir, finalfile)
                    )

        return 0

def main(argv):
    myapp = USArrayDeployMap(argv)
    return myapp.run()

if __name__ == "__main__":
    result = main(sys.argv)
    sys.exit(result)
