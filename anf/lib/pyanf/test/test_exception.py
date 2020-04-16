"""Tests for anf.error."""
import unittest

from anf.error import AnfError, AnfLibraryLoadError

class TestError(unittest.TestCase):
    """Test anf.error"""

    def test_AnfError(self):
        """Test AnfError exception creation."""
        with self.assertRaises(AnfError):
            raise AnfError("lol")

    def test_AnfLibraryLoadError(self):
        """Test AnfLibraryLoadError exception creation."""
        with self.assertRaises(AnfLibraryLoadError):
            raise AnfLibraryLoadError("can't do something")

