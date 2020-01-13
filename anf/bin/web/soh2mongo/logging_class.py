# Try to make a generic logging setup for ANF
# tools. This function will return an object
# of the logging class. If none available with
# requested name then it will configure one for
# you.

# Import like this...
#   try:
#       from db2mongo.logging_class import getLogger
#   except Exception, e:
#       raise metadataException("Problem loading logging_class. %s(%s)" % (Exception, e))

# Then create a new object like this...
# From main: logging = getLogger()
# logging = getLogger(self.__class__.__name__)

# You can then log strings to console using any of the
# provided methods.
#   -------------------------- allways prints
#   logging.critical(obj)
#   logging.critical('test')
#   logging.error(obj)
#   logging.error('test')
#   logging.warning(obj)
#   logging.warning('test')
#   logging.notify(obj)
#   logging.notify('test')
#   -------------------------- verbose mode or greater
#   logging.info(obj)
#   logging.info('test')
#   -------------------------- debug mode or greater
#   logging.debug(obj)
#   logging.debug('test')


import inspect
import json
import logging
import os
import sys


def getLogger(name="", loglevel=False):

    # Define some name for this instance.
    main = os.path.basename(sys.argv[0])
    inspectmain = os.path.basename(inspect.stack()[1][1])

    # If none provided then use the name of the file
    # with script calling the function.
    if not name:
        name += inspectmain

    # If there is some other function using the
    # getLogger then prepend the name of main script.
    if not main == inspectmain:
        name = "%s.%s" % (main, name)

    logger = logging.getLogger(name)
    logger.propagate = False

    if not len(logger.handlers):
        # We need new logger
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s %(name)s[%(levelname)s]: %(message)s"
        )

        handler.setFormatter(formatter)
        logger.addHandler(handler)

        # Adding new logging level
        logging.addLevelName(35, "NOTIFY")

        if not loglevel:
            logger.setLevel(logging.getLogger(main).getEffectiveLevel())
        else:
            logger.setLevel(logging.getLevelName(loglevel))

        def niceprint(msg):
            try:
                if isinstance(msg, str):
                    raise
                return "\n%s" % json.dumps(msg, indent=4, separators=(",", ": "))
            except:
                return msg

        def newcritical(self, message, *args, **kws):
            self.log(50, niceprint(message), *args, **kws)

        def newerror(self, message, *args, **kws):
            self.log(40, "")
            self.log(40, niceprint(message), *args, **kws)
            self.log(40, "")
            sys.exit("EXIT")

        def newnotify(self, message, *args, **kws):
            self.log(35, niceprint(message), *args, **kws)

        def newwarning(self, message, *args, **kws):
            self.log(30, niceprint(message), *args, **kws)

        def newinfo(self, message, *args, **kws):
            self.log(20, niceprint(message), *args, **kws)

        def newdebug(self, message, *args, **kws):
            self.log(10, niceprint(message), *args, **kws)

        # Not that we want to use the kill but just in case...
        def newkill(self, message, *args, **kws):
            self.log(50, "")
            self.log(50, niceprint(message), *args, **kws)
            self.log(50, "")
            sys.exit("\nExit from logging_class.\n")

        logging.Logger.critical = newcritical
        logging.Logger.error = newerror
        logging.Logger.notify = newnotify
        logging.Logger.notify = newwarning
        logging.Logger.info = newinfo
        logging.Logger.debug = newdebug
        logging.Logger.kill = newkill

    return logger
