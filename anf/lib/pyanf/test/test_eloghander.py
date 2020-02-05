"""Tests for anf.eloghandler."""
import logging
import unittest

import anf.eloghandler


class TestElogHandler(unittest.TestCase):
    """Test ElogHandler."""

    def setUp(self):
        """Set up the root level logger."""
        logging.basicConfig()
        self.rootlogger = logging.getLogger()
        self.rootlogger.setLevel(logging.WARNING)
        self.handler = anf.eloghandler.ElogHandler()
        self.rootlogger.handlers = []
        self.rootlogger.addHandler(self.handler)

    def test_default_loglevel(self):
        """Test logging at the default log level of WARNING."""
        self.rootlogger.debug("debug message DEFAULT should not print")
        self.rootlogger.info("info message DEFAULT should not print")
        self.rootlogger.warning("warning message DEFAULT should print")
        self.rootlogger.error("error message DEFAULT should print")
        self.rootlogger.critical("critical message DEFAULT should print")

    def test_debug_loglevel(self):
        """Test logging at the debug log level."""
        self.rootlogger.setLevel(logging.DEBUG)
        self.rootlogger.debug("debug message DEBUG should print")
        self.rootlogger.info("info message DEBUG should print")
        self.rootlogger.warning("warning message DEBUG should print")
        self.rootlogger.error("error message DEBUG should print")
        self.rootlogger.critical("critical message DEBUG should print")
