"""Database routines for deploymentmap."""

import collections
from pprint import pformat

from anf.logutil import fullname, getLogger
from antelope import datascope, stock
import six

from . import constant

LOGGER = getLogger(__name__)


class SeismicStationMetadata(
    collections.namedtuple(
        "SeismicStationMetadata",
        ["snet", "sta", "lat", "lon", "time", "endtime", "extra_channels"],
    )
):
    """Represents a station as metadata attributes.

    Note - this is currently defined as a tuple and thus most properties are
    read-only. The 'extra_sensor_mapping' is one exception - itcan be set after
    object creation.

    """

    extra_sensor_mapping = None
    """Override this to customize new sensors."""

    @property
    def extra_sensors(self):
        """Sensors in addition to the normal seismic suite."""

        if self.extra_sensor_mapping is None:
            LOGGER.debug("extra_sensors: No extra_sensor_mapping defined.")
            return None

        extra_sensors = []
        for sensor_name in self.extra_sensor_mapping.keys():
            for chan in self.extra_channels:
                if chan in self.extra_sensor_mapping[sensor_name]:
                    extra_sensors.append(sensor_name)
        # conversion to set gives us unique values.
        if len(extra_sensors) == 1:
            return extra_sensors[0]
        return set(extra_sensors)

    def is_active_after(self, time):
        """Check if the station is still active in the dbmaster at a given time.

        Args:
            time (numeric): Antelope timestamp value, will be compared with the
            station's endtime.

        Returns:
            (bool): True if the station's endtime is not set or the endtime is
            later than the given time, false if the station is not active.

        """

        if self.endtime is None:
            return True
        return self.endtime >= time


class DbMasterView:
    """Retrieve data about stations in a Datascope dbmaster.

    Intended to work with data stored in a USArray-style datascope database,
    this class may be able to be extended in the future to handle more general
    case deployments.
    """

    _dbmaster_pointer = None

    def __init__(
        self, dbmaster, extra_sensor_mapping=constant.DEFAULT_INFRASOUND_MAPPING
    ):
        """Initialize a new DbMaster view.

        Args:
            dbmaster (string): the name of the Datascope database containing the dbmaster.

            infrasound_mapping (dict): key/value pairs of sensor type to
            representative channels. Several functions use this mapping to
            determine what type of sensors are at a station, as a shorthand for
            looking in the dlsensor table.

        Infrasound Mapping dict format:
            {
                "MEMS":  ("LDM_EP"),
                "SETRA": ("BDO_EP, LDO_EP"),
                "NCPA":  ("BDF_EP", "LDF_EP")
            }

        """
        self.logger = getLogger(fullname(self))
        self.dbmaster = dbmaster
        self.extra_sensor_mapping = extra_sensor_mapping
        self._dbmaster_pointer = datascope.dbopen(dbmaster, "r")

    def get_pointer(self):
        """Get a datascope.Dbptr reference to the dbmaster.

        Used for direct datascope database manipulation.

        Be sure to Dbptr.free() the view when done to avoid memory leaks due to a limitation of the underlying drivers. This is best accomplished with the datascope.freeing context manager.

        Example:
            import antelope.datascope
            dbmasterview=DbMasterView("/path/to/db")

            with datascope.freeing(dbmasterview.get_pointer()) as dbp:
                print(repr(dbp))

        """

        return datascope.Dbptr(copy=self._dbmaster_pointer)

    def __del__(self):
        """Close the database pointer upon object garbage collection."""
        try:
            self._dbmaster_pointer.close()
            self._dbmaster_pointer = None
        except RuntimeWarning:
            self.logger.exception("Runtime warning on close.")
        except AttributeError:
            self.logger.debug("Database %s was not open.", self.dbmaster)
        except datascope.DbcloseError:
            self.logger.debug(
                "An error occurred closing the database %s.",
                self.dbmaster,
                exc_info=True,
            )

    @staticmethod
    def _timeendtime_subset(
        start_time, end_time, time_column="time", endtime_column="endtime"
    ):
        """Generate a dbexpression for subset by time/endtime."""
        assert start_time >= 0
        assert end_time is None or end_time >= 0

        subset = ""

        if end_time is not None:
            subset += "{time_column} <= {end_time:f}"
            if start_time > 0:
                subset += " && "
        if start_time > 0:
            subset += "{endtime_column} >= {start_time:f}"

        return subset.format(
            start_time=start_time,
            end_time=end_time,
            time_column=time_column,
            endtime_column=endtime_column,
        )

    @staticmethod
    def _onoff_subset(
        start_time, end_time, ondate_column="ondate", offdate_column="offdate"
    ):
        """Generate a dbexpression for subset by on/off date, given epoch time/endtime.

        Some Datascope db fields like ondate and offdate are in yearday format
        - rather than epoch timestamps used in the deployment tables. This
        helper method generates dbexpression strings using Antelope's yearday
        expression function to convert from epoch time to yearday and allow
        similar comparisons to time and endtime.

        Args:
            start_time, end_time (numeric): Antelope epoch times. These are
            converted to the yearday format and used in the subset expression.

            ondate_column, offdate_column (string): column names for ondate and
            offdate. Useful when mutiple tables are joined in a database view.

        Returns:
            string: dbexpression for dbsubset.

        """
        assert start_time >= 0
        assert end_time is None or end_time >= 0

        subset = ""

        if end_time is not None:
            subset += "{ondate_column} < yearday({end_time:f})"
            if start_time > 0:
                subset += " && "
        if start_time > 0:
            subset += "{offdate_column} >= yearday({start_time:f})"

        return subset.format(
            start_time=start_time,
            end_time=end_time,
            ondate_column=ondate_column,
            offdate_column=offdate_column,
        )

    @property
    def _extra_sensor_channels(self):
        """Get a list of extra channels based on the extra_sensor_mapping dict."""
        result = []
        for v in self.extra_sensor_mapping.values():
            if isinstance(v, six.string_types):
                result.append(v)
            else:
                result += v
        # pprint(result)
        if len(result) < 0:
            return None
        return sorted(result)

    def get_extra_sensor_metadata(self, start_time=0, end_time=None):
        """Retrieve extra sensor locations as a generator.

        Args:
            start_time, end_time: bounds for station endtime and time
        """
        assert start_time >= 0
        assert end_time is None or end_time >= 0

        # Build the Datascope query str.
        # qstr = "|".join(["|".join(v) for k, v in infrasound_mapping.items()])
        qstr = "|".join(self._extra_sensor_channels)

        self.logger.info(
            "Infrasound: Searching sitechan table for chans that match: " + qstr
        )

        # Construct a dbsubset format string
        dbsubset_cmd = self._timeendtime_subset(start_time, end_time)
        if len(dbsubset_cmd) > 0:
            dbsubset_cmd = "dbsubset " + dbsubset_cmd
        else:
            dbsubset_cmd = None

        # Compile our dbprocess list of commands
        process_list = ["dbopen sensor"]

        if dbsubset_cmd:
            process_list.append(dbsubset_cmd)

        process_list += [
            "dbsubset chan=~/({!s})/".format(qstr),
            "dbjoin snetsta",
            "dbjoin site",
            "dbsort sta ondate chan time",
        ]
        self.logger.debug(pformat(process_list))

        # Track our stats here
        stats = {
            "numsta": 0,
            "numrec": 0,
        }

        with datascope.freeing(self.get_pointer()) as infraptr:
            try:
                infraptr = infraptr.process(process_list)
            except Exception as e:
                self.logger.exception("Dbprocessing failed.")
                raise e

            try:
                infraptr_grp = infraptr.group("sta")
            except Exception as e:
                self.logger.exception("Dbgroup failed")
                raise e
            with datascope.freeing(infraptr_grp):
                # Get values into a easily digestible dict
                for sta_record in infraptr_grp.iter_record():
                    sta, [db, view, end_rec, start_rec] = sta_record.getv(
                        "sta", "bundle"
                    )
                    stats["numsta"] += 1
                    sta_data = {
                        "sta": sta,
                    }
                    extra_channels = []
                    for stachan_record in range(start_rec, end_rec):
                        infraptr.record = stachan_record
                        stats["numrec"] += 1

                        try:
                            (
                                sta_data["snet"],
                                sta_data["sta"],
                                chan,
                                sta_data["lat"],
                                sta_data["lon"],
                                time,
                                endtime,
                            ) = infraptr.getv(
                                "snet", "sta", "chan", "lat", "lon", "time", "endtime"
                            )
                        except TypeError:
                            self.logger.exception(
                                "infraptr.getv failed with dbprocess commands:\n%s",
                                pformat(process_list),
                            )
                            raise

                        # Append the channel name to the current extra_channels list.
                        extra_channels += chan
                        """Due to query sort order, we end up with only the
                        most recent lat/lon for the station."""

                        """We keep the oldest time and the newest endtime."""
                        try:
                            sta_data["time"] = min(sta_data["time"], time)
                        except KeyError:
                            sta_data["time"] = time

                        try:
                            sta_data["endtime"] = min(sta_data["endtime"], endtime)
                        except KeyError:
                            sta_data["endtime"] = endtime

                    # eliminate duplicate channels with set
                    sta_data["extra_channels"] = set(extra_channels)

                    # Create a new SeismicStationMetadata object from sta_data
                    # as keyword pairs.
                    metadata = SeismicStationMetadata(**sta_data)

                    # Set the extra_sensor_mapping attribute so that sensor
                    # mapping function works.
                    metadata.extra_sensor_mapping = self.extra_sensor_mapping

                    # Print progress stats after every 100 db rows.
                    if stats["numrec"] % 100 == 0:
                        LOGGER.debug(
                            "Progress: Retrieved %d stations with %d records.",
                            stats["numsta"],
                            stats["numrec"],
                        )

                    yield metadata
        LOGGER.debug(
            "Retrieved %d stations with %d records.", stats["numsta"], stats["numrec"]
        )

    def get_seismic_station_metadata(self, start_time=0, end_time=None):
        """Retrieve station locations from db and yield as a generator.

        Args:
            db (string): path to datascope dbmaster for the network
            maptype (string): cumulative or rolling
            start_time(numeric): unix timestamp. Stations with endtimes before this time will be excluded.
            end_time (numeric): unix timestamp. Stations with "time" after this time will be excluded.

        Yields:
            SeismicStationMetadata tuple: includes snet as one of the key/value pairs. Records are returned sorted by snet then by sta.
        """

        stats = {"numsta": 0}

        # Construct a dbsubset format string
        dbsubset_cmd = self._onoff_subset(start_time, end_time)

        print('dbsubset_cmd pre noning: "{!s}"'.format(dbsubset_cmd))
        if len(dbsubset_cmd) > 0:
            dbsubset_cmd = "dbsubset " + dbsubset_cmd
        else:
            dbsubset_cmd = None

        # Define dbops
        process_list = ["dbopen site"]

        if dbsubset_cmd is not None:
            process_list.append(dbsubset_cmd)

        process_list += [
            "dbjoin snetsta",
            "dbsort snet sta",
        ]

        print("Seismic process_list:\n" + pformat(process_list))
        with datascope.freeing(self.get_pointer()) as dbptr:
            dbptr = dbptr.process(process_list)

            for record in dbptr.iter_record():
                stats["numsta"] += 1
                vals = record.getv("snet", "sta", "lat", "lon", "ondate", "offdate")
                sta_data = SeismicStationMetadata(
                    snet=vals[0],
                    sta=vals[1],
                    lat=vals[2],
                    lon=vals[3],
                    time=stock.epoch(vals[4]),
                    endtime=stock.epoch(vals[5]),
                    extra_channels=None,
                )
                yield sta_data

        LOGGER.debug("Processed %d stations.", stats["numsta"])
