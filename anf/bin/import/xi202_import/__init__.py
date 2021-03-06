"""Import XI-202 data from XeosOnline MongoDB."""
from logging import getLogger

from anf.logutil import fullname, getModuleLogger
import antelope.orb as orb
import antelope.stock as stock

from .packet import Packet
from .statefile import stateFile

logger = getModuleLogger(__name__)


class XI202Importer:
    """Import XI-202 data from XeosOnline MongoDB.

    Read documents from a MongoDB Collection and produce xi202/pf/xeos packets
    that we can import into an ORB in Antelope. The last document read will be
    tracked in a state file.
    """

    def __init__(
        self,
        collection,
        orb,
        name="test",
        channel_mapping={},
        orbunits=None,
        q330units=None,
        mongo_select=None,
        mongo_reject=None,
        default_mongo_read=0,
        statefile=False,
        mongo_pull_wait=3,
        pckt_name_type="pf/xi",
        silent_pkt_fail=False,
    ):
        """Initialize the import class."""
        self.name = name

        self.logger = getLogger(fullname(self))

        self.logger.debug("init()")
        # self.dlmon = Dlmon(  stock.yesno(parse_opt) )
        self.cache = {}
        self.orb = False
        self.errors = 0
        self.lastread = 0
        self.timezone = "UTC"
        self.error_cache = {}
        # self.indexing = indexing
        self.timeformat = "%D (%j) %H:%M:%S %z"

        # from object options
        self.orbunits = orbunits
        self.q330units = q330units
        self.channel_mapping = channel_mapping
        self.packet = Packet(
            q330_dlnames=[self.q330units, self.orbunits],
            channel_mapping=self.channel_mapping,
        )
        self.collection = collection
        self.orbname = orb
        self.mongo_select = mongo_select
        self.mongo_reject = mongo_reject
        self.statefile = statefile
        self.state = None
        self.mongo_pull_wait = int(mongo_pull_wait)
        self.pckt_name_type = pckt_name_type
        self.silent_pkt_fail = silent_pkt_fail

        if default_mongo_read == "start":
            self.read_position = 0
        elif default_mongo_read == "oldest":
            self.read_position = 0
        elif default_mongo_read == "newest":
            self.read_position = -1
        elif default_mongo_read == "end":
            self.read_position = -1
        else:
            try:
                self.read_position = int(default_mongo_read)
            except Exception:
                self.logger.error(
                    "Cannot convert default_mongo_read [%s]" % default_mongo_read
                )

        # verify mongodb collection
        if self.collection.count() == 0:
            self.logger.warning("MongoDB collection [%s] is empty" % self.name)
            self.valid = False

        else:

            self.valid = True

            # StateFile
            self.state = stateFile(self.statefile, self.name, self.read_position)
            self.read_position = self.state.last_id()

            self.logger.debug("Last document read: %s" % self.read_position)

            self.logger.debug("Prep internal object")
            self._prep_orb()

    def isvalid(self):
        """Check if instance is valid."""
        return self.valid

    def __str__(self):
        """Return string representation of instance."""
        if self.valid:
            return str(self.name)
        else:
            return "*** INVALID INSTANCE *** %s" % self.name

    def _prep_orb(self):
        """Prepare documents for publishing to orbserver.

        Look into the Document Collection and pull new
        documents out. Convert them to xi202/pf/xeos packets
        and push them into an ORB.
        """

        # Open output ORB and track status
        self.logger.debug("Update ORB cache")

        self.logger.debug(self.orbname)

        if not self.orbname or not isinstance(self.orbname, str):
            raise LookupError("Problems with output orb [%s]" % (self.orbname))

        # Expand the object if needed
        if not self.orb:
            self.logger.debug("orb.Orb(%s)" % (self.orbname))
            self.orb = {}
            self.orb["orb"] = None
            self.orb["status"] = "offline"
            self.orb["last_success"] = 0
            self.orb["last_update"] = 0

        self._connect_to_orb()

    def close_orb(self):
        """Close the orbserver connection."""

        if not self.valid:
            return

        try:
            self.logger.debug("close orb connection %s" % (self.orbname))
            if self.orb["orb"]:
                self.orb["orb"].close()

        except orb.NotConnectedError:
            self.logger.warning("orb(%s) Already closed" % self.orbname)

        except Exception:
            self.logger.exception("Some exception occurred during orb.close.")

    def _test_orb(self):

        self.orb["status"] = self.orb["orb"].ping()

        self.logger.debug("orb.ping() => %s" % (self.orb["status"]))

        if int(self.orb["status"]) > 0:
            return True

        return False

    def _connect_to_orb(self):
        """Update internal state tracking and close/open an orb connection.

        Wrapper of dubious necessity around orb.close and orb.connect().

        Raises:
            antelope.orb.OrbError: if an orb connection can't be made for any reason
        """

        self.logger.debug("start connection to orb: %s" % (self.orbname))

        # If previous state then we close first and reconnect
        if self.orb["status"]:
            self.close_orb()

        # Now open new connection and save values in object
        self.logger.debug("connect to orb(%s)" % self.orbname)
        self.orb["orb"] = orb.Orb(self.orbname, permissions="w")
        self.orb["orb"].connect()
        self.orb["orb"].stashselect(orb.NO_STASH)

        self.logger.debug("ping orb: %s" % (self.orb["orb"]))

        if not self._test_orb():
            raise Exception("Problems connecting to (%s)" % self.orbname)

    def pull_data(self):
        """Get data from the MongoDB instance."""

        if not self.valid:
            self.logger.debug("*** INVALID INSTANCE *** %s" % self.name)
            return False

        if float(self.read_position) < 0.0:
            ignore_history = True
            logSeqNo = 0
            seqNo = 0
        else:
            ignore_history = False

            # ID has 2 parts. Need to split them.
            try:
                temp = str(self.read_position).split(".")
            except Exception:
                temp = [int(self.read_position)]

            if len(temp) == 2:
                logSeqNo = int(temp[0])
                seqNo = int(temp[1])
            else:
                logSeqNo = int(self.read_position)
                seqNo = False

        # Get all documents with id equal or grater than last successful id...
        for post in sorted(
            self.collection.find({"messageLogSeqNo": {"$gte": logSeqNo}}),
            key=lambda x: (x["messageLogSeqNo"], x["seqNo"]),
        ):

            try:
                # In case we bring an older segNo document...
                if logSeqNo == post["messageLogSeqNo"] and seqNo:
                    if seqNo >= post["seqNo"]:
                        self.logger.debug(
                            "Skipping processed packet %s.%s"
                            % (post["messageLogSeqNo"], post["seqNo"])
                        )
                        continue
            except Exception as e:
                self.logger.warning("Invalid document: %s: %s" % (Exception, e))
                continue

            # self.logger.notify( post )
            self.packet.new(
                post,
                name_type=self.pckt_name_type,
                select=self.mongo_select,
                reject=self.mongo_reject,
                silent=self.silent_pkt_fail,
            )

            if not self.packet.valid:
                continue

            # save packet id to state file
            self.state.set(self.packet.id, self.packet.time)

            # track last id
            self.read_position = self.packet.id

            if ignore_history:
                self.logger.info("Skip. Ignoring old packets.")
                continue

            if not self.packet.valid:
                self.logger.warning("*** SKIP - INVALID PACKET ***")
                continue

            # Test connection. Reset if missing
            if not self._test_orb():
                self._connect_to_orb()

            self.logger.debug("Put new packet in orb: %s" % self.packet.pkt)
            pkttype, pktbuf, srcname, time = self.packet.pkt.stuff()
            self.packet.orbid = self.orb["orb"].putx(srcname, self.packet.time, pktbuf)

        self.lastread = stock.now()
