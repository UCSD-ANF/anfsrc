import logging
import sys
from antelope import elog

class ElogHandler(logging.Handler):
    """
    A handler class which sends logging records to Antelope's
    elog routines.
    """

    def __init__(self, argv=sys.argv):
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
        """

        msg = self.format(record)

        if record.levelno == logging.DEBUG:
            elog.debug(msg)
        elif record.levelno == logging.INFO:
            elog.notify(msg)
        elif record.levelno == logging.WARNING:
            elog.alert(msg)
        elif record.levelno == logging.ERROR:
            elog.warning(msg)
        else: # logging.CRITICAL and others
            elog.complain(msg)
