"""Class representing Q330 serial numbers in an orb.

How to use...

q330units = ORBserials( [:orbs] )

print  q330units( '0100000A27B19B6A' )
>> TA_O53A

print  q330units.info( '0100000A27B19B6A' )
>> {'snet': 'TA', 'sta': 'O53A', 'dlname': 'TA_O53A'}

print q330units( '00000' )
>> False

print q330units( None )
>> False
"""

import collections
from logging import getLogger

from anf.logutil import fullname
from anf.orbpfparser import orbpfparse
from antelope import orb, stock
from six import string_types

DEFAULT_ORB_SELECT = ".*"
DEFAULT_ORB_REJECT = ".*/log"


class ORBserials:
    """Class representing Q330 serial numbers."""

    def __init__(
        self, orblist=[], orbselect=DEFAULT_ORB_SELECT, orbreject=DEFAULT_ORB_REJECT
    ):
        """Initialize the ORBSerials class."""

        self.logger = getLogger(fullname(self))

        self.update_frequency = 3600
        self.last_update = 0

        self.orb_select = orbselect
        self.orb_reject = orbreject
        self.serials = {}
        self.orblist = []
        self.add(orblist)
        self.update()

    def update(self):
        """Update the ORBSerials collection."""
        self.logger.info("Update orb serials")

        if isinstance(self.orblist, collections.Iterable):
            for orbname in self.orblist:
                self._get_orb_data(orbname)

            self.last_update = int(stock.now())

        else:
            self.logger.error("ORBLIST not iterable: " + str(self.orblist))

    def add(self, new_orbs):
        """Add a new orb to the configuration."""

        self.logger.debug("add to orb configuration: " + str(new_orbs))

        if not new_orbs:
            return

        if isinstance(new_orbs, collections.Iterable):
            orbs = new_orbs
        elif isinstance(new_orbs, string_types):
            orbs = [new_orbs]
        else:
            self.logger.error(
                "Need ORB to be string or iterable collection [%s]" % new_orbs
            )

        self.orblist.extend(orbs)

    def _parse_pf(self, line):
        """Read the parameter file."""

        parts = line.split()
        new_serial = parts[3]

        if (
            new_serial in self.serials
            and self.serials[new_serial]["dlname"] == parts[0]
        ):
            self.logger.debug(
                "New entry for %s: %s => %s"
                % (new_serial, self.serials[new_serial]["dlname"], parts[0])
            )
        elif new_serial in self.serials:
            self.logger.warning(
                "Updating value for %s: %s => %s"
                % (new_serial, self.serials[new_serial]["dlname"], parts[0])
            )
        else:
            self.logger.info("New serial %s: %s " % (parts[0], new_serial))

        self.serials[new_serial] = {
            "dlname": parts[0],
            "sta": parts[2],
            "snet": parts[1],
        }

    def _decode_dataloggers_from_pktbuf(self, srcname, pktbuf):
        """Decode q3302orb dataloggers data from an orb packet.

        Args:
            srcname (string): Antelope orb sourcename
            pktbuf (bytes): Contents of an orb packet as read by orb.getstash

        Returns:
            bool: True for success, False for otherwise.

        """

        dataloggers = []
        """dataloggers extracted from pf packet"""

        try:
            pf = orbpfparse(pktbuf)

            try:
                dataloggers = pf["q3302orb.pf"]["dataloggers"]
                self.logger.debug(dataloggers)

            except KeyError:
                self.logger.warning("No information in stash packet for " + srcname)
                return False

            if len(dataloggers) == 0:
                self.logger.debug("dataloggers missing from Pkt %s" % srcname)
                return False

            for dl in dataloggers:
                self.logger.debug("Parse: [%s]" % dl)
                self._parse_pf(dl)

        except UnicodeDecodeError:
            self.logger.exception("Could not decode packet as ASCII for " + srcname)
            return False

        except stock.PfCompileError:
            self.logger.exception("Could not parse pf packet for " + srcname)
            return False

        return True

    def _get_orb_data(self, orbname):
        """Read dataloggers from an orb.

        Look into every ORB listed on configuration
        and get list of dataloggers.

        Args:
            orbname (string): name:port of the orbserver to check
        """

        self.logger.debug(orbname)
        self.logger.debug("Read STASH_ONLY on %s" % orbname)

        if not orbname or not isinstance(orbname, str):
            self.logger.warning("Not valid: %s" % (orbname))
            return

        self.logger.debug("%s" % (orbname))

        temp_orb = orb.Orb(orbname)

        try:
            self.logger.debug("connect to orb(%s)" % orbname)
            temp_orb.connect()
            temp_orb.stashselect(orb.STASH_ONLY)

        except Exception as e:
            self.logger.error("Cannot connect to ORB: %s %s" % (orbname, e))
            raise (e)

        temp_orb.select(self.orb_select)
        temp_orb.reject(self.orb_reject)

        self.logger.debug("orb.after(0.0)")
        temp_orb.after(0.0)  # or orb.ORBOLDEST

        try:
            sources = temp_orb.sources()[1]
        except Exception:
            sources = []

        self.logger.debug(sources)

        for source in sources:
            srcname = source["srcname"]
            self.logger.debug("source: %s" % srcname)

            # Get stash for each source
            try:
                pkttime, pktbuf = temp_orb.getstash(srcname)

            except orb.OrbGetStashError:
                self.logger.debug("Couldn't read stash packet from " + srcname)
                pass

            else:
                self._decode_dataloggers_from_pktbuf(srcname, pktbuf)

        try:
            self.logger.debug("close orb(%s)" % orbname)
            temp_orb.close()
        except orb.OrbError:
            pass

    def _verify_cache(self):

        if (self.last_update + self.update_frequency) < int(stock.now()):
            self.logger.info("Need to update cache.")
            self.update()

    def __str__(self):
        """Return list of orbservers."""

        return "ORBSERVERS: " + ", ".join(self.orblist)

    def __call__(self, serial):
        """Implement call."""

        self._verify_cache()

        if serial in self.serials:
            return self.serials[serial]["dlname"]
        else:
            return None

    def info(self, serial):
        """Return data on a given serial."""

        if serial in self.serials:
            return self.serials[serial]
        else:
            return None

    def __getitem__(self, serial):
        """Implement getitem."""

        self._verify_cache()

        if serial in self.serials:
            return self.serials[serial]
        else:
            return None

    def __iter__(self):
        """Implement an iterator."""

        return iter(self.serials.keys())
