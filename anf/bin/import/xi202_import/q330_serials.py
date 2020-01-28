"""Manipulate Q330 serial numbers."""


import collections

from anf.getlogger import getLogger
from antelope import stock
from six import string_types


class Q330serials:
    """Parse Q330 Serial Numbers from parameter files.

    Usage:
        q330units = Q330serials( q330_pf_files )

    Example:
        q330units = Q330serials( q330_pf_files )
        print  q330units( '0100000A27B19B6A' )
        >> TA_O53A

        print  q330units.info( '0100000A27B19B6A' )
        >> {'snet': 'TA', 'sta': 'O53A', 'dlname': 'TA_O53A'}

        print q330units( '00000' )
        >> False

        print q330units( None )
        >> False

    """

    def __init__(self, pf_files=[]):
        """Initialize the Q330Serials object.

        Args:
            pf_files (list): list of q3302orb parameter file names to parse.
        """

        self.logging = getLogger("Q330serials")

        self.serials = {}
        self.add(pf_files)

    def add(self, pf_files):
        """Add a pf file to the configuration.

        Args:
            pf_files (list): list of q3302orb parameter files to parse.
        """

        self.logging.debug("add to pf file configuration: " + str(pf_files))

        if not pf_files:
            return

        if isinstance(pf_files, collections.Iterable):
            self.q330_pf_files = pf_files
        elif isinstance(pf_files, string_types):
            self.q330_pf_files = [pf_files]
        else:
            self.logging.error(
                "Need pf_files to be string or iterable collection [%s]" % pf_files
            )

        # self.logging.debug( str( self ) )

        # remove empty strings
        self.q330_pf_files = [t for t in self.q330_pf_files if t]

        for pf in self.q330_pf_files:
            self._read_pf(pf)

    def _read_pf(self, pf):

        self.logging.info("Read values from pf file %s" % pf)

        temp = stock.pfread(pf)

        dataloggers = temp.get("dataloggers")

        if not dataloggers:
            self.logging.warning("Nothing in the dataloggers parameter for %s" % pf)
        else:
            # self.logging.debug( dataloggers )
            pass

        for line in dataloggers:

            parts = line.split()
            new_serial = parts[3]

            if (
                new_serial in self.serials
                and self.serials[new_serial]["dlname"].strip() == parts[0].strip()
            ):
                self.logging.debug(
                    "Same value for %s: %s => %s"
                    % (new_serial, self.serials[new_serial]["dlname"], parts[0])
                )
            elif new_serial in self.serials:
                self.logging.info(
                    "Updating value for %s: %s => %s"
                    % (new_serial, self.serials[new_serial]["dlname"], parts[0])
                )
            else:
                self.logging.info("New serial %s: %s " % (parts[0], new_serial))

            self.serials[new_serial] = {
                "dlname": parts[0],
                "sta": parts[2],
                "snet": parts[1],
            }

    def __str__(self):
        """Display the names of the q330 parameter files."""

        return "q3302orb.pf file list: %s" % str(self.q330_pf_files)

    def __call__(self, serial):
        """Return the dlname associated with a serial number.

        Args:
            serial (string): serial number of the q330

        Returns:
            string: the dlname of the q330
            None: if nothing found
        """

        if serial in self.serials:
            return self.serials[serial]["dlname"]
        else:
            return None

    def info(self, serial):
        """Return the data associated with the given serial number."""

        return self.__getitem__(serial)

    def __getitem__(self, serial):
        """Return the data associated with the given serial number."""

        if serial in self.serials:
            return self.serials[serial]
        else:
            return None

    def __iter__(self):
        """Return an iterable of the known serial numbers."""

        return iter(self.serials.keys())
