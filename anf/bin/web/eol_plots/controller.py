#!/usr/bin/env python


# Import all the relevant modules

import sys
import re
import os
import json
import multiprocessing
import subprocess
import time
from time import gmtime, strftime
from optparse import OptionParser

sys.path.append( os.environ['ANTELOPE'] + '/data/python' )
from antelope.datascope import *
from antelope.stock import *

# Global vars
web_root       = '/anf/web/vhosts/anf.ucsd.edu'
report_pf = web_root + '/conf/report_exceptions.pf'
pf = pfread(report_pf)
np_sta_list = pf['national_parks']
np_sta_list_final = []


web_root       = '/anf/web/vhosts/anf.ucsd.edu'
common_pf      = web_root + '/conf/common.pf'
pf = pfread(common_pf)
cache_json = pf['CACHEJSON']
output_dir = pf['CACHE_EOLPLOTS']
json_file_path = '%s/stations/stations.json' % cache_json

# {{{ Local functions
def process_command_line(argv):
    '''Return a tuple: (verbose)
    'argv' is a list of arguments
    '''
    if argv is None:
        argv = sys.argv[1:]

    usage = 'Usage: %prog [options]'
    parser = OptionParser(usage=usage)
    parser.add_option("-n", "--network", action="store", dest="network", help="Network subset", default='.*')
    parser.add_option("-s", "--station", action="store", dest="station", help="Station subset", default='.*')
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose", help="verbose output", default=False)
    parser.add_option("-r", "--rebuild", action="store_true", dest="rebuild", help="rebuild station", default=False)
    parser.add_option("-j", "--json", action="store", type="string", dest="json", help="save as a json file", default=False)
    options, args = parser.parse_args(argv)

    return (options.verbose, options.json, options.network, options.station, options.rebuild)

def clean_up(my_list):
    cleaned = merge(my_list)
    cleaned = list(set(cleaned))
    cleaned.sort()
    return cleaned

def merge(seq):
    merged = []
    for s in seq:
        for x in s:
            merged.append(x)
    return merged

def pf_stalist(pf_file, key):
    pf_sta_list = []
    pf_array = pfget(pf_file, key)
    for snet in pf_array:
        for sta in pf_array[snet]:
            pf_sta_list.append(sta)
    return pf_sta_list


    print "\tgot %s adopted and decom stations" % len(json_sta_list)
    return json_sta_list

def work(staname, verbose=False):
    print 'Processing station: %s; Parent process id: %s; Process id: %s' % (staname, os.getppid(), os.getpid())
    print "bin/eol_plots/auto_event_dumper_matlab.py -s %s" % staname
    if verbose:
        cmd = [ "bin/eol_plots/auto_event_dumper_matlab.py", "-v", "-s", staname ]
    else:
        cmd = [ "bin/eol_plots/auto_event_dumper_matlab.py", "-s", staname ]
    return subprocess.call(cmd, shell=False)

# }}} Local functions

def main(argv=None):
    '''Main processing script
    for generating eol reports
    via multiprocessing module
    '''
    verbose, save_json, network_subset, station_subset, rebuild = process_command_line(argv)

    if verbose:
        print "Start of script at time %s" % strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())

    if verbose:
        print "Network subset:  %s" % network_subset
        print "Station subset:  %s" % station_subset

    network_match = re.compile(network_subset)
    station_match = re.compile(station_subset)

    # Open virtual display
    """
    Running Xvfb from Python
    """
    id = os.getpid()
    xvfb = subprocess.Popen('Xvfb :%s -fbdir /var/tmp -screen :%s 1600x1200x16' % (id,id), shell=True)
    os.environ["DISPLAY"] = ":%s" % id


    report_sta_list = []

    # Check National Parks stations

    for net in np_sta_list:
		net = str(net)
		if not network_match.match(net): continue
		for sta in np_sta_list[net]:
			sta = str(sta)
			if not station_match.match(sta): continue

			if rebuild:
				report_sta_list.append(sta)
			else:
				if os.path.exists('%s/%s/%s_info.pf' % (output_dir, sta, sta)):
					np_statinfo = os.stat('%s/%s/%s_info.pf' % (output_dir, sta, sta))
					time_diff = time.time() - np_statinfo.st_mtime
					if time_diff > 604800 :
						report_sta_list.append(sta)
				else:
					report_sta_list.append(sta)

    print "\tgot %s National Park stations" % len(report_sta_list)


    # Check Decom & Transitional stations
    t = json.load(open(json_file_path, 'r'))

    active = t['active']
    adopt = t['adopt']
    decom = t['decom']


    for type in [adopt,decom]:
		for sta in type:
			sta = str(sta)
			if not station_match.match(sta): continue
			if not network_match.match(type[sta]['snet']): continue
			if rebuild:
				report_sta_list.append(sta)
			else:
				#print 'TEST %s %s' % (type[sta]['snet'], sta)
				if not os.path.exists('%s/%s/%s_info.pf' % (output_dir, sta, sta) ) :
					report_sta_list.append(sta)


    # Get the number of processors available

    num_processes = int(multiprocessing.cpu_count()/2) + 1 

    if verbose:
        print '- Number of processes: %s' % (num_processes)
        print "- Number of stations to process: %s" % len(report_sta_list)
        print "- Number of stations to process: %s" % report_sta_list

    threads = []

    while threads or report_sta_list:
        '''
        If we aren't using all the processors AND 
        there is still data left to compute, then 
        spawn another thread
        '''
        if(len(threads) < num_processes) and report_sta_list:
            sta = report_sta_list.pop()
            if verbose:
                subprocess_args = [sta, 'v']
            else:
                subprocess_args = [sta]
            print "- Process station: %s" % sta
            p = multiprocessing.Process(target=work, args=subprocess_args)
            p.start()
            # print p, p.is_alive()
            threads.append(p)
        else:
            for thread in threads:
                if not thread.is_alive():
                    threads.remove(thread)

    print "xvfb.kill: %s" % xvfb.kill()


    if verbose:
        print "End of script at time %s" % strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())

    return 0

if __name__ == '__main__':
    status = main()
    sys.exit(status)
