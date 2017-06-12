#
#
# Try to make a generic logging setup configuration.
# This function will return an object
# of the logging class. If none available with
# requested name then it will configure one for
# you.

# Import like this...

#       from anf.logging_helper import getLogger

# Then create a new object like this...

#       option 1) logging = getLogger()
#       option 2) logging = getLogger(self.__class__.__name__)
#       option 3) logging = getLogger( 'my_function' )

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


if __name__ == "__main__":
    raise ImportError( "\n\n\tANF Python library. Not to run directly!!!! \n" )


import os, sys
import logging
import inspect


def getLogger(name='', loglevel=False, log_filename=False, file_count=5):

    # Define some name for this instance.
    main = os.path.basename( sys.argv[0] )
    inspectmain = os.path.basename( inspect.stack()[1][1] )

    # If none provided then use the name of the file
    # with script calling the function.
    if not name:
        name = inspectmain

    # If there is some main (parent) function using the
    # getLogger then prepend the name of main script.
    if not main == inspectmain:
        name = '%s.%s' % (main,name)
        return logging.getLogger(name)

    newlogger = logging.getLogger(name)
    newlogger.propagate = False

    if not len(newlogger.handlers):
        # We need new logger

        # Maybe we want to log to a file
        if log_filename:

            handler = logging.handlers.RotatingFileHandler( log_filename,
                                                    backupCount=file_count)

            # Check if log exists and should therefore be rolled
            if os.path.isfile(log_filename): handler.doRollover()

        else:
            handler = logging.StreamHandler()

        formatter = logging.Formatter( '%(asctime)s %(name)s[%(levelname)s]: %(message)s')
        handler.setFormatter(formatter)
        newlogger.addHandler(handler)

        # Adding new logging level
        logging.addLevelName(35, "NOTIFY")

        if not loglevel:
            newlogger.setLevel( logging.getLogger(main).getEffectiveLevel() )
        else:
            newlogger.setLevel( logging.getLevelName( loglevel ) )


        def niceprint(msg):
            try:
                if isinstance(msg, str): raise
                return "\n%s" % json.dumps( msg, indent=4, separators=(',', ': ') )
            except:
                return msg

        def newcritical(self, message, *args, **kws):
            self.log(50, niceprint(message), *args, **kws)

        def newerror(self, message, *args, **kws):
            self.log(40, niceprint(message), *args, **kws)
            sys.exit( 2 )

        def newnotify(self, message, *args, **kws):
            self.log(35, niceprint(message), *args, **kws)

        def newwarning(self, message, *args, **kws):
            self.log(30, niceprint(message), *args, **kws)

        def newinfo(self, message, *args, **kws):
            self.log(20, niceprint(message), *args, **kws)

        def newdebug(self, message, *args, **kws):
            self.log(10, niceprint(message), *args, **kws)

        def newkill(self, message, *args, **kws):
            self.log(50, niceprint(message), *args, **kws)
            sys.exit( 3 )

        logging.Logger.critical = newcritical
        logging.Logger.error = newerror
        logging.Logger.notify = newnotify
        logging.Logger.info = newinfo
        logging.Logger.debug = newdebug
        logging.Logger.kill = newkill


    return newlogger
