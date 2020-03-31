"""The main poc2mongo module."""


from collections import namedtuple
from logging import getLogger
from optparse import OptionParser

from anf.logutil import fullname, getModuleLogger
from antelope import orb, stock
from pymongo import MongoClient
from pymongo.errors import (
    ConfigurationError as pmConfigurationError,
    ServerSelectionTimeoutError,
)

# TODO: use anf.stateFile or whatever it ends up being called.
from .error import Poc2MongoAuthError, Poc2MongoConfigError, Poc2MongoError
from .util import (
    MAX_EXTRACT_ERRORS,
    ConfigurationError,
    OrbConnectError,
    OrbRejectException,
    OrbSelectException,
    Poc,
    TooManyExtractError,
    stateFile,
)

logger = getModuleLogger(__name__)

MongoDbConfig = namedtuple(
    "MongoDbConfig", ["user", "host_and_port", "password", "namespace", "collection"]
)


class Poc2MongoApp:
    """Application instance for poc2mongo."""

    def __init__(self, argv=None):
        """Initialize object, read config."""
        # Read configuration from command-line
        usage = "Usage: %prog [options]"

        parser = OptionParser(usage=usage)
        parser.add_option(
            "-s",
            action="store",
            dest="state",
            help="track orb id on this state file",
            default=False,
        )
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
            default="poc2mongo",
        )

        (self.options, self.args) = parser.parse_args()

        self.options.loglevel = "WARNING"
        if self.options.debug:
            self.options.loglevel = "DEBUG"
        elif self.options.verbose:
            self.options.loglevel = "INFO"

        self.logger = getLogger(fullname(__name__))

        # Get PF file values
        self.logger.info("Read parameters from pf file %s" % self.options.pf)
        self.pf = stock.pfread(self.options.pf)

        # Get MongoDb parameters from PF file
        self.options.mongo = MongoDbConfig(
            user=self.pf.get("mongo_user"),
            host_and_port=self.pf.get("mongo_host"),
            password=self.pf.get("mongo_password"),
            namespace=self.pf.get("mongo_namespace"),
            collection=self.pf.get("mongo_collection"),
        )

        self.options.orbserver = self.pf.get("orbserver")
        self.options.orb_select = self.pf.get("orb_select")
        self.options.orb_reject = self.pf.get("orb_reject")
        self.options.default_orb_read = self.pf.get("default_orb_read")
        self.options.include_pocc2 = self.pf.get("include_pocc2")
        self.options.reap_wait = self.pf.get("reap_wait")
        self.options.reap_timeout = self.pf.get("reap_timeout")
        self.options.timeout_exit = self.pf.get("timeout_exit")

    def run(self):
        """Run the application."""

        self.logger.debug("Mongo settings: %s", self.options.mongo)
        # Configure MongoDb instance
        try:
            self.logger.info("Init MongoClient(%s)", self.options.mongo.host_and_port)
            self.mongo_instance = MongoClient(self.options.mongo.host_and_port)

            self.logger.info(
                "Get namespace %s in mongo_db", self.options.mongo.namespace
            )
            self.mongo_db = self.mongo_instance.get_database(
                self.options.mongo.namespace
            )

            self.logger.info("Authenticate mongo_db")
            self.mongo_db.authenticate(
                self.options.mongo.user, self.options.mongo.password
            )

        except pmConfigurationError as e:
            raise Poc2MongoConfigError(e)
        except ServerSelectionTimeoutError as e:
            raise Poc2MongoAuthError(e)
        except Exception as e:
            raise Poc2MongoError(e)

        # May need to nuke the collection before we start updating it
        # Get this mode by running with the -c flag.
        if self.options.clean:
            self.logger.info(
                "Drop collection %s.%s"
                % (self.options.mongo.namespace, self.options.mongo.collection)
            )
            self.mongo_db.drop_collection(self.options.mongo.collection)
            logger.info(
                "Drop collection %s.%s_errors"
                % (self.options.mongo.namespace, self.options.mongo.collection)
            )
            self.mongo_db.drop_collection("%s_errors" % self.options.mongo.collection)

        self.logger.debug("orbserver => [%s]" % self.options.orbserver)
        self.logger.debug("orb_select => [%s]" % self.options.orb_select)
        self.logger.debug("orb_reject => [%s]" % self.options.orb_reject)
        self.logger.debug("default_orb_read => [%s]" % self.options.default_orb_read)
        self.logger.debug("include_pocc2 => [%s]" % self.options.include_pocc2)
        self.logger.debug("reap_wait => [%s]" % self.options.reap_wait)
        self.logger.debug("reap_timeout => [%s]" % self.options.reap_timeout)
        self.logger.debug("timeout_exit => [%s]" % self.options.timeout_exit)

        instance = poc2mongo(
            self.mongo_db[self.options.mongo.collection],
            self.options.orbserver,
            orb_select=self.options.orb_select,
            orb_reject=self.options.orb_reject,
            default_orb_read=self.options.default_orb_read,
            statefile=self.options.state,
            reap_wait=self.options.reap_wait,
            reap_timeout=self.options.reap_timeout,
            timeout_exit=self.options.timeout_exit,
        )

        self.logger.info("Starting poc2mongo instance.")
        return instance.run_forever()


class poc2mongo:
    """Read an ORB for POC packets and update a MongoDatabase.

    Set the serial of the instrument as the main id and update that entry with
    the latest packet that comes into the orbserver. We can also run with the
    clean option and clean the archive before we start putting data in it.
    There is a position flag to force the reader to jump to a particular part
    of the ORB and the usual statefile to look for a previous value for the
    last packet id read.
    """

    def __init__(
        self,
        collection,
        orb,
        orb_select=None,
        orb_reject=None,
        default_orb_read=0,
        statefile=False,
        reap_wait=3,
        timeout_exit=True,
        reap_timeout=5,
    ):
        """Initialize the poc2mongo reader."""
        self.logging = getLogger(fullname(self))

        self.logging.debug("init()")

        self.poc = Poc()
        self.cache = {}
        self.orb = False
        self.errors = 0
        self.orbname = orb
        self.lastread = 0
        self.timezone = "UTC"
        self.position = False
        self.error_cache = {}
        self.timeout_exit = timeout_exit
        self.reap_wait = int(reap_wait)
        self.statefile = statefile
        self.collection = collection
        self.orb_select = orb_select
        self.orb_reject = orb_reject
        self.reap_timeout = int(reap_timeout)
        self.timeformat = "%D (%j) %H:%M:%S %z"
        self.default_orb_read = default_orb_read

        # StateFile
        self.state = stateFile(self.statefile, self.default_orb_read)
        self.position = self.state.last_packet()
        # self.last_time = self.state.last_time()

        if not self.orb_select:
            self.orb_select = None
        if not self.orb_reject:
            self.orb_reject = None

    def run_forever(self):
        """Track POC packets from orbservers."""

        self.logging.debug("Update ORB cache")

        self.logging.debug(self.orbname)

        if not self.orbname:
            raise ConfigurationError("orbname is missing [%s]" % (self.orbname))

        # Create the orbserver state tracking dict if needed
        if not self.orb:
            self.logging.debug("orb.Orb(%s)" % (self.orbname))
            self.orb = {}
            self.orb["orb"] = None
            self.orb["status"] = "offline"
            self.orb["last_success"] = 0
            self.orb["last_check"] = 0

        self._connect_to_orb()

        while True:
            # Reset the connection if no packets in reap_timeout window
            if (
                self.orb["last_success"]
                and self.reap_timeout
                and ((stock.now() - self.orb["last_success"]) > self.reap_timeout)
            ):
                self.logging.warning("Possible stale ORB connection %s" % self.orbname)
                if stock.yesno(self.timeout_exit):
                    break
                else:
                    self._connect_to_orb()

            if self._extract_data():
                # self.logging.debug( "Success on extract_data(%s)" % (self.orbname) )
                pass
            else:
                self.logging.warning("Problem on extract_data(%s)" % (self.orbname))
                self._connect_to_orb()

        self.orb["orb"].close()

    def _test_orb(self):
        self.logging.debug("test orb connection %s" % (self.orbname))
        try:
            self.orb["status"] = self.orb["orb"].ping()
        except Exception:
            return False
        else:
            return True

    def _connect_to_orb(self):
        self.logging.debug("start connection to orb: %s" % (self.orbname))
        if self.orb["status"]:
            try:
                self.logging.debug("close orb connection %s" % (self.orbname))
                self.orb["orb"].close()
            except Exception:
                self.logging.exception("orb.close(%s) failed" % self.orbname)
                pass

        try:
            self.logging.debug("connect to orb(%s)" % self.orbname)
            self.orb["orb"] = orb.Orb(self.orbname)
            self.orb["orb"].connect()
            self.orb["orb"].stashselect(orb.NO_STASH)
        except Exception as e:
            raise OrbConnectError(self.orbname, e)

        if self.position:
            try:
                self.orb["orb"].position("p%s" % int(self.position))
                self.logging.debug("position orb on pckt: %s" % (self.position))
            except orb.OrbException:
                self.orb["orb"].position(self.default_orb_read)
                self.logging.debug("default_orb_read: %s" % (self.default_orb_read))

        if self.orb_select:
            self.logging.debug("orb.select(%s)" % self.orb_select)
            if not self.orb["orb"].select(self.orb_select):
                raise OrbSelectException(self.orb["orb"], self.orb_select)

        if self.orb_reject:
            self.logging.debug("orb.reject(%s)" % self.orb_reject)
            if not self.orb["orb"].reject(self.orb_reject):
                raise OrbRejectException(self.orb["orb"], self.orb_reject)

        self.logging.debug("ping orb: %s" % (self.orb["orb"]))
        try:
            self.logging.debug("orb position: %s" % (self.orb["orb"].tell()))
        except orb.OrbException:
            self.logging.debug("orb position: NONE")

    def _extract_data(self):
        """Look for all poc packets."""

        self.orb["last_check"] = stock.now()

        if self.errors > MAX_EXTRACT_ERRORS:
            raise TooManyExtractError("10 consecutive errors on orb.reap()")

        try:
            self.poc.new(self.orb["orb"].reap(self.reap_wait))
        except orb.OrbIncompleteException:
            self.logging.debug("OrbIncompleteException orb.reap(%s)" % self.orbname)
            return True
        except Exception as e:
            self.logging.warning(
                "%s Exception in orb.reap(%s) [%s]" % (Exception, self.orbname, e)
            )
            self.errors += 1
            return False
        else:
            # reset error counter
            self.errors = 0
            # save ORB id to state file
            self.state.set(self.poc.id, self.poc.time)

        if self.poc.valid:
            self.logging.info("%s" % self.poc)
            # we print this on the statusFile class too...
            self.logging.debug(
                "orblatency %s" % (stock.strtdelta(stock.now() - self.poc.time))
            )
            self.position = self.poc.id
            self.logging.debug("orbposition %s" % self.position)
            self.orb["last_success"] = stock.now()

            self._update_collection()

        return True

    def _update_collection(self):

        self.logging.info("update_collection()")

        if self.poc.valid:
            self.logging.debug("collection.update(%s)" % self.poc.sn)
            self.collection.update(
                {"sn": self.poc.sn}, {"$set": self.poc.data()}, upsert=True
            )
