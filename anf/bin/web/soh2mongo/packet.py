"""Soh2Mongo packet module."""
from anf.getlogger import getLogger
from antelope import Pkt, stock


class Packet:
    """Represent a state-of-heath (SOH) Packet."""

    def __init__(self):
        """Set up Packet."""
        self._clean()
        self.logging = getLogger("Packet")

    def _clean(self):
        """Clean up object state for reuse."""
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
            self.logging.info(
                "Bad Packet: %s %s %s" % (rawpkt[0], rawpkt[1], rawpkt[2])
            )
            return

        self._clean()

        self.rawpkt = rawpkt

        self.logging.debug(rawpkt)

        self.id = rawpkt[0]
        self.time = float(rawpkt[2])
        self.strtime = stock.epoch2str(self.time, "%D %H:%M:%S %Z").strip()

        # Try to extract information from packet
        pkt = Pkt.Packet(rawpkt[1], rawpkt[2], rawpkt[3])

        self.srcname = pkt.srcname if pkt.srcname else rawpkt[1]

        self.logging.info("%s %s %s" % (self.id, self.time, self.strtime))
        # self.logging.debug( pkt.pf )

        if "dls" in pkt.pf:
            self.dls = pkt.pf["dls"]

            if "imei" in pkt.pf:
                self.logging.info("Found imei: %s" % (pkt.pf["imei"]))
                self.imei = pkt.pf["imei"]
            if "q330" in pkt.pf:
                self.logging.info("Found q330: %s" % (pkt.pf["q330"]))
                self.q330 = pkt.pf["q330"]

            self.valid = True
            self.__str__()

        else:
            self.dls = {}
            self.valid = False

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
