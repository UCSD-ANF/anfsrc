"""Tests for anf.deploymentmap.gmt."""

import unittest

from anf.deploymentmap import gmt

TEST_REGION_DATA=[
    "  conus,       Contiguous US,    15,     50,     -119,   -64,    usa.grd,         usa.grad",
    "  saltonsea,   Salton Sea,       15,     50,     -119,   -64,    saltonsea.grd,   saltonsea.grad",
    "  deathvalley, Death Valley,     15,     50,     -119,   -64,    deathvalley.grd, deathvalley.grad",
    "  alaska,      Alaska,           51,     71,     -169,   -119,   alaska.grd,      alaska.grad"
]

class TestGmtRegion(unittest.TestCase):
    """Test GmtRegion."""

    def setUp(self):
        """Initialize a test coordinates object."""
        self.regions = gmt.CsvRegionReader(TEST_REGION_DATA)
        self.coords = next(self.regions)

    def test_centerlat(self):
        """Test centerlat."""
        self.assertEqual(self.coords.centerlat, 32.5, "incorrect center latitude")

    def test_centerlon(self):
        """Test centerlon."""
        self.assertEqual(self.coords.centerlon, -91.5, "incorrect center longitude")

    def test_regionstr(self):
        """Test regionstr."""
        self.assertEqual(
            self.coords.regionstr, "-119/15/-64/50r", "incorrect region string"
        )

    def test_azeq_center_str(self):
        """Test get_azeq_center_str."""

        self.assertEqual(
            self.coords.get_azeq_center_str(4),
            "32/-92/4i",
            "incorrect center string with width=4",
        )
