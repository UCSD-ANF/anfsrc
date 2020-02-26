"""The anf.deploymentmap module."""

import argparse
import collections
import os
from pprint import pformat
import string

from anf.logutil import fullname, getLogger, getModuleLogger
from antelope import stock

from . import constant, database, gmtplotter, util
from .. import gmt

LOGGER = getModuleLogger(__name__)

DEFAULT_PARAMS = {
    "symsize": constant.DEFAULT_SYMSIZE,
    "use_color": constant.DEFAULT_USE_COLOR,
    "log_level": constant.DEFAULT_LOG_LEVEL,
}
"""These items may be overriden by read_pf."""

MapFilenames = collections.namedtuple(
    "MapFilenames",
    [
        "intermediate_file_prefix",
        "intermediate_file_suffix",
        "final_file_prefix",
        "final_file_suffix",
    ],
)


class DeploymentMapMaker:
    """Generalized class for generating deployment maps in GMT."""

    pfname = "deploymentmap"
    """Name of the parameter file associated with this class.
    It can be redefined in subclasses to customize the parameter file location
    without having to redefine read_pf."""

    loglevel = "NOTIFY"
    """Logging level of this class."""

    logger = getLogger(__name__)
    """The Logging instance used by class. Overridden for instances in __init__."""

    size_deploy_type_fileformats = constant.SIZE__DEPLOY_TYPE__FILE_FORMATS
    """Filename format strings organized by size, then map_type."""

    def parse_args(self, argv):
        """Parse our command-line arguments.

        Args:
            argv(dict): arguments to parse. Default: sys.argv[1:].
        """

        parser = argparse.ArgumentParser()

        parser.add_argument(
            "deploy_type",
            type=str,
            help="type of deployment to plot",
            choices=constant.DEPLOYMENT_TYPES + ["both"],
            default="both",
            action=util.StoreDeployType,
        )

        parser.add_argument(
            "map_type",
            type=str,
            help="type of map to plot",
            choices=constant.MAP_TYPES + ["both"],
            default="both",
            action=util.StoreMapType,
        )

        parser.add_argument(
            "-v", "--verbose", action="store_true", help="verbose output"
        )

        parser.add_argument("-d", "--debug", action="store_true", help="debug output")

        parser.add_argument(
            "-s",
            "--size",
            type=str,
            help="generate different sizes",
            default=constant.DEFAULT_SIZE,
        )

        parser.add_argument(
            "-t",
            "--time",
            type=int,
            nargs=2,
            help="year and month to plot",
            default=util.YearMonth.get_default(),
            action=util.ValidateYearMonth,
        )

        parser.add_argument(
            "-p",
            "--pfname",
            type=str,
            help="parameter file",
            default=self.__class__.pfname,
        )

        return parser.parse_args(argv)

    def _init_logging(self, debug, verbose):
        """Intialize the logging instance.

        As this is called from __init__, and this class isn't intended to be
        run as is as the main method, we don't call getAppLogger here.
        """
        if debug:
            self.loglevel = "DEBUG"
        elif verbose:
            self.loglevel = "INFO"
        # else use class default

        #  Set the log level for the module itself, as this class "runs the
        #  show" for the whole deploy_map module.
        module_logger = getModuleLogger(__name__)
        module_logger.setLevel(self.loglevel)

        # Set the log level for this particular class instance. Note that the
        # result of fullname(self) isn't under the same log hierarchy as
        # __name__
        self.logger = getLogger(fullname(self))
        self.logger.setLevel(self.loglevel)

        self.logger.notify("Logging intialized for %s", __name__)

    def _test_logger(self):
        self.logger.debug("debug")
        self.logger.info("info")
        self.logger.notify("notify")
        self.logger.warning("warning")

    def read_pf(self, pfname):
        """Read the parameter files associated with this class.

        Returns:
            (dict) : the contents of self.args.pfname as a dict. common_pf and
            stations_pf are inserted under the keys common and station.

        Parameter File Keys:
        Looks for the following keys.
            * common_pf - Path to a "common.pf", which is a holdover from the
            old ANF web configuration framework.
            * stations_pf - Path to a "stations.pf", which contains a list of
            parameters for stations.

            Note that neither of the above paths are given the normal Antelope
            PFPATH treatment. They are expected to be a full path, but can
            contain shortcuts like the tilde character in order to resolve a
            username. For example: `~rt/rtsystems/foo.pf` is valid, as is
            `/export/home/rtsystems/foo.pf`. However
            `/export/home/rt/rtsystems/foo` (without the `.pf` suffix) is NOT
            valid.
        """
        # Get the main parameters as a dictionary
        params = stock.pfread(pfname).pf2dict()

        # load each child parameter file
        self.logger.debug("Starting load of child parameter files.")
        for srckey, destkey in [("common_pf", "common"), ("stations_pf", "stations")]:
            self.logger.debug("Loading %s into params[%s]", srckey, destkey)
            if srckey in params:
                srckey_filename = os.path.abspath(os.path.expanduser(params[srckey]))
                self.logger.debug("Using filename %s", srckey_filename)
                params[destkey] = stock.pfin(srckey_filename).pf2dict()
            else:
                raise ValueError(
                    'Could not find key "%s" in parameter file %s' % (srckey, pfname)
                )

        return params

    def __init__(self, argv):
        """Initialize a new DeploymentMapMaker.

        Args:
            argv: typically the contents of sys.argv.


        A note about arguments, parameters, and defaults:
            Command-line parameters take precendence over any similarly named
            parameter file values. If loglevel is defined in the parameter file
            as INFO, but --debug is specified as an argument, the log level is
            set to DEBUG. In this way, it's possible to set some sane defaults
            in the paramter file, and then override them on a case-by-case
            basis.
        """

        parsed_args = self.parse_args(argv[1:])
        self._init_logging(parsed_args.debug, parsed_args.verbose)

        # Set defaults
        self.params = DEFAULT_PARAMS

        # Load parameters from parameter file
        self.logger.info("Reading params from %s", parsed_args.pfname)
        self.params.update(self.read_pf(parsed_args.pfname))

        # Override parameter file with parsed arguments, which gives us one
        # place to look for configuration once we finish init.
        self.params.update(vars(parsed_args))

        # Turn off color in debug mode.
        if self.params["debug"]:
            self.params["use_color"] = False
            self.logger.warning("*** DEBUGGING ON ***")
            self.logger.warning(
                "*** No grd or grad files - just single color for speed ***"
            )

        # Original script set a bunch of globals:
        # self.dbmaster = self.common_pf.get("USARRAY_DBMASTER")
        # self.networks = self.stations_pf.get("network")
        # self.infrasound = self.stations_pf.get("infrasound")
        # self.colors = self.stations_pf.get("colors")
        # self.usa_coords = self.common_pf.get("USACOORDS")
        # self.ak_coords = self.common_pf.get("AKCOORDS")
        # self.web_output_dir = self.common_pf.get("CACHE_MONTHLY_DEPLOYMENT")
        # self.web_output_dir_infra = self.common_pf.get("CACHE_MONTHLY_DEPLOYMENT_INFRA")
        # self.infrasound_mapping = self.common_pf.get("INFRASOUND_MAPPING")
        # self.output_dir = self.parameter_file.get("output_dir")
        #

        # Parse region data into gmt.Region objects.
        raw_regions = self.params["regions"]
        self.params["regions"] = [x for x in gmt.CsvRegionReader(raw_regions)]

        # Initialize GMT options with the parsed Region objects
        self.gmt_options = gmt.GmtConfig(
            regions=self.params["regions"],
            region_positions=self.params["region_positions"],
        )

        # Handle user specified size (-s option), default is constant.DEFAULT_SIZE ("default")
        try:
            size_opts = self.params["output_sizes"][self.params["size"]]
            self.gmt_options.global_options["ps_page_orientation"] = size_opts[
                "ps_page_orientation"
            ]
        except KeyError:
            self.logger.exception(
                "Problem setting options for plot size %s", self.params["size"]
            )
            raise

    def _get_map_filename_parts(
        self,
        year,
        month,
        size="default",
        deploy_type="seismic",
        map_type="cumulative",
        output_format=constant.DEFAULT_OUTPUT_FORMAT.lower(),
    ) -> MapFilenames:
        """Retrieve filename prefixes and suffixes for the given map_type.

        The suffix and prefix return values are suitable for passing to tempfile.mkstemp().

        Within the logic of the original program, intermediate is a postscript
        format of the map file. Finalfile is the desired final image filename,
        and is typically in format PNG.

        Args:
            year (int) : requested year between START_MONTH to current year
            month (int): requested month in range 1..12
        """

        if size is None:
            size = "default"

        assert year in constant.VALID_YEARS
        assert month in constant.VALID_MONTHS

        # Iterate over each named format string in size_deploy_type_formats, and
        # apply string.format to generate the actual prefix and suffix values.
        formatted = {
            format_string: values.format(
                size=string.capwords(size, sep="_"),
                deploy_type=deploy_type,
                map_type=map_type,
                year=year,
                month=month,
                intermediate_format=constant.INTERMEDIATE_FORMAT.lower(),
                output_format=output_format.lower(),
            )
            for format_string, values in self.size_deploy_type_fileformats[size][
                deploy_type
            ].items()
        }

        return MapFilenames(**formatted)

    def create_map(
        self, dbmasterview: database.DbMasterView, map_type: string, deploy_type: string
    ) -> string:
        """Create a single map with the given map_type and deploy_type.

        Args:
            dbmasterview (database.DbMasterView): database interaction class instance.
            map_type (string): one of cumulative, rolling
            deploy_type (string): one of seismic, inframet

        Returns:
            string: The path to the output filename

        Raises:
            DbopenError: if the dbmaster couldn't be opened.
        """
        assert map_type in constant.MAP_TYPES
        assert deploy_type in constant.DEPLOYMENT_TYPES
        assert dbmasterview is not None

        util.set_working_dir(self.params["data_dir"])

        # gmt.set_options(self.gmt_options.options)

        start_time, end_time = util.get_start_end_timestamps(
            **(self.params["time"]._asdict())
        )

        self.logger.info("Creating map type: %s", map_type)
        partparams = {
            "size": self.params["size"],
            "deploy_type": deploy_type,
            "map_type": map_type,
            "year": self.params["time"].year,
            "month": self.params["time"].month,
        }

        self.logger.debug(
            "Retrieving filename parts with params: %s", pformat(partparams)
        )
        file_name_parts = self._get_map_filename_parts(**partparams)
        self.logger.debug("Using filename parts: %s", file_name_parts)

        # get the needed metadata from the database.
        md = dbmasterview.get_station_metadata(
            map_type, start_time=start_time, end_time=end_time
        )

        gmt_plotter = gmtplotter.GmtDeployMapPlotter(
            map_type=map_type,
            deployment_type=deploy_type,
            config=self.gmt_options,
            start_time=start_time,
            end_time=end_time,
            station_metadata_objects=md,
            file_prefix=file_name_parts.intermediate_file_prefix,
            file_suffix=file_name_parts.intermediate_file_suffix,
        )

        final_file = (
            file_name_parts.final_file_prefix + file_name_parts.final_file_suffix
        )

        self.logger.info("Output target: %s", final_file)

        gmt_plotter.plot()

        rgbs = {"1_DECOM": constant.DEPLOY_TYPE_DECOM_RGBS[deploy_type]}
        snets_text = {}

        self.logger.debug("RGBs initialized to: %s", pformat(rgbs))

        # Assemble our rgbs and snet_text dictionaries.
        # self.networks = self.stations_pf.get("network")
        # self.infrasound = self.stations_pf.get("infrasound")
        if self.params["deploy_type"] == "inframet":
            networkdefs = self.params["stations"].get("infrasound")
        else:
            networkdefs = self.params["stations"].get("network")

        # TODO: finish assembling RGBs and snets_text dicts, and pass them to the plotter.

        return final_file

    def run(self):
        """Create the maps."""
        self.logger.debug("Starting run().")

        output_files = []
        map_errors = 0

        dbview = database.DbMasterView(
            dbmaster=self.params["dbmaster"],
            extra_sensor_mapping=self.params["infrasound_mapping"],
        )

        for map_type in self.params["map_type"]:
            for deploy_type in self.params["deploy_type"]:
                try:
                    output_files.append(
                        self.create_map(
                            dbmasterview=dbview,
                            map_type=map_type,
                            deploy_type=deploy_type,
                        )
                    )
                except Exception:
                    self.logger.exception(
                        "The map for map_type %s, deploy_type %s failed to generate."
                        % (map_type, deploy_type)
                    )
                    map_errors += 1

        self.logger.notify("End of run. Summary:")
        self.logger.notify("%s maps were generated.", len(output_files))
        if len(output_files) > 0:
            self.logger.notify(pformat(output_files))
        if map_errors:
            self.logger.notify("%d maps failed to generate.", map_errors)
            return -1
        return 0
