"""Wrapper around Generic Mapping Tools for deployment map making."""

import os
import tempfile

from anf import logutil

from . import util
from ..gmt import GmtXYStationFileInfo, command

LOGGER = logutil.getModuleLogger(__name__)


class GmtDeployMapPlotter:
    """Plot a deployment map for a given start_time and end_time."""

    deployment_types = {}

    def __init__(
        self,
        map_type,
        deployment_type,
        start_time,
        end_time,
        station_metadata_objects,
        config,
        file_prefix: str,
        file_suffix: str,
    ):
        """Initialize a deployment map plotter for a particular time period.

        Args:
            map_type (basestring): type of map - either cumulative or rolling
            deployment_type: instrument deployment type to plot. Built-ins include seismic and inframet.
             Others can be added with register_deployment_type.
            start_time (float): epoch start time of active stations
            end_time (float): epoch end time of active stations
            station_metadata_objects (list): list of StationMetadata
            config(GmtConfig): global options for the session

        """
        self.logger = logutil.getLogger(logutil.fullname(self))

        self.start_time = start_time
        self.end_time = end_time
        self.map_type = map_type
        self.deployment_type = deployment_type
        self.station_metadata_objects = station_metadata_objects
        self.config = config
        self.file_prefix = file_prefix
        self.file_suffix = file_suffix

        # Register the two default deployment types, with their XY file generator functions.
        self.register_deployment_type("seismic", self.generate_station_xy_files)
        self.register_deployment_type(
            "inframet",
            self.generate_extra_sensor_xy_files,
            classifer=util.InframetClassifier,
        )

    @classmethod
    def register_deployment_type(cls, name, xy_file_generator, **kwargs):
        """Register a new deployment type.

        Args:
            name (basestring): the name of the deployment type
            xy_file_generator (function): reference to a function that generates XY files.

        """
        deploy_params = kwargs
        deploy_params["xy_file_generator"] = xy_file_generator
        cls.deployment_types[name] = {deploy_params}

    def plot(self) -> str:
        """Make the deployment maps."""
        # TODO: finish implementing this.

        # Generate a tempfile
        fd, path = tempfile.mkstemp(suffix=self.file_suffix, prefix=self.file_prefix,)
        self.logger.info("Intermediate filename: %s", path)
        station_loc_files = None
        try:
            # Feed md as the input to the XY file generator function
            station_loc_files, counter = self.generate_xy_files(
                self.deployment_type,
                map_type=self.map_type,
                start_time=self.start_time,
                end_time=self.end_time,
            )

            # gmt.gmt_plot_region(
            #    outfile=path,
            #    time=self.time,
            #    map_type=self.map_type,
            #    name="CONUS",
            #    description="Contiguous United States (Lower 48)",
            #    coords=self.params["usa_coords"],
            #    use_color=self.params.useColor,
            # )
            # gmt.gmt_plot_region(
            #    outfile=path,
            #    time=self.params.time,
            #    name="AK",
            #    description="Alaska",
            #    map_type=map_type,
            #    coords=self.params["ak_coords"],
            #    use_color=self.params.useColor,
            # )
            # TODO: implement region layout plotting funtion, calling gmt_plot_region on the main region and any inlays
            # TODO: Replace the above calls with data from self.options
        # TODO: Create the basemaps and plot our files.

        finally:

            if station_loc_files is not None:
                for locfile in sorted(station_loc_files.keys()):
                    os.remove(station_loc_files[locfile])

        return path

    def generate_xy_files(self, deploy_type, *args, **kwargs):
        """Generate XY files based on the given deploy type.

        Calls a specific generator function based on the deploy_type. The Generator function
        must be registered for the given deployment type with register_deployment_type first.
        """

        return self.deployment_types[deploy_type]["xy_file_generator"](args, kwargs)

    def generate_extra_sensor_xy_files(self, classifier):
        """Output Inframet locations to GMT xy files.

        Args:
            classifier (StationSensorClassifier): utility method to classify a station based on it's extra_sensors

        Returns:
            tuple of filenames and file type counts
        """

        xys = {}
        file_list = {}
        counter = {}

        for sensor_class in classifier.sensor_classes:
            xys[sensor_class] = tempfile.mkstemp(
                suffix=".xy",
                prefix="deployment_list_inframet_{}_".format(sensor_class.upper()),
            )

            file_list[sensor_class] = xys[sensor_class][1]
            counter[sensor_class] = 0

        if self.map_type == "cumulative":
            xys["decom"] = tempfile.mkstemp(
                suffix=".xy", prefix="deployment_list_inframet_DECOM_"
            )
            # Add the DECOM by hand as it is a manufactured
            # file, not a snet per se. Call it _DECOM to force
            # it to plot first
            file_list["1_DECOM"] = xys["decom"][1]
            counter["decom"] = 0

        # Process dict
        for sta_data in self.station_metadata_objects:
            LOGGER.info("Working on station %s" % sta_data.sta)

            if self.map_type == "cumulative" and sta_data.is_decomissioned_at(
                self.start_time
            ):
                os.write(
                    xys["decom"][0],
                    "{lat:f}    {lon:f}    # DECOM {sta} \n".format(
                        lat=sta_data.lat, lon=sta_data.lon, sta=sta_data.sta
                    ).encode(),
                )
                counter["decom"] += 1
                continue

            xy_line = "{lat:f}    {lon:f}    # {sta} \n".format(
                lat=sta_data.lat, lon=sta_data.lon, sta=sta_data.sta
            ).encode()

            s = classifier.classify(sta_data.extra_sensors)

            if s is not None:
                os.write(xys[s][0], xy_line)
                counter[s] += 1

        for file_info in list(xys.values()):
            os.close(file_info[0])

        return GmtXYStationFileInfo(file_list, counter)

    def generate_station_xy_files(self):
        """Write station locations to GMT xy files.

        Returns:
            A tuple (fnames, counter), where:
                fnames is a dict of `snet` and the respective XY file
                counter is a dict of `snet` and the number of stations of each snet.

        TODO: fix upstream function so that it only takes one 1x2 dict
        TODO: make the fake snet for decomissioned stations match - currently '1_DECOM' (fnames) and 'decom' (counter)
        """

        counter = {"decom": 0}
        """Types of station are tracked in `counter`, by snet. 'decom' is a dummy snet."""

        decom_file_data = tempfile.mkstemp(
            suffix=".xy", prefix="deployment_list_DECOM_"
        )
        file_info = {"1_DECOM": decom_file_data}

        for station in self.station_metadata_objects:
            try:
                snet_file_data = file_info[station.snet]
            except KeyError:
                counter[station.snet] = 0
                snet_file_data = tempfile.mkstemp(
                    suffix=".xy", prefix="deployment_list_%s_" % station.snet
                )
                file_info[station.snet] = snet_file_data

            if station.is_decommissioned_at(self.start_time):
                counter[station.snet] += 1
                os.write(
                    snet_file_data[0],
                    "{lat:f}    {lon:f}    # {snet} {sta}\n".format(
                        **(
                            station._asdict()
                        )  # _asdict is not actually protected, see docs for collection.NamedTuple
                    ).encode(),
                )
            else:  # station is decomissioned
                counter["decom"] += 1
                os.write(
                    decom_file_data[0],
                    "{lat:f}    {lon:f}    # DECOM {snet} {sta}\n".format(
                        **(
                            station._asdict()
                        )  # _asdict is not actually protected, see docs for collection.NamedTuple
                    ).encode(),
                )

        # close out all of the file handles
        for fh in [fdata[0] for fdata in file_info.values()]:
            fh.close()

        file_list = {k: v[1] for k, v in file_info}

        return GmtXYStationFileInfo(file_list, counter)

    def set_options(self):
        """Call gmt set to configure global default parameters in the current working directory."""

        command.set_default_options(self.config.global_options)
