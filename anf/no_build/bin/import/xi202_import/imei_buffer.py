"""Buffer of IMEI data from an XI-202.

How to use...

imei = IMEIbuffer()
#
imei( imei='300234062061770', serial='0100000A27B19B6A')

print  imei( '300234062061770' )
>> '0100000A27B19B6A'

print imei( '00000' )
>> False

print imei( None )
>> False

"""

from logging import getLogger

from anf.logutil import fullname

logger = getLogger(__name__)


class IMEIbuffer:
    """Buffer of IMEI data."""

    def __init__(self):
        """Set up the class."""

        self.logger = getLogger(fullname(self))

        self.cache = {}

    def add(self, imei=None, serial=None):
        """Add an IMEI to the buffer."""

        self.logger.debug("add %s to cache with value %s " % (imei, serial))

        if not imei:
            self.logger.warning("Need valid value for IMEI: [%s]" % imei)

        if not serial:
            self.logger.warning("Need valid value for serial: [%s]" % serial)

        try:
            if int(serial) < 1:
                self.logger.warning("NULL serial: [%s]" % serial)
                return False
        except Exception:
            pass

        if imei in self.cache:
            if serial == self.cache[imei]:
                return True
            self.logger.info(
                "Updating value for %s: %s => %s" % (imei, self.cache[imei], serial)
            )
        else:
            self.logger.info("New imei %s: %s " % (imei, serial))

        self.cache[imei] = serial

        return True

    def __str__(self):
        """Provide string representation of the IMEI buffer."""

        return "IMEIbuffer: %s" % str(self.cache)

    def __call__(self, imei):
        """Implement call."""

        if imei in self.cache:
            return self.cache[imei]
        else:
            return None

    def __getitem__(self, imei):
        """Implement getitem functionality."""

        if imei in self.cache:
            return self.cache[imei]
        else:
            return None

    def __iter__(self):
        """Implement an iterator on the buffer."""

        return iter(self.cache.keys())
