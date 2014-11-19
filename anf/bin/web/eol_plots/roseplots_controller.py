#!/usr/bin/env python

# {{{ Header tags
#
# $Id$
#
# Get all the active stations to regenerate Matlab maps and graphs for
#
# @package    Datascope
# @author     Rob Newman <rlnewman@ucsd.edu> x21333
# @version    $Revision$
# @license    MIT style license
# @notes      Cannot use Processing Pool functions. See posted question at Stack Overflow website:
#                 http://stackoverflow.com/questions/740717/dynamic-processes-in-python
#                 http://stackoverflow.com/questions/884650/python-spawn-parallel-child-processes-on-a-multi-processor-system-use-multipro
#
# }}} Header tags

# {{{ Import all the relevant modules

import sys
import os
import json
import multiprocessing
import subprocess

# Load Antelope datascope functions
sys.path.append( os.environ['ANTELOPE'] + '/data/python' )
from antelope.datascope import *
from antelope.stock import *

# }}} Import all the relevant modules

# {{{ Global vars
web_root       = '/anf/web/vhosts/anf.ucsd.edu'
common_pf      = web_root + '/conf/common.pf'
pf = pfread(common_pf)
cache_json     = pf['CACHEJSON']
cache_rose     = pf['CACHE_ROSEPLOTS']
json_file_path = cache_json + '/stations/stations.json'
# }}} Global vars

def json_stalist(json_file):
    json_sta_list = []
    t = json.load( open(json_file,'r') )

    active = t['active']
    # adopt = t['adopt']
    # decom = t['decom']

    for a_staname in active:
        if active[a_staname]["snet"] == 'TA':
            json_sta_list.append(a_staname)

    # for d_staname in decom:
    #     if decom[d_staname]["snet"] == 'TA':
    #         json_sta_list.append(d_staname)

    # for ad_staname in adopt:
    #     if adopt[ad_staname]["snet"] == 'TA':
    #         json_sta_list.append(ad_staname)

    return json_sta_list

def work(staname):
    print 'Processing station: %s; Parent process id: %s; Process id: %s' % ( staname, os.getppid(), os.getpid() )
    print "bin/eol_plots/roseplots.py -v -s %s" % (staname)
    cmd = [ "bin/eol_plots/roseplots.py", "-v", "-s", staname ]
    return subprocess.call(cmd, shell=False)


if __name__ == '__main__':

    # Open virtual display
    """
    Running Xvfb from Python
    """
    id = os.getpid()
    xvfb = subprocess.Popen('Xvfb :%s -fbdir /var/tmp -screen :%s 1600x1200x24' % (id,id), shell=True)
    os.environ["DISPLAY"] = ":%s" % id


    report_sta_list = json_stalist(json_file_path)

    report_sta_list.sort()


    # Only work on those that have not been already created
    # report_ex = os.listdir(cache_rose)

    # Print out the complete station list for testing
    # print report_sta_list

    # Get the number of processors available
    # num_processes = multiprocessing.cpu_count()
    num_processes = 4

    print '+++ Number of processes: %s' % (num_processes)
    print 'Now trying to assign all the processors'

    threads = []

    len_stas = len(report_sta_list)

    print "+++ Number of stations to process: %s" % (len_stas)

    # run until all the threads are done, and there is no data left
    while threads or report_sta_list:

        # if we aren't using all the processors AND there is still data left to
        # compute, then spawn another thread

        if( len(threads) < num_processes ) and report_sta_list:

            sta = report_sta_list.pop()

            # if not sta in report_ex:

            print "+++ Station to process roseplots for: %s" % (sta)

            p = multiprocessing.Process(target=work,args=[sta])

            p.start()

            threads.append(p)


        else:

            for thread in threads:

                if not thread.is_alive():

                    threads.remove(thread)

    print "xvfb.kill: %s" % xvfb.kill()
