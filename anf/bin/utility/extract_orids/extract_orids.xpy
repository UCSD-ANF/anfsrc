#!/opt/antelope/5.8/bin/python

"""
    
    extract_orids.xpy

    Selects a set of orids within a database that satisfies the constraints defined by the flags 

"""

import os, sys
import subprocess
from subprocess import call
from optparse import OptionParser
import time
import site
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

sys.path.append(os.environ['ANTELOPE'] + "/contrib/data/python")
sys.path.append(os.environ['ANTELOPE'] + "/data/python")
site.addsitedir(os.environ['ANF'] + "/lib/python")
sys.path.append(os.environ['ANF'] + "/data/python")

import obspy

from antelope.datascope import *
import antelope.datascope as datascope

#from functions import dbmoment_pdf

from antelope.datascope import *
import antelope.datascope as datascope
import antelope.stock as stock


"""
    
Configure parameters from command line

"""
usage = "\n\t\extract_orids [-r] [--lat latitude-bounds] [--lon longitude-bounds] [-p pfname] [-m magnitude] [-b start-time] [-e end-time] [-a author] database \n"

parser = OptionParser(usage=usage)

# verbose output on dbmoment
parser.add_option("-o", action="store_true", dest="orids_only", default=False, help="return list of orids without running dbmoment")

# constrain origin to reviewed events only
parser.add_option("-r", action="store_true", dest="review", default=False, help="reviewed origins only")

# master parameter file for dbmoment
parser.add_option("-p", action="store", dest="pf", type="string", default=None, help="parameter file path")

# contrain latitude
parser.add_option("--lat",  action="store", dest="lat", default=None, help="origin latitude bounds")

# contrain latitude
parser.add_option("--lon", action="store", dest="lon", default=None, help="origin longitude bounds")

# magnitude minimum constraint
parser.add_option("-m", action="store", dest="magnitude", type="int", default=0, help="minimum magnitude")

# begin time constraint
parser.add_option("-b", action="store", dest="ts", default=0, help="start-time in %Y-%m-%d %H:%M:%S or epoch")

# begin time constraint
parser.add_option("-e", action="store", dest="te", default=int(time.time()), help="end-time in %Y-%m-%d %H:%M:%S or epoch")

# constrain origin to specific author
parser.add_option("-a", action="store", dest="author", type="string", default="auth=~/.*/", help="origin author string (e.g. auth=~/USGS/")


(options, args) = parser.parse_args()
if len(args) == 0:
    sys.exit(usage)

database = args[0]

"""

Open databases and tables

"""

try:
    db = datascope.dbopen( database, "r+" )
except Exception,e:
    error('Problems opening database: %s %s %s' % (database,Exception, e) )

# set up table pointers
site_table = db.lookup(table="site")
origin_table = db.lookup(table="origin")
netmag_table = db.lookup(table="netmag")

"""

Define parameters to constrain origins

"""

# define time constraint
try:
    ts = float(options.ts)
    te = float(options.te)

except ValueError:
    ts = float(stock.str2epoch(options.ts))
    te = float(stock.str2epoch(options.te))

# define location constraints
lens = site_table.query(dbRECORD_COUNT)


if options.lat:
    lat = options.lat.split(',')
    minlat = min(options.lat.split(','))
    maxlat = max(options.lat.split(','))
else:
    minlat = -90
    maxlat = 90

if options.lon:
    lon = options.lon.split(',')
    minlon = min(options.lon.split(','))
    maxlon = max(options.lon.split(','))
else:
    minlon = -180
    maxlon = 180

"""

Subset table based on constraints given in command-line

"""

if options.review:
    express = "review=='y' && %s && lat>='%0.4f' && lat<='%0.4f' && lon>='%0.4f' && lon<='%0.4f' && magnitude>=%0.2f && time>=%0.1f && time<=%0.1f"\
                    % (options.author, minlat, maxlat, minlon, maxlon, options.magnitude, ts, te)
else:
    express = "%s && lat>='%0.4f' && lat<='%0.4f' && lon>='%0.4f' && lon<='%0.4f' && magnitude>=%0.2f && time>=%0.1f && time<=%0.1f"\
                    % (options.author, minlat, maxlat, minlon, maxlon, options.magnitude, ts, te)

print(express)
table_join = origin_table.join(netmag_table)
table_subset = table_join.subset(express)

"""

Get unique orids and run dbmoment on each

"""

lens = table_subset.query(dbRECORD_COUNT)

orids = []
for x in range(0, lens):
    table_subset.record = x
    orid = table_subset.getv("orid")[0]
    # only grab orid not in list
    try:
        orids.index(orid)
    except ValueError:
        orids.append(orid)
        print orid
    else:
        pass
