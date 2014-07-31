"""
Network-wide mass recenters to JSON run via cron daily
"""

import logging
import json
import gzip
import string
import tempfile
from optparse import OptionParser
from collections import defaultdict
from pprint import pprint, pformat
from time import time, mktime
from datetime import datetime
from dateutil.relativedelta import relativedelta

from antelope import datascope
from antelope import stock
from antelope import elog

def deep_auto_convert(data):
    """
    call stock.auto_convert on all entries in a dict or array.

    the stock.ParameterFile.get() routine in the Antelope 5.3+ python bindings
    calls stock.auto_convert, but that routine doesn't recursively auto-convert
    all of the entries in a pf Arr object or a Tbl object.
    """

    if type(data) is dict:
        for i in data.keys():
            data[i] = deep_auto_convert(data[i])
    elif type(data) is list:
        for i in range(len(data)):
            data[i] = deep_auto_convert(data[i])
    elif type(data) is str:
        data = stock.auto_convert(data)
    else:
        pass # no-op on unrecognized items

    return data

class ElogHandler(logging.Handler):
    """
    A handler class which sends logging records to Antelope's
    elog routines.
    """

    def __init__(self, argv=sys.argv):
        """
        Initialize a handler.

        If argv is specified, antelope.elog.init is called with argv.
        """

        logging.Handler.__init__(self)

        elog.init(argv)

    def emit(self, record):
        """
        Emit a record.

        The record is handed off to the various elog routines based on
        the record's priority.
        """

        msg = self.format(record)

        if record.levelno == logging.DEBUG:
            elog.debug(msg)
        elif record.levelno == logging.INFO:
            elog.notify(msg)
        elif record.levelno == logging.WARNING:
            elog.alert(msg)
        elif record.levelno == logging.ERROR:
            elog.warning(msg)
        else: # logging.CRITICAL and others
            elog.complain(msg)

class MassRecenters2JSON:
    def __init__(self, options):

        self.options = options
        self.logger = logging.getLogger(self.options.loggername)

        self.options.tmpoutfile = '%s+' % self.options.outfile

        # Load parameter file
        self.options.pf = stock.pfupdate(self.options.pfname)
        self.options.pf.auto_convert = True # doesn't seem to have an effect inside of dicts

        # stock.paramterfile.get loads items into a dict, which is not ordered
        # so we have the _SCALE entries in the parameter file to work around this
        self.options.groupings      = self.options.pf.get('MASSRECENTERS_ARR')
        self.options.grouporder     = self.options.pf.get('MASSRECENTERS_SCALE')
        self.options.periods        = self.options.pf.get('MASSRECENTERS_PERIODS')
        self.options.periodorder    = self.options.pf.get('MASSRECENTERS_PERIODS_SCALE')

        # BUG WORKAROUND: stock.pf.get isn't calling stock.auto_convert on
        # entries in Arrs, so we have to perform the deep conversion ourselves.
        self.options.groupings = deep_auto_convert(self.options.groupings)
        self.options.periods   = deep_auto_convert(self.options.periods)

    def get_sta_dict(self):
        """Populate station and null fields dictionaries """

        self.logger.info('Create the stations dictionary')

        self.stations = defaultdict(dict)
        self.nulls    = defaultdict(dict)

        db = datascope.dbopen(self.options.database, 'r')
        with datascope.closing(db):

            deployment = db.lookup(table='deployment')

            dbview = deployment.join('site', outer=True)
            with datascope.freeing(dbview):

                # Populate null values table
                for tblfield in dbview.query('dbTABLE_FIELDS'):

                    nullrecord=dbview.lookup(field=tblfield, record='dbNULL')
                    self.nulls[tblfield] = nullrecord.getv(tblfield)[0]

                ss='snet =~/%s/' % self.options.snet_match
                self.logger.debug("Subsetting with: "+ ss)
                with datascope.freeing(dbview.subset(ss)) as dbmysnets:

                    nrec=dbmysnets.query('dbRECORD_COUNT')
                    self.logger.debug('Nrec after ss: %d' % nrec)
                    for i in range(nrec):

                        dbmysnets.record = i

                        (snet,
                         sta,
                         time,
                         endtime,
                         lat,
                         lon,
                         elev,
                         staname) = dbmysnets.getv('snet',
                                                   'sta',
                                                   'time',
                                                   'endtime',
                                                   'lat',
                                                   'lon',
                                                   'elev',
                                                   'staname')

                        dlname = '%s_%s' % (snet, sta)

                        if dlname not in self.stations:
                            self.stations[dlname]={}

                        self.stations[dlname]['time'] = stock.epoch2str(
                            time, '%Y-%m-%d %H:%M:%D')

                        self.stations[dlname]['endtime'] = endtime

                        if endtime == self.nulls['endtime']:

                            self.stations[dlname]['endtime_readable'] = \
                                    '&mdash;'
                            self.stations[dlname]['status'] = 'online'

                        else:

                            self.stations[dlname]['endtime_readable'] = \
                                    stock.epoch2str(endtime,
                                                    '%Y-%m-%d %H:%M:%S')
                            self.stations[dlname]['status'] = 'offline'

                        self.stations[dlname]['lat'] = lat
                        self.stations[dlname]['lon'] = lon
                        self.stations[dlname]['elev'] = elev
                        self.stations[dlname]['staname'] = staname

        self.logger.debug(pformat(self.stations))

    def get_dlname_events(self):
        """Get all mass recenter events associated with a dlname"""

        self.logger.info('Generate the dlevents dictionary')

        self.dlevents = {}

        #dlev_db = datascope.dbopen(self.options.database, 'r')
        with datascope.closing(
            datascope.dbopen(self.options.database, 'r')
        ) as dlev_db:
            dlevent = dlev_db.lookup(table='dlevent')

            #dlev_db.subset('dlevtype =~ /^massrecenter.*/')
            ss = 'dlevtype =~ /^massrecenter.*/'
            with datascope.freeing( dlevent.subset(ss) )as mru:
                #dlev_db.sort(('dlname','time'))
                with datascope.freeing( mru.sort(['dlname','time']) ) as mrs:
                    dlev_grp = mrs.group('dlname')
                    with datascope.freeing(dlev_grp):

                        for i in range(dlev_grp.query('dbRECORD_COUNT')):
                            dlev_grp.record = i
                            (dlname, [ db, view, end_rec, start_rec ]) = \
                                    dlev_grp.getv('dlname', 'bundle')

                            if (dlname not in self.dlevents) :
                                self.dlevents[dlname] = []

                            for j in range(start_rec, end_rec):
                                mrs.record = j
                                (dlname, time) = mrs.getv('dlname', 'time')
                                self.dlevents[dlname].append(int(time))

            self.logger.info('Historical massrecenters: \n' + pformat(self.dlevents))

    def process_dlevents(self):
        """Iterate over stations and append all the mass recenters """

        self.logger.info('Add dlevents to the stations dictionary')

        for i in sorted(self.stations.iterkeys()):

            if i in self.dlevents:

                self.stations[i].update(dlevs=self.dlevents[i])
                chron_color = self.chronology_color_calc(i)
                self.stations[i].update(dlevs_chronology=chron_color)
                total = len(self.dlevents[i])

            else:

                self.logger.info('\t\tStation %s: no massrecenters' % i)
                self.stations[i].update(dlevs=[])
                self.stations[i].update(dlevs_chronology="FFFFFF")
                total = 0

            self.stations[i].update(dlevstotal=total)

            # Scale color
            for j in self.options.groupings.keys():

                if self.options.groupings[j]['max'] == -1:
                    maximum = 99999999
                else:
                    maximum = self.options.groupings[j]['max']

                if self.options.groupings[j]['min'] == -1:
                    if total == maximum:
                        color = self.options.groupings[j]['hexadecimal']
                else:
                    if total <= maximum and total >= self.options.groupings[j]['min']:
                        color = self.options.groupings[j]['hexadecimal']

            if color:
                self.stations[i].update(dlevscolor=color)
            else:
                self.logger.warning('\tNo color for dlname %s' % self.stations[i])

        self.logger.debug('Pretty print for dlname TA_034A for debugging: ' +
                      pformat(self.stations['TA_034A']))

    def chronology_color_calc(self, stacode):
        """Calculate the hexadecimal of the most recent mass recenter at this
        station"""

        station_info = self.stations[stacode]
        per_sta_dlevents = self.dlevents[stacode]

        if station_info['endtime'] == self.nulls['endtime']:

            self.logger.info("Station '%s' is online" % stacode)
            stanow = datetime.now()

        else:

            self.logger.info("Station '%s' is offline" % stacode)
            stanow = datetime.fromtimestamp(station_info['endtime'])

        # Calc times for offline stations
        six_hrs = stanow + relativedelta(hours=-6)
        twelve_hrs = stanow + relativedelta(hours=-12)
        day = stanow + relativedelta(days=-1)
        week = stanow + relativedelta(weeks=-1)
        month = stanow + relativedelta(months=-1)
        six_months = stanow + relativedelta(months=-6)
        one_year = stanow + relativedelta(years=-1)
        two_year = stanow + relativedelta(years=-2)
        three_year = stanow + relativedelta(years=-3)
        three_year_plus = stanow + relativedelta(years=-20) # Twenty years default

        periods = {
            'six_hrs': {
                'epoch':mktime(six_hrs.timetuple()),
                'hexadecimal': self.options.periods['six_hrs']['hexadecimal']
            },
            'twelve_hrs': {
                'epoch': mktime(twelve_hrs.timetuple()),
                'hexadecimal': self.options.periods['twelve_hrs']['hexadecimal']
            },
            'day': {
                'epoch': mktime(day.timetuple()),
                'hexadecimal': self.options.periods['day']['hexadecimal']
            },
            'week': {
                'epoch': mktime(week.timetuple()),
                'hexadecimal': self.options.periods['week']['hexadecimal']
            },
            'month': {
                'epoch': mktime(month.timetuple()),
                'hexadecimal': self.options.periods['month']['hexadecimal']
            },
            'six_months': {
                'epoch': mktime(six_months.timetuple()),
                'hexadecimal': self.options.periods['six_months']['hexadecimal']
            },
            'year': {
                'epoch': mktime(one_year.timetuple()),
                'hexadecimal': self.options.periods['year']['hexadecimal']
            },
            'two_year': {
                'epoch': mktime(two_year.timetuple()),
                'hexadecimal': self.options.periods['two_year']['hexadecimal']
            },
            'three_year': {
                'epoch': mktime(three_year.timetuple()),
                'hexadecimal': self.options.periods['three_year']['hexadecimal']
            },
            'three_year_plus': {
                'epoch': mktime(three_year_plus.timetuple()),
                'hexadecimal': self.options.periods['three_year_plus']['hexadecimal']
            }
        }

        # default is never
        hexadecimal = self.options.periods['never']['hexadecimal']

        if len(per_sta_dlevents) > 0:
            for p in self.options.periods.keys():
                # TODO: handle missing keys in periods
                if p != 'never':
                    if per_sta_dlevents[-1] > periods[p]['epoch']:
                        hexadecimal = periods[p]['hexadecimal']
                        break
                else:
                    pass

        return hexadecimal

    def create_metadata(self):
        """Create metadata dictionary """

        self.metadata = defaultdict(dict)
        self.metadata['last_modified_readable'] = stock.epoch2str(int(time()), "%Y-%m-%d %H:%M:%S")
        self.metadata['last_modified'] = int(time())
        self.metadata['caption'] = 'Total number of mass recenters'
        self.metadata['caption_alt'] = 'Most recent mass recenter time'
        self.logger.debug(pformat(self.metadata))

    def create_scale(self):
        """
        Create scale array

        Convert the dict to an array using the order specified in the parameter
        file

        Hopefully this will also deep-convert the values inside the dict, since
        just grabbing the dict itself leaves everything inside of the pf Arr as
        strings
        """

        scale = []
        for i in self.options.grouporder:
            scale.append(self.options.groupings[i])

        self.logger.debug(pformat(scale))

        return scale

    def create_chronology_scale(self):
        """
        Create the chronology scale array

        Use the order specified in the parameter file. Reading each item in the
        pf Arr individually rather than grabbing the whole Arr as a dict
        hopefully will force auto-conversion of each value.
        """

        chron_scale = []
        periodorder = self.options.periodorder
        if 'never' not in self.options.periodorder:
            periodorder.append('never')

        for i in self.options.periodorder:
            chron_scale.append({
                'value'         : self.options.periods[i]['value'],
                'hexadecimal'   : self.options.periods[i]['hexadecimal']},
            )

        self.logger.debug(pformat(chron_scale))
        return chron_scale

    def process(self):
        """ Process the specified database """

        self.logger.info('Process network-wide mass recenters')
        self.get_sta_dict()
        self.get_dlname_events()
        self.process_dlevents()

    def serialize(self):
        """ Create a datastructure suitable for json dumpage """

        # Run this every time for the freshest in timestamping
        self.create_metadata()

        mycoolobj={
            'metadata':     self.metadata,
            'scale':        self.create_scale(),
            'chron_scale':  self.create_chronology_scale(),
            'stations':     self.stations,
        }

        return mycoolobj

    def jsondumps(self):
        return json.dumps(self.serialize(), sort_keys=True, indent=2)

    def jsondumpf(self):
        """ dump JSON representation of object to the file specified in
        self.options.outfile

        Does an atomic update - the file is initially written out to
        self.options.tempoutfile
        """
        self.logger.info("Dump JSON file '%s'" % self.options.outfile)
        with open(self.options.tmpoutfile, 'w') as f:
            json.dump(self.serialize(), f, sort_keys=True, indent=2)
            f.flush()

        # Move the file to replace the older one
        os.rename(self.options.tmpoutfile, self.options.outfile)

def parseargs(argv,logger):
    """
    Parse the command line arguments, and return the resulting options
    """
    usage = "Usage: %prog [options] db outfile.json"
    parser = OptionParser(usage=usage)
    parser.add_option("-v", action="store_true", dest="verbose",
                      help="verbose output", default=False)
    parser.add_option("-x", action="store_true", dest="debug",
                      help="debug output", default=False)
    parser.add_option('-n', action='store', dest='snet_match',
                      help = 'regex to match desired SEED Netcodes',
                      default='.*')
    parser.add_option('-p', action='store', dest='pfname',
                      help = 'parameter file name',
                      default='common')
    (options, args) = parser.parse_args(argv)
    logging.debug(pformat(args))
    if len(args) != 3:
        parser.error("incorrect number of arguments")

    options.database = args[1]
    options.outfile  = args[2]

    return options



def main(argv):

    baseloggername='massrecenters2json'

    logging.basicConfig(level=logging.WARNING)
    logger = logging.getLogger(baseloggername)
    eloghandler = ElogHandler(argv)
    #logger.removeHandler(logger.handlers[0])
    logger.addHandler(eloghandler)
    logger.propagate = False

    options = parseargs(argv,logger)
    options.loggername=baseloggername

    # Set up logging
    loglevel=logging.WARNING

    if options.verbose:
        loglevel=logging.INFO
    if options.debug:
        loglevel=logging.DEBUG

    logger.setLevel(loglevel)


    try:
        mr2json = MassRecenters2JSON(options)
    except stock.PfUpdateError, e:
        logger.critical("Couldn't read the parameter file")
        return 1

    #pprint (mr2json.create_scale())

    try:
        mr2json.process()
    except Exception, e:
        logger.critical('Processing failed')
        return (5)

    #pprint(mr2json.serialize())
    #print(mr2json.jsondumps())

    # Move the file to replace the older one
    try:
        mr2json.jsondumpf()
    except OSError,e:
        logging.critical("OSError: %s when renaming '%s' to '%s'" % (
            e, mr2json.options.tmpoutfile, mr2json.options.outfile))
        return (5)
    except Exception,e:
        logging.critical("Unknown exception occured: " + str(e))
        return (5)

    return 0

if __name__ == '__main__':
    status = main(sys.argv)
    sys.exit(status)
# vim:ft=python
