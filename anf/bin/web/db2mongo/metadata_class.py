"""The db2monogo metadata module."""
# from datetime import datetime, timedelta
from collections import defaultdict
from datetime import datetime
import json
from logging import getLogger
import re

from anf.logutil import fullname
import antelope.Pkt as Pkt
import antelope.datascope as datascope
import antelope.orb as orb
import antelope.stock as stock

from .util import (
    db2mongoException,
    extract_from_db,
    get_md5,
    parse_sta_date,
    parse_sta_time,
    readable_time,
    test_table,
    test_yesno,
    verify_db,
)

logger = getLogger(__name__)


class metadataException(db2mongoException):
    """Base Exception class for this module."""


class AutoVivification(dict):
    """Implementation of perl's autovivification feature."""

    def __getitem__(self, item):
        """Automatically revive requested items."""
        try:
            return dict.__getitem__(self, item)
        except KeyError:
            value = self[item] = type(self)()
            return value


class dlsensor_cache:
    """Store a cache of the dlsensor table.

    The tool returns the name for the provided serial. You can search for a
    sensor or for a digitizer. If not found then you get NULL value. In this
    case we set NULL to be "-".

    Usage:
        cache_object = dlsensor_cache()

        cache_object.add( dlident, dlmodel, snident, snmodel, time, endtime )

        sname = cache_object.sensor(snident, time)
        dname = cache_object.digitizer(dlident, time)

    """

    def __init__(self):
        """Initialize the dlsensor_cache."""
        self.logger = getLogger(fullname(self))

        self.logger.debug("init()")

        self.defaultTime = 0.0
        self.defaultEndtime = 9999999999.9
        self.sensors = {}
        self.digitizers = {}

    def add(self, dlident, dlmodel, snident, snmodel, time="-", endtime="-"):
        """Insert new rows from the dlsensor table into the cache.

        This will create an object for each type of instrument tracked.
        """

        try:
            time = float(time)
        except Exception:
            time = self.defaultTime

        try:
            endtime = float(endtime)
        except Exception:
            endtime = self.defaultEndtime

        if snident not in self.sensors:
            self.sensors[snident] = []

        self.logger.debug(
            "dlsensor_cache.add(%s,%s,%s,%s,%s,%s)"
            % (dlident, dlmodel, snident, snmodel, time, endtime)
        )

        # Add a new entry to the sensor cache.
        if snident not in self.sensors:
            self.sensors[dlident] = []

        self.sensors[snident].append(
            {"time": time, "endtime": endtime, "model": snmodel}
        )

        # Add a new entry to the digitizer cache.
        if dlident not in self.digitizers:
            self.digitizers[dlident] = []

        self.digitizers[dlident].append(
            {"time": time, "endtime": endtime, "model": dlmodel}
        )

    def _search(self, group, ident, time=False):
        """Find dlmodel for this serial.

        Generic internal function for looking at the cached data for a match
        entry.
        """

        self.logger.debug("dlsensor_cache.search(%s,%s,%s)" % (group, ident, time))

        name = "-"
        timeless = False

        if not time:
            timeless = True

        else:
            try:
                time = float(time) + 1.0
            except Exception:
                timeless = True
                time = False

        test = getattr(self, group)

        if ident in test:
            for k in test[ident]:
                self.logger.debug(
                    "Look for %s in time:%s,endtime:%s )"
                    % (time, k["time"], k["endtime"])
                )
                if timeless or time >= k["time"] and time <= k["endtime"]:
                    name = k["model"]
                    break

        self.logger.debug("dlsensor_cache.search() => %s" % name)

        return name

    def digitizer(self, ident, time=False):
        """Return digitizers matching ident and time."""
        return self._search("digitizers", ident, time)

    def sensor(self, ident, time=False):
        """Return sensors matching ident and time."""
        return self._search("sensors", ident, time)


class Metadata(dlsensor_cache):
    """Track station configuration and metadata from multiple tables.

    Load information from multiple Datascope tables that track station
    configuration and metadata values. Some information is appended to the
    objects if a value for an ORB is provided and the station is found on it.
    We track all packets related to the station and we have the option to
    extract some information from the pf/st packets.

    Usage:
        metadata = Metadata(db,orbs,db_subset,orb_select)

        metadata.validate()

        while True:
            if metadata.need_update():
                metadata.update()
                data,error = metadata.data()
            sleep(time)

    """

    def __init__(self, db=False, orbs={}, db_subset=False, orb_select=False):
        """Initialize the Metadata object."""
        self.logger = getLogger(self.__class__.__name__)

        self.logger.debug("Metadata.init()")

        self.orbs = {}
        self.cache = {}
        self.db = False
        self.database = db
        self.dbs_tables = {}
        self.perf_db = False
        self.perf_subset = False
        self.orbservers = orbs
        self.timezone = "UTC"
        self.error_cache = {}
        self.perf_days_back = 30
        self.db_subset = db_subset
        self.orb_select = orb_select
        self.timeformat = "%D (%j) %H:%M:%S %z"

        self.tables = ["site"]

        self.seismic_sensors = {}

        self.tags = False
        self.deployment = False
        self.sensor = False
        self.comm = False
        self.digitizer = False
        self.balers = False
        self.windturbine = False

        self.dlsensor_cache = False

    def validate(self):
        """Validate the module configuration."""
        self.logger.debug("validate()")

        if self.db:
            return True

        # Vefiry database files
        if self.database:
            if verify_db(self.database):
                self.db = self.database
            else:
                raise metadataException("Not a vaild database: %s" % (self.database))
        else:
            raise metadataException("Missing value for database")

        # Test configuration to see how many
        # tables we are using.

        if test_yesno(self.deployment):
            self.tables.append("deployment")

        if test_yesno(self.sensor):
            self.tables.append("stage")
            self.tables.append("calibration")
            self.tables.append("snetsta")

        if test_yesno(self.comm):
            self.tables.append("comm")
            self.tables.append("snetsta")

        if test_yesno(self.digitizer):
            self.tables.append("stage")
            self.tables.append("snetsta")

        if test_yesno(self.balers):
            self.tables.append("stabaler")

        if test_yesno(self.windturbine):
            self.tables.append("windturbine")

        # Verify tables
        for table in self.tables:
            path = test_table(self.db, table)
            if not path:
                raise metadataException("Empty or missing: %s %s" % (self.db, table))

            # Save this info for tracking of the tales later
            self.dbs_tables[table] = {"path": path, "md5": False}
            self.logger.debug("run validate(%s) => %s" % (table, path))

        # Track Channel Perf database if needed
        if self.perf_db:
            path = test_table(self.perf_db, "chanperf")
            if not path:
                raise metadataException(
                    "Empty or missing: %s %s" % (self.perf_db, "chanperf")
                )

            # Save this info for tracking of the tales later
            self.dbs_tables["chanperf"] = {"path": path, "md5": False}
            self.logger.debug("run validate(%s) => %s" % ("chanperf", path))

        return True

    def need_update(self, dbonly=False):
        """Check if md5 checksum has changed on any table.

        NOTE: By default we return True because we want to update any ORB data
        that we can find for the sites.  We can override this and verify the
        actual checksums by setting dbonly=True or if we don't specify any ORBs
        to check.

        Args:
            dbonly(boolean): use the database values rather than assuming we
            always want an update.
        """
        self.logger.debug("need_update()")

        if not dbonly and len(self.orbs) > 0:
            return True

        for name in self.tables:

            md5 = self.dbs_tables[name]["md5"]
            test = get_md5(self.dbs_tables[name]["path"])

            self.logger.debug(
                "(%s) table:%s md5:[old: %s new: %s]" % (self.db, name, md5, test)
            )

            if test != md5:
                return True

        return False

    def update(self, forced=False):
        """Update cached data from database.

        Args:
            forced (bool): force an update to the cache.
        """
        if not self.db:
            self.validate()

        if forced or self.need_update(dbonly=True):
            for name in self.tables:
                self.dbs_tables[name]["md5"] = get_md5(self.dbs_tables[name]["path"])
            self._get_db_data()

        self._get_orb_data()

    def data(self):
        """Export the data from the tables."""
        self.logger.debug("data(%s)" % (self.db))

        if not self.db:
            self.validate()

        return (self._clean_cache(self.cache), self._clean_cache(self.error_cache))

    def _verify_cache(self, snet, sta, group=False, primary=False):
        """Verify we have an entry for the snet-sta value.

        Args:
            primary (bool): Make missing entries if true. If false, don't update.
        """

        if not snet:
            return False
        if not sta:
            return False

        if snet not in self.cache:
            if not primary:
                return False
            self.cache[snet] = {}

        if sta not in self.cache[snet]:
            if not primary:
                return False
            self.cache[snet][sta] = {}

        if group and group not in self.cache[snet][sta]:
            self.cache[snet][sta][group] = defaultdict(lambda: defaultdict())

        return True

    def _not_in_db(self, snet, sta, table):
        """Check if a snet or sta is in the database.

        Sometimes the Datascope metadata tables will have invalid entries. Some
        snet or sta values that are not real sites. If we identify any using
        the function self._verify_cache() then we use this method to put that
        information on the "ERROR" cache that we send out to the user during
        the .data() call.
        """
        self.logger.warning("ERROR ON DATABASE [%s_%s] %s" % (snet, sta, table))

        if snet not in self.error_cache:
            self.error_cache[snet] = {}

        if sta not in self.error_cache[snet]:
            self.error_cache[snet][sta] = {}

        try:
            len(self.error_cache[snet][sta][table])
        except Exception:
            self.error_cache[snet][sta][table] = []

        self.error_cache[snet][sta][table].append(
            "FOUND DATA ON TABLE BUT NOT A VALID SNET_STA ON DEPLOYMENT"
        )

    def _get_orb_data(self):
        """Retrieve data from the orbs.

        Look into every ORB listed on the parameter file
        and get some information from them.
        1) The clients of the ORB (not using this now)
        2) List of sources.

        Then we track the time of every packet type that
        we see for every station.
        """

        self.logger.debug("Updat ORB cache")

        self.logger.debug(self.orbservers)

        for orbname in self.orbservers:
            if not orbname or not isinstance(orbname, str):
                continue
            self.logger.debug("init ORB %s" % (orbname))

            # Expand the object if needed
            if orbname not in self.orbs:
                self.orbs[orbname] = {}
                self.logger.debug("orb.Orb(%s)" % (orbname))
                self.orbs[orbname]["orb"] = orb.Orb(orbname)

            # Clean all local info related to this ORB
            self.orbs[orbname]["clients"] = {}
            self.orbs[orbname]["sources"] = {}
            self.orbs[orbname]["info"] = {
                "status": "offline",
                "last_check": 0,
            }

            try:
                self.logger.debug("connect to orb(%s)" % orbname)
                self.orbs[orbname]["orb"].connect()
                self.orbs[orbname]["orb"].stashselect(orb.NO_STASH)
            except Exception as e:
                raise metadataException("Cannot connect to ORB: %s %s" % (orbname, e))

            # Extract the information
            self._get_orb_sta_latency(orbname)
            self._get_orb_sta_inp(orbname)

            self.orbs[orbname]["orb"].close()

    def _get_orb_sta_latency(self, name):
        """Get client and source orb latencies."""

        self.logger.debug("Check ORB(%s) sources" % name)

        pkt = Pkt.Packet()

        self.orbs[name]["orb"].select(self.orb_select)
        self.orbs[name]["orb"].reject(".*/pf.*|.*/log|/db/.*|.*/MSTC")

        self.orbs[name]["info"]["status"] = "online"
        self.orbs[name]["info"]["last_check"] = stock.now()

        # get clients
        self.logger.debug("get clients orb(%s)" % name)
        result = self.orbs[name]["orb"].clients()

        for r in result:
            if isinstance(r, float):
                self.orbs[name]["info"]["clients_time"] = r
                self.logger.debug("orb(%s) client time %s" % (name, r))
            else:
                self.orbs[name]["clients"] = r

        # get sources
        self.logger.debug("get sources orb(%s)" % name)
        result = self.orbs[name]["orb"].sources()

        for r in result:
            # Verify if this is a valid field or just the reported time
            if isinstance(r, float):
                self.orbs[name]["info"]["sources_time"] = r
                self.logger.debug("orb(%s) sources time %s" % (name, r))
            else:
                for stash in r:
                    srcname = stash["srcname"]
                    pkt.srcname = Pkt.SrcName(srcname)
                    snet = pkt.srcname.net
                    sta = pkt.srcname.sta

                    # Not sure if this will ever occur
                    if not snet or not sta:
                        continue

                    self.logger.debug("orb(%s) update %s %s" % (name, snet, sta))

                    self._verify_cache(snet, sta, "orb", primary=True)

                    self.cache[snet][sta]["orb"][srcname] = parse_sta_time(
                        stash["slatest_time"]
                    )

                    if "lastpacket" not in self.cache[snet][sta]:
                        self.cache[snet][sta]["lastpacket"] = 0

                    if (
                        self.cache[snet][sta]["lastpacket"]
                        < self.cache[snet][sta]["orb"][srcname]
                    ):
                        self.cache[snet][sta]["lastpacket"] = self.cache[snet][sta][
                            "orb"
                        ][srcname]

    def _get_orb_sta_inp(self, name):

        self.logger.debug("Check ORB(%s) sources" % name)

        pkt = Pkt.Packet()

        self.logger.debug("get pf/st packets from orb(%s)" % name)
        self.orbs[name]["orb"].reject("")
        self.orbs[name]["orb"].select(".*/pf/st")

        # get pf/st packet sources
        sources = self.orbs[name]["orb"].sources()
        self.logger.debug(sources)

        # Make list of all valid packet names
        valid_packets = []
        for r in sources:
            if isinstance(r, float):
                continue
            for stash in r:
                srcname = stash["srcname"]
                pkt.srcname = Pkt.SrcName(srcname)
                self.logger.debug("sources => %s" % srcname)
                valid_packets.append(srcname)

        # loop over each source
        for pckname in valid_packets:
            # get pf/st packets
            self.logger.debug("get %s packets from orb(%s)" % (pckname, name))
            self.orbs[name]["orb"].select(pckname)
            attempts = 0
            while True:
                attempts += 1
                self.logger.debug(
                    "get ORBNEWEST packet from orb(%s) for %s" % (name, pckname)
                )
                pktid, srcname, pkttime, pktbuf = self.orbs[name]["orb"].get(
                    orb.ORBNEWEST
                )
                self.logger.debug("pktid(%s)" % pktid)
                # Verify pckt id
                if int(float(pktid)) > 0:
                    break
                if attempts > 10:
                    break

            # Don't have anything useful here
            if attempts > 10:
                continue

            # Try to extract name of packet. Default to the orb provided name.
            pkt = Pkt.Packet(srcname, pkttime, pktbuf)
            srcname = pkt.srcname if pkt.srcname else srcname
            self.logger.debug("srcname: %s" % srcname)

            if "dls" in pkt.pf.keys():
                for netsta in pkt.pf["dls"]:
                    self.logger.debug("Packet: extract: %s" % netsta)
                    try:
                        temp = netsta.split("_")
                        snet = temp[0]
                        sta = temp[1]
                    except Exception:
                        self.logger.debug("ERROR ON PF/ST parse: netsta=[%s] " % netsta)
                        continue

                    self._verify_cache(snet, sta, "orbcomms", primary=True)

                    if "inp" not in pkt.pf["dls"][netsta]:
                        self.logger.debug("NO inp value in pkt: %s" % pckname)
                        continue

                    self.cache[snet][sta]["orbcomms"] = {
                        "id": pktid,
                        "name": pckname,
                        "time": pkttime,
                        "inp": pkt.pf["dls"][netsta]["inp"],
                    }

    def _get_db_data(self):
        """Load the data from the tables."""
        self.logger.debug("_get_db_data(%s)" % (self.db))

        self.cache = {}
        self.error_cache = {}

        if test_yesno(self.deployment):
            self._get_deployment_list()
        else:
            self._get_main_list()

        if test_yesno(self.digitizer):
            self._get_digitizer()
        if test_yesno(self.sensor):
            self._get_sensor()
        if test_yesno(self.comm):
            self._get_comm()
        if test_yesno(self.balers):
            self._get_stabaler()
        if test_yesno(self.windturbine):
            self._get_windturbine()
        if test_yesno(self.adoption):
            self._get_adoption()
        if test_yesno(self.tags):
            self._set_tags()
        if self.perf_db:
            self._get_chanperf()

    def _get_chanperf(self):

        self.logger.debug("_get_chanperf()")

        today = stock.str2epoch(str(stock.yearday(stock.now())))
        lastmonth = today - (86400 * int(self.perf_days_back))

        fields = ["snet", "sta", "chan", "time", "perf"]
        steps = [
            "dbopen chanperf",
            "dbjoin -o snetsta",
            "dbsubset time >= %s" % lastmonth,
        ]

        if self.perf_subset:
            steps.append("dbsubset %s" % self.perf_subset)

        for v in extract_from_db(self.perf_db, steps, fields, self.db_subset):
            snet = v.pop("snet")
            sta = v.pop("sta")
            chan = v.pop("chan")

            self.logger.debug("_get_chanperf(%s_%s)" % (snet, sta))

            if self._verify_cache(snet, sta, "chanperf"):
                try:
                    if len(self.cache[snet][sta]["chanperf"][chan]) < 1:
                        raise
                except Exception:
                    self.cache[snet][sta]["chanperf"][chan] = {}

                # v['time'] = readable_time( v['time'], '%Y-%m-%d' )
                v["time"] = int(v["time"])
                self.cache[snet][sta]["chanperf"][chan][v["time"]] = v["perf"]

    def _get_adoption(self):

        self.logger.debug("_get_adoption()")

        steps = ["dbopen adoption"]

        fields = ["sta", "snet", "time", "newsnet", "newsta", "atype", "auth"]

        for v in extract_from_db(self.db, steps, fields, self.db_subset):
            sta = v.pop("sta")
            snet = v.pop("snet")
            v["time"] = parse_sta_time(v["time"])

            self.logger.debug("_get_adoption(%s_%s)" % (snet, sta))

            if self._verify_cache(snet, sta, "adoption"):
                try:
                    if len(self.cache[snet][sta]["adoption"]) < 1:
                        raise
                except Exception:
                    self.cache[snet][sta]["adoption"] = []

                self.cache[snet][sta]["adoption"].append(v)

            else:
                self._not_in_db(snet, sta, "adoption")

    def _get_sensor(self):

        self.logger.debug("_get_sensor()")

        tempcache = AutoVivification()

        # We need dlsensor information for this.
        if not self.dlsensor_cache:
            self.dlsensor_cache = dlsensor_cache()
            self._load_dlsensor_table()

        steps = [
            "dbopen stage",
            "dbsubset gtype !~ /digitizer|Q330.*|FIR.*/",
            "dbjoin -o calibration sta chan stage.time#calibration.time::calibration.endtime",
            "dbjoin -o snetsta",
            "dbsort sta chan stage.time stage.endtime",
        ]

        fields = [
            "snet",
            "sta",
            "chan",
            "calibration.samprate",
            "segtype",
            "calib",
            "ssident",
            "snname",
            "dlname",
            "gtype",
            "stage.time",
            "calibration.insname",
            "calibration.units",
            "stage.endtime",
        ]

        for db_v in extract_from_db(self.db, steps, fields, self.db_subset):
            sta = db_v["sta"]
            snet = db_v["snet"]
            ssident = db_v["ssident"]
            snname = db_v["snname"]
            dlname = db_v["dlname"]
            gtype = db_v["gtype"]
            chan = db_v["chan"]
            samprate = db_v["calibration.samprate"]
            units = db_v["calibration.units"]
            segtype = db_v["segtype"]
            calib = db_v["calib"]
            insname = db_v["calibration.insname"]

            time = parse_sta_time(db_v["stage.time"])
            endtime = parse_sta_time(db_v["stage.endtime"])
            twin = "%s.%s" % (time, endtime)

            self.logger.debug("_get_sensor(%s_%s)" % (snet, sta))

            if re.match(r"\@.+", snname):
                snname = dlname

            if re.match(r"q330.*", snname):
                snname = "soh-internal"

            if re.match(r"\qep_soh_only", snname):
                snname = "qep"

            # Translate "sensor" to a value from the dlsensor table
            # if gtype == 'sensor':
            #    #gtype = self.dlsensor_cache.sensor(ssident,time)
            #    gtype = snname

            # if snname == '-':
            #    snname = gtype
            if snname == "-":
                try:
                    snname = (
                        re.split("/|,|=|", insname)[0]
                        .lower()
                        .replace(".", "_")
                        .replace(" ", "_")
                    )
                except Exception:
                    if dlname != "-":
                        snname = dlname
                    else:
                        snname = gtype

            # self.logger.debug( "gtype:%s snname:%s)" % (gtype,snname) )
            self.logger.debug("snname:%s)" % (snname))

            if self._verify_cache(snet, sta, "sensor"):
                # Saving to temp var to limit dups
                tempcache[snet][sta][snname][ssident][twin][chan] = insname

                # Saving channels and calibs to new list
                try:
                    len(self.cache[snet][sta]["channels"][chan])
                except Exception:
                    try:
                        len(self.cache[snet][sta]["channels"])
                    except Exception:
                        self.cache[snet][sta]["channels"] = {}
                    self.cache[snet][sta]["channels"][chan] = []

                self.cache[snet][sta]["channels"][chan].append(
                    {
                        "time": time,
                        "endtime": endtime,
                        "samprate": samprate,
                        "segtype": segtype,
                        "units": units,
                        "calib": calib,
                    }
                )

            else:
                self._not_in_db(snet, sta, "sensor")

        for snet in tempcache:
            for sta in tempcache[snet]:

                activeseismic = {}
                activesensors = {}
                for snname in tempcache[snet][sta]:
                    for ssident in tempcache[snet][sta][snname]:
                        for twin in tempcache[snet][sta][snname][ssident]:

                            # Option to add variable with channel list
                            tempchans = []
                            tempname = "-"
                            for chan in tempcache[snet][sta][snname][ssident][twin]:
                                tempchans.append(chan)
                                tempname = tempcache[snet][sta][snname][ssident][twin][
                                    chan
                                ]

                            start, end = twin.split(".")
                            if end == "-":
                                activesensors[snname] = 1
                                try:
                                    if snname in self.seismic_sensors:
                                        activeseismic[self.seismic_sensors[snname]] = 1
                                except Exception:
                                    activeseismic["error"] = 1

                            try:
                                len(self.cache[snet][sta]["sensor"][snname][ssident])
                            except Exception:
                                self.cache[snet][sta]["sensor"][snname][ssident] = []

                            self.cache[snet][sta]["sensor"][snname][ssident].append(
                                {
                                    "time": start,
                                    "endtime": end,
                                    "channels": tempchans,
                                    "insname": tempname,
                                }
                            )
                if len(activesensors) > 0:
                    self.cache[snet][sta]["activesensors"] = activesensors.keys()
                if len(activeseismic) > 0:
                    self.cache[snet][sta]["activeseismic"] = activeseismic.keys()

    def _load_dlsensor_table(self):
        self.logger.debug("_load_dlsensor_table()")

        steps = ["dbopen dlsensor"]

        fields = [
            "dlmodel",
            "dlident",
            "chident",
            "time",
            "endtime",
            "snmodel",
            "snident",
        ]

        for k in extract_from_db(self.db, steps, fields):
            self.dlsensor_cache.add(
                k["dlident"],
                k["dlmodel"],
                k["snident"],
                k["snmodel"],
                k["time"],
                k["endtime"],
            )

    def _get_windturbine(self):
        self.logger.debug("_get_windturbine()")

        steps = ["dbopen windturbine", "dbjoin -o snetsta", "dbsort sta time"]

        fields = ["snet", "sta", "time", "endtime", "manu", "model", "wtsn", "comment"]

        for v in extract_from_db(self.db, steps, fields):
            snet = v.pop("snet")
            sta = v.pop("sta")

            v["time"] = parse_sta_time(v["time"])
            v["endtime"] = parse_sta_time(v["endtime"])

            self.logger.debug("_get_windturbine(%s_%s)" % (snet, sta))

            if self._verify_cache(snet, sta, "windturbine"):
                try:
                    if len(self.cache[snet][sta]["windturbine"]) < 1:
                        raise
                except Exception:
                    self.cache[snet][sta]["windturbine"] = []

                self.cache[snet][sta]["windturbine"].append(v)

            else:
                # Ignore this error
                # self._not_in_db(snet, sta, 'stabaler')
                pass

    def _get_stabaler(self):
        self.logger.debug("_get_stabaler()")

        steps = ["dbopen stabaler", "dbsort net sta time"]

        fields = [
            "net",
            "sta",
            "time",
            "inp",
            "last_reg",
            "last_reboot",
            "model",
            "nreg24",
            "nreboot",
            "firm",
            "ssident",
        ]

        for v in extract_from_db(self.db, steps, fields):
            snet = v.pop("net")
            sta = v.pop("sta")

            v["time"] = parse_sta_time(v["time"])
            v["last_reg"] = parse_sta_time(v["last_reg"])
            v["last_reboot"] = parse_sta_time(v["last_reboot"])

            self.logger.debug("_get_stabaler(%s_%s)" % (snet, sta))

            if self._verify_cache(snet, sta, "stabaler"):
                try:
                    if len(self.cache[snet][sta]["stabaler"]) < 1:
                        raise
                except Exception:
                    self.cache[snet][sta]["stabaler"] = []

                self.cache[snet][sta]["stabaler"].append(v)

            else:
                # We cannot run with self.db_subset. Ignore this error
                # self._not_in_db(snet, sta, 'stabaler')
                pass

    def _get_comm(self):

        self.logger.debug("_get_comm()")

        steps = ["dbopen comm", "dbjoin -o snetsta"]

        fields = [
            "sta",
            "snet",
            "time",
            "endtime",
            "commtype",
            "provider",
            "power",
            "dutycycle",
        ]

        for v in extract_from_db(self.db, steps, fields, self.db_subset):
            sta = v.pop("sta")
            snet = v.pop("snet")
            v["time"] = parse_sta_time(v["time"])
            v["endtime"] = parse_sta_time(v["endtime"])

            self.logger.debug("_get_comm(%s_%s)" % (snet, sta))

            if self._verify_cache(snet, sta, "comm"):
                try:
                    if len(self.cache[snet][sta]["comm"]) < 1:
                        raise
                except Exception:
                    self.cache[snet][sta]["comm"] = []

                self.cache[snet][sta]["comm"].append(v)

                if v["endtime"] == "-":
                    self.cache[snet][sta]["power"] = v["power"]
                    self.cache[snet][sta]["dutycycle"] = v["dutycycle"]
                    self.cache[snet][sta]["activecommtype"] = v["commtype"]
                    self.cache[snet][sta]["activeprovider"] = v["provider"]

            else:
                self._not_in_db(snet, sta, "comm")

    def _get_digitizer(self):

        self.logger.debug("get_digitizer()")

        # We need dlsensor information for this.
        if not self.dlsensor_cache:
            self.dlsensor_cache = dlsensor_cache()
            self._load_dlsensor_table()

        steps = [
            "dbopen stage",
            "dbsubset gtype =~ /digitizer/ && iunits =~ /V/ && ounits =~ /COUNT|COUNTS|counts/",
            "dbjoin calibration sta chan time",
            "dbsort -u sta time endtime ssident dlname",
            "dbjoin -o snetsta",
        ]

        fields = [
            "snet",
            "sta",
            "ssident",
            "gtype",
            "time",
            "endtime",
            "insname",
            "dlname",
        ]

        activedigitizers = {}

        for v in extract_from_db(self.db, steps, fields, self.db_subset):
            sta = v.pop("sta")
            snet = v.pop("snet")
            fullname = "%s_%s" % (snet, sta)
            ssident = v.pop("ssident")
            gtype = v.pop("gtype")
            dlname = v.pop("dlname")
            v["time"] = parse_sta_time(v["time"])
            v["endtime"] = parse_sta_time(v["endtime"])
            time = v["time"]
            endtime = v["endtime"]

            if re.match(r"\qep_.+", dlname):
                dlname = "qep"

            if dlname == "-":
                dlname = gtype

            self.logger.debug(
                "_get_digitizer(%s_%s, %s, %s)" % (snet, sta, time, endtime)
            )

            # Translate "digitizer" to a value from the dlsensor table
            # if ssident:
            #    gtype = self.dlsensor_cache.digitizer(ssident,time)

            # self.logger.debug( "gtype:%s ssident:%s)" % (gtype,ssident) )
            self.logger.debug("dlname:%s ssident:%s)" % (dlname, ssident))

            # Track active values
            if endtime == "-":
                try:
                    len(activedigitizers[fullname])
                except Exception:
                    activedigitizers[fullname] = {}

                # activedigitizers[fullname][gtype] = 1
                activedigitizers[fullname][dlname] = 1

            if self._verify_cache(snet, sta, "digitizer"):

                try:
                    # len(self.cache[snet][sta]['digitizer'][gtype][ssident])
                    len(self.cache[snet][sta]["digitizer"][dlname][ssident])
                except Exception:
                    # self.cache[snet][sta]['digitizer'][gtype][ssident] = []
                    self.cache[snet][sta]["digitizer"][dlname][ssident] = []

                # self.cache[snet][sta]['digitizer'][gtype][ssident].append( v )
                self.cache[snet][sta]["digitizer"][dlname][ssident].append(v)

            else:
                self._not_in_db(snet, sta, "digitizer")

        for name in activedigitizers.iterkeys():
            temp = name.split("_")
            snet = temp[0]
            sta = temp[1]
            try:
                self.cache[snet][sta]["activedigitizers"] = activedigitizers[
                    name
                ].keys()
            except Exception:
                self._not_in_db(snet, sta, "activedigitizers")

    def _get_main_list(self):

        self.logger.debug("_get_main_list()")

        # Default is with no snetsta
        steps = ["dbopen site", "dbsort sta"]
        fields = [
            "sta",
            "ondate",
            "offdate",
            "lat",
            "lon",
            "elev",
            "staname",
            "statype",
            "dnorth",
            "deast",
        ]

        # Test if we have snetsta table
        with datascope.closing(datascope.dbopen(self.db, "r")) as db:
            dbtable = db.lookup(table="snetsta")
            if dbtable.query(datascope.dbTABLE_PRESENT):
                steps = ["dbopen site", "dbjoin -o snetsta", "dbsort sta"]
                fields = [
                    "snet",
                    "sta",
                    "ondate",
                    "offdate",
                    "lat",
                    "lon",
                    "elev",
                    "staname",
                    "statype",
                    "dnorth",
                    "deast",
                ]

        for v in extract_from_db(self.db, steps, fields, self.db_subset):
            sta = v["sta"]
            if "snet" in v:
                snet = v["snet"]
            else:
                snet = "-"

            self.logger.debug("_get_main_list(%s_%s)" % (snet, sta))

            # Fix values of time and endtime
            v["time"] = parse_sta_date(v["ondate"], epoch=True)
            v["endtime"] = parse_sta_date(v["offdate"], epoch=True)

            # Readable times
            v["strtime"] = readable_time(v["time"], self.timeformat, self.timezone)
            v["strendtime"] = readable_time(
                v["endtime"], self.timeformat, self.timezone
            )

            # Need lat and lon with 2 decimals only
            v["latlat"] = v["lat"]
            v["lonlon"] = v["lon"]
            v["lat"] = round(v["lat"], 2)
            v["lon"] = round(v["lon"], 2)

            self._verify_cache(snet, sta, primary=True)

            self.cache[snet][sta] = v

    def _get_deployment_list(self):

        self.logger.debug("_get_deployment_list()")

        steps = ["dbopen deployment", "dbjoin -o site"]

        fields = [
            "vnet",
            "snet",
            "sta",
            "time",
            "endtime",
            "equip_install",
            "equip_remove",
            "cert_time",
            "decert_time",
            "pdcc",
            "lat",
            "lon",
            "elev",
            "staname",
            "statype",
            "ondate",
            "offdate",
        ]

        for v in extract_from_db(self.db, steps, fields, self.db_subset):
            sta = v["sta"]
            snet = v["snet"]

            self.logger.debug("_get_deployment_list(%s_%s)" % (snet, sta))

            # fix values of date
            for f in ["ondate", "offdate"]:
                v[f] = parse_sta_date(v[f])

            # fix values of time
            for f in [
                "time",
                "endtime",
                "equip_install",
                "equip_remove",
                "cert_time",
                "decert_time",
            ]:
                v[f] = parse_sta_time(v[f])

            # Readable times
            v["strtime"] = readable_time(v["time"], self.timeformat, self.timezone)
            v["strendtime"] = readable_time(
                v["endtime"], self.timeformat, self.timezone
            )

            # Need lat and lon with 2 decimals only
            v["latlat"] = v["lat"]
            v["lonlon"] = v["lon"]
            v["lat"] = round(v["lat"], 2)
            v["lon"] = round(v["lon"], 2)

            self._verify_cache(snet, sta, primary=True)

            self.cache[snet][sta] = v

    def _set_tags(self):
        """Add quick identifier based on geo region.

        TA array expands into multiple geographical regions.
        We need to add some quick identifier to the data blob.
        """
        for snet in self.cache:
            if not snet:
                continue
            for sta in self.cache[snet]:
                if not sta:
                    continue

                self.logger.debug("_set_tags(%s_%s)" % (snet, sta))

                if self._verify_cache(snet, sta, "tags"):
                    try:
                        if len(self.cache[snet][sta]["tags"]) < 1:
                            raise
                    except Exception:
                        self.cache[snet][sta]["tags"] = []

                    # Tags for sites on the YUKON area
                    if (
                        self.cache[snet][sta]["lat"] > 58.0
                        and self.cache[snet][sta]["lon"] > -147.0
                    ):
                        self.cache[snet][sta]["tags"].append("yukon")

                    # Tags for TA **ONLY**
                    if snet == "TA":
                        self.cache[snet][sta]["tags"].append("usarray")

                        if self.cache[snet][sta]["vnet"] == "_CASCADIA-TA":
                            self.cache[snet][sta]["tags"].append("cascadia")

                        if self.cache[snet][sta]["lat"] > 50:
                            self.cache[snet][sta]["tags"].append("alaska")
                        else:
                            self.cache[snet][sta]["tags"].append("low48")

                        # Need to identify active BGAN connections
                        bgantag = "non-bgan"
                        try:
                            for c in self.cache[snet][sta]["comm"]:
                                # active?
                                if c["endtime"] == "-":
                                    # BGAN?
                                    if c["commtype"] == "BGAN":
                                        # matched
                                        bgantag = "bgan"
                        except Exception:
                            pass

                        # Add BGAN results
                        self.cache[snet][sta]["tags"].append(bgantag)

                    # Activity tag
                    if (
                        self.cache[snet][sta]["time"] == "-"
                        or self.cache[snet][sta]["time"] > stock.now()
                    ):
                        self.cache[snet][sta]["tags"].append("prelim")
                    elif (
                        self.cache[snet][sta]["endtime"] == "-"
                        or self.cache[snet][sta]["endtime"] > stock.now()
                    ):
                        self.cache[snet][sta]["tags"].append("active")
                    else:
                        self.cache[snet][sta]["tags"].append("decommissioned")

                    # Adoption tag
                    if "adoption" in self.cache[snet][sta]:
                        self.cache[snet][sta]["tags"].append("adopted")

                    # Certification tag
                    if "cert_time" in self.cache[snet][sta]:
                        if (
                            self.cache[snet][sta]["cert_time"] == "-"
                            or self.cache[snet][sta]["cert_time"] > stock.now()
                        ):
                            self.cache[snet][sta]["tags"].append("uncertified")
                        elif (
                            self.cache[snet][sta]["decert_time"] == "-"
                            or self.cache[snet][sta]["decert_time"] < stock.now()
                        ):
                            self.cache[snet][sta]["tags"].append("certified")
                        else:
                            self.cache[snet][sta]["tags"].append("decertified")

    def _clean_cache(self, cache):
        """Reinitilize the collection."""
        results = []

        for snet in cache:
            if not snet:
                continue
            for sta in cache[snet]:
                if not sta:
                    continue
                # Stringify the dict. This will avoid loosing decimal places
                oldEntry = json.loads(json.dumps(cache[snet][sta]))

                # Generic id for this entry
                oldEntry["id"] = snet + "_" + sta
                oldEntry["dlname"] = snet + "_" + sta

                if "snet" not in oldEntry:
                    oldEntry["snet"] = snet
                if "sta" not in oldEntry:
                    oldEntry["sta"] = sta

                # add entry for autoflush index and IM checks
                oldEntry["lddate"] = datetime.fromtimestamp(stock.now())
                results.append(oldEntry)

        return results
