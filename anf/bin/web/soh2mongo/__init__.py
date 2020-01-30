"""The soh2mongo application module."""

from logging import getLogger
from optparse import OptionParser

from anf.logutil import fullname, getAppLogger, getModuleLogger
import antelope.stock as stock
import pymongo

from .soh import SOH_mongo
from .util import MongoConfigError, MongoConnectionTimeout

logger = getModuleLogger(__name__)
logger.critical("Test")


class App:
    """Generate an application for soh2mongo."""

    options = None
    """Command line options."""
    args = None
    """Command line arguments, if any."""
    loglevel = "WARNING"
    """Verbosity of log output."""
    logging = None
    """A logger instance."""
    mongo_db = None
    """MongoDB connection for this App."""

    def __init__(self, argv):
        """Initialize the soh2mongo App."""
        self._init_parse_options()
        self._init_logging()
        self._init_pf()

    def _init_parse_options(self):
        """Read configuration from command-line."""
        parser = OptionParser()
        parser.add_option(
            "-s",
            action="store",
            dest="state",
            help="track orb id in this state file",
            default=None,
        )
        parser.add_option(
            "-c",
            action="store_true",
            dest="clean",
            help="run 'drop' collection on start",
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
            dest="pfname",
            type="string",
            help="parameter file name",
            default="soh2mongo",
        )

        (self.options, self.args) = parser.parse_args()

    def _init_logging(self):
        """Initialize the logging instance."""
        if self.options.debug:
            loglevel = "DEBUG"
        elif self.options.verbose:
            loglevel = "INFO"
        else:
            loglevel = "WARNING"

        self.loglevel = loglevel

        getAppLogger(__name__, loglevel)
        self.logger = getLogger(fullname(self))
        self.logger.debug("Hi my name is " + __name__)

    def _init_pf(self):
        """Load values from the parameter file."""

        self.logger.info("Read parameters from pf file %s" % self.options.pfname)
        self.pf = stock.pfread(self.options.pfname)
        # Get MongoDb parameters from PF file

        MONGO_PF_KEYS = ["user", "host", "password", "collection", "namespace"]
        ORB_PF_KEYS = [
            "orbserver",
            "orb_select",
            "orb_reject",
            "default_orb_read",
            "reap_wait",
            "reap_timeout",
            "timeout_exit",
            "parse_opt",
            "indexing",
        ]

        SENSITIVE_FIELD_NAMES = ["password"]

        for k in ("mongo_" + x for x in MONGO_PF_KEYS):
            v = self.pf.get(k)
            sens = ("mongo_" + x for x in SENSITIVE_FIELD_NAMES)
            if k in sens and v is not None:
                v = "**REDACTED**"
            self.logger.debug("%s => [%s]" % (k, v))

        for k in ORB_PF_KEYS:
            v = self.pf.get(k)
            self.logger.debug("%s => [%s]" % (k, v))

    def run(self):
        """Run the soh2mongo application."""
        self._connect_to_mongo()

        # Run main process now
        try:
            result = SOH_mongo(
                self.mongo_db[self.pf.get("mongo_collection")],
                self.pf.get("orbserver"),
                orb_select=self.pf.get("orb_select"),
                orb_reject=self.pf.get("orb_reject"),
                default_orb_read=self.pf.get("default_orb_read"),
                statefile=self.options.state,
                reap_wait=self.pf.get("reap_wait"),
                reap_timeout=self.pf.get("reap_timeout"),
                timeout_exit=self.pf.get("timeout_exit"),
                parse_opt=self.pf.get("parse_opt"),
                indexing=self.pf.get("indexing"),
            ).start_daemon()
        except Exception:
            self.logger.exception("exit daemon")
            return -1

        return result

    def _connect_to_mongo(self):
        """Connect to mongo, and optionally clean old collection."""

        hostname = self.pf.get("mongo_host")
        namespace = self.pf.get("mongo_namespace")
        user = self.pf.get("mongo_user")
        password = self.pf.get("mongo_password")
        namespace = self.pf.get("mongo_namespace")
        collection = self.pf.get("mongo_collection")

        try:
            self.logger.info("Init MongoClient(%s)" % hostname)
            mongo_instance = pymongo.MongoClient(hostname)

            self.logger.info("Get namespace %s in mongodb" % namespace)
            self.mongo_db = mongo_instance.get_database(namespace)

            self.logger.info("Authenticate mongo_db")
            self.mongo_db.authenticate(user, password)

        except pymongo.errors.ConfigurationError as e:
            self.logger.exception("Problem connecting to MongoDB.")
            raise MongoConfigError(e)
        except pymongo.errors.ServerSelectionTimeoutError as e:
            self.logger.exception("MongoDB connection timeout.")
            raise MongoConnectionTimeout(e)

        # May need to nuke the collection before we start updating it
        # Get this mode by running with the -c flag.
        if self.options.clean:
            self.logger.info("Drop collection %s.%s" % (namespace, collection))
            self.mongo_db.drop_collection(collection)
            self.logger.info("Drop collection %s.%s_errors" % (namespace, collection))
            self.mongo_db.drop_collection("%s_errors" % collection)


def main(argv=None):
    """Run soh2mongo."""
    myapp = App(argv)
    exit(myapp.run())
