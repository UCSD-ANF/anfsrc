#!/usr/bin/env python

'''
Simple script for pulling station ranking
from IRIS DMC tool and save as JSON

@author   Rob Newman <robertlnewman@gmail.com> 858.822.1333
@version  1.0
@modified 2011-11-17
@license  MIT-style license
@notes    IRIS creates the source files daily at 06:03. If this
          script is run via cron, it needs to take place after
          that time.
          Need to ensure we get the station lat lons from the dbmaster
'''

# Import modules
import sys
import os
import re
import json
from time import time, gmtime, strftime, strptime, mktime
from optparse import OptionParser
import urllib2
# Load datascope functions
sys.path.append(os.environ['ANTELOPE'] + '/local/data/python/antelope')
import datascope
from stock import pfupdate, pfget, epoch2str, epoch, str2epoch, strtime, yearday

# Get command line arguments
usage = "Usage: %prog [options]"
parser = OptionParser(usage=usage)
parser.add_option("-v", "--verbose", action="store_true", dest="verbose", help="verbose output", default=False)
parser.add_option("-s", "--station", action="store", dest="station_override", help="station override", default=False)
parser.add_option("-x", "--debug", action="store_true", dest="debug", help="debug script", default=False)
(options, args) = parser.parse_args()
if options.verbose:
    verbose = True
else:
    verbose = False
if options.station_override:
    station = options.station_override
else:
    station = False
if options.debug:
    debug = options.debug
else:
    debug = False

def determine_verbosity(verbose=False, debug=False):
    """Determine the
    verbosity of the 
    script"""
    verbosity = 0
    if verbose:
        verbosity = 1
    if debug:
        verbosity = 2
    return verbosity

def grab_means_and_periods(url, headers, verbosity=0):
    """Grab the mean noise
    levels and periods from
    the IRIS url"""
    if verbosity > 0:
        print "- Get the mean noise levels into dictionary from file %s" % url
    means_dict = {}
    time_periods = []
    try:
        mean_page = urllib2.Request(url, None, headers)
    except urllib2.URLError:
        print urllib2.URLError
    except:
        print "- Unknown urllib2 error for url '%s'" % url
    else:
        opened_mean_page = urllib2.urlopen(mean_page)
        means_file = opened_mean_page.readlines()
        for line in means_file:
            period, mean_bhe_bhn, mean_bhz = (line.rstrip()).split()
            time_periods.append(period)
            means_dict[period] = {'BHE_BHN':mean_bhe_bhn,'BHZ':mean_bhz}
    if verbosity > 0:
        print "Periods:"
        print time_periods
        print "means_dict:"
        print means_dict
    return means_dict, time_periods

def soup_metadata(url, headers, html_codes, verbosity=0):
    """Grab the metadata from
    the IRIS url and parse
    with BeautifulSoup"""
    if verbosity > 0:
        print "- Get color scale for one period and channel from file %s" % url
    scale_dict = {'caption':'', 'scale':[]}
    metadata = {}
    try:
        from BeautifulSoup import BeautifulSoup
    except ImportError:
        print "- Import Error: Do you have BeautifulSoup installed correctly?"
        exit()
    else:
        try:
            scale_page = urllib2.Request(url, None, headers)
        except urllib2.URLError:
            print urllib2.URLError
        except:
            print "- Unknown urllib2 error for url '%s'" % scale_url
        else:
            opened_scale_page = urllib2.urlopen(scale_page)
            soup = BeautifulSoup(opened_scale_page)
            metadata['days'] = soup.findAll(text=re.compile("Noise levels"))[0]
            metadata['iris_generation_time'] = soup.findAll(text=re.compile("was generated"))[0]
            scale_table = soup.find('table')
            scale_dict['caption'] = scale_table.th.find('font').contents[0].__str__().strip()
            for i in scale_table.findAll('td'):
                '''
                Format is currently: 
                <td bgcolor="foo" align="BAR">
                    <font color="baz">
                        <font size="x">
                            STRING THAT CONTAINS 'd'
                        </font>
                    </font>
                </td>
                Note that this could change without notice
                !!! FIX: Currently IRIS has text strings instead 
                         of hexadecimal for 'red' and 'orange' 
                         only. No idea why. This may change in 
                         the future, so need a generic function 
                         to test for text string and convert to 
                         hexadecimal.
                '''
                bgcolor = i['bgcolor'].__str__().strip()
                if bgcolor == 'orange':
                    bgcolor = '#FFA500'
                elif bgcolor == 'red':
                    bgcolor = '#FF0000'
                if bgcolor.find('#') == -1:
                    bgcolor = '#%s' % bgcolor
                value = i.find(text=re.compile("d")).__str__().strip()
                val_range = value.split()
                if len(val_range) < 4:
                    if val_range[1] == html_codes['gte']:
                        val_min = int(val_range[2])
                        val_max = None
                    elif val_range[1] == html_codes['lt']:
                        val_min = None
                        val_max = int(val_range[2])
                else:
                    val_min = int(val_range[0])
                    val_max = int(val_range[4])
                if verbosity == 2:
                    print i
                    print "bgcolor: %s" % bgcolor
                    print "value: %s" % value
                    print "range: min: %s, max: %s" % (val_min, val_max)
                scale_dict['scale'].append({
                    'bgcolor': bgcolor, 
                    'value': value, 
                    'min': val_min, 
                    'max': val_max}
                )
    if verbosity == 2:
        print scale_dict
    return scale_dict, metadata

def calc_hexa(entry, scales):
    """Determine the 
    hexadecimal value 
    for the entry"""
    for i in range(len(scales)):
        if scales[i]['min'] == None:
            if float('-inf') < entry < scales[i]['max']:
                value = scales[i]['bgcolor']
        elif scales[i]['max'] == None:
            if scales[i]['min'] <= entry < float('inf'):
                value = scales[i]['bgcolor']
        else:
            if scales[i]['min'] <= entry < scales[i]['max']:
                value = scales[i]['bgcolor']
    return value

def grab_data(url_pre, url_suffix, headers, periods, 
              chans, scale_dict, time_periods, means_dict, verbosity=0):
    """Grab the main data
    source that powers the
    application from the
    IRIS url"""
    if verbosity > 0:
        print "- Get data values for all channels for one period"
    values_dict = {} # Holder (for debug)
    values_final_dict = {} # Calculated vals (for debug)
    values_final_hexa_dict = {} # Calculated hexadecimal vals
    stacode_list = []
    incr = 1
    for p in periods:
        for c in chans:
            values_dict[c] = {}
            values_final_dict[c] = {}
            values_final_hexa_dict[c] = {}
            if verbosity > 0:
                print " - Grab data for period %s and channel %s" % (p, c)
            incr += 1
            full_url = '%s%s_%s%s' % (url_pre, c, p, url_suffix)
            try:
                values_page = urllib2.Request(full_url, None, headers)
            except urllib2.URLError:
                print urllib2.URLError
            except:
                print " - Unknown urllib2 error for url '%s'" % full_url
            else:
                opened_values_page = urllib2.urlopen(values_page)
                values_file = opened_values_page.readlines()
                values_keys = values_file.pop(0)
                values_keys_list = values_keys.split()
                del values_keys_list[0]
                if verbosity > 0:
                    print values_keys_list
                for line in values_file:
                    per_sta_list = line.split()
                    stacode = per_sta_list.pop(0)
                    stacode_list.append(stacode)
                    values_dict[c][stacode] = []
                    values_final_dict[c][stacode] = []
                    values_final_hexa_dict[c][stacode] = []
                    if len(per_sta_list) != len(means_dict):
                        print "Lists are not the same length - skipping chan '%s'" % c
                    else:
                        for i in range(len(per_sta_list)):
                            '''
                            Determine the real value to insert
                            which is entry_clean minus the period
                            value from the means_dict
                            Both lists should be the same length
                            Entry is of the form: -128/20 - need to rip out the /20 part
                            '''
                            entry_clean = per_sta_list[i].split('/')
                            this_period = time_periods[i]
                            if c == 'BHZ':
                                this_mean = means_dict[this_period]['BHZ']
                            else:
                                this_mean = means_dict[this_period]['BHE_BHN']
                            real_entry_float = float(entry_clean[0]) - float(this_mean)
                            real_entry = "%3.2f" % real_entry_float
                            real_hexa = calc_hexa(real_entry_float, scale_dict['scale'])
                            if verbosity > 0 and stacode == '936A' and c == 'BHZ':
                                lng_str = []
                                lng_str.append("Station:936A\t")
                                lng_str.append("Period:%s\t" % this_period)
                                lng_str.append("Channel:%s\t" % c)
                                lng_str.append("Raw val:%s\t" % entry_clean[0])
                                lng_str.append("Mean:%s\t" % means_dict[this_period]['BHZ'])
                                lng_str.append("Real entry: %s\t" % real_entry)
                                lng_str.append("Real hexa: %s" % real_hexa)
                                print ''.join(lng_str)
                            values_dict[c][stacode].append(entry_clean[0])
                            values_final_dict[c][stacode].append(real_entry)
                            values_final_hexa_dict[c][stacode].append(real_hexa)
                if debug:
                    print values_dict
                    print values_final_dict
    return values_dict, values_final_dict, values_final_hexa_dict, stacode_list

def datascope_station_retrieval(dbmaster, stacode_list, verbosity=0):
    """Use the Antelope Datascope
    interface to create a dictionary
    of all the Transportable Array
    stations"""
    if verbosity > 0:
        print "- Get station locations from dbmaster '%s'" % dbmaster
    sta_locations_dict = {}
    dbptr = datascope.dbopen(dbmaster, 'r')
    dbptr.lookup(table='snetsta')
    dbptr.join('site')
    dbptr.subset('snet =~ /TA/')
    if verbosity > 0:
        print '- Number of records: %d' % dbptr.query('dbRECORD_COUNT')
    for i in range(dbptr.query('dbRECORD_COUNT')):
        dbptr[3] = i
        sta, lat, lon = dbptr.getv('sta', 'lat', 'lon')
        if sta in stacode_list:
            sta_locations_dict[sta] = [lat,lon]
    return sta_locations_dict

def write_out_metadata(iris_metadata, scale_url, verbosity=0):
    """Create a metadata
    dictionary to help with
    debugging sources"""
    if verbosity > 0:
        print "- Write out helpful metadata"
    metadata_dict = {}
    metadata_dict['iris_days_string'] = iris_metadata['days']
    metadata_dict['iris_generation_time'] = iris_metadata['iris_generation_time']
    metadata_dict['last_modified'] = time()
    metadata_dict['last_modified_readable'] = strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())
    metadata_dict['source'] = scale_url
    return metadata_dict

def write_to_json(json_file, time_periods, scale_dict, means_dict, 
                  values_dict, values_final_dict, values_final_hexa_dict, 
                  sta_locations_dict, metadata_dict, verbosity=0):
    """Create JSON file
    on disc and write out
    dictionary"""
    if verbosity > 0:
        print "- Save to json file '%s'" % json_file
    f = open(json_file + '+', 'w')
    if verbosity > 0:
        complete_dict = {
            'periods': time_periods, 
            'scale': scale_dict, 
            'means': means_dict, 
            'values': values_dict, 
            'values_final': values_final_dict, 
            'values_final_hexa': values_final_hexa_dict, 
            'stations': sta_locations_dict, 
            'metadata': metadata_dict
        }
    else:
        complete_dict = {
            'periods': time_periods, 
            'scale': scale_dict, 
            'values_final_hexa': values_final_hexa_dict, 
            'stations': sta_locations_dict, 
            'metadata': metadata_dict
        }
    json.dump(complete_dict, f, sort_keys=True, indent=2)
    f.flush()

    try:
        os.rename(json_file+'+', json_file)
    except OSError:
        print "  - Cannot rename JSON file '%s'. Permissions problem?" % json_file
        return -1
    else:
        return 0

def main():
    """Grab and parse
    source data from 
    IRIS webpage
    """
    mean_noise_levels = 'http://crunch.iris.washington.edu/stationinfo/scripts/gks/MeanNoiseLevels'
    base_prefix = 'http://crunch.iris.washington.edu/stationinfo/TA/rank/PDFMode/PDFMode-'
    base_suffix = '_sec'
    # Just need one period
    # periods = ['1.037', '2.467', '30.443', '102.4']
    periods = ['1.037']
    chans = ['BHE', 'BHN', 'BHZ']
    # Spoof a browser
    user_agent = "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3"
    accept = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    accept_encoding = "gzip,deflate"
    keep_alive = "115"
    connection = "keep-alive"
    headers = {
        'User-Agent':user_agent,
        'Accept':accept,
        'Accept-Encoding':accept_encoding,
        'Keep-Alive':keep_alive,
        'Connection':connection
    }
    # HTML codes for mathematical symbols
    html_codes = {
        'lte': '&#x2264',
        'gte': '&#x2265',
        'lt': '&lt;',
        'gt': '&gt;'
    }

    print "Start of script at time %s" % strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())
    verbosity = determine_verbosity(verbose, debug)
    if verbosity == 2:
        dbmaster = '/anf/TA/rt/usarray/usarray'
        json_file = '/var/tmp/ranking.json'
    else:
        common_pf = 'common.pf'
        if verbosity > 0:
            print " - Parse configuration parameter file (%s)" % common_pf
        pfupdate(common_pf)
        dbmaster = pfget(common_pf, 'USARRAY_DBMASTER')
        json_path = '%s/tools/' % pfget(common_pf, 'CACHEJSON')
        json_file = '%sstation_ranking/ranking.json' % json_path
    means, time_periods = grab_means_and_periods(mean_noise_levels, headers, verbosity)
    scale_url = '%s%s_mean_%s%s.html' % (base_prefix, chans[0], periods[0], base_suffix)
    scale, iris_metadata = soup_metadata(scale_url, headers, html_codes, verbosity)
    vals, vals_final, hexa, stacodes = grab_data(base_prefix, base_suffix, headers, periods, chans, scale, time_periods, means, verbosity)
    sta_locs = datascope_station_retrieval(dbmaster, stacodes, verbosity)
    metadata = write_out_metadata(iris_metadata, scale_url, verbosity)
    write_to_json(json_file, time_periods, scale, means, vals, vals_final, hexa, sta_locs, metadata, verbosity)
    print "End of script at time %s" % strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())

    return 0

if __name__ == '__main__':
    status = main()
    sys.exit(status)
