# -*- coding: utf-8 -*
"""Logging utility functions."""
import inspect
import json
import logging
import os
import sys

###
# Module Globals
###
LOG_FORMAT = "%(asctime)s %(name)s[%(levelname)s]: %(message)s"
"""A format string suitable for displaying messages from logging."""


def addNotifyLevel():
    """Adding logging level "NOTIFY" at priority 35.

    This level, 35, is right between the default levels of WARNING(30) and
    ERROR(40). It is intended to mimic Antelope elog levels.
    """
    logging.addLevelName(35, "NOTIFY")
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


def newcritical(self, message, *args, **kws):
    """Reformat the logging.critical function with jsonprint."""
    self.log(50, jsonprint(message), *args, **kws)


def newerror(self, message, *args, **kws):
    """Reformat the logging.error function with jsonprint."""
    self.log(40, "")
    self.log(40, jsonprint(message), *args, **kws)
    self.log(40, "")
    sys.exit("EXIT")


def lognotify(self, message, *args, **kws):
    """Implement a plain log handler function for the notify level."""
    self.log(35, message, *args, **kws)


def newnotify(self, message, *args, **kws):
    """Implement the logging.notify function using jsonprint."""
    self.log(35, jsonprint(message), *args, **kws)


def newwarning(self, message, *args, **kws):
    """Reformat the logging.warning function with jsonprint."""
    self.log(30, jsonprint(message), *args, **kws)


def newinfo(self, message, *args, **kws):
    """Reformat the logging.info function with jsonprint."""
    self.log(20, jsonprint(message), *args, **kws)


def newdebug(self, message, *args, **kws):
    """Reformat the logging.debug function with jsonprint."""
    self.log(10, jsonprint(message), *args, **kws)


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
