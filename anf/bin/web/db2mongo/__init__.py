"""The db2mongo module."""
import collections
import importlib
from optparse import OptionParser
from time import sleep

import antelope.stock as stock
from pymongo import MongoClient
from six import iteritems

from . import util
from .logging_class import getLogger


class App:
    """The db2mongo application.

    Usage:

        myapp=App(sys.argv)
        app.run()
    """

    _index = {}
    """Tracks mongodb collection indexes."""

    _loadedmodules = {}
    """Tracks db2mongo modules that have been loaded."""

    module_params = None

    def __init__(self, argv=None):
        """Initialize the db2mongo application.

        Does not make any database connections or validate any databases.
        """
        self._init_parse_args(argv)
        self._init_logger()
        self._init_load_pf()

    def _init_parse_args(self, argv):
        """Read configuration options from command-line."""

        parser = OptionParser()
        parser.add_option(
            "-c",
            action="store_true",
            dest="clean",
            help="clean 'drop' collection on start",
            default=False,
        )
        parser.add_option(
            "-v",
            action="store_true",
            dest="verbose",
            help="verbose output",
            default=False,
        )
        parser.add_option(
            "-d", action="store_true", dest="debug", help="debug output", default=False
        )
        parser.add_option(
            "-p",
            "--pf",
            action="store",
            dest="pf",
            type="string",
            help="parameter file path",
            default="db2mongo",
        )

        (self.options, self.args) = parser.parse_args()

        return True

    def _init_logger(self):
        self.loglevel = "WARNING"
        if self.options.debug:
            self.loglevel = "DEBUG"
        elif self.options.verbose:
            self.loglevel = "INFO"

        # Need new object for logging work.
        self.logging = getLogger(loglevel=self.loglevel)

        return True

    def _init_load_pf(self):
        """Get data from parameter file.

        Return:
            True if successful, False otherwise

        """

        self.logging.info("Read parameters from pf file %s" % self.options.pf)
        self.pf = stock.pfread(self.options.pf)

        # Get MongoDb parameters from PF file
        self.mongo_user = self.pf.get("mongo_user")
        self.mongo_host = self.pf.get("mongo_host")
        self.mongo_password = self.pf.get("mongo_password")
        self.mongo_namespace = self.pf.get("mongo_namespace")

        # Verify we have a valid "refresh" value in PF file
        try:
            refresh = int(self.pf["refresh"])
            if not refresh:
                raise KeyError
        except KeyError:
            refresh = 60

        self.refresh = refresh

        self.logging.info("refresh every [%s]secs" % self.refresh)

        # Get list from PF file
        self.module_params = self.pf.get("modules")
        if not isinstance(self.module_params, collections.Mapping):
            raise ValueError("Parameter File modules must be an Arr")

        self.logging.notify("Modules to load: " + ", ".join(self.module_params.keys()))

        return True

    def get_module_params(self, modulename):
        """Retrive parameter file section for a given db2mongo module.

        Note: class must have loaded ParameterFile object successfully.

        Args:
            modulename (string): name of module.

        Returns:
            dict: parameter file data for the given module.

        Raises:
            KeyError: if self.ParameterFile

        """
        params = self.pf[self.module_params[modulename]]
        self.logging.debug("Parameters for module %s:" % (modulename), params)
        if not params:
            raise KeyError("Missing parameters for module %s" % modulename)

        return params

    def load_modules(self):
        """Dynamically load all modules needed by the db2mongo App.

        Assumes that self.module_params is a Collection with a key of the
        modulename and value of the parameter file section to look for options,
        like so:

            {
                "events": "events_params",
                "metadata": "metadata_params
            }

        """
        for modulename in self.module_params.keys():
            self.logging.notify("Loading module %s" % (modulename))
            params = self.get_module_params(modulename)

            # File and class name should be in parameter blob
            filename = "db2mongo.%s" % params["filename"]
            classname = params["class"]
            self.logging.debug("filename:%s     class:%s" % (filename, classname))

            # Import class into namespace
            self.logging.notify("load %s import %s and init()" % (classname, filename))
            self._loadedmodules[modulename] = getattr(
                importlib.import_module(filename), classname
            )()
            self.logging.debug("New loaded object:")
            self.logging.debug(dir(self._loadedmodules[modulename]))

            # Configure new object from values in PF file
            for key, val in iteritems(params):
                # We avoid "index", this is for the MongoDB collection
                if key == "index":
                    self._index[modulename] = val
                    continue
                # Already used class and filename
                if key == "class":
                    continue
                if key == "filename":
                    continue

                # The rest we send to the class
                self.logging.info("setattr(%s,%s,%s)" % (classname, key, val))
                setattr(self._loadedmodules[modulename], key, val)

            # We want to validate the configuration provided to
            # the new object.
            if self._loadedmodules[modulename].validate():
                self.logging.info("Module %s is ready." % modulename)
            else:
                raise util.ModuleLoadError(
                    "Module %s failed to load properly." % modulename
                )

        self.logging.notify("ALL MODULES READY!")

    def load_mongodb(self):
        """Connect to mongodb and validate that required collections exist."""

        self.logging.debug("Init MongoClient(%s)" % self.mongo_host)
        self.mongo_instance = MongoClient(self.mongo_host)

        self.logging.info("Get namespace %s in mongo_db" % self.mongo_namespace)
        self.mongo_db = self.mongo_instance.get_database(self.mongo_namespace)

        self.logging.info("Authenticate mongo_db")
        self.mongo_db.authenticate(self.mongo_user, self.mongo_password)

        # May need to nuke the collection before we start updating it
        # Get this mode by running with the -c flag.
        if self.options.clean:
            for modulename in self._loadedmodules.keys():
                self.logging.info(
                    "Drop collection %s.%s" % (self.mongo_namespace, modulename)
                )
                self.mongo_db.drop_collection(modulename)
                self.logging.info(
                    "Drop collection %s.%s_errors" % (self.mongo_namespace, modulename)
                )
                self.mongo_db.drop_collection("%s_errors" % modulename)
        pass

    def update_module(self, modulename):
        """Update mongodb data for a given module.

        Args:
            modulename (string): the name of the module to update.

        """
        self.logging.debug("%s.need_update()" % modulename)

        # Verify if there is new data
        if self._loadedmodules[modulename].need_update():

            try:
                useindex = self._index[modulename]
            except KeyError:
                useindex = None

            # Update the internal cache of the object
            self.logging.debug("%s.refresh()" % modulename)
            self._loadedmodules[modulename].update()

            # Dump the cached data into local variables
            self.logging.debug("%s.data()" % modulename)
            data, errors = self._loadedmodules[modulename].data()

            # Send the data to MongoDB
            util.update_collection(self.mongo_db, modulename, data, useindex)
            util.update_collection(self.mongo_db, "%s_error" % modulename, errors)

    def run_forever(self):
        """Retrieve data from datascope and place it in mongodb."""
        while True:

            # for each module loaded...
            for modulename in self._loadedmodules.keys():
                self.update_module(modulename)

            # Pause this loop
            self.logging.debug("Pause for [%s] seconds" % self.refresh)
            sleep(self.refresh)


def main(argv=None):
    """Run db2mongo.

    Args:
        argv: sys.argv formatted command-line arguments

    Returns:
        int: 0 if successful, -1 if failure
    """

    myapp = App(argv)

    try:
        myapp.load_modules()
        myapp.load_mongodb()
        myapp.run_forever()

    except Exception as e:
        myapp.logging.exception(e)
        return -1

    return 0
