"""Constants for the anf.deployementmap module."""

import datetime

from anf.logutil import LOG_NOTIFY_NAME

MAP_TYPES = ["cumulative", "rolling"]
DEPLOYMENT_TYPES = ["seismic", "inframet"]

START_YEAR = 2004
"""The first year that data is available for a given project."""

MAX_YEAR = datetime.date.today().year
"""The last year that data is available for."""
# it's not really a constant, but close enough.

VALID_YEARS = range(START_YEAR, MAX_YEAR)


WET_RGB = "202/255/255"

# Plot Media options
DEFAULT_PS_PAGE_ORIENTATION = "portrait"
DEFAULT_PS_PAGE_COLOR = "255/255/255"
DEFAULT_PS_MEDIA = "a1"

# Basemap annotation options
DEFAULT_MAP_ANNOT_OFFSET_PRIMARY = "0.2c"
DEFAULT_MAP_ANNOT_OFFSET_SECONDARY = "0.2c"
DEFAULT_MAP_LABEL_OFFSET = "0.2c"

# Basemap Layout options
DEFAULT_MAP_FRAME_WIDTH = "0.2c"
DEFAULT_MAP_SCALE_HEIGHT = "0.2c"
DEFAULT_MAP_TICK_LENGTH = "0.2c"
DEFAULT_X_AXIS_LENGTH = "25c"
DEFAULT_Y_AXIS_LENGTH = "15c"
DEFAULT_MAP_ORIGIN_X = "2.5c"
DEFAULT_MAP_ORIGIN_Y = "2.5c"
DEFAULT_MAP_LOGO_POS = "BL/-0.2c/-0.2c"
DEFAULT_MAP_LINE_STEP = "0.025c"

# Misc options
DEFAULT_PROJ_LENGTH_UNIT = "inch"
DIR_GSHHG = "/usr/share/gshhg-gmt-nc4"


DEFAULT_SYMSIZE = "0.15"
DEFAULT_USE_COLOR = True

DEFAULT_LOG_LEVEL = LOG_NOTIFY_NAME
