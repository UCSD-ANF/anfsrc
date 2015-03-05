""" Python script to remake station detail maps
Calls make_dbrecenteqs_map Perl script written
by Kent Lindquist

@notes       1. Use tempfile to dynamically create a tmp pf file
             on the fly. Delete after use.
"""

import tempfile
import re
from subprocess import call
from datetime import datetime, timedelta
from optparse import OptionParser


import antelope.datascope as datascope
import antelope.stock as stock

usage = "Usage: %prog [options]"
parser = OptionParser(usage=usage)
parser.add_option("-v", action="store_true", dest="verbose", help="verbose output", default=False)
(options, args) = parser.parse_args()
if options.verbose:
    verbose = True
else:
    verbose = False

class GetMetadata:
    """Class for getting metadata
    """
    def __init__(self, dbptr, stapf, verbose=False):
        """Initialize"""
        self.dbptr = datascope.dbopen(dbptr, 'r')
        self.stapf = stock.pfupdate(stapf)
        self.verbose = verbose
    def get_networks(self):
        """Get unique networks
        """
        network = {}
        networks = self.dbptr.lookup(table='site')
        networks = networks.join('snetsta')
        networks = networks.sort(('snet'), unique=True)
        for i in range(networks.query('dbRECORD_COUNT')):
            networks.record = i
            mynetwork = networks.getv('snet')[0]
            color = self.stapf['network'][mynetwork]['color']
            rgb = self.stapf['colors'][color]['rgb'].replace(',', '/')
            network[mynetwork] = rgb
        return network
    def get_stations(self):
        """Get unique stations
        """
        stations = {}
        db = self.dbptr.lookup(table='site')
        db = db.join('snetsta')
        db = db.join('deployment', outer=True)
        # db.subset('snet!~/TA/')
        #db = db.subset('offdate==NULL || offdate > now()')
        db = db.sort(('snet','sta'), unique=True)
        for i in range(db.query('dbRECORD_COUNT')):
            db.record = i
            # Get values
            sta, lat, lon, snet = db.getv('sta', 'lat', 'lon', 'snet')
            stations[sta] = {}
            stations[sta]['lat'] = lat
            stations[sta]['lon'] = lon
            stations[sta]['snet'] = snet
            stations[sta]['ps'] = '%s_%s.ps' % (snet, sta)
            stations[sta]['png'] = '%s_%s.png' % (snet, sta)
        return stations

class RecreateMap:
    """Class to recreate maps
    """
    def __init__(self, new_color, orig_color, pffile):
        self.new_color = new_color
        self.orig_color = orig_color
        self.pffile = pffile

    def write_pf(self):
        """Open pre-existing pf file
        and replace with new one, 
        with correct color
        """
        f = open(self.pffile, 'r')
        blob1 = f.read()
        f.close()
        blob2 = re.sub(r'.*focus_sta_color.*'+self.orig_color, '\tfocus_sta_color         '+self.new_color, blob1)
        this_tempfile = tempfile.mktemp(suffix='.pf')
        f = open(this_tempfile, 'w') 
        f.write(blob2)
        f.close()
        # Test to see if it got replaced ok
        pf = stock.pfupdate(this_tempfile)
        if verbose:
            focus_sta_new_color = pf['mapspec']['focus_sta_color']
            print '   - Tempfile is: %s' % this_tempfile
            print '   - Focus station color is now %s' % focus_sta_new_color
        return this_tempfile

    def run_cmd(self, cmd):
        """Run the command in a subprocess
        """
        try:
            retcode = call(cmd, shell=True)
        except OSError,e:
            print 'Execution failed: %s' % e
            return False
        else:
            if retcode < 0:
                print 'Child terminated by signal: %s' % retcode
            return True

def main():
    """Main processing script
    for (re)creating station 
    detail maps
    """
    pffile = 'pf/make_dbrecenteqs_map.pf'
    pf = stock.pfupdate(pffile)
    usarray_dbmaster = pf['USARRAY_DBMASTER']
    cacheimages = pf['CACHEIMAGES']
    tmpfile = '/var/tmp/make_dbrecenteqs_map_output'
    degrees = 2
    outputpath = '%s/maps/stations/' % cacheimages
    month = 60*60*24*28
    sub_exec = 'make_dbrecenteqs_map'
    # Get list of colors for different networks
    stations_pf = 'stations.pf'
    focus_sta_color = pf['mapspec']['focus_sta_color']

    print 'Start of script to recreate station maps at %s' % datetime.utcnow()
    mymetadata = GetMetadata(usarray_dbmaster, stations_pf)
    network_colors = mymetadata.get_networks()
    stations = mymetadata.get_stations()

    for key in sorted(stations.iterkeys()):
        print 'Working on station: %s' % key
        snet = stations[key]['snet']
        replace_color = network_colors[snet]

        if os.path.isfile('%s/%s' % (outputpath, stations[key]['png'])):
            # Is image older than a month?
            stat = os.stat( '%s%s' % (outputpath, stations[key]['png']))
            delta = datetime.fromtimestamp(stat.st_mtime) - datetime.now()
            month_ago = timedelta(days=-30)
            # Comparing negative values, so have to do delta < month_ago
            if delta < month_ago:
                print '  - Station map %s is older than a month - recreating' % stations[key]['png']
                rebuild = True
            else:
                rebuild = False
        else:
            rebuild = True

        # Test for station maps
        if rebuild:
            print '  - Station map %s does not exist - creating' % stations[key]['png']
            mymap = RecreateMap(replace_color, focus_sta_color, pffile)
            pffile_tmp = mymap.write_pf()
            print '  - Temp pf file %s' % pffile_tmp
            mycmd = "%s -p %s -c %s:%s -s %s -l %s -f '%s' -r %s %s%s" % (sub_exec, pffile_tmp, stations[key]['lon'], stations[key]['lat'], usarray_dbmaster, tmpfile, key, degrees, outputpath, stations[key]['ps'])
            print '  - CMD: [%s]' % mycmd
            mymap.run_cmd(mycmd)
            os.remove(pffile_tmp)

        # Clean up
        if os.path.isfile('%s/%s' % (outputpath, stations[key]['ps'])):
            os.remove('%s/%s' % (outputpath, stations[key]['ps']))
        if os.path.isfile('%s/%s.pf' % (outputpath, stations[key]['png'])):
            os.remove('%s/%s.pf' % (outputpath, stations[key]['png']))
        # Final check - did the file get made?
        if not os.path.isfile('%s/%s' % (outputpath, stations[key]['png'])):
            print '  - Station %s_%s map still does not exist. Something went wrong' % \
                    (outputpath, stations[key]['png'])
    print 'End of script to recreate station maps at %s' % datetime.utcnow()

if __name__ == '__main__':
    main()
