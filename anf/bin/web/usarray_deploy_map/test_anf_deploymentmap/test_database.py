"""Tests for anf.deploymentmap.database."""

import unittest

from anf.deploymentmap import constant, database
from antelope import datascope

#  1262304000.000 (001) 2010-01-01  00:00:00.00000 UTC Friday
METADATA_TIME = 1262304000.000
#  1264982400.000 (032) 2010-02-01  00:00:00.00000 UTC Monday
METADATA_ENDTIME = 1264982400.000
METADATA_DEFAULTS = {
    "snet": "XX",
    "sta": "TEST",
    "lat": "33.12345",
    "lon": "-118.12345",
    "time": METADATA_TIME,
    "endtime": METADATA_ENDTIME,
    "extra_channels": None,
}


class TestSeismicStationMetadata(unittest.TestCase):
    """Test SeismicStationMetadata."""

    def setUp(self):
        """Initialize a test metadata object."""

        self.stametadata = database.SeismicStationMetadata(**METADATA_DEFAULTS)

    def tearDown(self):
        """Tear down the metadata object."""
        # force del to run regardless of whether or not the garbage collector gets around to it.
        self.stametadata = None

    def test_extra_sensors_no_extra_channels(self):
        """Test extra_sensors with no extra_channels defined."""
        assert self.stametadata.extra_sensors is None

    def test_extra_sensors_with_extra_channels_but_no_mapping(self):
        """Test extra_sensors with extra_channels defined but no mapping."""
        assert self.stametadata.extra_sensors is None

    def test_extra_sensors_with_extra_channels_and_mapping(self):
        """Test extra_sensors with extra_channels and mapping defined."""
        new_kwargs = METADATA_DEFAULTS
        new_kwargs["extra_channels"] = ["LDM_EP", "BDF_EP"]
        md = database.SeismicStationMetadata(**new_kwargs)
        md.extra_sensor_mapping = constant.DEFAULT_INFRASOUND_MAPPING
        assert md.extra_sensors == set(["MEMS", "NCPA"])

    def test_is_active_after(self):
        """Test is_active_after."""

        # 1265760000.000 (041) 2010-02-10  00:00:00.00000 UTC Wednesday
        t = 1265760000
        assert METADATA_ENDTIME < t
        assert self.stametadata.endtime < t
        assert self.stametadata.is_active_after(t) is False
        assert self.stametadata.is_active_after(METADATA_TIME) is True
        assert self.stametadata.is_active_after(METADATA_ENDTIME) is False

    def test_is_active_after_null_endtime(self):
        """Test is_active_after with null endtime."""
        # 1265760000.000 (041) 2010-02-10  00:00:00.00000 UTC Wednesday
        t = 1265760000

        new_kwargs = METADATA_DEFAULTS.copy()
        new_kwargs["endtime"] = None
        md = database.SeismicStationMetadata(**new_kwargs)
        assert md.is_active_after(t) is True
        assert md.is_active_after(METADATA_TIME) is True
        assert md.is_active_after(METADATA_TIME + 1) is True
        assert md.is_active_after(METADATA_TIME - 1) is True

    def test_is_active_before(self):
        """Test is_active_before."""

        # 1265760000.000 (041) 2010-02-10  00:00:00.00000 UTC Wednesday
        assert self.stametadata.is_active_before(1265760000) is False
        assert self.stametadata.is_active_before(METADATA_TIME) is False
        assert self.stametadata.is_active_before(METADATA_TIME - 1) is False

        new_kwargs = METADATA_DEFAULTS.copy()
        new_kwargs["endtime"] = None
        md = database.SeismicStationMetadata(**new_kwargs)
        assert md.is_active_before(1265760000) is True
        assert md.is_active_before(METADATA_TIME) is False

    def test_is_decommissioned_at(self):
        """Test is_decommissioned_at."""

        # 1265760000.000 (041) 2010-02-10  00:00:00.00000 UTC Wednesday
        t = 1265760000
        assert self.stametadata.is_decommissioned_at(t) is True
        assert self.stametadata.is_decommissioned_at(METADATA_ENDTIME) is False
        assert self.stametadata.is_decommissioned_at(METADATA_ENDTIME + 1) is True
        assert self.stametadata.is_decommissioned_at(METADATA_TIME) is False

    def test_is_decommissioned_at_null_endtime(self):
        """Test is_decommissioned_at with a null endtime."""

        t = 1265760000
        new_kwargs = METADATA_DEFAULTS.copy()
        new_kwargs["endtime"] = None
        md = database.SeismicStationMetadata(**new_kwargs)
        assert md.is_decommissioned_at(t) is False
        assert md.is_decommissioned_at(METADATA_TIME) is False


class TestDbMasterView(unittest.TestCase):
    """Test DbMasterView class."""

    def setUp(self):
        """Set up self.dbv for future test cases."""
        self.dbv = database.DbMasterView(dbmaster="/opt/antelope/data/db/demo/demo")

    def tearDown(self):
        """Deinit self.dbv."""
        self.dbv.__del__()  # force it to run regarless of the garbage collector.
        self.dbv = None

    def testBadPath(self):
        """Test opening a non-existant database."""
        with self.assertRaises(datascope.DatascopeError):
            dbv = database.DbMasterView(dbmaster="/path/to/nonexistant/file")
            dbv.get_pointer()

    def testGetPointer(self):
        """Test retrieving a new database pointer."""
        assert self.dbv.get_pointer() is not None

    def testExtraSensors(self):
        """Test basic functionality of get_extra_sensor_metadata()."""
        stas = self.dbv.get_extra_sensor_metadata()
        assert stas is not None
        allstas = [x for x in stas]
        assert len(allstas) == 2  # demodb only has two stations with inframet chans
        print(allstas[0])
        print(allstas[0].extra_channels)
        assert allstas[0].extra_channels == {
            "LDM_EP",
            "BDO_EP",
            "BDF_EP",
            "LDF_EP",
            "LDO_EP",
        }
        assert allstas[0].extra_sensors == {"MEMS", "NCPA", "SETRA"}

    def testExtraSensorsWithEndtimeBeforeFirstSta(self):
        """Test extra sensors with end time before the first inframet station."""
        # 1270684800.000 (098) 2010-04-08  00:00:00.00000 UTC Thursday
        # One day before TPFO got it's MET sensors
        stas = self.dbv.get_extra_sensor_metadata(end_time=1270684800.000)
        assert stas is not None
        allstas = list(stas)
        assert len(allstas) == 0

    def testInframetWithStarttimeAfterTRFD(self):
        """Test inframet with start time after TRFD was removed."""
        # 1483228800.000 (001) 2017-01-01  00:00:00.00000 UTC Sunday
        # One after before TRFD lost it's MET sensors
        stas = self.dbv.get_extra_sensor_metadata(start_time=1483228800.000)
        assert stas is not None
        allstas = list(stas)
        assert len(allstas) == 1

    def testSeismicStationMetadata(self):
        """Test basic functionality of get_seismic_station_metadata()."""
        stas = self.dbv.get_seismic_station_metadata()
        assert stas is not None
        allstas = [x for x in stas]
        print("Seismic allstas has {:d} records.".format(len(allstas)))
        assert len(allstas) == 54  # demodb has 54 stations

    def testSeismicWithEndtimeBeforeFirstSta(self):
        """Test seismic with end time in before the first station."""
        #   347155200.000 (001) 1981-01-01  00:00:00.00000 UTC Thursday
        # oldest station went in on 1982 day 274
        stas = self.dbv.get_seismic_station_metadata(end_time=347155200.000)
        assert stas is not None
        allstas = list(stas)
        print("Seismic allstas has {:d} records.".format(len(allstas)))
        assert len(allstas) == 0

    def testSeismicWithStarttimeAfterTRFD(self):
        """Test seismic with start time after 2016 year-end closures."""
        # 1483228800.000 (001) 2017-01-01  00:00:00.00000 UTC Sunday
        # One after before TRFD lost it's MET sensors
        stas = self.dbv.get_seismic_station_metadata(start_time=1483228800.000)
        assert stas is not None
        allstas = list(stas)
        print("Seismic allstas has {:d} records.".format(len(allstas)))
        assert len(allstas) == 11
