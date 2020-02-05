# -*- coding: utf-8 -*-
"""Logging utility functions.

anf.logutil contains several classes and functions to handle logging in python
in a somewhat consistent manner.

Usage:

    From a script:
        * use getAppLogger(__name__) to set up output of log messages

    From the top module of a new module tree:
        * use getModuleLogger(__name__) to set up a Null output handler for the
        module and any submodules.

    From a submodule:
        * use getLogger(__name__) to retrieve a logger instance. Same
        funtionality as logging.getLogger

    From a Class:
        * use getLogger(__name__) to get a class-level logger.

    From an object instance of a class:
        * use getLogger(fullname(__name__)) from the __init__ funciton to get
        an object instance level logger (which overrides the class level
        logger.)

Usage Scenario #1: single script with no included modules:

    File myscript.xpy:

        import sys
        from anf.logutil import getAppLogger

        if __name__ == '__main__':
            logger = getAppLogger(__name__, argv=sys.argv)
            logger.notify("Test message")

Usage Scenario #2: application with included module and submodules:

    File structure:
        myapplication.xpy (compiles to myapplication)
        mymodule/
         * __init__.py
         * submodule1.py
         * submodule2/
         ** __init__.py
         ** submodule2a.py

         myapplication.xpy:
             import sys
             from anf.apputil import getAppLogger, getLogger, fullname

             def main(argv):
                 logger = getAppLogger(__name__)
                 logger.notify("hello from %s", __name__)
                 # Prints hello from __main__
                 f = MainFoo()
                 # Prints "Hello from __main__.MainFoo

             class MainFoo():
                 logger = getLogger(fullname(self))
                 logger.print "Hello from %s", fullname(self))
                 # Prints "Hello from myapplication.MainFoo"
                 def __init__(self):
                     self.logger = getModuleLogger(fullname(self))
                     self.logger.notify("Hello from %s", fullname(self)
                     # Prints "Hello from __main__.MainFoo

             if __name__=='__main__':
                 exit (main(sys.argv))

         mymodule/__init__.py:
             import sys
             from anf.logutil import getModuleLogger

             LOGGING = getModuleLogger(__name__)
             # Note: getModuleLogger, because it's the top of a submodule structure.
             # Only needs to be called at the top of a module. No need to call
             # it in mymodule/submodule1.

             LOGGING.notify("Hello from %s", __name__)
             # prints "Hello from mymodule"

         mymodule/submodule1.py
             from anf.logutil import getLogger

             LOGGING = getLogger(__name__)  # NOTE: getLogger, not getModuleLogger
             LOGGING.notify("Hello from %s", __name__)
             # prints "Hello from mymodule/submodule1"

         mymodule/submodule2/__init__.py
             from anf.logutil import getLogger

             LOGGING = getLogger(__name__) # NOTE: getLogger, not getModuleLogger
             LOGGING.notify("Hello from %s", __name)
             # prints "Hello from mymodule/submodule2"

@author Geoff Davis
"""


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

LOG_LEVEL_DEFAULT = LOG_NOTIFY_NAME
"""Default log level for anf.logutil."""


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


def getAppLogger(name=None, level=LOG_LEVEL_DEFAULT, mode="elog", argv=None):
    """Configure application or script level logging.

    By default, this routine sets up Antelope Elog to output log messages from the Python logging module. It can be configured to use the native python log handlers with the `mode` parameter.

    Args:
        name (string or None): the name of the application's logging instance.
        level (string): the name of the lowest logging level that should be output. This also includes the "NOTIFY" level introduced by this module.
        mode ("elog" or "native"): If elog (default), use the Antelope Elog routines. If native, use Python Logging's log handler.
        argv: Applications arguments. If provided, they are used to initialize Elog with elog.init. No-op for getNativeAppLogger.

    Returns:
        logging.Logger: the logger configured by this routine. Suitable for chaining additional commands to, or direct assignment to a variable.
    """

    if mode == "elog":
        return getElogAppLogger(name, level, argv)
    elif mode == "native":
        return getNativeAppLogger(name, level)
    else:
        raise ValueError("The mode provided (%s) is invalid.", mode)


def getElogAppLogger(name=None, level=LOG_LEVEL_DEFAULT, argv=None):
    """Configure application-level logging using Antelope elog routines.

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


def getNativeAppLogger(name, level=LOG_LEVEL_DEFAULT):
    """Configure application or script level logging with native python logging.

    This function, intended to be called from the main function of an
    application or script, will set up a formatter and configure the log level
    of the root logger. It will also return an instance the logger named
    `name`, suitable for later use by the script or application.

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
