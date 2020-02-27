"""Abstraction of a geographic region for GMT."""

import ast
import collections
import csv

from anf.gmt import LOGGER
import six

GMTREGION_FIELDS = [
    "name",
    "description",
    "minlat",
    "maxlat",
    "minlon",
    "maxlon",
    "grdfile",
    "gradiantfile",
]


class GmtRegion(collections.namedtuple("GmtRegion", GMTREGION_FIELDS)):
    """Describe a GMT region_data and various metadata including coordinates.

    Use the regionstr method to generate a string suitable for passing with the -R option to GMT.
    """

    __slots__ = ()  # save memory by not creating an internal dict

    @property
    def centerlat(self):
        """Generate the center latitude from the max and min."""
        return (self.maxlat - self.minlat) / 2 + self.minlat

    @property
    def centerlon(self):
        """Generate the center longitude from the max and min."""
        return (self.maxlon - self.minlon) / 2 + self.minlon

    @property
    def regionstr(self):
        """Get a GMT region_data string for the region_data."""
        return "{minlon:.0f}/{minlat:.0f}/{maxlon:.0f}/{maxlat:.0f}r".format(
            **(self._asdict())
        )

    def get_azeq_center_str(self, width):
        """Get a center string for an Equal Azimuth projection."""

        return "{centerlat:.0f}/{centerlon:.0f}/{width}i".format(
            centerlat=self.centerlat, centerlon=self.centerlon, width=width
        )

    def __str__(self):
        """Format the object in a human readable manner."""
        return (
            "GmtRegionCoordinates: Min=({minlat:3.6f}, {minlon:3.6f})"
            " Max=({maxlat:3.6f}, {maxlon:3.6f})"
            " Center=({centerlat:3.6f},{centerlon:3.6f)".format(
                minlat=self.minlat,
                minlon=self.minlon,
                maxlat=self.maxlat,
                maxlon=self.maxlon,
                centerlat=self.centerlon,
            )
        )


class CsvRegionReader(six.Iterator):
    """Parse gmt.GmtRegion objects from a list of CSV lines."""

    def __init__(self, csvfile, *args, **kwds):
        """Create a csv.Reader-like object that parses GmtRegion objects from a csvfile.

        Args:
            csvfile (list or iterator): lines of a CSV

        Returns:
            an object which operates like a regular csv.reader but maps the information read into a GMTRegion object,
            which can be treated in a similar fashion to a csv.DictReader. The fields are hard-coded, as the format of
            the table is application dependent. They are as follows:
            * name (string)
            * description (string)
            * minlat (float)
            * maxlat (float)
            * minlin (float)
            * maxlon (float)
            * gridlines (float)
            * gridfile (filename)
            * gradiantfile (filename)

        """

        self.reader = csv.reader(csvfile, skipinitialspace=True, *args, **kwds)
        self.line_num = 0

    @staticmethod
    def _parse(field):
        try:
            cursor = ast.literal_eval(field)
        except SyntaxError:
            cursor = field

        return cursor

    def __iter__(self):
        """Return self as an iterator helper method."""
        return self

    def __next__(self):
        """Retrieve the next GmtRegion."""
        row = next(self.reader)
        self.line_num = self.reader.line_num

        # unlike the basic reader, we prefer not to return blanks,
        # because we will typically wind up with a dict full of None
        # values
        while not row:
            row = next(self.reader)

        lf = len(GMTREGION_FIELDS)
        lr = len(row)
        if lf < lr:
            LOGGER.warning(
                "GmtRegion row has too many fields ({:d}). Ignoring {:d} fields.".format(
                    lr, lr - lf
                )
            )
        elif lf > lr:
            LOGGER.warning(
                "Padding {:d} slots in row with too few fields. (Expected: {:d}, Got: {:d})".format(
                    lf - lr, lf, lr
                )
            )
            for i in range(lr, lf):
                row[i] = None

        return GmtRegion(
            row[0],  # name
            row[1],  # description
            self._parse(row[2]),  # minlat
            self._parse(row[3]),  # maxlat
            self._parse(row[4]),  # minlon
            self._parse(row[5]),  # maxlon
            row[6],  # gridfile
            row[7],  # gradientfile
        )
