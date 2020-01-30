"""Soh2Mongo packet module."""
from logging import getLogger
import warnings

from anf.logutil import fullname
from antelope import Pkt, stock

logger = getLogger(__name__)


class Packet:
    """Represent a state-of-heath (SOH) Packet."""

    def __init__(self):
        """Set up Packet."""
        self.logger = getLogger(fullname(self))
        self._clean()

    def _clean(self):
        """Clean up object state for reuse."""
        self.logger.debug("Cleaning state.")
        self.id = False
        self.time = False
        self.strtime = False
        self.valid = False
        self.srcname = "-"
        self.sn = False
        self.q330 = False
        self.imei = False
        self.dls = False
        self.rawpkt = {}

    def new(self, rawpkt):
        """Create a new Packet object.

        This works a little differently than most python objects because the
        underlying Antelope C code is leaky. The recommended way to manipulate
        packets is to create a packet buffer in memory and continually
        write/rewrite to that, rather than reallocate new memory from the heap.

        Caveats:
            This whole class is not at all Pythonic, and really a gigantic hack.
        """

        if not rawpkt[0] or int(float(rawpkt[0])) < 1:
            self.logger.info("Bad Packet: %s %s %s" % (rawpkt[0], rawpkt[1], rawpkt[2]))
            return

        self._clean()

        self.rawpkt = rawpkt

        self.logger.debug(rawpkt)

        self.id = rawpkt[0]
        self.time = float(rawpkt[2])
        self.strtime = stock.epoch2str(self.time, "%D %H:%M:%S %Z").strip()

        # Try to extract information from packet
        pkt = Pkt.Packet(rawpkt[1], rawpkt[2], rawpkt[3])

        self.srcname = pkt.srcname if pkt.srcname else rawpkt[1]

        self.logger.info("%s %s %s" % (self.id, self.time, self.strtime))
        # self.logger.debug( pkt.pf )

        # Antelope 5.7 stock.ParameterFile.__getitem__ doesn't like the "foo in
        # bar" format.
        # Just try retrieving the value and catch whatever exception we get.
        # Antelope throws warnings if the key isn't found. We don't care.
        # https://stackoverflow.com/questions/14463277/how-to-disable-python-warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                self.dls = pkt.pf["dls"]
                self.valid = True
            except (KeyError, TypeError):
                self.dls = {}
                self.valid = False

            if self.valid:
                try:
                    self.imei = pkt.pf["imei"]
                    self.logger.info("Found imei: %s" % (pkt.pf["imei"]))
                except KeyError:
                    pass

                try:
                    self.q330 = pkt.pf["q330"]
                    self.logger.info("Found q330: %s" % (pkt.pf["q330"]))
                except KeyError:
                    pass

    def __str__(self):
        """Return string representation of an orb packet."""
        if self.valid:
            return "(%s) => [time:%s] %s " % (
                self.srcname,
                self.strtime,
                str(self.dls.keys()),
            )
        else:
            return "(**invalid**) => [pkid:%s pktsrc:%s pktime:%s]" % (
                self.rawpkt[0],
                self.rawpkt[1],
                self.rawpkt[2],
            )

    def __getitem__(self, name):
        """Implement getitem functionality."""
        if self.valid:
            return self.dls[name]
        else:
            return False

    def __iter__(self):
        """Implement iterator functionality."""
        if self.valid:
            return iter(self.dls.keys())
        else:
            return iter()

    def data(self):
        """Retrieve the salient details about a packet as a dict."""
        if self.valid:

            return {
                "pcktid": self.id,
                "time": int(self.time),
                "strtime": self.strtime,
                "srcname": "%s" % self.srcname,
                "dls": self.dls,
            }
        else:
            return {}
