#
# Template to run Matlab code
# from command line.
#

from time import sleep
from optparse import OptionParser
import subprocess

import antelope.stock as stock

python_code = 'bw_journal_map’
code_sub_folder = 'bw_journal_map'
matlab_code_folder = os.environ['ANF'] + '/' + code_sub_folder
sys.path.append( matlab_code_folder )
matlab_code = matlab_code_folder + ‘bw_journal_map_lib.m’



#
# Get command-line arguments
#
usage = "Usage: %prog [options]"

parser = OptionParser(usage=usage)

parser.add_option("-v", action="store_true", dest="verbose",
        help="verbose output", default=False)
parser.add_option("-p", action="store", type="string", dest="pf",
        help="parameter file", default=python_code+'.pf')
parser.add_option("-w", action="store_true", dest="window",
        help="run on active display", default=False)

(options, args) = parser.parse_args()



pf = stock.pfread( options.pf )
pf_file = stock.pffiles( options.pf )[0]

if not os.path.isfile(pf_file):
    sys.exit( 'Cannot find parameter file [%s]' % options.pf )



matlab_path = pf['matlab_path']
matlab_flags = pf['matlab_flags']
xvfb_path = pf['xvfb_path']
matlab_nofig = pf['matlab_nofig']


def logging( msg):
    if options.verbose:
        print msg



#
# Main script
#
logging( "Start: %s %s" % ( python_code,  stock.strtime( stock.now() ) )  )
logging( "Start: configuration parameter file %s" % options.pf  )
logging( " - Xvfb path: %s" % xvfb_path  )
logging( " - Matlab path: %s" % matlab_path  )
logging( " - Matlab flags: %s" % matlab_flags  )



#
# Set virtual display if needed
#
if not options.window and xvfb_path:
    """
    Open virtual display. Running Xvfb from Python
    """

    pid = os.getpid()
    cmd = '%s :%s -fbdir /var/tmp -screen :%s 1600x1200x24' % (xvfb_path, pid, pid)

    logging( " - Start virtual display: %s" % cmd  )

    xvfb = subprocess.Popen( cmd, shell=True)

    if xvfb.returncode:
        stdout, stderr = xvfb.communicate()
        logging( " - xvfb: stdout: %s" % stdout  )
        logging( " - xvfb: stderr: %s" % stderr  )
        sys.exit('Problems on %s ' % cmd )

    os.environ["DISPLAY"] = ":%s" % pid

    logging( " - xvfb.pid: %s" % xvfb.pid  )
    logging( " - $DISPLAY => %s" % os.environ["DISPLAY"]  )


#
# Run Matlab code
#

cmd = "%s %s %s -r \"run_verbose='%s'; pf='%s'\" < %s" % \
        (matlab_path, matlab_flags, matlab_nofig, options.verbose, pf_file, matlab_code)

logging( " - Run Matlab script:"  )
logging( "   %s " % cmd  )

try:

    mcmd = subprocess.Popen( cmd, shell=True, env={"DISPLAY": os.environ['DISPLAY']},
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    stdout, stderr = mcmd.communicate()

    if mcmd.returncode:
        logging( " - mcmd: stdout: %s" % stdout  )
        logging( " - mcmd: stderr: %s" % stderr  )

except Exception,e:
    print " - Problem on: [%s] " % cmd
    print " - Exception %s => %s" % (Exception,e)

if options.verbose:
    logging( "Done: %s %s" % ( python_code,  stock.strtime( stock.now() ) )  )


#
# Kill virtual display if needed
#
if not options.window:
    logging( "xvfb.kill: %s" % xvfb.terminate() )
