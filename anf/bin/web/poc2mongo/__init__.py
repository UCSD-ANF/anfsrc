"""The main poc2mongo module."""


from anf.getlogger import getLogger
from antelope import orb, stock

# TODO: use anf.stateFile or whatever it ends up being called.
from .util import (
    ConfigurationError,
    OrbConnectError,
    OrbRejectException,
    OrbSelectException,
    Poc,
    TooManyExtractError,
    stateFile,
)

MAX_EXTRACT_ERRORS = 10


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
        self.logging = getLogger("poc_class")

        self.logging.debug("Pocs.init()")

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

    def get_pocs(self):
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
