"""Constants for the anf.deployementmap module."""

import datetime

MAP_TYPES = ["cumulative", "rolling"]
DEPLOYMENT_TYPES = ["seismic", "inframet"]

START_YEAR = 2004
"""The first year that data is available for a given project."""

MAX_YEAR = datetime.date.today().year
"""The last year that data is available for."""
# it's not really a constant, but close enough.


WET_RGB = "202/255/255"

DEFAULT_PAPER_ORIENTATION = "portrait"
DEFAULT_PAPER_MEDIA = "a1"
DEFAULT_SYMSIZE = "0.15"
DEFAULT_USE_COLOR = True
