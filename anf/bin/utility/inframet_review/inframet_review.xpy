"""

inframet_review
    Make report for inframet-only gaps.


@overview
    Perform some analysis on the inframet channels
    for common problems with the instrumentation
    and/or databases.
    Channels associated with the inframet:
        BDF_EP - NCPA
        LDF_EP - NCPA
        BDO_EP - SETRA
        LDO_EP - SETRA
        LDM_EP - MEMS

    Some known problems that the script will track:
        - gaps exclusive to the inframet channels
        - spikes in the time-series  (missing)
        - suden jumps or dips in the time-series  (missing)
        - flat-line of the time-series  (missing)


@future work
    Missing the spikes detection, suden jumps detection
    and flat-line detections.


@authors
    Juan Reyes <reyes@ucsd.edu>
    Jon Tytell <jtytell@ucsd.edu>


@last update
    5/2013


@notes
    + try:except Exceptions can be access like this...

        print 'Exc Instance: %s' % type(e) # the exception instance$
        print 'Exc Args: %s' % e.args      # arguments stored in .args$
        print 'Exc __str__: %s' % e        # __str__ printed directly$


@Database example

vista{reyes}% dbselect -h  /tmp/inframet_gaps.gap
tagname   sta     chan         time    tgap  filled      lddate
-        C39A   LCE_EP    1329303738   45047 -  1330543311
-        C39A   LCO_EP    1329303738   45047 -  1330543311
-        C39A   LDM_EP    1329303710   45047 -  1330543311
-        C39A   LEP_EP    1329303738   45047 -  1330543311
-        C39A   LIM_EP    1329303738   45047 -  1330543311
-        C39A   LKM_EP    1329303710   45047 -  1330543311


"""

#
#  Import libraries
#
import re
from os import remove, path
from sys import stdout, exit
import subprocess
from optparse import OptionParser
import traceback

#
# ANTELOPE
#
try:
    import antelope.stock as stock
    import antelope.datascope as datascope
except Exception, original_error:
    exit_now("Antelope Import Error")


class GapTest():
    """
    Main class for calculating gaps in inframet data
    The tools will run a gap analisys on the inframet
    data and a gap database is produced. Then we review
    the database and we compare the entries with the
    seismic database. If the data is missing in the
    BHZ seismic channel too then we remove the entry
    and we continue the process. We only want to keep
    a table of gaps UNIQUE to the inframet.
    At the end of the process the table is printed
    nicely to screen. The temporary table is left in
    /tmp for manaula processing if needed.

    """

    def __init__(self, pfile, verbosity=False):
        self.verbose = False
        self.debug = False

        if verbosity > 1:
            self.debug = True
        elif verbosity > 0:
            self.verbose = True

        self.pf = pfile
        self.min_gap = 0
        self.gap_threshold = 0
        self.inframet_db = ''
        self.subset_sta = ''
        self.inframet_chan = ''
        self.seismic_db = ''
        self.seismic_chan = ''
        self.temp_db = ''
        self.subset = ''

        self._parse_pf()

    def _parse_pf(self):
        """
        Read the parameter file and assign values to vars
        that will be used throughout the script.

        """

        try:
            pf = stock.pfread(self.pf)
            self.min_gap = pf.get('min_gap')
            self.gap_threshold = pf.get('gap_threshold')
            self.inframet_db = pf.get('inframet_db')
            self.subset_sta = pf.get('subset_sta')
            self.inframet_chan = pf.get('inframet_chan')
            self.seismic_db = pf.get('seismic_db')
            self.seismic_chan = pf.get('seismic_chan')
            self.temp_db = pf.get('temp_db')
        except Exception, original_error:
            exit_now("Antelope PF Import Error")

        if self.debug:
            print 'GapTest(): Parse parameter file %s' % self.pf
            print '\tsubset_sta => %s' % self.subset_sta
            print '\tinframet_db => %s' % self.inframet_db
            print '\tmin_gap => %s' % self.min_gap
            print '\tgap_threshold => %s' % self.gap_threshold
            print '\tinframet_chan => %s' % self.inframet_chan
            print '\tseismic_db => %s' % self.seismic_db
            print '\tseismic_chan => %s' % self.seismic_chan
            print '\ttemp_db => %s' % self.temp_db

    def gaps(self, start, end, subset=False):
        """
        Calculate gaps in database

        NOTE:
        The subsets are from the parameter file. We get values
        from:
            inframet_chan   [..._EP]
            subset_sta      [.*]

        The values are introduced into a regex...
            "sta=~/%s/ && chan=~/%s/" % (subset_sta, inframet_chan)


        The built regex can be ignore if the user sets the
        flag -s at command-line and that will be sent instead
        to datascope for the subset.

        """

        #
        # Build subset from PF or get from command-line
        #
        if subset:
            self.subset = subset
        else:
            self.subset = "sta=~/%s/ && chan=~/%s/" % \
                (self.subset_sta, self.inframet_chan)

        if self.debug:
            print "\tInframetTest(): Using subset [%s]" % self.subset

        #
        # Clean temp files
        #
        for tabel in ['gap', 'chanperf']:
            temp = "%s.%s" % (self.temp_db, tabel)
            if path.exists(temp):
                try:
                    remove(temp)
                except Exception, original_error:
                    exit_now('ERROR: Cannot remove old file [%s]' % temp)

        #
        # Build gap database
        #
        cmd = 'rtoutage -d %s -s "%s" %s %s %s' % \
            (self.temp_db, self.subset, self.inframet_db, start, end)
        if self.debug:
            print "\tInframetTest(): Build gap table [%s]" % cmd
        try:
            subp = subprocess.Popen('%s' % cmd, shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT)
            if self.debug:
                print '======================='
            for line in subp.stdout.readlines():
                if self.debug:
                    print ('\tInframetTest(): rtoutage output: %s' %
                           line.strip())
            if self.debug:
                print '\n'
            subp.wait()
        except Exception, original_error:
            exit_now('ERROR: Cannot run rtoutage [%s]' % cmd)

        #
        # Compare gaps to seismic database
        #
        if self.debug:
            print "\tInframetTest(): Open database: %s" % \
                self.temp_db

        try:
            temp_db = datascope.dbopen(self.temp_db, "r+")
            temp_db = temp_db.lookup(table='gap')

        except Exception, original_error:
            exit_now('ERROR: dbopen() %s\n\n' % self.temp_db)

        try:
            records = temp_db.query(datascope.dbRECORD_COUNT)
        except Exception, original_error:
            records = 0

        if not records:
            print "\nNO GAPS FOUND IN (%s)?!?!\n" % self.inframet_db
            return

        for i in range(records):

            temp_db.record = i
            try:
                (sta, chan, time,
                 tgap) = temp_db.getv('sta', 'chan',
                                      'time', 'tgap')
            except Exception, original_error:
                exit_now('ERROR: Problems with db %s\n\n' % slef.temp_db)

            if self.debug:
                print ('\tInframetTest(): Test gap [%s, %s, %s, %s]' %
                       (sta, chan, stock.strtime(time), tgap))

            if tgap <= self.min_gap:
                temp_db.mark()  # mark database rows for deletion
                if self.verbose:
                    print ('\t%s  %s  %s  %s  %s  too small ' %
                           (sta, chan, stock.strtime(time),
                           stock.strtime(time+tgap), tgap))
                continue

            #
            # Run rtoutage on seismic
            #
            total = 0
            lines = []
            subset = "sta=~/%s/ && chan=~/%s/" % (sta,
                                                  self.seismic_chan)
            cmd = 'rtoutage -SA -s "%s" %s %s %s' % (subset,
                                                     self.seismic_db,
                                                     time, tgap)
            if self.debug:
                print "\tInframetTest(): Test seismic [%s]" % cmd

            try:
                subp = subprocess.Popen('%s' % cmd, shell=True,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT)

                if self.debug:
                    print '\tInframetTest(): ======================='
                for line in subp.stdout.readlines():
                    lines.append(line.strip())
                    if self.debug:
                        print '\tInframetTest(): rtoutage : %s' % line
                subp.wait()

            except Exception, original_error:
                exit_now('ERROR: Cannot run rtoutage [%s]' % cmd)

            # test for sta and channel in string
            for line in lines:
                if self.debug:
                    print '\tInframetTest(): parse line: %s' % line
                words = line.split()
                if sta in words:
                    total = total + float(words[-1])

            if self.debug:
                print '\tInframetTest(): end of regex total:%s' % total

            ratio = int((total/tgap)*100)

            if self.debug:
                print '\tInframetTest(): gaps inframet:[%s] ' % total
                print '\tInframetTest(): gaps seismic:[%s]' % tgap
                print '\tInframetTest(): %s in both' % ratio

            if ratio < self.gap_threshold:
                if self.verbose:
                    print ('\t%s  %s  %s  %s  %s  on inframet ONLY' %
                           (sta, chan, stock.strtime(time),
                           stock.strtime(time+tgap), tgap))
                else:
                    print ('\t%s  %s  start:%s  end:%s  [ %s ]' %
                           (sta, chan, stock.strtime(time),
                           stock.strtime(time+tgap),
                           stock.strtdelta(tgap)))
            else:
                temp_db.mark()  # mark database rows for deletion
                if self.debug:
                    print ('\t%s  %s  %s  %s  %s  on ALL' %
                           (sta, chan, stock.strtime(time),
                           stock.strtime(time+tgap), tgap))

        try:
            temp_db.crunch()  # Delete database rows marked for deletion
            temp_db.close()
        except Exception, original_error:
            pass

        if self.verbose:
            print 'Database with valid gaps in: [%s]' % self.temp_db

        return 0


def configure():
    """
    Configure parameters from command-line and the pf-file

    """

    usage = ("\n\tUsage: \n"
             "\tinframet_review [-vd] [-s subset] "
             "[-p pfname] start end \n"
             "\n"
             "\t\t-d              debug mode\n"
             "\t\t-v              verbose mode \n"
             "\t\t-p file         parameter file \n"
             "\t\t-s regex        subset regex \n\n")

    parser = OptionParser(usage=usage)
    parser.add_option("-v", "--verbose", action="store_true",
                      dest="verbose", default=False,
                      help="verbose output")
    parser.add_option("-d", "--debug", action="store_true",
                      dest="debug", default=False,
                      help="debug application")
    parser.add_option("-p", "--pf", action="store",
                      dest="pf", type="string",
                      help="parameter file path")
    parser.add_option("-s", "--subset", action="store",
                      dest="subset", type="string",
                      help="subset sta:chan")

    (options, args) = parser.parse_args()

    verbosity = 0
    if options.verbose:
        verbosity += 1

    if options.debug:
        verbosity += 2

    #
    # Command-line arguments [start and end times]
    #
    if len(args) != 2:
        exit_now(usage)
    else:
        start = args[0]
        end = args[1]

    #
    # Convert Times
    #
    try:
        start = stock.str2epoch(str(start))
    except Exception, original_error:
        exit_now('ERROR: Cannot convert start(%s) to epoch' % start)

    if re.match(r"^\d+$", end):
        end = int(end)
    else:
        try:
            end = stock.str2epoch(str(end))
        except Exception, original_error:
            exit_now('ERROR: Cannot convert end(%s) to epoch' % start)

    if start < 0 or start > stock.now():
        exit_now('ERROR: Wrong start(%s) time.' % (start))

    if end < 0 or end > stock.now():
        exit_now('ERROR: Wrong end(%s) time.' % (end))

    #
    # Default pf name
    #
    if not options.pf:
        options.pf = 'inframet_review'

    #
    # Get path to pf file
    #
    try:
        options.pf = stock.pffiles(options.pf)[0]
    except Exception, original_error:
        exit_now('ERROR: problem loading pf(%s) class' % options.pf)

    if verbosity > 1:
        print "Parameter file to use [%s]" % options.pf

    return start, end, options.pf, options.subset, verbosity


def main():
    """
    Main script processing

    """
    start, end, pf, subset, verbosity = configure()

    #
    # Init the class ONLY!!!!
    #
    try:
        if verbosity > 1:
            print '\nLoading GapTest()\n'
        inframet = GapTest(pf, verbosity)
    except Exception, original_error:
        exit_now('ERROR: problem GapTest(%s, %s)' % (pf, verbosity))

    #
    # Run gap analysis
    #
    try:
        if verbosity > 1:
            print ('\nInframet.gaps(%s, %s, %s)\n' %
                   (start, end, subset))
        inframet.gaps(start, end, subset)
    except Exception, original_error:
        exit_now('ERROR: problem during gaps(%s, %s, %s)' %
                 (start, end, subset))

    return 0


def exit_now(string=''):
    """
    New method to exit the code nicely
    and print the error reported.
    """
    #print "\nError in code:"
    print '-'*60
    print "\t%s" % string
    print '-'*60
    traceback.print_exc()
    exit(1)
    #raise Exception(string)


if __name__ == '__main__':
    exit(main())
else:
    raise SystemExit('ERROR: Cannot import GapTest() into the code!!!')
