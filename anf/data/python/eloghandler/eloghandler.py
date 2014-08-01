import logging
import sys
from antelope import elog

class ElogHandler(logging.Handler):
    """
    A handler class which sends logging records to Antelope's
    elog routines.
    """

    def __init__(self, argv=None):
        """
        Initialize a handler. Calls antelope.elog.init()

        If argv is specified, antelope.elog.init is called with argv.
        """

        logging.Handler.__init__(self)

        elog.init(argv)

    def emit(self, record):
        """
        Emit a record.

        The record is handed off to the various elog routines based on
        the record's priority.

        Although the underlying C library in Antelope has more severity levels,
        the python antelope.elog module only supports debug, notify, and
        complain. Thus, logging.DEBUG maps to elog.debug, logging.INFO maps to
        elog.notify and everything else maps to elog.complain
        """

        msg = self.format(record)

        if record.levelno == logging.DEBUG:
            elog.debug(msg)
        elif record.levelno == logging.INFO:
            elog.notify(msg)
        else: # logging.WARNING, ERROR, CRITICAL
            elog.complain(msg)
