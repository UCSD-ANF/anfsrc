"""Utility classes and functions for db2mongo module.

Classes and functions needed for db2mongo and
associated classes that will query Datascope
and upload the data to MongoDB.

"""

from datetime import datetime
import hashlib
import json
import os
import re
import subprocess

import antelope.datascope as datascope
import antelope.stock as stock
from db2mongo.logging_class import getLogger


class db2mongoException(Exception):
    """Base Exception class for the db2mongo modules."""

    def __init__(self, message):
        """Override init in order to track a user defined message.

        Args:
            message (string): message to print for the exception

        """
        super(db2mongoException, self).__init__(message)
        self.message = message


class ModuleLoadError(db2mongoException):
    """A module load error occurred."""

    pass


class InvalidDatabaseError(db2mongoException):
    """The given database name is invalid."""

    def __init__(self, dbname):
        """Override the message with more detail."""
        super(InvalidDatabaseError, self).__init__(
            'The given database name "%s" is invalid.' % dbname
        )


def verify_db(db):
    """Verify a Datascope database can be opened."""
    logging = getLogger()

    logging.debug("Verify database: [%s]" % (db))

    name = False

    if isinstance(db, str):
        with datascope.closing(datascope.dbopen(db, "r")) as pointer:

            if pointer.query(datascope.dbDATABASE_COUNT):
                logging.debug(pointer.query(datascope.dbDATABASE_NAME))
                name = pointer.query(datascope.dbDATABASE_NAME)
                logging.info("%s => valid" % name)

            else:
                logging.warning("PROBLEMS OPENING DB: %s" % db)

    else:
        logging.error("Not a valid parameter for db: [%s]" % db)

    return name


def extract_from_db(db, steps, fields, subset=""):
    """Retrieve data from a datascope database."""
    logging = getLogger()

    if subset:
        steps.extend(["dbsubset %s" % subset])

    logging.debug("Extract from db: " + ", ".join(steps))

    results = []

    with datascope.closing(datascope.dbopen(db, "r")) as dbview:
        dbview = dbview.process(steps)
        logging.debug("Records in new view: %s" % dbview.record_count)

        if not dbview.record_count:
            logging.warning(
                "No records after deployment-site join %s"
                % dbview.query(datascope.dbDATABASE_NAME)
            )
            return None

        for temp in dbview.iter_record():
            results.append(dict(zip(fields, temp.getv(*fields))))

    return results


def run(cmd, directory="./"):
    """Run a command by wrapping subprocess.Popen."""
    logging = getLogger()
    logging.debug("run()  -  Running: %s" % cmd)
    p = subprocess.Popen(
        [cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=directory, shell=True
    )
    stdout, stderr = p.communicate()

    if stderr:
        raise db2mongoException("STDERR present: %s => \n\t%s" % (cmd, stderr))

    for line in iter(stdout.split("\n")):
        logging.debug("stdout:\t%s" % line)

    if p.returncode != 0:
        raise db2mongoException("Exitcode (%s) on [%s]" % (p.returncode, cmd))

    return stdout


def find_snet(blob, sta, debug=False):
    """Find the snet value of a station from a station data blob."""

    logging = getLogger()

    for status in blob:
        for snet in blob[status]:
            if sta in blob[status][snet]:
                logging.info("find_snet(%s) => %s" % (sta, snet))
                return snet

    logging.info("find_snet(%s) => False" % sta)
    return False


def find_status(blob, sta, debug=False):
    """Check if station is active or offline from a station data blob."""
    logging = getLogger()

    for status in blob:
        for snet in blob[status]:
            if sta in blob[status][snet]:
                logging.info("find_status(%s) => %s" % (sta, status))
                return status

    logging.info("find_status(%s) => False" % sta)
    return False


def parse_sta_date(time, epoch=False, nullval="-"):
    """Verify that we have a valid ondate/offdate."""

    try:
        if float(time) < 1.0:
            raise
        if stock.epoch(int(time)) > stock.now():
            raise

        if epoch:
            return stock.epoch(int(time))
        else:
            return int(time)

    except Exception:
        return nullval


def parse_sta_time(time, nullval="-"):
    """Verify that we have a valid time, not in the future."""

    try:
        if float(time) < 1.0:
            raise
        if float(time) > stock.now():
            raise
        return int(float(time))
    except Exception:
        return nullval


def readable_time(time, tformat="%D (%j) %H:%M:%S %z", tzone="UTC"):
    """Format epoch time in a human readable format."""

    try:
        if parse_sta_time(time) == "-":
            raise
        return stock.epoch2str(time, tformat, tzone)
    except Exception:
        return "-"


def test_yesno(v):
    """Verify if we have true or false on variable."""
    return str(v).lower() in ("y", "yes", "true", "t", "1")


def test_table(dbname, tbl, verbose=False):
    """Verify that we can work with table.

    Args:
        dbname (string): name of the Datascope database.
        tbl (string): name of the database table.
        verbose (bool): be more verbose in output.

    Returns:
        string: path if valid and we see data.
        False: if table is invalid for any reason.
    """

    logging = getLogger()

    path = False

    try:
        with datascope.closing(datascope.dbopen(dbname, "r")) as db:
            db = db.lookup(table=tbl)

            if not db.query(datascope.dbTABLE_PRESENT):
                logging.warning("No dbTABLE_PRESENT on %s" % dbname)
                return False

            if not db.record_count:
                logging.warning("No %s.record_count" % dbname)

            path = db.query("dbTABLE_FILENAME")

    except Exception as e:
        logging.warning("Prolembs with db[%s]: %s" % (dbname, e))
        return False

    return path


def index_db(collection, indexlist):
    """Set index values on MongoDB collection."""

    logging = getLogger()

    re_simple = re.compile(".*simple.*")
    re_text = re.compile(".*text.*")
    re_sparse = re.compile(".*sparse.*")
    re_hashed = re.compile(".*hashed.*")
    re_unique = re.compile(".*unique.*")

    logging.debug(indexlist)

    for field, param in indexlist.iteritems():

        unique = 1 if re_unique.match(param) else 0
        sparse = 1 if re_sparse.match(param) else 0

        style = 1
        if re_text.match(param):
            style = "text"
        elif re_hashed.match(param):
            style = "hashed"
        elif re_simple.match(param):
            style = 1

        try:
            expireAfter = float(param)
        except Exception:
            expireAfter = False

        logging.debug(
            "ensure_index( [(%s,%s)], expireAfterSeconds = %s, unique=%s, sparse=%s)"
            % (field, style, expireAfter, unique, sparse)
        )
        collection.ensure_index(
            [(field, style)],
            expireAfterSeconds=expireAfter,
            unique=unique,
            sparse=sparse,
        )

    collection.reindex()

    for index in collection.list_indexes():
        logging.debug(index)


def get_md5(test_file, debug=False):
    """Verify the checksum of a table.

    Returns:
        int: md5sum of the file
        False: if no file found.
    """
    logging = getLogger()

    logging.debug("get_md5(%s) => test for file" % test_file)

    if os.path.isfile(test_file):
        f = open(test_file)
        md5 = hashlib.md5(f.read()).hexdigest()
        f.close()
        return md5
    else:
        raise db2mongoException("get_md5(%s) => FILE MISSING!!!" % test_file)

    return False


def dict_merge(a, b):
    """Recursively merges dicts.

    Not just simple a['key'] = b['key']. If both a and b have a key who's value
    is a dict then dict_merge is called on both values and the result stored in
    the returned dictionary.
    """
    if not isinstance(b, dict):
        return b
    for k, v in b.iteritems():
        if k in a and isinstance(a[k], dict):
            a[k] = dict_merge(a[k], v)
        else:
            a[k] = v
    return a


def update_collection(mongo_db, name, data, index=[]):
    """Update a MongoDB collection somewhat safely."""

    logging = getLogger()

    logging.info("update_collection(%s)" % name)

    # Verify if we need to update MongoDB
    if data:

        temp_name = "%s_temp" % name

        logging.debug("Update temp collection %s with data" % temp_name)
        collection = mongo_db[temp_name]

        for entry in data:
            logging.debug("collection.update(%s)" % entry["id"])
            collection.update({"id": entry["id"]}, {"$set": entry}, upsert=True)

        # Create/update some indexes for the collection
        if index and len(index) > 0:
            index_db(collection, index)

        logging.debug("Move collection %s => %s" % (temp_name, name))
        collection.rename(name, dropTarget=True)

    else:
        logging.debug("NO DATA FROM OBJECT: %s" % name)


def clean_cache_object(cache, id="dlname"):
    """Clean db2mongo cache data.

    Prepare memory dictionary for injection of data into
    a MongoDb structure. We have several requirements:
        1) Base key "dlname" on every element. Unless "id" is defined.
        2) All data should be convertible by json.load()
        3) Base key "time" should be present. This is the time of the data.

    We create a new key "id" for our returned object. This is unique
    and if objects repeat in the cache then the function will silently
    overwrite previous entries. We append a new key "lddate" with the time of
    the object creation.  All data returned should be strings safe to be sent
    directly to MongoDB.
    """

    logging = getLogger()

    logging.info("clean_cache_object(%s)" % id)

    results = []

    for entry in cache:
        if id not in entry:
            continue

        # Convert to JSON then back to dict to stringify numeric keys
        entry = json.loads(json.dumps(entry))

        try:
            # Try to find object for id
            if id != "id":
                entry["id"] = entry[id]
        except Exception:
            # Generic id for this entry
            entry["id"] = len(results)

        # add entry for autoflush index
        entry["time_obj"] = datetime.fromtimestamp(entry["time"])

        # add entry for last load of entry
        entry["lddate"] = datetime.fromtimestamp(stock.now())

        results.append(entry)

    return results
