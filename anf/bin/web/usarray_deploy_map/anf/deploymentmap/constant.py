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

VALID_YEARS = range(START_YEAR, MAX_YEAR + 1)  # "..up to but not including stop."
VALID_MONTHS = range(1, 13)


WET_RGB = "202/255/255"

INTERMEDIATE_FORMAT = "PS"
"""The format for the GMT working copy. Normally Postscript."""

DEFAULT_OUTPUT_FORMAT = "PNG"
"""The default format for the final output image, normally Portable Network Graphic (PNG)"""

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

SIZE_DEPLOYTYPE_FILEFORMATS = {
    "wario": {
        "seismic": {
            "intermediate_file_prefix": "deployment_history_map_{deploytype!s}_{year:04d}_{month:02d}_{maptype}_{size}_",
            "intermediate_file_suffix": ".{intermediateformat}",
            # final file name was "make it yourself" message in original.
            "final_file_prefix": "deploymap_{year:04d}_{month:02d}.{maptype}_{size}",
            "final_file_suffix": ".{outputformat}",
        },
        "inframet": {
            "intermediate_file_prefix": "deployment_history_map_{deploytype!s}_{year:04d}_{month:02d}_{maptype}_{size}_",
            "intermediate_file_suffix": ".{intermediateformat}",
            # final file name was "make it yourself" message in original.
            "final_file_prefix": "deploymap_{deploytype}_{year:04d}_{month:02d}.{maptype}_{size}",
            "final_file_suffix": ".{outputformat}",
        },
    },
    "default": {
        "seismic": {
            "intermediate_file_prefix": "deployment_history_map_{deploytype!s}_{year:04d}_{month:02d}_{maptype}_",
            "intermediate_file_suffix": ".{intermediateformat}",
            "final_file_prefix": "deploymap_{year:04d}_{month:02d}.{maptype}",
            "final_file_suffix": ".{outputformat}",
        },
        "inframet": {
            "intermediate_file_prefix": "deployment_history_map_{deploytype!s}_{year:04d}_{month:02d}_{maptype!s}_",
            "intermediate_file_suffix": ".{intermediateformat}",
            "final_file_prefix": "deploymap_{deploytype}_{year:04d}_{month:02d}.{maptype}",
            "final_file_suffix": ".{outputformat}",
        },
    },
}
"""Filename format strings organized by size, then maptype."""

DEPLOYTYPE_DECOM_RGB = {"seismic": "77/77/77", "inframet": "255/255/255"}
