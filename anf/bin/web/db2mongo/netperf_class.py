"""db2mongo module netperf.

This module contains an implementation of a db2mongo module to track network
performance of Q330 dataloggers.
"""
from logging import getLogger

from anf.logutil import fullname
from antelope import stock

from .util import (
    clean_cache_object,
    db2mongoException,
    extract_from_db,
    get_md5,
    test_table,
    verify_db,
)

logger = getLogger(__name__)


class NetPerfException(db2mongoException):
    """Base exception class for this db2mongo module."""

    pass


class NetPerf:
    """Track q330 network performance."""

    def __init__(self, db_list=[], subset=False):
        """Load class and retrieve data from netperf table.

        Usage:
            netperf = NetPerf(db,subset=False)

            netperf.validate()

            while True:
                if netperf.need_update():
                    netperf.update()
                    data,error = netperf.data()
                sleep(time)

        """

        self.logging = getLogger(fullname(self))

        self.logging.debug("init()")

        self.db = {}
        self.database_list = db_list
        self.db_subset = subset
        self.cache = []
        self.error_cache = []

        self.tables = ["netperf"]

    def data(self, refresh=False):
        """Export all values stored in memory."""

        if refresh:
            self.update()

        return (
            clean_cache_object(self.cache, "id"),
            clean_cache_object(self.error_cache, "id"),
        )

    def need_update(self):
        """Check if the md5 checksum changed on any table."""

        self.logging.debug("need_update()")

        for db in self.db:
            for table in self.tables:

                md5 = self.db[db][table]["md5"]
                test = get_md5(self.db[db][table]["path"])

                self.logging.debug(
                    "(%s) table:%s md5:[old: %s new: %s]" % (db, table, md5, test)
                )

                if test != md5:
                    return db

        return False

    def update(self):
        """Update the data from the netperf tables."""
        if not self.db:
            self.validate()

        self.logging.debug("refresh(%s)" % (self.db))

        self._get_netperf()

        for db in self.db:
            for table in self.tables:
                self.db[db][table]["md5"] = get_md5(self.db[db][table]["path"])

    def validate(self):
        """Validate database tables."""

        self.logging.debug("validate()")

        if self.db:
            return True

        # Verify database files
        for test_db in self.database_list:
            name = verify_db(test_db)
            if name:
                self.db[name] = {}
            else:
                raise NetPerfException("Not a valid database: %s" % (self.database))

        if not len(self.db):
            raise NetPerfException("Missing value for database")

        # Verify tables
        for db in self.db:
            for table in self.tables:
                path = test_table(db, table)
                if not path:
                    raise NetPerfException("Empty or missing: %s %s" % (self.db, table))

                self.db[db][table] = {"path": path, "md5": False}
                self.logging.debug("run validate(%s) => %s" % (table, path))

        return True

    def _get_netperf(self):
        self.logging.debug("_get_netperf()")
        self.cache = []
        self.error_cache = []

        steps = ["dbopen netperf"]

        fields = ["snet", "time", "npsta", "perf"]

        for db in self.db:
            for v in extract_from_db(db, steps, fields, self.db_subset):

                try:
                    v["perf"] = int(v["perf"])
                    v["time"] = int(v["time"])

                    v["year"] = int(stock.epoch2str(v["time"], "%Y", "UTC"))
                    v["jday"] = int(stock.epoch2str(v["time"], "%j", "UTC"))

                    v["id"] = "%s_%s_%s" % (v["snet"], v["jday"], v["year"])

                    self.logging.debug("netperf() => %s, %s)" % (v["id"], v["perf"]))

                    self.cache.append(v)
                except Exception as e:
                    self.logging.complain("netperf() => parse exception)")
                    v["exception"] = Exception
                    v["error"] = e

                    self.logging.complain(v)

                    self.error_cache.append(v)
