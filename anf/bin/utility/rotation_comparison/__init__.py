"""The rotation_comparison Application.

Calculates the orientation of a sensor(s) at a given station(s) to the
orientation of a reference sensor. Relies on Antelope Python Interface
(Datascope and Stock), NumPy, and Matplotlib.

Print help:
        rotation_comparison -h

@author:
    Rebecca Rodd <rebecca.rodd.91@gmail.com>
"""

from optparse import OptionParser

from anf.logutil import getModuleLogger
from antelope import stock

from .comparison import Comparison

logger = getModuleLogger()


def main(argv=None):
    """Run the rotation_comparison command."""
    # Configure parameters from command-line.

    usage = "%prog [options] database time/orid"

    parser = OptionParser(usage=usage)

    # Verbose output
    parser.add_option(
        "-v", action="store_true", dest="verbose", default=False, help="verbose output"
    )

    # Parameter file
    parser.add_option(
        "-p",
        action="store",
        dest="pf",
        type="string",
        default="rotation_comparison.pf",
        help="parameter file",
    )

    # Filter
    parser.add_option(
        "-f", action="store", dest="filter", type="string", default=None, help="filter"
    )

    # Time window
    parser.add_option(
        "-t", action="store", dest="tw", type="float", default=None, help="time window"
    )

    # Mode
    parser.add_option(
        "-o", action="store_true", dest="origin", default=False, help="arg2 is orid"
    )

    # Mode
    parser.add_option(
        "-r",
        action="store",
        dest="reference",
        type="string",
        default=None,
        help="reference regex",
    )

    # Stations
    parser.add_option(
        "-c",
        action="store",
        dest="compare",
        type="string",
        default=False,
        help="comparison regex",
    )

    # Plot each data group for a site and wait.
    parser.add_option(
        "-x",
        action="store_true",
        dest="debug_plot",
        default=False,
        help="debug output each station plot",
    )

    # Plot results
    parser.add_option(
        "--noplot",
        action="store_true",
        dest="noplot",
        default=False,
        help="plot azimuth rotation results",
    )

    parser.add_option(
        "--nosave",
        action="store_true",
        dest="nosave",
        default=False,
        help="save results to csv file",
    )

    (options, args) = parser.parse_args(argv[1:])

    # If we don't have 2 arguments then exit.
    if len(args) != 2:
        parser.error("Incorrect number of arguments.")

    # If we don't have station list or reference station than exit

    # Set log level
    loglevel = "WARNING"
    if options.verbose:
        loglevel = "INFO"

    # New logger object and set loglevel
    logger.setLevel(loglevel)
    logger.info("loglevel=%s" % loglevel)

    # parse arguments from command-line
    databasename = args[0]
    logger.info("Database [%s]" % databasename)

    # read parameters from parameter file
    logger.info("Parameter file to use [%s]" % options.pf)

    stock.pfread(options.pf)

    rot_compare = Comparison(options, databasename)
    rot_compare.comp(args[1])
    return 0
