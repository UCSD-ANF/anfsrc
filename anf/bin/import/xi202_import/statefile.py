"""The stateFile class.

This modules was pretty much undocumented. G. Davis added as much as possible
from a cursory read of the code, but it's unclear why the entire Antelope
statefile mechanism was reinvented from scratch by J. Reyes.

TODO: Convert this program to use a normal Antelope statefile.
"""
import os

from anf.logging import getLogger
from antelope import stock


class stateFileException(Exception):
    """Base exception thrown by this class."""

    pass


class stateFile:
    """Track some information from the realtime process.

    Generates a bunch of state files in a very specific fashion used by the
    mongodb code.
    Save value of pktid in file.
    """

    def __init__(self, filename=False, name="default", start=0):
        """Initialize a new stateFile object.

        Args:
            filename (boolean or string): no-op if false. Otherwise, name of
            subfile in the main statefile directory.
            name (string): name of the stateFile object
            start (int): orb packet id to start at, or something.

        """

        self.logging = getLogger("stateFile")

        self.logging.debug("stateFile.init()")

        self.filename = filename
        self.name = name
        self.id = start
        self.time = 0
        self.strtime = "n/a"
        self.latency = "n/a"
        self.pid = "PID %s" % os.getpid()

        if not filename:
            return

        self.directory, self.filename = os.path.split(filename)

        if self.directory and not os.path.isdir(self.directory):
            os.makedirs(self.directory)

        self.file = os.path.join(self.directory, "%s_%s" % (self.name, self.filename))

        self.logging.debug("Open file for STATE tracking [%s]" % self.file)
        if os.path.isfile(self.file):
            self.open_file("r+")
            self.read_file()
        else:
            self.open_file("w+")

        if not os.path.isfile(self.file):
            raise stateFileException("Cannot create STATE file %s" % self.file)

    def last_id(self):
        """Return the last id from the state file."""
        self.logging.info("last id:%s" % self.id)
        return self.id

    def last_time(self):
        """Return the last time from the state file."""
        self.logging.info("last time:%s" % self.time)
        return self.time

    def read_file(self):
        """Read the stateFile represented by this object."""
        self.pointer.seek(0)

        if not self.filename:
            return

        try:
            temp = self.pointer.read().split("\n")
            self.logging.info("Previous STATE file %s" % self.file)
            self.logging.info(temp)

            self.id = float(temp[0])
            self.time = float(temp[1])
            self.strtime = temp[2]
            self.latency = temp[3]

            self.logging.info(
                "Previous - %s ID:%s TIME:%s LATENCY:%s"
                % (self.pid, self.id, self.time, self.latency)
            )

            if not float(self.id):
                raise TypeError("id is not a float")

        except Exception:
            self.logging.warning(
                "Cannot find previous state on STATE file [%s]" % self.file
            )

    def set(self, id, time):
        """Write out the statefile."""

        if not self.filename:
            return

        self.logging.debug("set %s to %s" % (self.filename, id))

        self.id = id
        self.time = time
        self.strtime = stock.strlocalydtime(time).strip()
        self.latency = stock.strtdelta(stock.now() - time).strip()

        # self.logging.debug( 'latency: %s' % self.latency )

        try:
            self.pointer.seek(0)
            self.pointer.write(
                "%s\n%s\n%s\n%s\n%s\n"
                % (self.id, self.time, self.strtime, self.latency, self.pid)
            )
        except Exception as e:
            raise stateFileException(
                "Problems while writing to state file: %s %s" % (self.file, e)
            )

    def open_file(self, mode):
        """Wrap open in order to throw a different exception.

        Raises:
            stateFileException if a state file can't be opened.

        """

        try:
            self.pointer = open(self.file, mode)
        except Exception as e:
            raise stateFileException(
                "Problems while opening state file: %s %s" % (self.file, e)
            )
