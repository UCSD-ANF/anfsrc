"""Routines to run gmt subcommands."""

from subprocess import check_call

from anf.logutil import getLogger

LOGGER = getLogger(__name__)


def run_gmt(command_name: str, parameters: list, outfile=None):
    """Run a GMT command with a wrapper function."""
    args = ["gmt", command_name]
    args += parameters
    if outfile is not None:
        out_fh = open(outfile, "rw")
    else:
        out_fh = None
    try:
        check_call(parameters, stdout=out_fh, shell=False)
    except OSError:
        LOGGER.exception("gmt %s execution failed", command_name)
    finally:
        out_fh.close()


def run_ps_command(
    command_name: str,
    parameters: list,
    outfile: str,
    omit_header=False,
    keep_open=False,
):
    """Run a GMT command that is expected to output to a postscript file."""

    if omit_header:
        parameters.append("-O")
    if keep_open:
        parameters.append("-K")

    run_gmt(command_name, parameters, outfile)


def set_default_options(options):
    """Call `gmt set` to configure global default options in the current working directory."""

    command_name = "set"
    parameters = []
    for key, value in options.items():
        parameters.extend([key.upper(), value])

    run_gmt(command_name, parameters)


def psxy(xy_file, outfile, psxy_options: list = None, **kwargs):
    """Run psxy with the provided arguments."""
    if psxy_options is None:
        psxy_options = []

    parameters = [xy_file]
    parameters += psxy_options

    run_ps_command("psxy", parameters, outfile, **kwargs)


def pscoast(center, wet_rgb, outfile, pscoast_options=None, region_name=None, **kwargs):
    """Run pscoast.

    Args:
        region_name (str): Name of the region to plot.
        center (str): equal-area plot x,y borders N,E,S,W
        wet_rgb (str): "R,G,B"
        pscoast_options (list): extra options for pscoast
        outfile (str): intermediate postscript output file name

    """
    if pscoast_options is None:
        pscoast_options = []
    parameters = ["-JE{}".format(center), "-S{}".format(wet_rgb)]
    parameters += pscoast_options
    if region_name:
        parameters.insert(0, "-R".format(region_name))

    run_ps_command("pscoast", parameters, outfile, **kwargs)


def grdimage(
    grid_file: str,
    center: str,
    gradiant_file: str,
    outfile: str,
    region_name: str = None,
    grdimage_options: list = None,
    **kwargs
):
    """Run gmt grdimage.

    Args:
        grid_file: filename of GMT grid file
        center: equalarea boundaries, n,e,s,w
        gradiant_file: color gradient definition file for GMT
        outfile: output postscript filename
        region_name: name of the region to grid
        grdimage_options: extra options for grdimage
    """
    if grdimage_options is None:
        grdimage_options = []
    parameters = [grid_file]
    if region_name:
        parameters.append("-R{}".format(region_name))
    parameters.append("-JE{}".format(center))
    parameters.append("-I{}".format(gradiant_file))
    parameters += grdimage_options

    run_ps_command("grdimage", parameters, outfile, **kwargs)
