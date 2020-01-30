# -*- coding: utf-8 -*
"""Logging utility functions.

By default, this module will add a new logging level called notify to mimic Antelope elog, using `addNotifyLevel`.
"""
import inspect
import json
import logging
import os
import sys

from deprecation import deprecated

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
    return logger


def getAppLogger(name, level="WARNING"):
    """Set up logging for an application or script.

    This function, intended to be called from the main function of an application or script, will set up a formatter and configure the log level of the root logger. It will also return an instance the logger named `name`, suitable for later use by the script or application.

    Args:
        name (string): the logger name to use.
        level (string or int): Python logging level as either a string or a number.

    Usage:
        logger = getlogger.getAppLogger(__name__, level=LEVEL)
    """
    logging.basicConfig(format=LOG_FORMAT, level=level)
    logger = logging.getLogger(name)
    logger.info("Log level set to: " + level)
    return logger


@deprecated
def getLogger(name="", loglevel=False):
    """Retrieve a logging.logger instance in an ANF-style.

    This function will return an object of the logging class. If none available
    with requested name then it will configure one for you.

    NOTE: this module is very opinionated, and expects to be run from within an
    Antelope-style script (top-level foo.xpy) with any utility functions or classes
    in a module named foo.

    If you try to move your log intialization function out of the foo.xpy, bad
    things happen. It's best to just call logging.basicConfig

    NOTE: the getLogger routine monkey patches the `logger` module, rather than
    just setting a format string and subclassing logging.Formatter. It's brittle,
    and probably will break at some point.

    Usage:

        Import like this...

            from anf.logutil import getLogger

        Then create a new object like this from main:

            mylogger = getLogger()

            mylogger = getLogger(self.__class__.__name__)

         You can then log strings to console using any of the
         provided methods.

           -------------------------- allways prints
           mylogger.critical(obj)
           mylogger.critical('test')
           mylogger.error(obj)
           mylogger.error('test')
           mylogger.warning(obj)
           mylogger.warning('test')
           mylogger.notify(obj)
           mylogger.notify('test')
           -------------------------- verbose mode or greater
           mylogger.info(obj)
           mylogger.info('test')
           -------------------------- debug mode or greater
           mylogger.debug(obj)
           mylogger.debug('test')


    Caveats:
        Forces propagation of log messages to be disabled.

        Dangerously monkey patches the logging module for dubious reasons.

        NOT RECOMMENDED FOR NEW SCRIPTS.
    """

    # Define some name for this instance.
    main = os.path.basename(sys.argv[0])
    inspectmain = os.path.basename(inspect.stack()[1][1])

    # If none provided then use the name of the file
    # with script calling the function.
    if not name:
        name += inspectmain

    """If there is some other function using the getLogger then prepend the
    name of main script. NOTE: this breaks horribly if you are using this
    function anywhere else than a legacy ANF style program with the main
    function in foo.xpy."""
    if not main == inspectmain:
        name = "%s.%s" % (main, name)

    logger = logging.getLogger(name)
    logger.propagate = False

    if not len(logger.handlers):
        # We need new logger
        handler = logging.StreamHandler()
        formatter = logging.Formatter(LOG_FORMAT)

        handler.setFormatter(formatter)
        logger.addHandler(handler)

        addNotifyLevel()

        """Originally, this function tried to determin the log level based on
        the paraent level, even though logging has a mechanism to determine the
        log level based on the parent already. That functionality has been
        disabled."""
        if loglevel:
            logger.setLevel(logging.getLevelName(loglevel))

        """Monkey patch the logging module with new format strings.

        TODO: this should be done by setting a new Formatter on the logging
        instance, NOT by monkey patching."""
        logging.Logger.critical = newcritical
        logging.Logger.error = newerror
        logging.Logger.notify = newnotify
        logging.Logger.warning = newwarning
        logging.Logger.info = newinfo
        logging.Logger.debug = newdebug
        logging.Logger.kill = newkill

    return logger


###
# Init module
###
addNotifyLevel()
"""On module import, add a new logging level called NOTIFY at priorty 35."""
