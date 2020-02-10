"""The anf.deploymentmap module."""

import argparse
import collections
import os
from pprint import pformat
import string
import tempfile

from anf.logutil import fullname, getLogger, getModuleLogger
from antelope import stock
from antelope.datascope import DbopenError

from . import constant, gmt, util

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

    size_deploytype_fileformats = constant.SIZE_DEPLOYTYPE_FILEFORMATS
    """Filename format strings organized by size, then maptype."""

    def parse_args(self, argv):
        """Parse our command-line arguments.

        Args:
            args(dict): arguments to parse. Default: sys.argv[1:].
        """

        parser = argparse.ArgumentParser()

        parser.add_argument(
            "deploytype",
            type=str,
            help="type of deployment to plot",
            choices=constant.DEPLOYMENT_TYPES + ["both"],
            default="both",
            action=util.StoreDeployType,
        )

        parser.add_argument(
            "maptype",
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

        parser.add_argument("-s", "--size", type=str, help="generate different sizes")

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
        self.gmt_options = gmt.GmtOptions()

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

        self.params["usa_coords"] = self._load_coords("USACOORDS")
        self.params["ak_coords"] = self._load_coords("AKCOORDS")
        if self.params["size"] == "wario":
            self.gmt_options.options["PS_PAGE_ORIENTATION"] = "landscape"
            self.params["usa_coords"].width = 44  # not stored in param file
            self.params["ak_coords"].width = 10  # also not stored in param file

    def _load_coords(self, coords):
        """Load a gmt.GmtRegionCoordinates object from a subsection of the parameter file."""
        self.logger.debug(pformat(self.params["common"][coords]))
        coord_params = {k.lower(): v for k, v in self.params["common"][coords].items()}
        self.logger.debug(pformat(coord_params))
        return gmt.GmtRegionCoordinates(**coord_params)

    def _get_map_filename_parts(
        self,
        year,
        month,
        size="default",
        deploytype="seismic",
        maptype="cumulative",
        outputformat=constant.DEFAULT_OUTPUT_FORMAT.lower(),
    ):
        """Retrieve filename prefixes and suffixes for the given maptype.

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

        # Iterate over each named format string in size_deploytype_formats, and
        # apply string.format to generate the actual prefix and suffix values.
        formatted = {
            k: v.format(
                size=string.capwords(size, sep="_"),
                deploytype=deploytype,
                maptype=maptype,
                year=year,
                month=month,
                intermediateformat=constant.INTERMEDIATE_FORMAT.lower(),
                outputformat=outputformat.lower(),
            )
            for k, v in self.size_deploytype_fileformats[size][deploytype].items()
        }

        return MapFilenames(**formatted)

    def createMap(self, maptype, deploytype):
        """Create a map with the given maptype and deploytype.

        Args:
            maptype (string): one of cumulative, rolling
            deploytype (string): one of seismic, inframet

        Returns:
            string: The path to the output filename

        Raises:
            DbopenError: if the dbmaster couldn't be opened.
        """
        assert maptype in constant.MAP_TYPES
        assert deploytype in constant.DEPLOYMENT_TYPES

        self.logger.info("Creating map type: %s", maptype)
        partparams = {
            "size": self.params["size"],
            "deploytype": deploytype,
            "maptype": maptype,
            "year": self.params["time"].year,
            "month": self.params["time"].month,
        }
        self.logger.debug(
            "Retrieving filename parts with params: %s", pformat(partparams)
        )
        filenameparts = self._get_map_filename_parts(**partparams)
        self.logger.debug("Using filename parts: %s", filenameparts)

        # Generate a tempfile
        fd, path = tempfile.mkstemp(
            suffix=filenameparts.intermediate_file_suffix,
            prefix=filenameparts.intermediate_file_prefix,
        )

        finalfile = filenameparts.final_file_prefix + filenameparts.final_file_suffix
        self.logger.info("Intermediate filename: %s", path)
        self.logger.info("Output target: %s", finalfile)

        rgbs = {"1_DECOM": constant.DEPLOYTYPE_DECOM_RGB[deploytype]}
        self.logger.debug("RGBs initialized to: %s", pformat(rgbs))

        station_loc_files = None
        counter = 0
        try:
            with os.fdopen(fd, "w") as tmp:
                # do stuff with temp file
                self.logger.debug("Got a tempfile: %s", tmp)
            get_params = {
                "db": self.params["dbmaster"],
                "maptype": maptype,
                "year": self.params["time"].year,
                "month": self.params["time"].month,
            }
            if deploytype == "seismic":
                station_loc_files, counter = gmt.generate_sta_locations(**get_params)
            elif deploytype == "inframet":
                station_loc_files, counter = gmt.generate_inframet_locations(
                    **get_params, infrasound_mapping=self.params["infrasound_mapping"]
                )
        except DbopenError:
            self.logger.exception("Couldn't open the database.")
            raise
        finally:
            os.remove(path)

            if station_loc_files is not None:
                for locfile in sorted(station_loc_files.keys()):
                    os.remove(station_loc_files[locfile])

        return finalfile

    def run(self):
        """Create the maps."""
        self.logger.debug("Starting run().")

        util.set_working_dir(self.params["data_dir"])

        gmt.set_options(self.gmt_options.options)

        outputfiles = []
        maperrors = 0

        for maptype in self.params["maptype"]:
            for deploytype in self.params["deploytype"]:
                try:
                    outputfiles.append(self.createMap(maptype, deploytype))
                except Exception:
                    self.logger.exception(
                        "The map for maptype %s, deploytype %s failed to generate."
                        % (maptype, deploytype)
                    )
                    maperrors += 1

        self.logger.notify("End of run. Summary:")
        self.logger.notify("%s maps were generated.", len(outputfiles))
        if len(outputfiles) > 0:
            self.logger.notify(pformat(outputfiles))
        if maperrors:
            self.logger.notify("%d maps failed to generate.", maperrors)
            return -1
        return 0
