"""Tests for anf.deploymentmap.gmt."""

import unittest

from anf.deploymentmap import gmt


class TestGmtRegionCoordinates(unittest.TestCase):
    """Test GmtRegionCoordinates."""

    def setUp(self):
        """Initialize a test coordinates object."""
        self.coords = gmt.GmtRegionCoordinates(
            minlat=15, maxlat=50, minlon=-119, maxlon=-64, width=16, gridlines=5
        )

    def test_centerlat(self):
        """Test centerlat."""
        self.assertEqual(self.coords.centerlat, 32.5, "incorrect center latitude")

    def test_centerlon(self):
        """Test centerlon."""
        self.assertEqual(self.coords.centerlon, -91.5, "incorrect center longitude")

    def test_get_regionstr(self):
        """Test get_regionstr."""
        self.assertEqual(
            self.coords.get_regionstr(), "-119/15/-64/50r", "incorrect region string"
        )

    def test_get_azeq_center_str(self):
        """Test get_azeq_center_str."""
        self.assertEqual(
            self.coords.get_azeq_center_str(),
            "32/-92/16i",
            "incorrect center string with defaults",
        )

        self.assertEqual(
            self.coords.get_azeq_center_str(4),
            "32/-92/4i",
            "incorrect center string with widthoverride=4",
        )
