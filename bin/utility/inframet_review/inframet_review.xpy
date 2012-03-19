"""
inframet_review

# {{{ Headers

    Perform some analysis on the inframet channels
    for common problems with the instrumentation
    and/or databases.
    Channels associated with the inframet:
        BDF_EP
        BDO_EP
        LDF_EP
        LDO_EP
        LDM_EP

    Some known problems to target with the script:
        - gaps exclusive to the inframet channels
        - spikes in the time-series
        - suden jumps or dips in the time-series
        - flat-line of the time-series

    @authors
        Juan Reyes <reyes@ucsd.edu>
        Rob Newman <robertlnewman@gmail.com>
        Jon Tytell <jtytell@ucsd.edu>

    @notes
        +
        +


    @build
        + try:except Exceptions can be access like this...

            print 'Exc Instance: %s' % type(e)     # the exception instance$
            print 'Exc Args: %s' % e.args          # arguments stored in .args$
            print 'Exc __str__: %s' % e            # __str__ allows args to printed directly$

# }}}
"""

# {{{ Import libraries
import os
import re
import sys
import subprocess
#import math as math
#from pprint import pprint
#from time import gmtime, time
#from datetime import datetime
from optparse import OptionParser
#from collections import defaultdict

#{{{ ANTELOPE
try:
    import antelope.stock as stock
    import antelope.datascope as datascope
except Exception,e:
    sys.exit("Antelope Import Error: [%s]" % e.args)
# }}}

# {{{ MATPLOTLIB
try:
    import matplotlib as mpl
except Exception,e:
    sys.exit("Import Error: [%s] Do you have MatplotLib installed correctly?" % e.args)
else:
    mpl.use('tkagg')
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MultipleLocator, FormatStrFormatter
# }}}

# }}}

class InframetTest():
    """
    Main class for calculating
    gaps in inframet data
    """
    # {{{ InframetTest

    def __init__(self, pf, verbosity=False):
        # {{{
        if verbosity > 1:
            self.debug = True
        elif verbosity > 0:
            self.verbose = True

        self.pf = pf

        try:
            self._parse_pf()
        except Exception,e:
            sys.exit('ERROR: problem during parsing of pf file[%s] class.[%s]' % (self.pf, e.args) )
        # }}}

    def _parse_pf(self):
        """Parse the parameter file
        and assign to vars that will be
        used throughout the script
        """
        # {{{

        if self.debug: print 'InframetTest(): Parse parameter file %s' % self.pf

        self.min_gap = stock.pfget_double(self.pf, 'min_gap')
        if self.debug: print '\tmin_gap => %s' % self.min_gap

        self.gap_threshold = stock.pfget_double(self.pf, 'gap_threshold')
        if self.debug: print '\tgap_threshold => %s' % self.gap_threshold

        self.inframet_db = stock.pfget_string(self.pf, 'inframet_db')
        if self.debug: print '\tinframet_db => %s' % self.inframet_db

        self.subset_sta = stock.pfget_string(self.pf, 'subset_sta')
        if self.debug: print '\tsubset_sta => %s' % self.subset_sta

        self.inframet_chan = stock.pfget_string(self.pf, 'inframet_chan')
        if self.debug: print '\tinframet_chan => %s' % self.inframet_chan

        self.seismic_db = stock.pfget_string(self.pf, 'seismic_db')
        if self.debug: print '\tseismic_db => %s' % self.seismic_db

        self.seismic_chan = stock.pfget_string(self.pf, 'seismic_chan')
        if self.debug: print '\tseismic_chan => %s' % self.seismic_chan

        self.temp_db = stock.pfget_string(self.pf, 'temp_db')
        if self.debug: print '\ttemp_db => %s' % self.temp_db

        # }}}

    def gaps(self, start, end, subset=False):
        """Calculate gap analysis
        """
        # {{{

        #
        # Build current subset
        #
        if subset:
            self.subset = subset
        else:
            self.subset = "sta=~/%s/ && chan=~/%s/" % (self.subset_sta,self.inframet_chan)

        if self.debug: print "\tInframetTest(): Using subset [%s]" % self.subset

        #
        # Clean temp files
        #
        for file in ['gap','chanperf']:
            temp = "%s.%s" % (self.temp_db,file)
            if os.path.exists(temp):
                if self.debug: print "\tInframetTest(): Remove old temp file [%s]" % temp
                try:
                    os.remove(temp)
                except Exception,e:
                    sys.exit('ERROR: Cannot remove old file [%s] => [%s]' % (temp,e.args) )

        #
        # Build gap database
        #
        cmd = 'rtoutage -d %s -s "%s" %s %s %s' % (self.temp_db,self.subset,self.inframet_db,start,end)
        if self.debug: print "\tInframetTest(): Build gap table [%s]" % cmd
        try:
            p = subprocess.Popen('%s'%cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            if self.debug: print '======================='
            for line in p.stdout.readlines():
                if self.debug: print '\tInframetTest(): rtoutage output: %s' % line.strip()
            if self.debug: print '\n'
            retval = p.wait()
        except Exception,e:
            sys.exit('ERROR: Cannot run rtoutage command [%s] => [%s]' % (cmd,e.args) )

        #
        # Compare gaps to seismic database
        #
        if self.debug: print "\tInframetTest(): Open temp database: %s" % self.temp_db

        try:
            temp_db = datascope.dbopen( self.temp_db, "r+" )
            temp_db.lookup( table='gap' )

        except Exception, e:
            raise SystemExit('ERROR: dbopen() %s => %s\n\n' % (self.temp_db,e.args))

        try:
            records = temp_db.query(datascope.dbRECORD_COUNT)
        except Exception,e:
            records = 0 

        if not records:
            print "\nNo gaps found in database(%s)\n" % self.inframet_db
            return

        # vista{reyes}% dbselect -h  /tmp/inframet_gaps.gap
        # tagname   sta     chan         time              tgap        filled      lddate      
        # -        C39A   LCE_EP    1329303738.00000       45047.00000 -  1330543311.84233
        # -        C39A   LCO_EP    1329303738.00000       45047.00000 -  1330543311.85095
        # -        C39A   LDM_EP    1329303710.66668       45047.00000 -  1330543311.86047
        # -        C39A   LEP_EP    1329303738.00000       45047.00000 -  1330543311.86794
        # -        C39A   LIM_EP    1329303738.00000       45047.00000 -  1330543311.87569
        # -        C39A   LKM_EP    1329303710.66668       45047.00000 -  1330543311.88293

        for i in range(records):

            temp_db.record = i
            try:
                (sta,chan,time,tgap) = temp_db.getv('sta','chan','time','tgap')
            except Exception,e:
                raise SystemExit('ERROR: Problems while extracting from database %s: %s\n\n' % (slef.temp_db,e.args))

            if self.debug:
                print '\tIframetTest(): Test seismic for gap [%s, %s, %s, %s]' % (sta,chan,stock.strtime(time),tgap)

            if tgap <= self.min_gap:
                temp_db.mark() # mark Datascope database rows for deletion
                if self.verbose:
                    print '\t%s  %s  %s  %s  %s  too small for review' % (sta,chan,stock.strtime(time),stock.strtime(time+tgap),tgap)
                continue

            #
            # Run rtoutage on seismic
            #
            total = 0
            lines = []
            subset = "sta=~/%s/ && chan=~/%s/" % (sta,self.seismic_chan)
            cmd = 'rtoutage -SA -s "%s" %s %s %s' % (subset,self.seismic_db,time,tgap)
            if self.debug: print "\tInframetTest(): Test seismic [%s]" % cmd
            try:
                p = subprocess.Popen('%s'%cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

                if self.debug: print '\tInframetTest(): ======================='
                for line in p.stdout.readlines():
                    lines.append(line.strip())
                    if self.debug: print '\tInframetTest(): rtoutage output: %s' % line
                retval = p.wait()

            except Exception,e:
                sys.exit('ERROR: Cannot run rtoutage command [%s] => [%s]' % (cmd,e.args) )


            # test for sta and channel in string
            for line in lines:
                if self.debug: print '\tInframetTest(): parse line: %s' % line
                words = line.split()
                if sta in words:
                    total = total + float(words[-1])

            if self.debug: print '\tInframetTest(): end of regex total:%s' % total


            ratio = int((total/tgap)*100)
            if self.debug: 
                print '\tInframetTest(): gaps in inframet:[%s] gaps in seismic:[%s]' % (total,tgap)
                print '\tInframetTest(): %s of the gap is in seismic too' % ratio

            if ratio < self.gap_threshold: 
                if self.verbose:
                    print '\t%s  %s  %s  %s  %s  on inframet ONLY' % (sta,chan,stock.strtime(time),stock.strtime(time+tgap),tgap)
                else:
                    print '\t%s  %s  %s  %s  %s' % (sta,chan,stock.strtime(time),stock.strtime(time+tgap),tgap)
            else:
                temp_db.mark() # mark Datascope database rows for deletion
                if self.verbose:
                    print '\t%s  %s  %s  %s  %s  on ALL' % (sta,chan,stock.strtime(time),stock.strtime(time+tgap),tgap)

        try:
            temp_db.crunch() # Delete Datascope database rows marked for deletion
            temp_db.close()
        except:
            pass

        if self.verbose:
            print 'Database with valid gaps in: [%s]' % self.temp_db

        return 0

        # }}}

    # }}}

def configure():
    """
    Configure parameters
    from command-line and
    the pf-file
    """
    # {{{ configure
    usage = "Usage: inframet_review [-vd] [-s subset] [-p pfname] start end"
    parser = OptionParser(usage=usage)
    parser.add_option("-v", "--verbose", action="store_true",
                      dest="verbose", default=False, help="verbose output")
    parser.add_option("-d", "--debug", action="store_true",
                      dest="debug", default=False, help="debug application")
    parser.add_option("-p", "--pf", action="store",
                      dest="pf", type="string", help="parameter file path")
    parser.add_option("-s", "--subset", action="store",
                      dest="subset", type="string", help="subset sta:chan")

    (options, args) = parser.parse_args()

    #
    # Determine verbosity
    #
    verbosity = 0
    if options.verbose:
        verbosity += 1

    if options.debug:
        verbosity += 2

    #
    # Command-line arguments [start and end times]
    #
    if len(args) != 2:
        sys.exit(usage)
    else:
        start = args[0]
        end = args[1]

    #
    # Convert Times
    #
    try:
        start = stock.str2epoch(str(start))
    except Exception,e:
        sys.exit('ERROR: Cannot convert start(%s) to epoch time.[%s]' % (start,e.args) )

    if re.match("^\d+$",end):
        end = int(end)
    else:
        try:
            end = stock.str2epoch(str(end))
        except Exception,e:
            sys.exit('ERROR: Cannot convert end(%s) to epoch time.[%s]' % (start,e.args) )

    if start < 0 or start > stock.now():
        sys.exit('ERROR: Wrong start(%s) time.' % (start) )

    if end < 0 or end > stock.now():
        sys.exit('ERROR: Wrong end(%s) time.' % (end) )

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
    except Exception,e:
        sys.exit('ERROR: problem loading pf(%s) class.[%s => %s]' % (options.pf, type(e), e.args) )

    if verbosity > 1:
        print "Parameter file to use [%s]" % options.pf

    return start, end, options.pf, options.subset, verbosity
    # }}}

def main():
    """Main script
    processing"""
    # {{{ main
    start, end, pf, subset, verbosity = configure()

    #
    # Init class
    #
    try:
        if verbosity > 1:
            print '\nLoading InframetTest()\n'
        Inframet = InframetTest(pf, verbosity)
    except Exception,e:
        sys.exit('ERROR: problem loading main InframetTest(%s, %s) class.[%s => %s]' % (pf, verbosity, Exception, e) )

    #
    # Run gap analysis
    #
    try:
        if verbosity > 1:
            print '\nInframet.gaps(%s,%s,%s)\n' % (start, end, subset)
        Inframet.gaps(start, end, subset)
    except Exception,e:
        sys.exit('ERROR: problem during gaps(%s,%s,%s): [%s]' % (start, end, subset, e.args))

    return 0
    # }}}

if __name__ == '__main__':
    status = main()
    sys.exit(status)
else:
    sys.exit('ERROR: Cannot import InframetTest() into the code!!!')
