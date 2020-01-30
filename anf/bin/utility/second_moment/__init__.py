# -*- coding: utf-8 -*
"""Python wrapper for McGuire 2017 MATLAB second moment program.

This module contains the second_moment app and utility modules.
"""
import errno
from optparse import OptionParser
import os
import subprocess
import sys

from anf.logutil import getAppLogger, getLogger
from antelope import stock

from .util import execute, get_model_pf, safe_pf_get

logger = getLogger(__name__)


class App:
    """The second_moment application."""

    def __init__(self, args):
        """Initialize the second_moment application."""
        self._parse_opts(args)
        self._set_logging(self.options)
        self._parse_pf(self.options.pf)

    def _parse_opts(self, args):
        usage = "Usage: %prog [options] database orid"

        parser = OptionParser(usage=usage)

        parser.add_option(
            "-v",
            "--verbose",
            action="store_true",
            dest="verbose",
            help="verbose output",
            default=False,
        )

        parser.add_option(
            "-d",
            "--debug",
            action="store_true",
            dest="debug",
            help="debug output",
            default=False,
        )

        parser.add_option(
            "-x",
            "--debug_plot",
            action="store_true",
            dest="debug_plot",
            help="debug plot output",
            default=False,
        )

        parser.add_option(
            "-i",
            "--interactive",
            action="store_true",
            dest="interactive",
            help="run in interactive mode",
            default=False,
        )

        parser.add_option(
            "--no_figure",
            action="store_true",
            dest="no_figure",
            help="save plots",
            default=False,
        )

        parser.add_option(
            "-w",
            action="store_true",
            dest="window",
            help="run on active display",
            default=False,
        )

        parser.add_option(
            "-e",
            "--egf",
            action="store",
            type="string",
            dest="egf",
            help="egf orid",
            default=-99,
        )

        parser.add_option(
            "-p",
            action="store",
            type="string",
            dest="pf",
            help="parameter file",
            default="second_moment.pf",
        )

        parser.add_option(
            "-s",
            "--select",
            action="store",
            type="string",
            dest="select",
            help="station select",
            default=".*",
        )

        parser.add_option(
            "-r",
            "--reject",
            action="store",
            type="string",
            dest="reject",
            help="station reject",
            default="",
        )

        parser.add_option(
            "-f",
            "--filter",
            action="store",
            type="string",
            dest="filter",
            help="filter",
            default=None,
        )

        parser.add_option(
            "-t",
            "--time_window",
            action="store",
            type="string",
            dest="tw",
            help="time window",
            default=None,
        )

        parser.add_option(
            "-m",
            "--model",
            action="append",
            type="string",
            dest="model",
            help="velocity model",
            default=[],
        )

        parser.add_option(
            "--fault",
            action="store",
            type="string",
            dest="fault",
            help="strike1,dip1,strike2,dip2",
            default="",
        )

        (self.options, args) = parser.parse_args(args)

        if len(args) != 2:
            parser.error("Incorrect number of arguments.")

        self.database = args[0]
        self.orid = args[1]

        if not os.path.exists(self.database):
            raise FileNotFoundError(
                errno.ENOENT, os.strerror(errno.ENOENT), self.database
            )

    def _set_logging(self, options):
        """Set log level."""

        loglevel = "WARNING"
        if options.verbose:
            loglevel = "INFO"
        if options.debug:
            loglevel = "DEBUG"

        # New logger object and set loglevel
        self.logger = getAppLogger(__name__, level=loglevel)
        self.logger.info("loglevel=%s" % loglevel)

    def _parse_pf(self, pfname):
        """Parse parameter file."""

        pf_file = stock.pffiles(pfname)[-1]

        if not os.path.isfile(pf_file):
            self.logger.critical("Cannot find parameter file [%s]" % pfname)
            return -1

        pf = stock.pfread(pfname)
        self.pf = pf

        # matlab inversion parameters
        self.loaddatafile = float(safe_pf_get(pf, "loaddatafile"))
        self.domeas = float(safe_pf_get(pf, "domeasurement"))
        self.doinversion = float(safe_pf_get(pf, "doinversion"))
        self.dojackknife = float(safe_pf_get(pf, "dojackknife"))
        self.azband = float(safe_pf_get(pf, "azband"))
        self.dobootstrap = float(safe_pf_get(pf, "dobootstrap"))
        self.nb = float(safe_pf_get(pf, "nb"))
        self.bconf = float(safe_pf_get(pf, "bconf"))
        self.niter = float(safe_pf_get(pf, "niter"))
        self.testfault = float(safe_pf_get(pf, "testfault"))

        # folder and path params
        self.image_dir = os.path.relpath(
            safe_pf_get(pf, "image_dir", "second_moment_images")
        )
        self.temp_dir = os.path.relpath(safe_pf_get(pf, "temp_dir", ".second_moment"))
        self.model_path = safe_pf_get(pf, "model_path")
        if not self.options.model:
            self.options.model = safe_pf_get(pf, "velocity_model")

        # on/off for features
        self.auto_arrival = safe_pf_get(pf, "auto_arrival")

        # egf selection criteria
        self.loc_margin = float(safe_pf_get(pf, "location_margin"))
        self.dep_margin = float(safe_pf_get(pf, "depth_margin"))
        self.time_margin = float(safe_pf_get(pf, "time_margin"))

        # filter and time window
        if not self.options.filter:
            self.options.filter = safe_pf_get(pf, "filter")

        if not self.options.tw:
            self.options.tw = safe_pf_get(pf, "time_window")

        # L-curve time duration maximum
        self.stf_duration_criteria = float(safe_pf_get(pf, "misfit_criteria"))

        self.matlab_code_path = safe_pf_get(pf, "matlab_code_path")
        self.matlab_path = safe_pf_get(pf, "matlab_path")
        self.matlab_flags = safe_pf_get(pf, "matlab_flags")
        self.xvfb_path = safe_pf_get(pf, "xvfb_path")

        # Get model information
        self.model = get_model_pf(self.options.model, self.model_path)

    def _setup_folders(self):
        # set up folders
        if not os.path.exists(self.image_dir):
            os.makedirs(self.image_dir)

        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)

    def _setup_xvfb(self):
        """Open virtual display with Xvfb.

        Return:
            boolean - False if xvfb fails, True otherwise
        """

        pid = os.getpid()
        cmd = "%s :%s -fbdir /var/tmp -screen :%s 1600x1200x24" % (
            self.xvfb_path,
            pid,
            pid,
        )

        self.logger.info(" - Start virtual display: %s" % cmd)

        self.xvfb = subprocess.Popen(cmd, shell=True)

        if self.xvfb.returncode:
            stdout, stderr = self.xvfb.communicate()
            self.logger.info(" - xvfb: stdout: %s" % stdout)
            self.logger.info(" - xvfb: stderr: %s" % stderr)
            self.logger.critical(
                "Problems running %s. Return code: %s" % (cmd, self.xvfb.returncode)
            )
            return False

        os.environ["DISPLAY"] = ":%s" % pid

        self.logger.info(" - xvfb.pid: %s" % self.xvfb.pid)
        self.logger.info(" - $DISPLAY => %s" % os.environ["DISPLAY"])

        return True

    def _run_matlab(self):
        """Run Matlab code."""

        cmd = """%s -r \"matlab_code='%s';
verbose='%s';
debug='%s';
debug_plot='%s';
interactive='%s';
no_figure='%s';
image_dir='%s';
temp_dir='%s';
db='%s';
orid=%d;
egf=%s;
vel_model='%s';
reject='%s';
select='%s';
filter='%s';
tw='%s';
misfit_criteria=%.2f;
loc_margin=%.4f;
dep_margin=%.2f;
time_margin=%.1f;
LOADDATAFILE=%d;
DOMEAS=%d;
DOINVERSION=%d;
DOJACKKNIFE=%d;
azband=%d;
DOBOOTSTRAP=%d;
NB=%d;
bconf=%.2f;
NITER=%d;
TESTFAULT=%d;
auto_arrival='%s';
fault='%s';
\" < '%s'""" % (
            self.matlab_path,
            self.matlab_code_path,
            self.options.verbose,
            self.options.debug,
            self.options.debug_plot,
            self.options.interactive,
            self.options.no_figure,
            self.image_dir,
            self.temp_dir,
            self.database,
            int(self.orid),
            self.options.egf,
            self.model,
            self.options.reject,
            self.options.select,
            self.options.filter,
            self.options.tw,
            self.stf_duration_criteria,
            self.loc_margin,
            self.dep_margin,
            self.time_margin,
            self.loaddatafile,
            self.domeas,
            self.doinversion,
            self.dojackknife,
            self.azband,
            self.dobootstrap,
            self.nb,
            self.bconf,
            self.niter,
            self.testfault,
            self.auto_arrival,
            self.options.fault,
            self.matlab_code,
        )

        self.logger.info(" - Run Matlab script:")
        self.logger.info("   %s " % cmd)

        try:
            mcmd = execute(cmd)
        except Exception:
            self.logger.exception(
                'Problem with command: "' + cmd + '". Result: ' + mcmd
            )

        if self.options.verbose:
            self.logger.info(
                "Done: %s %s" % ("second_moment", stock.strtime(stock.now()))
            )

    def _kill_xvfb(self):
        self.logger.info("xvfb.kill: %s" % self.xvfb.terminate())

    def run(self):
        """Run second_moment App."""

        # Create any necessary folders.
        self._setup_folders()

        # set path of matlab script
        sys.path.append(self.matlab_code_path)
        self.matlab_code = self.matlab_code_path + "/" + "run_second_moment.m"

        # -- Set matlab info
        self.logger.info("Start: %s %s" % ("second_moment", stock.strtime(stock.now())))
        self.logger.info("Start: configuration parameter file %s" % self.options.pf)
        self.logger.info(" - Xvfb path: %s" % self.xvfb_path)
        self.logger.info(" - Matlab path: %s" % self.matlab_path)
        self.logger.info(" - Matlab flags: %s" % self.matlab_flags)

        # Set virtual display if needed
        if not self.options.window and self.xvfb_path:
            result = self._setup_xvfb()
            if not result:
                logger.error("Xvfb setup failed. Can't continue.")
                return -1

        self._run_matlab()

        # -- Kill virtual display if needed -- #
        if not self.options.window:
            self._kill_xvfb()


def main(argv=None):
    """Implement main function for second_moment."""

    myapp = App(argv[1:])
    return myapp.run()
