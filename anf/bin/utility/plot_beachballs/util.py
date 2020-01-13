from __main__ import *  # Get all the libraries from parent


class Origin:
    """Extract origin information from database."""

    def __init__(self, databasename=None, options=None):
        self.databasename = databasename
        self.options = options

        # Open database and make new object for it
        try:
            self.db = datascope.dbopen(self.databasename, "r+")
        except Exception, e:
            error("Problems opening database: %s %s %s" % (database, Exception, e))

        # Point to origin table
        try:
            self.origin_table = self.db.lookup(table="origin")
        except Exception, e:
            error("Problems pointing to origin table: %s %s" % (Exception, e))

        # Point to event table
        try:
            self.event_table = self.db.lookup(table="event")
        except Exception, e:
            error("Problems pointing to event table: %s %s" % (Exception, e))

        # Point to mt table
        try:
            self.mt_table = self.db.lookup(table="mt")
        except Exception, e:
            error("Problems pointing to mt table: %s %s" % (Exception, e))

        # Join origin & mt tables
        self.table_join = self.origin_table.join(self.event_table)
        self.table_join = self.table_join.join(self.mt_table)

        self.params_subset(self.options)

    def params(self, options):
        # Assign location bounds
        try:
            self.bounds = options.loc.split(",")
        except Exception:
            self.bounds = self.get_location_bounds()

        # Assign timing bounds
        try:
            self.time = options.time.split(",")
        except Exception:
            self.time = self.get_time_bounds()
        return self

    def get_location_bounds(self):
        """Get location boundary of events."""
        min_lon = self.table_join.ex_eval("min(lon)")
        max_lon = self.table_join.ex_eval("max(lon)")
        min_lat = self.table_join.ex_eval("min(lat)")
        max_lat = self.table_join.ex_eval("max(lat)")

        return [str(min_lon), str(max_lon), str(min_lat), str(max_lat)]

    def get_time_bounds(self):
        """Get time minimum and maximum of events."""
        min_time = "%0.20f" % self.table_join.ex_eval("min(time)")
        max_time = "%0.20f" % self.table_join.ex_eval("max(time)")

        return [str(min_time), str(max_time)]

    def params_subset(self, options):
        """Database subset from parameters."""
        self.params(options)
        express = " ".join(
            [
                "lat >=",
                self.bounds[2],
                "&&",
                "lat <=",
                self.bounds[3],
                "&&",
                "lon >=",
                self.bounds[0],
                "&&",
                "lon <=",
                self.bounds[1],
                "&&",
                "time >=",
                '"',
                self.time[0],
                '"',
                "&&",
                "time <=",
                '"',
                self.time[1],
                '"',
            ]
        )

        try:
            self.table = self.table_join.subset(express)
        except Exception, e:
            sys.exit("EXIT: Failed to subset table: Check location or time format")
        return self

    def moment_array(self):
        """Get moment tensor info."""
        lens = self.table.query("dbRECORD_COUNT")
        if lens == 0:
            sys.exit("EXIT: No events found")
        else:
            for x in range(0, lens):
                self.table.record = x
                result = self.table.getv(
                    "orid",
                    "evid",
                    "mt.auth",
                    "prefor",
                    "lat",
                    "lon",
                    "depth",
                    "drmag",
                    "scm",
                    "tmtt",
                    "tmpp",
                    "tmrr",
                    "tmtp",
                    "tmrt",
                    "tmrp",
                    "time",
                    "estatus",
                    "str1",
                    "str2",
                    "dip1",
                    "dip2",
                    "rake1",
                    "rake2",
                )
                # append data to numpy array
                if x == 0:
                    results = np.array(result)
                else:
                    results = np.vstack([results, result])
        return results


def mt_comp(row, ind):
    """Divide mt component by scalar moment."""
    mc = float(row[ind]) / float(row[8])
    return mc


def convert_to_rgb(minval, maxval, val, colors):
    """Get rgb color from a colorscale for given value."""
    max_index = 256
    v = float(val - minval) / float(maxval - minval) * max_index
    i1, i2 = int(v), min(int(v) + 1, max_index)
    (r1, g1, b1) = colors(i1)[0], colors(i1)[1], colors(i1)[2]
    (r2, g2, b2) = colors(i2)[0], colors(i2)[1], colors(i2)[2]
    f = v - i1
    return r1 + f * (r2 - r1), g1 + f * (g2 - g1), b1 + f * (b2 - b1)


def strs2floats(vector):
    """Convert vector of strings to floats."""
    float_vals = []
    for str_val in vector:
        float_vals.append(float(str_val))

    return float_vals


def distance(x1, x2, y1, y2):
    """Distance formula from lat/lon coordinates."""
    lat1 = radians(y1)
    lon1 = radians(x1)
    lat2 = radians(y2)
    lon2 = radians(x2)
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    dist = 6373.0 * c
    return dist


def myround(x, base=5):
    """Round value."""
    return int(base * round(float(x) / base))
