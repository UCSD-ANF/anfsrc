"""Tests for anf.deploymentmap.util."""
import unittest

from anf.deploymentmap.util import read_pf_to_dict
from test_anf_deploymentmap.constants import DEFAULT_PF_NAME


class UtilTestCase(unittest.TestCase):
    """Test cases for the util module."""

    def test_pfread(self):
        """Read pf with extra files."""
        params = read_pf_to_dict(DEFAULT_PF_NAME)
        self.assertIsNotNone(params["stations"]["infrasound"])

    def test_pfread_no_extra(self):
        """Don't read the extra files."""

        params = read_pf_to_dict(DEFAULT_PF_NAME, load_extra=False)
        with self.assertRaises(KeyError):
            params["stations"]["infrasound"]


if __name__ == "__main__":
    unittest.main()
