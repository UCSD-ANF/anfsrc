"""Module dlevent for db2mongo.

This module contains an implementation of a db2mongo module to handle Antelope
datalogger events.
"""
from datetime import datetime
import json

from antelope import datascope, stock

from .logging_class import getLogger  # TODO: use anf.logging.getLogger, FFS.
from .util import (
    InvalidDatabaseError,
    db2mongoException,
    extract_from_db,
    get_md5,
    test_table,
    verify_db,
)


class DleventException(db2mongoException):
    """Base exception class for this db2mongo module."""

    pass


class Dlevent:
    """Track Antelope dlevent data."""

    def __init__(self, db=False, subset=False):
        """Query a Datascope dlevent database and cache values in memory.

        Usage:
            dlevent = Dlevent(db,subset=False)

            dlevent.validate()

            while True:
                if dlevent.need_update():
                    dlevent.update()
                    data,error = dlevent.data()
                sleep(time)

        """

        self.logging = getLogger(self.__class__.__name__)

        self.logging.debug("init()")

        self.db = False
        self.database = db
        self.db_subset = subset
        self.cache = []
        self.error_cache = []

        self.tables = ["dlevent"]
        self.dbs_tables = {}

    def data(self, refresh=False):
        """Export all values stored in memory."""

        if refresh:
            self.update()

        return (self._clean_cache(self.cache), self._clean_cache(self.error_cache))

    def need_update(self):
        """Check if the md5 checksum changed on any table."""
        self.logging.debug("need_update()")

        for name in self.tables:

            md5 = self.dbs_tables[name]["md5"]
            test = get_md5(self.dbs_tables[name]["path"])

            self.logging.debug(
                "(%s) table:%s md5:[old: %s new: %s]" % (self.database, name, md5, test)
            )

            if test != md5:
                return True

        return False

    def update(self):
        """Update the data in the cache from the dlevent db tables."""
        if not self.db:
            self.validate()

        self.logging.debug("refresh(%s)" % (self.db))

        for name in self.tables:
            self.dbs_tables[name]["md5"] = get_md5(self.dbs_tables[name]["path"])

        self._get_dlevents()

    def validate(self):
        """Verify database files and datascope table files."""

        self.logging.debug("validate()")

        if self.db:
            return True

        # Vefiry database files
        if self.database is not None:
            try:
                verify_db(self.database)
                self.db = self.database
            except datascope.DbopenError:
                raise InvalidDatabaseError(self.database)
        else:
            raise DleventException("Missing value for database")

        # Verify tables
        for table in self.tables:
            path = test_table(self.db, table)
            if not path:
                raise DleventException("Empty or missing: %s %s" % (self.db, table))

            self.dbs_tables[table] = {"path": path, "md5": False}
            self.logging.debug("run validate(%s) => %s" % (table, path))

        return True

    def _get_dlevents(self):

        self.logging.debug("_get_dlevents()")
        self.cache = []
        self.error_cache = []

        steps = ["dbopen dlevent"]

        fields = ["dlname", "dlevtype", "dlcomment", "time"]

        for v in extract_from_db(self.db, steps, fields, self.db_subset):

            self.logging.debug("dlevent(%s)" % (v["dlname"]))
            snet, sta = v["dlname"].split("_", 1)
            v["snet"] = snet
            v["sta"] = sta

            v["year"] = stock.epoch2str(v["time"], "%Y", "UTC")
            v["month"] = stock.epoch2str(v["time"], "%L", "UTC")

            self.cache.append(v)

    def _clean_cache(self, cache):

        results = []

        for entry in cache:
            if "dlname" not in entry:
                continue

            # Convert to JSON then back to dict to stringify numeric keys
            entry = json.loads(json.dumps(entry))

            # Generic id for this entry
            entry["id"] = len(results)

            # add entry for autoflush index
            entry["time_obj"] = datetime.fromtimestamp(entry["time"])

            # add entry for last load of entry
            entry["lddate"] = datetime.fromtimestamp(stock.now())

            results.append(entry)

        return results
