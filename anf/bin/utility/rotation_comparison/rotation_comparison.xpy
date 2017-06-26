#!/opt/antelope/5.6/bin/python

import os
import sys
import signal

signal.signal(signal.SIGINT, signal.SIG_DFL)
sys.path.append(os.environ['ANTELOPE'] + "/data/python")
sys.path.append(os.environ['ANTELOPE'] + "/contrib/data/python")

import re
import glob
import stat
import json
import inspect
import logging
import csv
import time
import subprocess

from math import sin, cos, sqrt, atan2, radians, log
from tempfile import mkstemp
from distutils import spawn
from datetime import datetime
from optparse import OptionParser
from collections import defaultdict
from mpl_toolkits.axes_grid1 import make_axes_locatable, axes_size

import matplotlib.pyplot as plt


try:
    from antelope.datascope import closing,\
                                   dbopen
    from antelope.stock import epoch2str,\
                               pfin,\
                               pfread,\
                               str2epoch
    import antelope.datascope as datascope
    from antelope import elog
    from antelope import stock
#    from antelope.bqplot import *
#    from antelope.buvector import *
#    from antelope.pfsubs import *
except Exception,e:
    sys.exit("Import Error: [%s] Do you have ANTELOPE installed correctly?" % e)

from argparse import ArgumentParser
from numpy import arange
from scipy.signal import resample
from scipy import signal
from obspy.signal.cross_correlation import xcorr
import numpy as np



"""
Configure parameters from command-line.
"""

usage = "\n\tUsage:\n"
usage += "\t\trotation_comparison -vx -o --noplot [-p parameter file] [-s station list] [-r reference station] [-c channel code] [-f filter] [-t time window] database time/orid \n"

parser = OptionParser(usage=usage)

# Verbose output
parser.add_option("-v", action="store_true", dest="verbose",
        default=False, help="verbose output")


# Parameter file
parser.add_option("-p", action="store", dest="pf", type="string", default="dbxcorr.pf", help="parameter file")


# Filter 
parser.add_option("-f", action="store", dest="filter", type="string", default=None, help="filter")

# Time window 
parser.add_option("-t", action="store", dest="tw", type="float", default=None, help="time window")

# Mode
parser.add_option("-o", action="store_true", dest="origin", default=False, help="arg2 is orid")

# Mode
parser.add_option("-r", action="store", dest="ref_sta", type="string", default=None, help="reference station")

# Stations
parser.add_option("-s", action="store", dest="select", type="string", default=None, help="station list or regex")

# Chan
parser.add_option("-c", action="store", dest="chan", type="string", default=None, help="channel code")

# Plot each data group for a site and wait.
parser.add_option("-x", action="store_true", dest="debug_plot",
        default=False, help="debug output each station plot")

# Plot results
parser.add_option("--noplot", action="store_true", dest="noplot", default=False, help="plot azimuth rotation results")

(options, args) = parser.parse_args()

# If we don't have 2 arguments then exit.
if len(args) != 2:
    sys.exit( usage );

# If we don't have station list or reference station than exit 
if not (options.select or options.ref_sta) : 
    sys.exit("ERROR: DbXcorr requires reference station and station list %s" % usage)

# Set log level
loglevel = 'WARNING'
if options.verbose:
    loglevel = 'INFO'

# All modules should use the same logging function. We have
# a nice method defined in the logging_helper lib that helps
# link the logging on all of the modules.
try:
    from rotation_comparison.logging_helper import *
except Exception,e:
    sys.exit('Problems loading logging lib. %s' % e)

# New logger object and set loglevel
logging = getLogger(loglevel=loglevel)
logging.info('loglevel=%s' % loglevel)

# Import other modules

try:
    from rotation_comparisons.functions import *
except Exception,e:
    sys.exit("Import Error: [%s] Problem with functions load." % e)

try:
    from rotation_comparisons.data import * 
except Exception,e:
    sys.exit("Import Error: [%s] Problem with data load." % e)

try:
    from rotation_comparison.comparison import *
except Exception,e:
    sys.exit("Import Error: [%s] Problem with xcorr load." % e)

# parse arguments from command-line
databasename = args[0]
logging.info("Database [%s]" % databasename)

# need to write functions for each

# read parameters from parameter file
logging.info("Parameter file to use [%s]" % options.pf)

pf_object = stock.pfread(options.pf)

rot_compare = Comparison(options, databasename, logging)
results = rot_compare.comp(args[1])

#params = Parameters(options, logging)
#
#if params.origin:
#    event_data = Origin(databasename, args[1])
#    event_data.get_stations(params.select)
#else:
#    try:
#        time = args[1]
#        if isinstance(time, str): time = str2epoch(time)
#    except Exception:
#        sys.exist(usage)
#
## get station list
##site = Site(options.stas, databasename)
##station_list = site.sites 
#
#data = Waveforms(databasename)
## grab ref sta tr
#results = {}
#
#ref_sta = options.ref_sta
#data.get_waveforms(sta=ref_sta, chan=params.chan, start_time=event_data.stations[ref_sta]['ptime'] - 2, tw=params.tw, bw_filter=params.filter)
#results[ref_sta] = data.set_refsta_data(ref_sta)
#
## for loop through all stations and get data   
#for sta in event_data.stations:
#    if sta!=ref_sta:
#        data.get_waveforms(sta=sta, chan=params.chan, start_time=event_data.stations[sta]['ptime']-2, tw=params.tw, bw_filter=params.filter)
#        results[sta] = data.get_azimuth(ref_sta, sta, event_data.stations, plot=options.plot, image_dir=params.image_dir, debug_plot=options.debug_plot)
#
##graphic = Graphics(width=800, height=200)        
##Graphics(width=800, height=200, results=results, ref_sta=ref_sta, ts=time-2, te=time-2+parameters.tw)
#
# 
