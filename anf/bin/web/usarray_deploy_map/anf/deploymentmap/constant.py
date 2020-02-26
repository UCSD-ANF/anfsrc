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
VALID_MONTHS = range(
    1, 13
)  # python range() is weird, includes start number, but excludes stop number.


WET_RGB = "202/255/255"

INTERMEDIATE_FORMAT = "PS"
"""The format for the GMT working copy. Must be Postscript for GMT.

This gets down-cased and used as the suffix of the intermediate file."""

DEFAULT_OUTPUT_FORMAT = "PNG"
"""The default format for the final output image, normally Portable Network Graphic (PNG).

This gets down-cased and used as the suffix of the final output image.
"""

DEFAULT_SYMSIZE = "0.15"
DEFAULT_USE_COLOR = True

DEFAULT_LOG_LEVEL = LOG_NOTIFY_NAME

DEFAULT_INFRASOUND_MAPPING = {
    "MEMS": ("LDM_EP"),
    "SETRA": ("BDO_EP", "LDO_EP"),
    "NCPA": ("BDF_EP", "LDF_EP"),
}

DEFAULT_SIZE = "default"

SIZE__DEPLOY_TYPE__FILE_FORMATS = {
    "wario": {
        "seismic": {
            "intermediate_file_prefix": "deployment_history_map_{deploy_type!s}_{year:04d}_{month:02d}_{map_type}_{size}_",
            "intermediate_file_suffix": ".{intermediate_format}",
            # final file name was "make it yourself" message in original.
            "final_file_prefix": "deploymap_{year:04d}_{month:02d}.{map_type}_{size}",
            "final_file_suffix": ".{output_format}",
        },
        "inframet": {
            "intermediate_file_prefix": "deployment_history_map_{deploy_type!s}_{year:04d}_{month:02d}_{map_type}_{size}_",
            "intermediate_file_suffix": ".{intermediate_format}",
            # final file name was "make it yourself" message in original.
            "final_file_prefix": "deploymap_{deploy_type}_{year:04d}_{month:02d}.{map_type}_{size}",
            "final_file_suffix": ".{output_format}",
        },
    },
    "default": {
        "seismic": {
            "intermediate_file_prefix": "deployment_history_map_{deploy_type!s}_{year:04d}_{month:02d}_{map_type}_",
            "intermediate_file_suffix": ".{intermediate_format}",
            "final_file_prefix": "deploymap_{year:04d}_{month:02d}.{map_type}",
            "final_file_suffix": ".{output_format}",
        },
        "inframet": {
            "intermediate_file_prefix": "deployment_history_map_{deploy_type!s}_{year:04d}_{month:02d}_{map_type!s}_",
            "intermediate_file_suffix": ".{intermediate_format}",
            "final_file_prefix": "deploymap_{deploy_type}_{year:04d}_{month:02d}.{map_type}",
            "final_file_suffix": ".{output_format}",
        },
    },
}
"""Filename format strings organized by size, then map_type.

Retrieve the relevant sub key with DeploymentMapMaker._get_map_filename_parts().
"""

DEPLOY_TYPE_DECOM_RGBS = {"seismic": "77/77/77", "inframet": "255/255/255"}
"""Color values for decomissioned stations, by deployment type."""
