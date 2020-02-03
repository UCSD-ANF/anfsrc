"""GMT commands for deployment map making."""

import os
from subprocess import check_call
import tempfile

import anf.logutil
from antelope import datascope, stock

from . import constant, util

LOGGER = anf.logutil.getLogger(__name__)


class GmtOptions(object):
    """Track options for GMT commands."""

    def __init__(self, *args, **kwargs):
        """Set options for the GmtOptions class."""
        self.options = {
            "ps_page_orientation": constant.DEFAULT_PS_PAGE_ORIENTATION,
            "ps_page_color": constant.DEFAULT_PS_PAGE_COLOR,
            "ps_media": constant.DEFAULT_PS_MEDIA,
            # Basemap annotation options
            "map_annot_offset_primary": constant.DEFAULT_MAP_ANNOT_OFFSET_PRIMARY,
            "map_annot_offset_secondary": constant.DEFAULT_MAP_ANNOT_OFFSET_SECONDARY,
            "map_label_offset": constant.DEFAULT_MAP_LABEL_OFFSET,
            # Basemap Layout options
            "map_frame_width": constant.DEFAULT_MAP_FRAME_WIDTH,
            "map_scale_height": constant.DEFAULT_MAP_SCALE_HEIGHT,
            "map_tick_length": constant.DEFAULT_MAP_TICK_LENGTH,
            "x_axis_length": constant.DEFAULT_X_AXIS_LENGTH,
            "y_axis_length": constant.DEFAULT_Y_AXIS_LENGTH,
            "map_origin_x": constant.DEFAULT_MAP_ORIGIN_X,
            "map_origin_y": constant.DEFAULT_MAP_ORIGIN_Y,
            "map_logo_pos": constant.DEFAULT_MAP_LOGO_POS,
            "map_line_step": constant.DEFAULT_MAP_LINE_STEP,
            # Misc options
            "proj_length_unit": constant.DEFAULT_PROJ_LENGTH_UNIT,
            "dir_gshhg": constant.DIR_GSHHG,
        }

        self.options.update({k.lower(): v for k, v in kwargs})


def generate_inframet_locations(
    db, mtype, deploytype, year, month, imap=False, verbose=False, debug=False
):
    """Retrieve from db inframet locations and output to GMT xy files."""

    if mtype not in constant.MAP_TYPES:
        raise ValueError("Map type %s is not recognized.", mtype)

    # Build the Datascope query str.
    # For some reason this list comprehensions
    # has to be at the top of a function?
    # Cannot reproduce in independent tests?

    qstr = "|".join(["|".join(v) for k, v in imap.items()])
    start_time, end_time = util.generate_times(year, month)

    LOGGER.info("Infrasound: Searching sitechan table for chans that match: " + qstr)

    with datascope.closing(datascope.dbopen(db, "r")) as infraptr:
        process_list = [
            "dbopen sitechan",
            "dbjoin deployment",
            "dbjoin site",
            "dbsubset deployment.time <= %s" % end_time,
            "dbsubset chan=~/(%s)/" % qstr,
        ]

        if mtype == "rolling":
            # No decommissioned stations for rolling plot
            process_list.append("dbsubset deployment.endtime >= %s" % start_time)

        process_list.append("dbsort sta ondate chan time")

        try:
            infraptr = infraptr.process(process_list)
        except Exception:
            LOGGER.exception("Dbprocessing failed.")
            raise
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
                LOGGER.exception("Dbgroup failed")
                return -1
            else:
                with datascope.freeing(infraptr_grp):
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
                                LOGGER.warning("Channel %s not recognized" % chan)
                    #
                    LOGGER.debug(all_stations)

                    # Process dict
                    for sta in sorted(all_stations.iterkeys()):
                        LOGGER.info("Working on station %s" % sta)
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


def generate_sta_locations(
    db, mtype, deploytype, year, month, verbose=False, debug=False
):
    """Retrieve station locations from db and write to GMT xy files."""
    start_time, end_time = util.generate_times(year, month)

    # Define dbops
    process_list = [
        "dbopen site",
        "dbjoin snetsta",
        "dbjoin deployment",
        "dbsubset deployment.time <= %s" % end_time,
        "dbsort snet sta",
    ]
    with datascope.closing(datascope.dbopen(db, "r")) as dbptr:
        dbptr = dbptr.process(process_list)

        # Get networks
        snetptr = dbptr.sort("snet", unique=True)
        usnets = []
        try:
            with datascope.freeing(snetptr):
                for record in snetptr.iter_record():
                    mysnet = record.getv("snet")[0]
                    usnets.append(mysnet)
                    LOGGER.info("Adding snet:%s" % mysnet)
        except Exception:
            LOGGER.exception()
            raise

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

            LOGGER.info("generate_sta_locations(): Working on network: " + s)

            try:
                dbptr_snet = dbptr.subset("snet=~/%s/" % s)
            except Exception:
                LOGGER.exception()
                raise

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


def set_options(options):
    """Call gmtset to configure various parameters for this script."""

    commands = ["gmt", "set"]
    for key, value in options.items():
        commands.extend([key.upper(), value])

    check_call(commands)


def gmt_fix_land_below_sealevel(
    regionname, description, region, center, outfile, wet_rgb
):
    """Run psclip to fix coloring of dry areas that are below sea-level."""

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
        LOGGER.exception(description + " gmt psclip execution failed")
        raise

    # Make area 'land-only' and put into the clipping region
    try:
        check_call(
            "gmt grdimage %s -V -R%s -JE%s -C%s -I%s -O -K >> %s"
            % (grdfile, region, center, landfile, gradientfile, outfile),
            shell=True,
        )
    except OSError:
        LOGGER.exception(description + " gmt grdimage execution failed")
        raise

    # Color the actual water areas blue
    try:
        check_call(
            "gmt pscoast -V -R%s -JE%s -C%s -Df -O -K >> %s"
            % (region, center, wet_rgb, outfile),
            shell=True,
        )
    except OSError:
        LOGGER.exception(description + " gmt pscoast execution failed")
        raise

    # Close psclip
    try:
        check_call("gmt psclip -C -K -O >> %s" % outfile, shell=True)
    except OSError:
        LOGGER.exception(description + " gmt psclip execution failed")
        raise


def gmt_plot_wet_and_coast(region, center, wet_rgb, outfile):
    """Plot wet areas and coastline."""
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
        LOGGER.exception("A pscoast call failed.")
        raise


def gmt_overlay_grid(region, center, coords, legendloc, outfile):
    """Overlay the grid for a given region."""
    try:
        check_call(
            "gmt psbasemap -X0 -Y0 -R%s -JE%s -V -Bg%swesn -Lf%sk+l -O -K >> %s"
            % (region, center, coords, legendloc, outfile),
            shell=True,
        )
    except OSError:
        LOGGER.exception("gmt psbasemap execution failed.")
        raise


def gmt_add_stations(station_loc_files, symsize, rgbs, outfile):
    """Overlay the station icons."""
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
            LOGGER.exception("gmt psxy execution failed.")
            raise
