"""GMT commands for deployment map making."""

import collections
import os
from subprocess import check_call
import tempfile

import anf.logutil

from . import constant

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


GmtXYStationFileInfo = collections.namedtuple(
    "GmtXYStationFileInfo", ["file_list", "counts"]
)


class GmtRegionCoordinates(
    collections.namedtuple(
        "GmtRegionCoordinates",
        ["minlon", "maxlon", "minlat", "maxlat", "width", "gridlines"],
    )
):
    """Track various coordinates related to a region."""

    __slots__ = ()  # save memory by not creating an internal dict

    @property
    def centerlat(self):
        """Generate the center latitude from the max and min."""
        return (self.maxlat - self.minlat) / 2 + self.minlat

    @property
    def centerlon(self):
        """Generate the center longitude from the max and min."""
        return (self.maxlon - self.minlon) / 2 + self.minlon

    @property
    def regionstr(self):
        """Get a GMT region string for the region."""
        return "{minlon:.0f}/{minlat:.0f}/{maxlon:.0f}/{maxlat:.0f}r".format(
            **(self._asdict())
        )

    def get_azeq_center_str(self, widthoverride=None):
        """Get a center string for an Equal Azimuth projection."""
        if widthoverride is None:
            width = self.width
        else:
            width = widthoverride

        return "{centerlat:.0f}/{centerlon:.0f}/{width}i".format(
            centerlat=self.centerlat, centerlon=self.centerlon, width=width
        )

    def __str__(self):
        """Format the object in a human readable manner."""
        return (
            "GmtRegionCoordinates: Min=({minlat:3.6f}, {minlon:3.6f})"
            + " Max=({maxlat:3.6f}, {maxlon:3.6f})"
            + " Center=({centerlat:3.6f},{centerlon:3.6f)".format(
                minlat=self.minlat,
                minlon=self.minlon,
                maxlat=self.maxlat,
                maxlon=self.maxlon,
                centerlat=self.centerlon,
            )
        )


def generate_inframet_locations(stationmetadatas, maptype, start_time, end_time):
    """Output inframet locations to GMT xy files.

    Args:
        maptype (string): cumulative or rolling

    Returns:
        tuple of filenames and file type counts
    """

    xys = {}
    file_list = {}
    counter = {}

    for ftype in ["complete", "ncpa", "setra", "mems"]:
        xys[ftype] = tempfile.mkstemp(
            suffix=".xy", prefix="deployment_list_inframet_{}_".format(ftype.upper())
        )

        file_list[ftype] = xys[ftype][1]
        counter[ftype] = 0

    if maptype == "cumulative":
        xys["decom"] = tempfile.mkstemp(
            suffix=".xy", prefix="deployment_list_inframet_DECOM_"
        )
        # Add the DECOM by hand as it is a manufactured
        # file, not a snet per se. Call it _DECOM to force
        # it to plot first
        file_list["1_DECOM"] = xys["decom"][1]
        counter["decom"] = 0

    # Process dict
    for sta_data in stationmetadatas:
        LOGGER.info("Working on station %s" % sta_data.sta)
        lat = sta_data.lat
        lon = sta_data.lon
        sensors = sta_data.extra_sensors

        if maptype == "cumulative" and sta_data.is_decomissioned_at(start_time):
            os.write(
                xys["decom"][0],
                "{lat:f}    {lon:f}    # DECOM {sta} \n".format(
                    lat=lat, lon=lon, sta=sta_data.sta
                ).encode(),
            )
            counter["decom"] += 1
            continue

        xy_line = "{lat:f}    {lon:f}    # {sta} \n".format(
            lat=lat, lon=lon, sta=sta_data.sta
        ).encode()
        if sensors["MEMS"] and sensors["NCPA"] and sensors["SETRA"]:
            os.write(xys["complete"][0], xy_line)
            counter["complete"] += 1
        elif sensors["MEMS"] and sensors["NCPA"]:
            os.write(xys["ncpa"][0], xy_line)
            counter["ncpa"] += 1
        elif sensors["MEMS"] and sensors["SETRA"]:
            os.write(xys["setra"][0], xy_line)
            counter["setra"] += 1
        elif sensors["MEMS"]:
            os.write(xys["mems"][0], xy_line)
            counter["mems"] += 1

    for file_info in xys.values:
        os.close(file_info[0])

    return GmtXYStationFileInfo(file_list, counter)


def generate_sta_locations(stationmetadatas, maptype, start_time, end_time):
    """Retrieve station locations from db and write to GMT xy files.

    Args:
        stationmetadatas(iterator of StationMetadata objects): data describing each station.
        maptype (string): cumulative or rolling
        start_time, end_time: bounding times for active stations

    Returns:
        A tuple (fnames, counter), where:
            fnames is a dict of `snet` and the respective XY file
            counter is a dict of `snet` and the number of stations of each snet.

    TODO: fix upstream function so that it only takes one 1x2 dict
    TODO: make the fake snet for decomissioned stations match - currently '1_DECOM' (fnames) and 'decom' (counter)
    """

    file_info = {}

    counter = {"decom": 0}
    """Types of station are tracked in `counter`, by snet. 'decom' is a dummy snet."""

    decom_filedata = tempfile.mkstemp(suffix=".xy", prefix="deployment_list_DECOM_")
    file_info = {"1_DECOM": decom_filedata}

    for station in stationmetadatas:
        try:
            snet_filedata = file_info[station.snet]
        except KeyError:
            counter[station.snet] = 0
            snet_filedata = tempfile.mkstemp(
                suffix=".xy", prefix="deployment_list_%s_" % station.snet
            )
            file_info[station.snet] = snet_filedata

        if station.is_decommissioned_at(start_time):
            counter[station.snet] += 1
            os.write(
                snet_filedata[0],
                "{lat:f}    {lon:f}    # {snet} {sta}\n".format(
                    station._asdict()
                ).encode(),
            )
        else:  # station is decomissioned
            counter["decom"] += 1
            os.write(
                decom_filedata[0],
                "{lat:f}    {lon:f}    # DECOM {snet} {sta}\n".format(
                    station._asdict()
                ).encode(),
            )

    # close out all of the file handles
    for fh in [fdata[0] for fdata in file_info.values()]:
        fh.close()

    file_list = {k: v[1] for k, v in file_info}

    return GmtXYStationFileInfo(file_list, counter)


def set_options(options):
    """Call gmt set to configure various parameters for this script."""

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
    except OSError as e:
        LOGGER.exception(description + " gmt psclip execution failed")
        raise e

    # Make area 'land-only' and put into the clipping region
    try:
        check_call(
            "gmt grdimage %s -V -R%s -JE%s -C%s -I%s -O -K >> %s"
            % (grdfile, region, center, landfile, gradientfile, outfile),
            shell=True,
        )
    except OSError as e:
        LOGGER.exception(description + " gmt grdimage execution failed")
        raise e

    # Color the actual water areas blue
    try:
        check_call(
            "gmt pscoast -V -R%s -JE%s -C%s -Df -O -K >> %s"
            % (region, center, wet_rgb, outfile),
            shell=True,
        )
    except OSError as e:
        LOGGER.exception(description + " gmt pscoast execution failed")
        raise e

    # Close psclip
    try:
        check_call("gmt psclip -C -K -O >> %s" % outfile, shell=True)
    except OSError as e:
        LOGGER.exception(description + " gmt psclip execution failed")
        raise e


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
            symaptype = "d"
        else:
            symaptype = "t"

        try:
            check_call(
                "gmt psxy %s -R -JE -V -S%s%s -G%s -W -L -O -K -: >> %s"
                % (station_loc_files[key], symaptype, symsize, rgbs[key], outfile),
                shell=True,
            )
        except OSError:
            LOGGER.exception("gmt psxy execution failed.")
            raise


def gmt_plot_region(outfile, time, maptype, name, coords, useColor=True):
    """Plot a geographic region.

    Args:
        outfile (string): path to output file
        time (yearmonth): tuple of year, month in integer format, 1=Jan 12=Dec
        maptype (string): one of cumulative, rolling
        coords (GmtRegionCoordinates): Region XY info
        useColor (bool): plot in black and white for speed.
    """
    # plot the basemap
    if useColor is False:
        try:
            check_call(
                [
                    "gmt",
                    "pscoast",
                    "-R{region}".format(region=coords.regionstr),
                    "-JE{center}".format(center=coords.get_azeq_center_str()),
                    "-Df",
                    "-A5000",
                    "-S{wet_rgb}".format(constant.WET_RGB),
                    "-G40/200/40",
                    "-V",
                    "-X2",
                    "-Y2",
                    "-K",
                    ">>",
                    outfile,
                ].join(" "),
                shell=True,
            )
        except OSError:
            LOGGER.exception("gmt pscoast for %s failed", name)
            raise
