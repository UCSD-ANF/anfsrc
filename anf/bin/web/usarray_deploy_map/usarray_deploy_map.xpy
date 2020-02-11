"""Generate a new map for the usarray website.

@author     Juan Reyes
@author     Geoff Davis
@author     Rob Newman
@author     Malcolm White
@modified   25/07/2014 - Malcolm White
@notes      Updated to run under 5.4 of Antelope.
"""

import os
from os.path import basename
from shutil import move
import sys
import tempfile
from subprocess import check_call
import logging

from anf import logutil

from anf.deploymentmap import DeploymentMapMaker, constant, gmt
#from .exception import YearMonthValueError

LOGGER = logutil.getLogger(__name__)


class USArrayDeployMap(DeploymentMapMaker):
    """The usarray_deploy_map application."""

    pfname = "usarray_deploy_map"
    """Redefine the default parameter file for this class."""

    def new_run(self):
        for m in self.args.maptype:
            if self.args.size == "wario":
                ps = tempfile.mkstemp(
                    suffix=".ps",
                    prefix="deployment_history_map_%s_%d_%02d_%s_WARIO_"
                    % (self.args.deploytype, self.args.time.year, self.args.time.month, m),
                )
                png = "PNG not created for tiled display wario. Create by hand in Photoshop"
            else:
                ps = tempfile.mkstemp(
                    suffix=".ps",
                    prefix="deployment_history_map_%s_%d_%02d_%s_"
                    % (self.args.deploytype, self.args.time.year, self.args.time.month, m),
                )
                if self.args.deploytype == "inframet":
                    finalfile = "deploymap_%s_%d_%02d.%s.png" % (self.args.deploytype, self.args.time.year, self.args.time.month, m)
                else:
                    finalfile = "deploymap_%d_%02d.%s.png" % (self.args.time.year, self.args.time.month, m)
                png = "%s/%s" % (self.output_dir, finalfile)

            self.logger.info("Working on maptype: " + m)
            self.logger.info("Temp postscript file: " + ps[1])
            self.logger.info("Output target: " + png)

            # Determine region of interest and center of plot
            # The lat and lon padding ensures we get full topo and bathy.
            minlon = int(self.usa_coords["MINLON"])
            maxlon = int(self.usa_coords["MAXLON"])
            minlat = int(self.usa_coords["MINLAT"])
            maxlat = int(self.usa_coords["MAXLAT"])
            region = "%s/%s/%s/%s" % (minlon, minlat, maxlon, maxlat) + "r"
            centerlat = (maxlat - minlat) / 2 + minlat
            centerlon = (maxlon - minlon) / 2 + minlon

            ak_minlon = int(self.ak_coords["MINLON"])
            ak_maxlon = int(self.ak_coords["MAXLON"])
            ak_minlat = int(self.ak_coords["MINLAT"])
            ak_maxlat = int(self.ak_coords["MAXLAT"])
            ak_region = "%s/%s/%s/%s" % (ak_minlon, ak_minlat, ak_maxlon, ak_maxlat) + "r"
            ak_centerlat = (ak_maxlat - ak_minlat) / 2 + ak_minlat
            ak_centerlon = (ak_maxlon - ak_minlon) / 2 + ak_minlon

            if self.args.size == "wario":
                center = "%s/%s/%s" % (centerlon, centerlat, "44") + "i"
                ak_center = "%s/%s/%s" % (ak_centerlon, ak_centerlat, "10") + "i"
            else:
                center = "%s/%s/%s" % (centerlon, centerlat, self.usa_coords["WIDTH"]) + "i"
                ak_center = (
                    "%s/%s/%s" % (ak_centerlon, ak_centerlat, self.ak_coords["WIDTH"]) + "i"
                )

            self.logger.info("GMT USA region string: " + region)
            self.logger.info("GMT USA center location string: " + center)
            self.logger.info("GMT AK region string: " + ak_region)
            self.logger.info("GMT AK center location string: " + ak_center)

            if self.args.deploytype == "seismic":
                station_loc_files, counter = self.generate_sta_locations(
                    self.dbmaster, m, self.args.deploytype, self.args.time.year, self.args.time.month, self.args.verbose, self.args.debug
                )
                rgbs = {
                    "1_DECOM": "77/77/77"
                }  # Init with the missing color and force to be first plotted
            elif self.args.deploytype == "inframet":
                station_loc_files, counter = self.generate_inframet_locations(
                    self.dbmaster, m, self.args.deploytype, self.args.time.year, self.args.time.month, self.infrasound_mapping, self.args.verbose, self.args.debug
                )
                rgbs = {
                    "1_DECOM": "255/255/255"
                }  # Init with the missing color and force to be first plotted

            snets_text = {}
            for key in sorted(station_loc_files.iterkeys()):
                if self.args.deploytype == "seismic":
                    if key in self.networks:
                        color = self.networks[key]["color"]
                        rgbs[key] = self.colors[color]["rgb"].replace(",", "/")
                        snets_text[key] = self.networks[key]["abbrev"].replace(" ", "\ ")
                elif self.args.deploytype == "inframet":
                    self.logger.debug("Working on inframet key: " + key)
                    if key in self.infrasound:
                        color = self.infrasound[key]["color"]
                        rgbs[key] = self.colors[color]["rgb"].replace(",", "/")
                        snets_text[key] = self.infrasound[key]["name"].replace(" ", "\ ")
            # Extra key for the decommissioned stations group
            if m == "cumulative":
                if self.args.deploytype == "seismic":
                    color = self.networks["DECOM"]["color"]
                    rgbs["decom"] = self.colors[color]["rgb"].replace(",", "/")
                elif self.args.deploytype == "inframet":
                    color = self.infrasound["decom"]["color"]
                    rgbs["decom"] = self.colors[color]["rgb"].replace(",", "/")

        #... contents prior to this comment have been migrated to base class.
            # Create the contiguous United States topography basemap

            # {{{ Contiguous United States

            self.logger.info("Working on contiguous United States")

            if self.args.debug == True:
                try:
                    check_call(
                        "gmt pscoast -R%s -JE%s -Df -A5000 -S%s -G40/200/40 -V -X2 -Y2 -K >> %s"
                        % (region, center, constant.WET_RGB, ps[1]),
                        shell=True,
                    )
                except OSError:
                    self.logger.exception(
                        "gmt pscoast for contiguous United States execution failed"
                    )
                    raise
            else:
                try:
                    check_call(
                        "gmt grdimage usa.grd -R%s -JE%s -Cland_ocean.cpt -Iusa.grad -V -E100 -X2 -Y2 -K >> %s"
                        % (region, center, ps[1]),
                        shell=True,
                    )
                except OSError:
                    self.logger.exception("gmt grdimage for usa.grd execution failed")
                    raise

            # Plot land areas below sea level correctly

            # Salton Sea co-ords -R-116.8/-115/32/34
            USArrayDeployMap.gmt_fix_land_below_sealevel(
                "saltonsea", "Salton Sea", region, center, ps[1], constant.WET_RGB
            )

            # Death Valley co-ords -R
            USArrayDeployMap.gmt_fix_land_below_sealevel(
                "deathvalley", "Death Valley", region, center, ps[1], constant.WET_RGB
            )

            # Plot wet areas and coastline
            self.gmt_plot_wet_and_coast(region, center, constant.WET_RGB, ps[1])

            # Overlay the grid
            self.gmt_overlay_grid(
                region, center, self.usa_coords["GRIDLINES"], "-75/30/36/500", ps[1]
            )

            # Add stations from local text files
            self.gmt_add_stations(station_loc_files, self.symsize, rgbs, ps[1])

            # }}} Contiguous United States

            self.logger.info(" - Working on Alaska inset")

            # {{{ Alaska

            if self.args.debug == True:
                try:
                    check_call(
                        "gmt pscoast -R%s -JE%s -Df -A5000 -S%s -G40/200/40 -V -X0.1i -Y0.1i -O -K >> %s"
                        % (ak_region, ak_center, constant.WET_RGB, ps[1]),
                        shell=True,
                    )
                except OSError:
                    self.logger.exception("gmt pscoast for Alaska execution failed")
                    raise
            else:
                try:
                    check_call(
                        "gmt grdimage alaska.grd -R%s -JE%s -Cland_ocean.cpt -Ialaska.grad -V -E100 -X0.1i -Y0.1i -O -K >> %s"
                        % (ak_region, ak_center, ps[1]),
                        shell=True,
                    )
                except OSError:
                    self.logger.exception("gmt grdimage for alaska.grd execution failed")
                    raise

            # Plot wet areas and coastline
            gmt.gmt_plot_wet_and_coast(ak_region, ak_center,
                                                    constant.WET_RGB, ps[1])

            # Overlay the grid
            gmt.gmt_overlay_grid(
                ak_region, ak_center, self.ak_coords["GRIDLINES"], "-145/57/60/500", ps[1]
            )

            # Add stations from local text files
            gmt.gmt_add_stations(station_loc_files, self.symsize, rgbs, ps[1])

            # }}} Alaska

            # Clean up station files
            for key in sorted(station_loc_files.iterkeys()):
                os.unlink(station_loc_files[key])

            self.logger.debug("Working on year and month timestamp")
            # Create the text files of year & month and legend
            time_file = tempfile.mkstemp(suffix=".txt", prefix="year_month_")
            # time_file = "%syear_month.txt" % tmp
            tf = open(time_file[1], "w")
            tf.write("-75.5    17    20    0    1    BR    %d\ %02d" % (self.args.time.year, self.args.time.month))
            tf.close()

            self.logger.debug("Working on copyright file")
            copyright_file = tempfile.mkstemp(suffix=".txt", prefix="copyright_")
            # copyright_file = "%scopyright.txt" % tmp
            cf = open(copyright_file[1], "w")
            cf.write(
                "-67    48.7    11    0    1    BR    (c)\ {s}\ -\ {e}\ Array\ Network\ Facility,\ http://anf.ucsd.edu".format(s=constant.START_YEAR, e=self.args.time.year)
            )
            cf.close()

            self.logger.debug("Working on snet files")
            snets_file = tempfile.mkstemp(suffix=".txt", prefix="snets_")
            sf = open(snets_file[1], "w")
            if self.args.size == "wario":
                legend_symsize = "0.3"
            else:
                legend_symsize = "0.15"
            snet_file_txt = "G 0.06i\n"
            snet_file_txt += "H 14 Helvetica-Bold Network Legend\n"
            snet_file_txt += "D 0.06i 1p\n"  # A horizontal line
            snet_file_txt += "N 1\n"
            snet_file_txt += "V 0 1p\n"
            snet_symbol = "t"
            for key in sorted(snets_text.iterkeys()):
                snet_symbol = "t"
                self.logger.info("snets: " + key)
                if key == "IU" or key == "US":
                    snet_symbol = "d"
                snet_file_txt += "S 0.1i %s %s %s 0.25p 0.3i %s\ [%s]\n" % (
                    snet_symbol,
                    legend_symsize,
                    rgbs[key],
                    snets_text[key],
                    counter[key],
                )
            if m == "cumulative":
                snet_file_txt += "D 0.06i 1p\n"  # A horizontal line
                snet_file_txt += "S 0.1i %s %s %s 0.25p 0.3i Decommissioned\ [%s]\n" % (
                    snet_symbol,
                    legend_symsize,
                    rgbs["decom"],
                    counter["decom"],
                )
            sf.write(snet_file_txt)
            sf.close()

            # Overlay the copyright notice
            self.logger.info("Overlay the copyright notice")

            try:
                check_call(
                    "gmt pstext %s -R%s -JE%s -V -D0.25/0.25 -P -O -K >> %s"
                    % (copyright_file[1], region, center, ps[1]),
                    shell=True,
                )
            except OSError:
                self.logger.exception("Copyright msg plotting error: pstext execution failed")
                os.unlink(copyright_file[1])
                return -1
            else:
                os.unlink(copyright_file[1])

            # Overlay the date legend stamp
            self.logger.info("Overlay the date legend stamp")
            try:
                # " -W255/255/255o1p/0/0/0 -C50% -P -O -K >> " + ps[1],
                check_call(
                    "gmt pstext "
                    + time_file[1]
                    + " -R"
                    + region
                    + " -JE"
                    + center
                    + " -V -D0.25/0.25"
                    + " -G255 -C50% -P -O -K >> "
                    + ps[1],
                    shell=True,
                )
            except OSError:
                self.logger.exception("Time msg plotting error: pstext execution failed")
                return -1
            else:
                os.unlink(time_file[1])

            # Overlay the snet legend
            self.logger.info("Overlay the snet legend")

            if self.args.deploytype == "seismic":
                legend_width = "2.6"
                legend_height = "2.98"
            elif self.args.deploytype == "inframet":
                legend_width = "4.2"
                legend_height = "1.7"
            else:
                self.logger.error("unknown deploytype")
                raise ValueError("unknown deploytypte")

            try:
                check_call(
                    "gmt pslegend %s -R%s -JE%s -V -Dg-90/26+w%si/%si+jTC -F+g255/255/255 -P -O >> %s"
                    % (snets_file[1], region, center, legend_width, legend_height, ps[1]),
                    shell=True,
                )
            except OSError:
                self.logger.exception(
                    "Network (snet) legend plotting error: pslegend execution failed"
                )
                raise
            else:
                os.unlink(snets_file[1])

            # Run Imagemagick convert cmd on Postscript output
            if self.args.size == "wario":
                print("Your file for wario is ready for photoshop and is called " + ps[1])
            else:
                self.logger.info(
                    "Running Imagemagick's convert command on postscript file " + ps[1]
                )
                try:
                    check_call(
                        "convert -trim -depth 16 +repage %s %s" % (ps[1], png), shell=True
                    )
                except OSError:
                    self.logger.exception("convert Execution failed")
                    raise
                else:
                    os.unlink(ps[1])

                if self.args.deploytype == "inframet":
                    web_output_dir = self.web_output_dir_infra

                self.logger.info("Going to move %s to %s/%s" % (png, web_output_dir, finalfile))
                try:
                    move(png, "%s/%s" % (web_output_dir, finalfile))
                except OSError:
                    self.logger.exception("move failed")
                    raise
                else:
                    print(
                        "Your file is ready and is called %s/%s"
                        % (web_output_dir, finalfile)
                    )

        return 0

def main(argv=None):
    # Configure a logger with the default elog output handler
    logger = logutil.getAppLogger(argv=argv)

    # Instantiate the myapp, which will read command-line parameters
    myapp = USArrayDeployMap(argv)

    # Use command-line parameters to set the log level.
    logger.setLevel(myapp.loglevel)

    # Reset our instance logger to the name of the script.
    logger=logging.getLogger(basename(argv[0]))

    logger.notify("Loglevel set to {s}".format(s=myapp.loglevel))
    return myapp.run()



if __name__ == "__main__":
    result = main(sys.argv)
    sys.exit(result)
