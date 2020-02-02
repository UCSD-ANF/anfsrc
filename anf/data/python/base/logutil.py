# -*- coding: utf-8 -*
"""Logging utility functions."""
import inspect
import json
import logging
import os
import sys

from anf.eloghandler import ElogHandler

###
# Module Globals
###
LOG_FORMAT = "%(asctime)s %(name)s[%(levelname)s]: %(message)s"
"""Log format used for getAppLogger - mimics Antelope's elog(3) default
format."""

LOG_FORMAT_ELOG = "%(name)s: %(message)s"
"""Log format used for getElogLogger - no need for timestamps or levels since
elog(3) takes care of that."""

LOG_NOTIFY_NAME = "NOTIFY"
LOG_NOTIFY_LEVEL = 25  # Higher than logging.INFO, but lower than logging.WARNING
"""A format string suitable for displaying messages from logging."""


def addNotifyLevel():
    """Adding logging level "NOTIFY" at priority LOG_NOTIFY_LEVEL.

    This function operates on the root logger by default, and affects all new
    logging.Logger objects that are created.
    This level, 25, is right between the default levels of INFO(30) and
    WARNING(40). It is intended to mimic Antelope elog levels.
    """
    logging.addLevelName(LOG_NOTIFY_LEVEL, LOG_NOTIFY_NAME)
    logging.Logger.notify = lognotify


###
# Utility function definitions.
###


def fullname(o):
    """Get the full name of a class or module.

    Grabbed from https://stackoverflow.com/questions/2020014/get-fully-qualified-class-name-of-an-object-in-python
    """
    module = o.__class__.__module__
    if module is None or module == str.__class__.__module__:
        return o.__class__.__name__
    return module + "." + o.__class__.__name__


def jsonprint(msg):
    """Attempt to decode the msg as json, otherwise send it on unchanged.

    Args:
        msg (string): message to format

    """
    try:
        if isinstance(msg, str):
            raise
        return "\n%s" % json.dumps(msg, indent=4, separators=(",", ": "))
    except Exception:
        return msg


def lognotify(self, message, *args, **kws):
    """Implement a plain log handler function for the notify level."""
    self.log(LOG_NOTIFY_LEVEL, message, *args, **kws)


# Not that we want to use the kill but just in case...
def newkill(self, message, *args, **kws):
    """Reformat the logging.kill function with jsonprint."""
    self.log(50, "")
    self.log(50, jsonprint(message), *args, **kws)
    self.log(50, "")
    sys.exit("\nExit from logging_class.\n")


def getModuleLogger(name):
    """Set up a module level logger.

    Configure the logger for a module. Intended to be called from the module's `__init__.py`.

    This function will set up a null output formatter, per the recommendations of the Python logging tutorial at: http://docs.python.org/3/howto/logging.html. To whit:
        It is strongly advised that you do not add any handlers other than
        NullHandler to your library's loggers.
    """
    logger = logging.getLogger(name)
    logger.addHandler(logging.NullHandler())
    addNotifyLevel()
    return logger


def getElogLogger(name=None, level="WARNING", argv=None):
    """Configure logging using Antelope elog routines.

    Stands up a basic logging configuration with the root log handler set to an
    instance of anf.eloghandler.ElogHandler.

    Note that this does not make use of the LOG_FORMAT constant defined in this
    module.
    """
    handlers = [ElogHandler(argv)]
    addNotifyLevel()
    logging.basicConfig(level=level, handlers=handlers, format=LOG_FORMAT_ELOG)
    logger = logging.getLogger(name)
    logger.info("Log level set to: " + level)
    return logger


def getAppLogger(name, level="WARNING"):
    """Configure logging for an application or script.

    This function, intended to be called from the main function of an application or script, will set up a formatter and configure the log level of the root logger. It will also return an instance the logger named `name`, suitable for later use by the script or application.

    Args:
        name (string): the logger name to use.
        level (string or int): Python logging level as either a string or a number.

    Usage:
        logger = getlogger.getAppLogger(__name__, level=LEVEL)
    """
    logging.basicConfig(format=LOG_FORMAT, level=level)
    logger = logging.getLogger(name)
    addNotifyLevel()
    logger.info("Log level set to: " + level)
    return logger


def getLogger(*args, **kwargs):
    """Retrieve a logging.logger instance in an ANF-style."""

    # Define some name for this instance.
    # main = os.path.basename(sys.argv[0])
    inspectmain = os.path.basename(inspect.stack()[1][1])

    try:
        name = args[0]
    except KeyError:
        name = args.name

    # If none provided then use the name of the file
    # with script calling the function.
    if not name:
        kwargs.name = inspectmain

    logger = logging.getLogger(*args, **kwargs)

    addNotifyLevel()
    return logger


###
# Automatic functions
###
addNotifyLevel()
"""Automatically add notify level to logging.Logger class."""
