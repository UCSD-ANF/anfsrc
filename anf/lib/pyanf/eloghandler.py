# -*- coding: utf-8 -*-
"""Antelope Log Handler for Python."""
import ctypes
import ctypes.util
import logging
import os

from antelope import elog


class ElogHandler(logging.Handler):
    """A log handler class which uses Antelope's elog routines."""

    elog_initialized = False
    """Tracks whether elog.init() has been called yet.

    We'd rather not call elog.init() more than once. Unclear what the effects
    are if it is called more than once.
    """

    def __init__(self, argv=None):
        """Initialize the ElogHandler handler.

        Calls antelope.elog.init() to set up elog.

        If argv is specified, antelope.elog.init is called with argv.
        """
        logging.Handler.__init__(self)

        if not self.__class__.elog_initialized:
            elog.init(argv)  # elog.init is fine with argv being None
            self.__class__.elog_intialized = True

        libstockpath = ctypes.util.find_library(
            os.environ["ANTELOPE"] + "/lib/libstock"
        )
        if libstockpath is None:
            raise FileNotFoundError("Can't locate Antelope libstock")
        self.libstock = ctypes.cdll.LoadLibrary(libstockpath)

    def _elog_alert(self, msg):
        """Ctypes wrapper for elog_alert() which isn't in elog."""
        return self.libstock.elog_alert(0, msg)

    def emit(self, record):
        """Emit a log record.

        The record is handed off to the various elog routines based on
        the record's priority.

        Although the underlying C library in Antelope has more severity levels,
        only debug, notify, alert, and complain work without terminating the
        python script. This breaks the normal behavior of the python logging
        module.

        Thus, in order to keep the program from exiting unexpectedly, we don't
        map to elog.die().

        The default Python `logging levels
        <https://docs.python.org/3/library/logging.html#levels>`
        default Python levels map to the following numeric levels
            ============  =============  ==============
            Python Level  Numeric Value  Antelope Level
            ============  =============  ==============
            CRITICAL      50             complain
            ERROR         40             complain
            WARNING       30             alert
            NOTIFY [1]_   25             notify
            INFO          20             notify
            DEBUG         10             debug
            NOTSET        0              complain


        [1] Defined in anf.logutil. Can be added by running addNotifyLevel()
            Note that if custom `logging` levels are set that fall between two
            default levels, the level is effectively "rounded down" to the
            closest default `logging` level. So for example, the
            `anf.logutil.logging.NOTIFY` level is defined at a numeric value of
            25. This would map to the `elog.NOTIFY` level, along with the
            `logging.INFO` level.


        """
        msg = self.format(record)

        # logging module levels are numeric, with NOTSET being the lowest.
        if record.levelno == logging.NOTSET:
            elog.complain(msg)
        if record.levelno < logging.INFO:
            elog.debug(msg)
        elif record.levelno < logging.WARNING:
            elog.notify(msg)
        elif record.levelno < logging.ERROR:
            self._elog_alert(msg.encode())
        else:  # logging.ERROR, logging.CRITICAL, everything else.
            elog.complain(msg)
