"""The anf.deploymentmap module."""

import argparse
import os

from anf.logutil import fullname, getLogger, getModuleLogger
from antelope import stock

from . import constant, gmt, util

LOGGER = getModuleLogger(__name__)

DEFAULT_PARAMS = {
    "symsize": constant.DEFAULT_SYMSIZE,
    "use_color": constant.DEFAULT_USE_COLOR,
    "log_level": constant.DEFAULT_LOG_LEVEL,
}
"""These items may be overriden by read_pf."""


class DeploymentMapMaker:
    """Generalized class for generating deployment maps in GMT."""

    pfname = "deploymentmap"
    """Name of the parameter file associated with this class.
    It can be redefined in subclasses to customize the parameter file location
    without having to redefine read_pf."""

    loglevel = "NOTIFY"
    """Logging level of this class."""

    logger = getLogger(__name__)
    """Logging instance used by class. Overridden for instances in __init__."""

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
            default=util.YearMonth.getDefault(),
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
        params = stock.pfread(pfname).pf2dict()
        self.logger.warning("Starting load of child parameter files.")
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

        self.logger.info("Reading params from %s", parsed_args.pfname)
        self.params = DEFAULT_PARAMS
        self.params.update(self.read_pf(parsed_args.pfname))
        self.params.update(vars(parsed_args))

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
        if self.params["size"] == "wario":
            self.gmt_options.options["PS_PAGE_ORIENTATION"] = "landscape"

    def run(self):
        """Create the maps."""
        self.logger.notify("Starting run().")

        util.set_working_dir(self.params["data_dir"])

        gmt.set_options(self.gmt_options.options)

        return 0
