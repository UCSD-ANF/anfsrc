"""Wrapper around Generic Mapping Tools for ANF-style map making."""

import collections

from anf.logutil import getModuleLogger

from . import command, constant

LOGGER = getModuleLogger(__name__)


class GmtConfig(object):
    """Track options for GMT commands."""

    def __init__(self, regions, region_positions, global_options=None):
        """Set options for the GmtConfig class.

        Args:
            regions (list[anf.gmt.region.GmtRegion]): list of GmtRegions that this program knows about
            region_positions (dict): dictionary describing layout of various GMTRegions on the map
            global_options (dict): defaults for all instances in key-value format.
        """

        if global_options is None:
            global_options = {}

        self.global_options = {
            "ps_page_orientation": constant.DEFAULT_PS_PAGE_ORIENTATION,
            "ps_page_color": constant.DEFAULT_PS_PAGE_COLOR,
            "ps_media": constant.DEFAULT_PS_MEDIA,
            # Basemap annotation options
            "map_annot_offset_primary": constant.DEFAULT_MAP_ANNOT_OFFSET_PRIMARY,
            "map_annot_offset_secondary": constant.DEFAULT_MAP_ANNOT_OFFSET_SECONDARY,
            "map_label_offset": constant.DEFAULT_MAP_LABEL_OFFSET,
            # Basemap Layout options
            "map_frame_width": constant.DEFAULT_MAP_FRAME_WIDTH,
            "map_scale_height": constant.DEFAULT_MAP_SCALE_HEIGHT,
            "map_tick_length": constant.DEFAULT_MAP_TICK_LENGTH,
            "x_axis_length": constant.DEFAULT_X_AXIS_LENGTH,
            "y_axis_length": constant.DEFAULT_Y_AXIS_LENGTH,
            "map_origin_x": constant.DEFAULT_MAP_ORIGIN_X,
            "map_origin_y": constant.DEFAULT_MAP_ORIGIN_Y,
            "map_logo_pos": constant.DEFAULT_MAP_LOGO_POS,
            "map_line_step": constant.DEFAULT_MAP_LINE_STEP,
            # Misc options
            "proj_length_unit": constant.DEFAULT_PROJ_LENGTH_UNIT,
            "dir_gshhg": constant.DIR_GSHHG,
        }

        self.global_options.update({k.lower(): v for k, v in global_options.items()})

        self.regions = regions

        self.region_positions = region_positions


GmtXYStationFileInfo = collections.namedtuple(
    "GmtXYStationFileInfo", ["file_list", "counts"]
)


def gmt_add_stations(
    station_loc_files, symsize, rgbs, outfile, omit_header=True, keep_open=True
):
    """Overlay the station icons."""
    for key in sorted(station_loc_files.keys()):
        if key == "IU" or key == "US":
            # Plots diamond symbols for US backbone stations
            symaptype = "d"
        else:
            symaptype = "t"

        args = [
            "-R",
            "-JE",
            "-V",
            "-S{}{}".format(symaptype, symsize),
            "-G{}".format(rgbs[key]),
            "-W",
            "-L",
            "-:",
        ]
        command.psxy(
            psxy_options=args,
            xy_file=station_loc_files[key],
            outfile=outfile,
            omit_header=omit_header,
            keep_open=keep_open,
        )


def gmt_plot_background(outfile, region_name, center, wet_rgb, use_color, **kwargs):
    """Plot a background image using either psbasemap or pscoast."""
    # Orig US grdimage
    # "gmt grdimage usa.grd -R%s -JE%s -Cland_ocean.cpt -Iusa.grad -V -E100 -X2 -Y2 -K >> %s" % (
    # region, center, ps[1]),
    # Orig AK grdimage
    # "gmt grdimage alaska.grd -R%s -JE%s -Cland_ocean.cpt -Ialaska.grad -V"
    # " -E100 -X0.1i -Y0.1i -O -K >> %s" % (ak_region, ak_center, ps[1])

    # Orig US pscoast
    # "gmt pscoast -R%s -JE%s -Df -A5000 -S%s -G40/200/40 -V -X2 -Y2 -K >> %s"
    #                    % (region, center, constant.WET_RGB, ps[1]),

    # Orig AK pscoast
    # "gmt pscoast -R%s -JE%s -Df -A5000 -S%s -G40/200/40 -V -X0.1i -Y0.1i -O -K >> %s"
    #                    % (ak_region, ak_center, constant.WET_RGB, ps[1]),

    if use_color is False:
        args = ["-Df", "-A5000", "-G40/200/40", "-V", "-X2", "-Y2"]
        return command.pscoast(
            region_name=region_name,
            center=center,
            wet_rgb=wet_rgb,
            pscoast_options=args,
            outfile=outfile,
            **kwargs
        )

    else:
        args = ["-Cland_ocean.cpt", "-V", "-E100", "-X2", "-Y2"]
        return command.grdimage(
            grid_file="usa.grd",
            region_name=region_name,
            center=center,
            gradiant_file="usa.grad",
            grdimage_options=args,
            outfile=outfile,
            **kwargs
        )


def gmt_overlay_grid(region_coords, center, coords, legendloc, outfile, **kwargs):
    """Overlay the grid for a given region_data."""

    args = [
        "-X0",
        "-Y0",
        "-R{}".format(region_coords),
        "-JE{}".format(center),
        "-V",
        "-Bg{}wesn".format(coords),
        "-Lf{}sk+l".format(legendloc),
    ]

    command.run_ps_command("psbasemap", args, outfile, **kwargs)


def gmt_plot_wet_and_coast(
    region_coords, center, wet_rgb, outfile, omit_header=True, keep_open=True
):
    """Plot wet areas and coastline."""

    # Plot wet areas (not coast)
    args = [
        "-V",
        "-R{}".format(region_coords),
        "-JE{}".format(center),
        "-W0.5p,{}".format(wet_rgb),
        "-S{}".format(wet_rgb),
        "-A0/2/4",
        "-Df",
        "-K",
    ]

    command.run_ps_command(
        "pscoast", args, outfile, keep_open=True, omit_header=omit_header
    )

    # Plot coastline in black
    command.run_ps_command(
        "pscoast",
        [
            "-V",
            "-R{}".format(region_coords),
            "-JE{}".format(center),
            "-W0.5p,0/0/0",
            "-Df",
        ],
        outfile,
        omit_header=True,
        keep_open=True,
    )

    # Plot major rivers
    command.run_ps_command(
        "pscoast",
        [
            "-V",
            "-R{}".format(region_coords),
            "-JE{}".format(center),
            "-Ir/0.5p,0/0/255",
            "-Df",
        ],
        outfile,
        keep_open=True,
        omit_header=True,
    )

    # Plot national (N1) and state (N2) boundaries
    args = [
        "-V",
        "-R{}".format(region_coords),
        "-JE{}".format(center),
        "-N1/1",
        "-n2/0.2",
        "-Df",
    ]

    command.run_ps_command(
        "pscoast", args, outfile, keep_open=keep_open, omit_header=True
    )


def gmt_plot_region(
    outfile,
    time,
    map_type,
    region_data,
    position_data,
    output_size_name,
    output_size_data,
    use_color=True,
    omit_header=True,
    keep_open=True,
):
    """Plot a geographic region.

    Args:
        outfile (string): path to output file
        time (yearmonth): tuple of year, month in integer format, 1=Jan 12=Dec
        map_type (string): one of cumulative, rolling
        region_data (anf.gmt.region.GmtRegion): Region metadata
        position_data (dict): contains plot position data for the region being plotted
        output_size_name (string): name of the selected output size
        output_size_data (dict): data related to the selected output size
        use_color (bool): plot in black and white for speed.
        omit_header (bool): don't insert postscript preamble for new files if true
        keep_open (bool): don't close out postscript file if true
    """
    center_coords = region_data.get_azeq_center_str(
        position_data["width"][output_size_name]
    )
    # plot the base map
    gmt_plot_background(
        region_name=region_data.name,
        center=center_coords,
        outfile=outfile,
        wet_rgb=constant.WET_RGB,
        use_color=use_color,
        omit_header=omit_header,
        keep_open=True,
    )

    # Plot wet areas and coastline
    gmt_plot_wet_and_coast(
        region_data,
        center_coords,
        constant.WET_RGB,
        outfile,
        omit_header=True,
        keep_open=True,
    )

    # Overlay the grid
    gmt_overlay_grid(
        region_data.name,
        center_coords,
        output_size_data["gridlines"],
        position_data["scaleloc"],
        outfile=outfile,
        omit_header=True,
        keep_open=keep_open,
    )

    # Add stations from local text files
    # gmt_add_stations(station_loc_files, self.symsize, rgbs, outfile)

    # TODO: finish importing routines from old script


def gmt_fix_land_below_sea_level(
    region_name,
    region_coords,
    center,
    outfile,
    wet_rgb,
    omit_header=True,
    keep_open=True,
):
    """Run psclip to fix coloring of dry areas that are below sea-level."""

    land_file = "land_only.cpt"
    grd_file = region_name + ".grd"
    gradient_file = region_name + ".grad"
    xy_file = region_name + ".xy"

    # NOTE: formatting is unnecessarily verbose due to Python 2.7 not supporting format strings.
    # While we're in between Python releases, we need manually call .format() instead of just using f strings.

    # Define a clip region
    params = [xy_file, "-R{}".format(region_coords), "-JE{}".format(center), "-V"]

    command.run_ps_command(
        "psclip", params, outfile=outfile, omit_header=omit_header, keep_open=True
    )

    # Make area 'land-only' and put into the clipping region
    params = [
        grd_file,
        "-V",
        "-R{}".format(region_coords),
        "-JE{}".format(center),
        "-C{}".format(land_file),
        "-I%{}".format(gradient_file),
        "-O",
        "-K",
    ]

    command.run_ps_command(
        "grdimage", params, outfile=outfile, omit_header=True, keep_open=True
    )

    # Color the actual water areas blue
    params = [
        "-V",
        "-R{}".format(region_coords),
        "-JE{}".format(center),
        "-C{}".format(wet_rgb),
        "-Df",
    ]
    command.run_ps_command(
        "pscoast", params, outfile=outfile, omit_header=True, keep_open=True
    )

    # Close psclip
    params = ["-C", "-O"]

    command.run_ps_command(
        "psclip", params, outfile, omit_header=True, keep_open=keep_open
    )
