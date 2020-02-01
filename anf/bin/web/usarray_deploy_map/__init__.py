"""The anf.deploymentmap module."""

import argparse
import collections
import os

from anf.logutil import fullname, getLogger, getModuleLogger
from antelope import stock

from . import constant, util

LOGGER = getModuleLogger(__name__)


class DeploymentMapMaker:
    """Generalized class for generating deployment maps in GMT."""

    pfname = "deploymentmap"
    """Name of the parameter file associated with this class.
    It can be redefined in subclasses to customize the parameter file location
    without having to redefine parse_pf."""

    loglevel = "WARNING"
    """Logging level of this class."""

    args = {}
    """Configuration data is stored here."""

    def parse_args(self, args):
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
            default=util.get_default_yearmonth(),
            action=util.ValidateYearMonth,
        )

        parser.add_argument(
            "-p",
            "--pfname",
            type=str,
            help="parameter file",
            default=self.__class__.pfname,
        )

        self.args = parser.parse_args(args)

    def _init_logging(self):
        """Intialize the logging instance.

        As this is called from __init__, and this class isn't intended to be
        run as is as the main method, we don't call getAppLogger here.
        """
        if self.args.debug:
            loglevel = "DEBUG"
        elif self.args.verbose:
            loglevel = "INFO"
        else:
            loglevel = "WARNING"

        self.loglevel = loglevel

        self.logger = getLogger(fullname(self))
        self.logger.warning("Logging intialized for %s", __name__)

    def _test_logger(self):
        self.logger.debug("debug")
        self.logger.info("info")
        self.logger.notify("notify")
        self.logger.warning("warning")

    def read_pf(self):
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
        main = stock.pfread(self.args.pfname).pf2dict()
        main["common"] = stock.pfin(
            os.path.abspath(os.path.expanduser(main["common_pf"]))
        ).pf2dict()
        main["stations"] = stock.pfin(
            os.path.abspath(os.path.expanduser(main["stations_pf"]))
        ).pf2dict()

        return main

    def __init__(self, argv):
        """Initialize a new DeploymentMapMaker.

        Args:
            argv: typically the contents of sys.argv.
        """
        self.logger = getLogger(fullname(self))

        self.parse_args(argv[1:])
        self._init_logging()

        self.params = self.read_pf()

        if self.args.debug:
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
        GmtOptions = collections.namedtuple(
            "GmtOptions", ["paper_orientation", "paper_media", "symsize"]
        )
        if self.args.size == "wario":
            self.gmt_options = GmtOptions("landscope", "b0", "0.3")
        else:
            self.gmt_options = GmtOptions("portrait", "a1", "0.15")
