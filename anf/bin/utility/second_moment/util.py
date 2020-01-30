"""Utility functions for second_moment."""

import os
import subprocess
import sys

from anf.logutil import getLogger
from antelope import stock

logger = getLogger(__name__)


def safe_pf_get(pf, field, defaultval=False):
    """Safe wrapper around antelope.stock.pf.get().

    Method to extract values from parameter file
    with a default value option.

    NOTE: UNCLEAR WHY THIS IS NEEDED. stock.pf.get() takes a default argument.
    """

    value = defaultval
    if field in pf.keys():
        try:
            value = pf.get(field, defaultval)
        except Exception as e:
            stock.elog.die("Problems safe_pf_get(%s,%s)" % (field, e))
            pass
    if isinstance(value, (list, tuple)):
        value = [x for x in value if x]
    logger.debug("pf.get(%s,%s) => %s" % (field, defaultval, value))
    return value


def get_model_pf(mfile, path=[]):
    """Retrive model info from the parameter file."""
    model = False

    logger.debug("Get model: %s in %s" % (mfile, path))

    for d in path:
        if os.path.isfile(os.path.join(d, mfile)):
            logger.debug("Look for model: %s" % os.path.join(d, mfile))
            model = os.path.join(d, mfile)
            break
        else:
            pass  # Stop if we find one

    if not model:
        logger.error("Missing [%s] in [%s]" % (mfile, ", ".join(path)))

    return model


def execute(command):
    """Execute a command with subprocess.Popen().

    Used to execute the matlab script.
    """
    process = subprocess.Popen(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )

    # Poll process for new output until finished
    while True:
        nextline = process.stdout.readline()
        if nextline == "" and process.poll() is not None:
            break
        nextline = nextline.lstrip(">> ")
        nextline = nextline.lstrip("MATLAB_maci64: ")
        sys.stdout.write(nextline)
        sys.stdout.flush()

    output = process.communicate()[0]
    exitCode = process.returncode

    if exitCode == 0:
        return output
    else:
        raise subprocess.ProcessException(command, exitCode, output)


def num(s, r=None):
    """Automatically parse a number from a string.

    Args:
        s (string): string to parse.
        r (int or None): round floating point values to r number of places.

    """

    if r:
        return round(float(s), r)
    else:
        try:
            return int(s)
        except ValueError:
            return float(s)
