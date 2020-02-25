"""GMT commands for deployment map making."""

import ast
import collections
import csv
import os
import six
from subprocess import check_call
import tempfile

import anf.logutil

from . import constant
from . import util

LOGGER = anf.logutil.getLogger(__name__)


class GmtConfig(object):
    """Track options for GMT commands."""

    def __init__(self, regions, region_positions, global_options={}):
        """Set options for the GmtConfig class.

        Args:
            regions (list[GmtRegion]): list of GmtRegions that this program knows about
            region_positions (dict): dictionary describing layout of various GMTRegions on the map
            global_options (dict): defaults for all instances in key-value format.
        """

        self.global_options = {
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

        self.global_options.update({k.lower(): v for k, v in self.global_options.items()})

        self.regions = regions

        self.region_positions = region_positions


GmtXYStationFileInfo = collections.namedtuple(
    "GmtXYStationFileInfo", ["file_list", "counts"]
)

GMTREGION_FIELDS = [
    'name', 'description', "minlat", "maxlat", "minlon", "maxlon",
    'grdfile', 'gradiantfile']


class GmtRegion(
    collections.namedtuple(
        "GmtRegion", GMTREGION_FIELDS
    )
):
    """Describe a GMT region_data and various metadata including coordinates."""

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
        """Get a GMT region_data string for the region_data."""
        return "{minlon:.0f}/{minlat:.0f}/{maxlon:.0f}/{maxlat:.0f}r".format(
            **(self._asdict())
        )

    def get_azeq_center_str(self, width):
        """Get a center string for an Equal Azimuth projection."""

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
            centerlat=self.centerlon
        )
        )


class CsvRegionReader(six.Iterator):
    """Parse gmt.GmtRegion objects from a list of CSV lines."""

    def __init__(self, csvfile, *args, **kwds):
        """Create a csv.Reader-like object that parses GmtRegion objects from a csvfile.

        Args:
            csvfile (list or iterator): lines of a CSV

        Returns:
            an object which operates like a regular csv.reader but maps the information read into a GMTRegion object,
            which can be treated in a similar fashion to a csv.DictReader. The fields are hard-coded, as the format of
            the table is application dependent. They are as follows:
            * name (string)
            * description (string)
            * minlat (float)
            * maxlat (float)
            * minlin (float)
            * maxlon (float)
            * gridlines (float)
            * gridfile (filename)
            * gradiantfile (filename)

        """

        self.reader = csv.reader(csvfile, skipinitialspace=True, *args, **kwds)
        self.line_num = 0

    @staticmethod
    def _parse(field):
        try:
            cursor = ast.literal_eval(field)
        except SyntaxError:
            cursor = field

        return cursor

    def __iter__(self):
        """Iterator helper method."""
        return self

    def __next__(self):
        """Retrieve the next GmtRegion."""
        row = next(self.reader)
        self.line_num = self.reader.line_num

        # unlike the basic reader, we prefer not to return blanks,
        # because we will typically wind up with a dict full of None
        # values
        while not row:
            row = next(self.reader)

        lf = len(GMTREGION_FIELDS)
        lr = len(row)
        if lf < lr:
            LOGGER.warning("GmtRegion row has too many fields ({:d}). Ignoring {:d} fields.".format(lr, lr - lf))
        elif lf > lr:
            LOGGER.warning(
                "Padding {:d} slots in row with too few fields. (Expected: {:d}, Got: {:d})".format(lf - lr, lf, lr))
            for i in range(lr, lf):
                row[i] = None

        return GmtRegion(
            row[0],  # name
            row[1],  # description
            self._parse(row[2]),  # minlat
            self._parse(row[3]),  # maxlat
            self._parse(row[4]),  # minlon
            self._parse(row[5]),  # maxlon
            row[6],  # gridfile
            row[7]  # gradientfile
        )


class GmtDeployMapPlotter:
    """Plot a deployment map for a given start_time and end_time."""

    deployment_types = {}

    def __init__(self, map_type, deployment_type, start_time, end_time, station_metadata_objects, config):
        """Initialize a deployment map plotter for a particular time period.

        Args:
            map_type (basestring): type of map - either cumulative or rolling
            deployment_type: instrument deployment type to plot. Built-ins include seismic and inframet.
             Others can be added with register_deployment_type.
            start_time (float): epoch start time of active stations
            end_time (float): epoch end time of active stations
            station_metadata_objects (list): list of StationMetadata
            config(GmtConfig): global options for the session

        """

        self.start_time = start_time
        self.end_time = end_time
        self.map_type = map_type
        self.deployment_type = deployment_type
        self.station_metadata_objects = station_metadata_objects
        self.config = config
        self.logging = anf.logutil.getLogger(anf.logutil.fullname(self))

        # Register the two default deployment types, with their XY file generator functions.
        self.register_deployment_type("seismic", self.generate_station_xy_files)
        self.register_deployment_type("inframet", self.generate_extra_sensor_xy_files,
                                      classifer=util.InframetClassifier)

    @classmethod
    def register_deployment_type(cls, name, xy_file_generator, **kwargs):
        """Register a new deployment type.

        Args:
            name (basestring): the name of the deployment type
            xy_file_generator (function): reference to a function that generates XY files.

        """
        deploy_params = kwargs
        deploy_params['xy_file_generator'] = xy_file_generator
        cls.deployment_types[name] = {deploy_params}

    def plot(self) -> str:
        """Make the deployment maps."""
        return None
        # TODO: implement this.

    def generate_xy_files(self, deploy_type, *args, **kwargs):
        """Generate XY files based on the given deploy type.

        Calls a specific generator function based on the deploy_type. The Generator function
        must be registered for the given deployment type with register_deployment_type first.
        """

        return self.deployment_types[deploy_type]['xy_file_generator'](args, kwargs)

    def generate_extra_sensor_xy_files(self, classifier):
        """Output Inframet locations to GMT xy files.

        Args:
            classifier (StationSensorClassifier): utility method to classify a station based on it's extra_sensors

        Returns:
            tuple of filenames and file type counts
        """

        xys = {}
        file_list = {}
        counter = {}

        for sensor_class in classifier.sensor_classes:
            xys[sensor_class] = tempfile.mkstemp(
                suffix=".xy", prefix="deployment_list_inframet_{}_".format(sensor_class.upper())
            )

            file_list[sensor_class] = xys[sensor_class][1]
            counter[sensor_class] = 0

        if self.map_type == "cumulative":
            xys["decom"] = tempfile.mkstemp(
                suffix=".xy", prefix="deployment_list_inframet_DECOM_"
            )
            # Add the DECOM by hand as it is a manufactured
            # file, not a snet per se. Call it _DECOM to force
            # it to plot first
            file_list["1_DECOM"] = xys["decom"][1]
            counter["decom"] = 0

        # Process dict
        for sta_data in self.station_metadata_objects:
            LOGGER.info("Working on station %s" % sta_data.sta)

            if self.map_type == "cumulative" and sta_data.is_decomissioned_at(self.start_time):
                os.write(
                    xys["decom"][0],
                    "{lat:f}    {lon:f}    # DECOM {sta} \n".format(
                        lat=sta_data.lat, lon=sta_data.lon, sta=sta_data.sta
                    ).encode(),
                )
                counter["decom"] += 1
                continue

            xy_line = "{lat:f}    {lon:f}    # {sta} \n".format(
                lat=sta_data.lat, lon=sta_data.lon, sta=sta_data.sta
            ).encode()

            s = classifier.classify(sta_data.extra_sensors)

            if s is not None:
                os.write(xys[s][0], xy_line)
                counter[s] += 1

        for file_info in list(xys.values()):
            os.close(file_info[0])

        return GmtXYStationFileInfo(file_list, counter)

    def generate_station_xy_files(self):
        """Write station locations to GMT xy files.

        Returns:
            A tuple (fnames, counter), where:
                fnames is a dict of `snet` and the respective XY file
                counter is a dict of `snet` and the number of stations of each snet.

        TODO: fix upstream function so that it only takes one 1x2 dict
        TODO: make the fake snet for decomissioned stations match - currently '1_DECOM' (fnames) and 'decom' (counter)
        """

        counter = {"decom": 0}
        """Types of station are tracked in `counter`, by snet. 'decom' is a dummy snet."""

        decom_file_data = tempfile.mkstemp(suffix=".xy", prefix="deployment_list_DECOM_")
        file_info = {"1_DECOM": decom_file_data}

        for station in self.station_metadata_objects:
            try:
                snet_file_data = file_info[station.snet]
            except KeyError:
                counter[station.snet] = 0
                snet_file_data = tempfile.mkstemp(
                    suffix=".xy", prefix="deployment_list_%s_" % station.snet
                )
                file_info[station.snet] = snet_file_data

            if station.is_decommissioned_at(self.start_time):
                counter[station.snet] += 1
                os.write(
                    snet_file_data[0],
                    "{lat:f}    {lon:f}    # {snet} {sta}\n".format(
                        **(station._asdict())  # _asdict is not actually protected, see docs for collection.NamedTuple
                    ).encode(),
                )
            else:  # station is decomissioned
                counter["decom"] += 1
                os.write(
                    decom_file_data[0],
                    "{lat:f}    {lon:f}    # DECOM {snet} {sta}\n".format(
                        **(station._asdict())  # _asdict is not actually protected, see docs for collection.NamedTuple
                    ).encode(),
                )

        # close out all of the file handles
        for fh in [fdata[0] for fdata in file_info.values()]:
            fh.close()

        file_list = {k: v[1] for k, v in file_info}

        return GmtXYStationFileInfo(file_list, counter)

    def set_options(self):
        """Call gmt set to configure global default parameters in the current working directory."""

        set_default_options(self.config.global_options)

    def gmt_fix_land_below_sea_level(
            self, region_name, region_coords, center, outfile, wet_rgb
    ):
        """Run psclip to fix coloring of dry areas that are below sea-level."""

        landfile = "land_only.cpt"
        grdfile = region_name + ".grd"
        gradientfile = region_name + ".grad"
        xyfile = region_name + ".xy"

        # NOTE: formatting is unnecessarily verbose due to Python 2.7 not supporting format strings.
        # While we're in between Python releases, we need manually call .format() instead of just using f strings.

        # Define a clip region
        gmt_run_command("psclip", [xyfile, "-R{}".format(region_coords), "JE{}".format(center), "-V", "-K", "-O"],
                        outfile=outfile)

        # Make area 'land-only' and put into the clipping region
        gmt_run_command("grdimage",
                        [grdfile, "-V", "-R{}".format(region_coords), "-JE{}".format(center), "-C{}".format(landfile),
                         "-I%{}".format(gradientfile), "-O",
                         "-K"], outfile=outfile)

        # Color the actual water areas blue
        gmt_run_command("pscoast",
                        ["-V", "-R{}".format(region_coords), "-JE{}".format(center), "-C{}".format(wet_rgb), "-Df",
                         "-O", "-K"],
                        outfile=outfile)

        # Close psclip
        gmt_run_command("psclip", ["-C", "-K", "-O"], outfile)

    def gmt_plot_wet_and_coast(self, region_coords, center, wet_rgb, outfile):
        """Plot wet areas and coastline."""

        # Plot wet areas (not coast)
        gmt_run_command("pscoast",
                        ['-V', "-R{}".format(region_coords), "-JE{}".format(center), "-W0.5p,{}".format(wet_rgb),
                         "-S{}".format(wet_rgb), "-A0/2/4",
                         "-Df",
                         "-O", "-K"], outfile)

        # Plot coastline in black
        gmt_run_command("pscoast",
                        ['-V', "-R{}".format(region_coords), "-JE{}".format(center), '-W0.5p,0/0/0', '-Df', '-O', '-K'],
                        outfile)

        # Plot major rivers
        gmt_run_command("pscoast",
                        ['-V', "-R{}".format(region_coords), "-JE{}".format(center), '-Ir/0.5p,0/0/255', '-Df', '-O',
                         '-K'],
                        outfile)

        # Plot national (N1) and state (N2) boundaries
        gmt_run_command("pscoast",
                        ['-V', "-R{}".format(region_coords), "-JE{}".format(center), '-N1/1', '-n2/0.2', '-Df', '-O',
                         '-K'],
                        outfile)

    def gmt_overlay_grid(self, region_coords, center, coords, legendloc, outfile):
        """Overlay the grid for a given region_data."""
        gmt_run_command('psbasemap',
                        ['-X0', '-Y0', "-R{}".format(region_coords), "-JE{}".format(center), '-V',
                         "-Bg{}wesn".format(coords),
                         "-Lf{}sk+l".format(legendloc),
                         '-O', '-K'], outfile)

    def gmt_add_stations(self, station_loc_files, symsize, rgbs, outfile):
        """Overlay the station icons."""
        for key in sorted(station_loc_files.keys()):
            if key == "IU" or key == "US":
                # Plots diamond symbols for US backbone stations
                symaptype = "d"
            else:
                symaptype = "t"

            gmt_run_command('psxy',
                            [station_loc_files[key], '-R', '-JE', '-V', "-S{}{}".format([symaptype, symsize]),
                             "-G{}".format(rgbs[key]),
                             '-W', '-L', '-O', '-K', '-:'], outfile)

    def gmt_plot_background(self, outfile, region_name, center, wet_rgb, use_color):
        # Orig US grdimage
        # "gmt grdimage usa.grd -R%s -JE%s -Cland_ocean.cpt -Iusa.grad -V -E100 -X2 -Y2 -K >> %s" % (
        # region, center, ps[1]),
        # Orig AK grdimage
        # "gmt grdimage alaska.grd -R%s -JE%s -Cland_ocean.cpt -Ialaska.grad -V"
        # " -E100 -X0.1i -Y0.1i -O -K >> %s" % (ak_region, ak_center, ps[1])

        # Orig US pscoast
        # "gmt pscoast -R%s -JE%s -Df -A5000 -S%s -G40/200/40 -V -X2 -Y2 -K >> %s"
        #                    % (region, center, constant.WET_RGB, ps[1]),

        # Orig AK pscoast
        # "gmt pscoast -R%s -JE%s -Df -A5000 -S%s -G40/200/40 -V -X0.1i -Y0.1i -O -K >> %s"
        #                    % (ak_region, ak_center, constant.WET_RGB, ps[1]),

        if use_color is False:
            cmd_name = "pscoast"
            args = ["-R{}".format(region_name), "-JE{}".format(center), '-Df', '-A5000', "-S{}".format(wet_rgb),
                    '-G40/200/40', '-V', '-X2',
                    '-Y2', '-K']
        else:
            cmd_name = 'grdimage'
            args = ['usa.grd', "-R{}".format(region_name), "-JE{}".format(center), "-Cland_ocean.cpt", "-Iusa.grad",
                    "-V", "-E100",
                    "-X2", "-Y2", "-K"]

        gmt_run_command(cmd_name, args, outfile)

    def gmt_plot_region(self, outfile, time, map_type, region_data, position_data, output_size_name, output_size_data,
                        use_color=True):
        """Plot a geographic region.

        Args:
            outfile (string): path to output file
            time (yearmonth): tuple of year, month in integer format, 1=Jan 12=Dec
            map_type (string): one of cumulative, rolling
            region_data (GmtRegion): Region metadata
            position_data (dict): contains plot position data for the region being plotted
            output_size_name (string): name of the selected output size
            output_size_data (dict): data related to the selected output size
            use_color (bool): plot in black and white for speed.
        """
        center_coords = region_data.get_azeq_center_str(position_data['width'][output_size_name])
        # plot the base map
        self.gmt_plot_background(region_name=region_data.name, center=center_coords, outfile=outfile,
                                 wet_rgb=constant.WET_RGB, use_color=use_color)

        # Plot wet areas and coastline
        self.gmt_plot_wet_and_coast(region_data, center_coords, constant.WET_RGB, outfile)

        # Overlay the grid
        self.gmt_overlay_grid(
            region_data.name, center_coords, output_size_data["gridlines"], position_data['scaleloc'], outfile
        )

        # Add stations from local text files
        # gmt_add_stations(station_loc_files, self.symsize, rgbs, outfile)


def set_default_options(options):
    """Call `gmt set` to configure global default options in the current working directory."""

    command_name = "set"
    parameters = []
    for key, value in options.items():
        parameters.extend([key.upper(), value])

    gmt_run_command(command_name, parameters)


def gmt_run_command(command_name: str, parameters: list, outfile=None):
    """Run a GMT command with a wrapper function."""
    args = ["gmt", command_name]
    args += parameters
    if outfile is not None:
        out_fh = open(outfile, "rw")
    else:
        out_fh = None
    try:
        check_call(parameters, stdout=out_fh, shell=False)
    except OSError as e:
        LOGGER.exception("gmt %s execution failed", command_name)
    finally:
        out_fh.close()
