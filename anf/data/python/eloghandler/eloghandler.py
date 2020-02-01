"""Antelope Log Handler for Python."""
import ctypes
import ctypes.util
import logging
import sys

from antelope import elog


class ElogHandler(logging.Handler):
    """A log handler class which uses Antelope's elog routines."""

    elog_initialized = False
    """Tracks whether elog.init() has been called yet.

    We'd rather not call elog.init() more than once. Unclear what the effects
    are if it is called more than once.
    """

    def __init__(self, argv=sys.argv):
        """Initialize the ElogHandler handler.

        Calls antelope.elog.init() to set up elog.

        If argv is specified, antelope.elog.init is called with argv.
        """
        logging.Handler.__init__(self)

        if not self.__class__.elog_initialized:
            elog.init(argv)
            self.__class__.elog_intialized = True

        self.libstock = ctypes.cdll.LoadLibrary(ctypes.util.find_library("stock"))

    def _elog_alert(self, msg):
        """Ctypes wrapper for elog_alert() which isn't in elog."""
        c_msg = ctypes.c_char_p(msg)
        r = self.libstock.elog_alert(0, c_msg)
        return r

    def emit(self, record):
        """Emit a log record.

        The record is handed off to the various elog routines based on
        the record's priority.

        Although the underlying C library in Antelope has more severity levels,
        only debug, notify, alert, and complain work without terminating the
        python script. This breaks the normal behavior of the python logging
        module.

        Thus, logging.DEBUG maps to elog.debug, logging.INFO maps to
        elog.notify, logging.WARNING maps to elog_alert() via ctypes,
        and everything else (ERROR, CRITICAL, NOLEVELSET) maps to elog.complain
        """
        msg = self.format(record)

        if record.levelno == logging.DEBUG:
            elog.debug(msg)
        elif record.levelno == logging.INFO:
            elog.notify(msg)
        elif record.levelno == logging.WARNING:
            self._elog_alert(msg.encode())
        else:  # logging.ERROR, logging.CRITICAL
            elog.complain(msg)
