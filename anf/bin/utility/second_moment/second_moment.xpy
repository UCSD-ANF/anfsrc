
""" Python wrapper for McGuire 2017 MATLAB second moment program """

#
# -- Import modules
#

#import os
#import sys
#import signal
#
#signal.signal(signal.SIGINT, signal.SIG_DFL)
#sys.path.append(os.environ['ANTELOPE'] + "/data/python")
#sys.path.append(os.environ['ANTELOPE'] + "/contrib/data/python")

import re
import glob
import stat
import json
import inspect
import logging
import csv
import subprocess

from time import sleep
from optparse import OptionParser

import antelope.stock as stock

#
# -- Declare functions
#

def safe_pf_get(pf,field,defaultval=False):
    '''
    Safe method to extract values from parameter file
    with a default value option.
    '''
    value = defaultval
    if pf.has_key(field):
        try:
            value = pf.get(field,defaultval)
        except Exception,e:
            elog.die('Problems safe_pf_get(%s,%s)' % (field,e))
            pass
    if isinstance( value, (list, tuple)):
        value = [x for x in value if x]
    logging.debug( "pf.get(%s,%s) => %s" % (field,defaultval,value) )
    return value 


def get_model_pf( mfile, path=[]):
    model = False

    logging.debug('Get model: %s in %s' % (mfile, path) )

    for d in path:
        if os.path.isfile(os.path.join(d, mfile)):
            logging.debug('Look for model: %s' % os.path.join(d, mfile))
            model = os.path.join(d, mfile)
            break
        else:
            pass # Stop if we find one
    
    if not model:
        logging.error('Missing [%s] in [%s]' % ( mfile, ', '.join(path) ) )

    return model

#
# -- Set command-line arguments
#

usage = "\n\tUsage:\n"
usage += "\t\tsecond_moment -vdxw --nofig [-p parameter file] [-s select] [-r reject] [-f filter] [-t tw] database orid \n"

parser = OptionParser(usage=usage)

parser.add_option("-v", "--verbose", action="store_true", dest="verbose",
        help="verbose output", default=False)

parser.add_option("-d", "--debug", action="store_true", dest="debug",
        help="debug output", default=False)

parser.add_option("-x", "--debug_plot", action="store_true", dest="debug_plot",
        help="debug plot output", default=False)

parser.add_option("-i", "--interactive", action="store_true", dest="interactive",
        help="run in interactive mode", default=False)

parser.add_option("--no_figure", action="store_true", dest="no_figure",
        help="save plots", default=False)

parser.add_option("-w", action="store_true", dest="window",
        help="run on active display", default=False)

parser.add_option("-e", "--egf", action="store", type="string", dest="egf",
        help="egf orid", default=-99)

parser.add_option("-p", action="store", type="string", dest="pf",
        help="parameter file", default='second_moment.pf')

parser.add_option("-s", "--select", action="store", type="string", dest="select",
        help="station select", default=".*")

parser.add_option("-r", "--reject", action="store", type="string", dest="reject",
        help="station reject", default="")

parser.add_option("-f", "--filter", action="store", type="string", dest="filter",
        help="filter", default=None)

parser.add_option("-t", "--time_window", action="store", type="string", dest="tw",
        help="time window", default=None)

parser.add_option("-m", "--model", action="append", type="string", dest="model",
        help="velocity model", default=[])

parser.add_option("--fault", action="store", type="string", dest="fault",
        help="strike1,dip1,strike2,dip2", default="")

(options, args) = parser.parse_args()

#
# -- Set log level
#

loglevel = 'WARNING'
if options.verbose:
    loglevel = 'INFO'
if options.debug:
    loglevel = 'DEBUG'

try:
    from second_moment.logging_helper import getLogger
except Exception,e:
    sys.exit('Problems loading logging lib. %s' % e)

# New logger object and set loglevel
logging = getLogger(loglevel=loglevel)
logging.info('loglevel=%s' % loglevel)

#
# -- Parse parameter file
#

pf_file = stock.pffiles( options.pf )[-1]

if not os.path.isfile(pf_file):
    sys.exit( 'Cannot find parameter file [%s]' % options.pf )

pf = stock.pfread( options.pf )

# matlab inversion parameters
loaddatafile = float(safe_pf_get(pf, 'loaddatafile'))
domeas = float(safe_pf_get(pf, 'domeasurement'))
doinversion = float(safe_pf_get(pf, 'doinversion'))
dojackknife = float(safe_pf_get(pf, 'dojackknife'))
azband = float(safe_pf_get(pf, 'azband'))
dobootstrap = float(safe_pf_get(pf, 'dobootstrap'))
nb = float(safe_pf_get(pf, 'nb'))
bconf = float(safe_pf_get(pf, 'bconf'))
niter = float(safe_pf_get(pf, 'niter'))
testfault = float(safe_pf_get(pf, 'testfault'))

# set up folders
image_dir = os.path.relpath(safe_pf_get(pf, 'image_dir', 'second_moment_images'))
if not os.path.exists(image_dir):
    os.makedirs(image_dir)

temp_dir = os.path.relpath(safe_pf_get(pf, 'temp_dir', '.second_moment'))
if not os.path.exists(temp_dir):
    os.makedirs(temp_dir)

# model path
model_path = safe_pf_get(pf, 'model_path')
if not options.model:
    options.model = safe_pf_get(pf, 'velocity_model')

model = get_model_pf(options.model, model_path)

# on/off for features
auto_arrival = safe_pf_get(pf, 'auto_arrival')

# egf selection criteria
loc_margin = float(safe_pf_get(pf, 'location_margin'))
dep_margin = float(safe_pf_get(pf, 'depth_margin'))
time_margin = float(safe_pf_get(pf, 'time_margin'))

# filter and time window
if not options.filter:
    options.filter = safe_pf_get(pf, 'filter')

if not options.tw:
    options.tw = safe_pf_get(pf, 'time_window')

# L-curve time duration maximum
stf_duration_criteria = float(safe_pf_get(pf, 'misfit_criteria'))

# set path of matlab script
matlab_code_path = safe_pf_get(pf, 'matlab_code_path')
sys.path.append( matlab_code_path )
matlab_code = matlab_code_path + '/' + 'run_second_moment.m'

#
# -- Set matlab info
#

matlab_path = safe_pf_get(pf, 'matlab_path')
matlab_flags = safe_pf_get(pf, 'matlab_flags')
xvfb_path = safe_pf_get(pf, 'xvfb_path')
matlab_nofig = safe_pf_get(pf, 'matlab_nofig')

logging.info( "Start: %s %s" % ( 'second_moment',  stock.strtime( stock.now() ) )  )
logging.info( "Start: configuration parameter file %s" % options.pf  )
logging.info( " - Xvfb path: %s" % xvfb_path  )
logging.info( " - Matlab path: %s" % matlab_path  )
logging.info( " - Matlab flags: %s" % matlab_flags  )

# Set virtual display if needed
if not options.window and xvfb_path:
    """
    Open virtual display. Running Xvfb from Python
    """

    pid = os.getpid()
    cmd = '%s :%s -fbdir /var/tmp -screen :%s 1600x1200x24' % (xvfb_path, pid, pid)

    logging.info( " - Start virtual display: %s" % cmd  )

    xvfb = subprocess.Popen( cmd, shell=True)

    if xvfb.returncode:
        stdout, stderr = xvfb.communicate()
        logging.info( " - xvfb: stdout: %s" % stdout  )
        logging.info( " - xvfb: stderr: %s" % stderr  )
        sys.exit('Problems on %s ' % cmd )

    os.environ["DISPLAY"] = ":%s" % pid

    logging.info( " - xvfb.pid: %s" % xvfb.pid  )
    logging.info( " - $DISPLAY => %s" % os.environ["DISPLAY"]  )

#
# -- Run Matlab code
#

cmd = "%s -r \"matlab_code='%s'; verbose='%s'; debug='%s'; debug_plot='%s'; interactive='%s'; no_figure='%s' \
                ; image_dir='%s'; temp_dir='%s'; db='%s'; orid=%d; egf=%s; vel_model='%s'; reject='%s'; select='%s'; filter='%s' \
                ; tw='%s'; misfit_criteria=%.2f; loc_margin=%.4f; dep_margin=%.2f \
                ; time_margin=%.1f; LOADDATAFILE=%d; DOMEAS=%d; DOINVERSION=%d; DOJACKKNIFE=%d \
                ; azband=%d; DOBOOTSTRAP=%d; NB=%d; bconf=%.2f; NITER=%d; TESTFAULT=%d; auto_arrival='%s'; fault='%s'; \" < '%s'"  \
                % (matlab_path, matlab_code_path, options.verbose, options.debug, options.debug_plot, options.interactive \
                , options.no_figure, image_dir, temp_dir, args[0], int(args[1]), options.egf, model, options.reject \
                , options.select, options.filter, options.tw, stf_duration_criteria \
                , loc_margin, dep_margin, time_margin, loaddatafile, domeas, doinversion \
                , dojackknife, azband, dobootstrap, nb, bconf, niter, testfault, auto_arrival, options.fault, matlab_code)

logging.info( " - Run Matlab script:"  )
logging.info( "   %s " % cmd  )

def execute(command):
    """Executes the command to run matlab script."""
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    # Poll process for new output until finished
    while True:
        nextline = process.stdout.readline()
        if nextline == '' and process.poll() is not None:
            break
        nextline = nextline.lstrip('>> ')
        nextline = nextline.lstrip('MATLAB_maci64: ')
        sys.stdout.write(nextline)
        sys.stdout.flush()
 
    output = process.communicate()[0]
    exitCode = process.returncode

    if (exitCode == 0):
        return output
    else:
        raise subprocess.ProcessException(command, exitCode, output)

try:
    mcmd = execute(cmd)
except Exception,e:
    print " - Problem on: [%s] " % cmd
    print " - Exception %s => %s" % (Exception,e)

if options.verbose:
    logging.info( "Done: %s %s" % ( 'second_moment',  stock.strtime( stock.now() ) )  )


# -- Kill virtual display if needed -- #
if not options.window:
    logging.info( "xvfb.kill: %s" % xvfb.terminate() )

def num(s, r=None):
    if r:
        return round(float(s), r)
    else: 
        try:
            return int(s)
        except ValueError:
            return float(s)


