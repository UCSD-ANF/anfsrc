#!/usr/bin/env python

import re
import os, sys
import numpy as np
import urllib, json

from subprocess import Popen

sys.path.append(os.environ['ANTELOPE'] + "/data/python")
sys.path.append("/Library/TeX/Root/bin/universal-darwin")
import antelope.stock as stock

from optparse import OptionParser

import matplotlib
#matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.artist import Artist
#import matplotlib.animation as animation
from mpl_toolkits.basemap import Basemap
#import matplotlib.animation as manimation
from matplotlib.animation import FFMpegWriter
from matplotlib.cbook import get_sample_data
import matplotlib.patheffects as path_effects
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

defaulturl = "http://anf.ucsd.edu/api/ta/stations?fields=sta,snet,lat,lon,time,endtime&all=true"

# Read configuration from command-line
usage = "Usage: %prog [options]"

parser = OptionParser(usage=usage)
parser.add_option("-d", action="store", dest="directory",
                            help="work directory", default='.')
parser.add_option("-c", action="store_true", dest="cumulative",
                            help="plot cumulative view ", default=False)
parser.add_option("-v", action="store_true", dest="verbose",
                            help="verbose output", default=False)
parser.add_option("-t", action="store", dest="time",
                            help="Time to look for active sites.", default=False )
parser.add_option("-e", action="store", dest="endtime",
                            help="Make monthly movie until endtime", default=False)
parser.add_option("-o", action="store", dest="outputfile", type="string",
                            help="Output file to save product", default=False)
parser.add_option("-w", action="store_true", dest="shadow", 
                            help="Add shadows for added icons", default=False)
parser.add_option("-u", "--url", action="store", dest="url", type="string",
                            help="API URL for metadata information", default=defaulturl)
parser.add_option("-m", action="store", dest="movie", 
                            help="Save to movie file", default=None)
parser.add_option("-a", action="store_true", dest="all", 
                            help="Plot all sites including inactive", default=False)

(options, args) = parser.parse_args()


def logger( msg, notify=False):
    if options.verbose or notify:
        print "[ %s ]: %s" % ( stock.strlocaltime( stock.now()),  msg )



def _decode_list(data):
    rv = []
    for item in data:
        if isinstance(item, unicode):
            item = item.encode('utf-8')
        elif isinstance(item, list):
            item = _decode_list(item)
        elif isinstance(item, dict):
            item = _decode_dict(item)
        rv.append(item)
    return rv

def _decode_dict(data):
    rv = {}
    for key, value in data.iteritems():
        if isinstance(key, unicode):
            key = key.encode('utf-8')
        if isinstance(value, unicode):
            value = value.encode('utf-8')
        elif isinstance(value, list):
            value = _decode_list(value)
        elif isinstance(value, dict):
            value = _decode_dict(value)
        rv[key] = value
    return rv

class DeploymentMap( ):
    def __init__( self, figsize=(20,20), dpi=100, videofile=None, cumulative=False):

        self.cwd = os.getcwd()
        self.start = None
        self.end = None
        self.start_year = None
        self.start_month = None
        self.end_year = None
        self.end_month = None
        self.time_array = []

        self.cumulative = cumulative
        self.plotall = False

        self.time_box = False
        self.valid_snets = {}
        self.icon_list = {}
        self.stations = {}
        self.lgnd = None

        self.icons = []

        self.dpi = dpi
        self.fps = 5
        self.videofile = videofile
        self.videobitrate = 5000

        self.basemap = None
        self.figsize = figsize
        self.fig = None
        self.ax = None

        self.coastlines = True
        self.continents = True
        self.countries = True
        self.states = True
        self.rivers = True
        self.size_h = 5800000
        self.size_w = 7000000
        self.center_lat = 52.
        self.center_lon = -111.
        self.maptype = 'shaded' # bluemarble, etopo or shaded

        self.url = None
        self.data = []

        self.networks = {
            'ci': {'color': '39EF5A', 'name': 'Caltech Regional Seismic Network'},
            'gt': {'color': 'BE140F', 'name': 'Global Tel. Network (USAF/USGS)'},
            'co': {'color': 'B7FED0', 'name': 'South Carolina Seismic Network'},
            'cn': {'color': '3FA9FF', 'name': 'Canadian National Seismograph Network'},
            'ag': {'color': '7A3027', 'name': 'Arkansas Seismic Network'},
            'ak': {'color': '0F66A4', 'name': 'Alaska Regional Network'},
            'iu': {'color': 'E3DC63', 'name': 'Global Seismograph Network (GSN - IRIS/USGS)'},
            'ii': {'color': 'E81BF9', 'name': 'Global Seismograph Network (GSN - IRIS/IDA)'},
            'im': {'color': '1B5210', 'name': 'International Miscellaneous Stations (IMS)'},
            'at': {'color': '80C715', 'name': 'National Tsunami Warning  System'},
            'av': {'color': '24E17C', 'name': 'Alaska Volcano Observatory'},
            'az': {'color': 'CBB416', 'name': 'ANZA Regional Network'},
            'ep': {'color': '7126B7', 'name': 'UTEP Seismic Network'},
            'ld': {'color': 'F56721', 'name': 'Lamont-Doherty Cooperative Network'},
            'nm': {'color': '40B943', 'name': 'Cooperative New Madrid Seismic Network'},
            'nn': {'color': '736379', 'name': 'Western Great Basin/Eastern Sierra Nevada'},
            'py': {'color': '500F50', 'name': 'PFO Array'},
            'ne': {'color': '7A4D3A', 'name': 'New England Seismic Network'},
            'pb': {'color': 'F6C1E6', 'name': 'Plate Boundary Observatory Borehole Seismic Network'},
            'ny': {'color': '288D93', 'name': 'Yukon Northwest Seismic Network(YNSN)'},
            'pe': {'color': 'A87C28', 'name': 'Penn State Network'},
            'po': {'color': '35A0B9', 'name': 'Portable Obs. Geological Survey Canada'},
            'ta': {'color': 'DF1D25', 'name': 'USArray Transportable Array (NSF - EarthScope )'},
            'dk': {'color': 'D23636', 'name': 'Danish Seismological Network'},
            'yo': {'color': 'D6EAF8', 'name': 'Yukon Observatory'},
            'yn': {'color': '8BAD5E', 'name': 'San Jacinto Fault Zone'},
            'bk': {'color': 'F9CB8B', 'name': 'Berkeley Digital Seismograph Network'},
            'c' : {'color': '6DFDD6', 'name': 'Chilean National Seismic Network'},
            'ok': {'color': '624A93', 'name': 'Oklahoma Seismic Network'},
            'g' : {'color': 'FBE5A6', 'name': 'GEOSCOPE'},
            'uu': {'color': '8FC0C2', 'name': 'University of Utah Regional Network'},
            'us': {'color': '48F1FB', 'name': 'United States National Seismic Network'},
            'kp': {'color': 'A7F31C', 'name': 'Korea Polar Seismic Network'},
            'sc': {'color': 'FBCB43', 'name': 'New Mexico Tech Seismic Network'},
            'sb': {'color': '245D13', 'name': 'UC Santa Barbara Engineering Seismology Network'},
            'n4': {'color': '6CACDA', 'name': 'Central and Eastern US Network (NSF, USGS, DoE, US-NRC'},
            'zy': {'color': '33A266', 'name': 'Portable Southern California Seismic Networks'}
        }


        # Need to set FIG now
        self.init_map()

        if self.videofile:

            # Don't want unicode but string.
            self.videofile = str( self.videofile )

            if self.cumulative:
                self.videofile  = 'cumulative' + self.videofile
            else:
                self.videofile  = 'rolling' + self.videofile

            logger( 'remove previous movie file[%s]' % self.videofile )
            if os.path.exists(self.videofile):
                os.remove(self.videofile)

            self.metadata = dict(title='Transportable Array', artist='ANF - EarthScope', comment='Transportable Array')

            self.writer = FFMpegWriter( fps=self.fps, bitrate=self.videobitrate, metadata=self.metadata )

            self.writer.setup( self.fig, outfile=self.videofile, dpi=self.dpi )
            self.writer.frame_format = 'rgba'

            if not self.writer.isAvailable():
                sys.exit( 'MovieWriter VALID? [%s]' % self.writer.isAvailable() )


    def init_map( self ):

        try:
            self.fig.close()
        except:
            pass

        self.fig = plt.figure( figsize=self.figsize, dpi=self.dpi )
        self.ax = self.fig.add_subplot(111)
        self.fig.tight_layout()

        # Lambert Conformal
        self.basemap = Basemap(width=self.size_w,height=self.size_h,projection='lcc',
                resolution='l',lat_1=30.,lat_2=65,
                lat_0=self.center_lat,lon_0=self.center_lon)


        if self.maptype == 'etopo':
            # Draw an etopo relief image
            self.basemap.etopo()
        elif self.maptype == 'bluemarble':
            # Draw the NASA Blue Marble image
            self.basemap.bluemarble()
        elif self.maptype == 'shaded':
            self.basemap.shadedrelief()
        else:
            logger('No background selected for map.', True)


        # draw parallels and meridians, but don't bother labelling them.
        parallels = self.basemap.drawparallels(np.arange(-90.,99.,10.), color='gray', linewidth=.5)
        meridians = self.basemap.drawmeridians(np.arange(-180.,180.,10.), color='gray', linewidth=.5)
        #parallels = self.basemap.drawparallels(np.arange(-90.,99.,10.), color='gray',
        #        linewidth=.5, labels=[1,1,1,1] )
        #meridians = self.basemap.drawmeridians(np.arange(-180.,180.,10.), color='gray',
        #        linewidth=.5, labels=[1,1,1,1] )


        if self.coastlines:
            self.basemap.drawcoastlines(linewidth=0.2)

        if self.continents:
            self.basemap.fillcontinents(lake_color='#bad3ec', color='none')

        if self.countries:
            self.basemap.drawcountries(linewidth=0.4)

        if self.states:
            self.basemap.drawstates(linewidth=0.2)

        if self.rivers:
            self.basemap.drawrivers(linewidth=0.1, color='b')



        # LOGOS
        self.add_img(self.cwd + '/images/TA_logo.png', 'png', .5, .6, .7)
        self.add_img(self.cwd + '/images/es_logo.png', 'png', .045, .05, .3)
        self.add_img(self.cwd + '/images/nsf1.gif', 'gif', .25, .05, .8)


        #plt.show()
        #sys.exit('done')

    def network_name( self, test ):

        logger('Adding network %s to legend.' % test)

        string = ''

        if test in self.valid_snets:
            string += '%4d  ' % self.valid_snets[test]
        else:
            string += '%4d  ' % 0

        string += '%s  ' % test.upper()

        if test in self.networks:
            string += '-  %s' % self.networks[test]['name']
        else:
            string += '-  UNKNOWN'

        logger( string )

        return string



    def add_img(self, img, img_format, x, y, zoom):

        fn = get_sample_data(img , asfileobj=False)
        new_img = plt.imread(fn, format=img_format)
        imagebox = OffsetImage(new_img, zoom=zoom)
        image = self.ax.add_artist( AnnotationBbox(imagebox, [x,y], xybox=(x, y),
                            box_alignment=(0., 0.),xycoords='axes fraction',
                            boxcoords="axes fraction",
                            bboxprops = dict( fc='none', ec='none' ) ) )


    def set_time(self, start=None, end=None):
        # fix time values

        now = stock.now()
        self.time_array = []

        if start:
            self.start = start
        else:
            self.start = now

        if end:
            self.end = end
        else:
            self.end = now

        # Extract values for year and month
        self.start_year = int(stock.epoch2str( int(self.start), '%Y'))
        self.start_month = int(stock.epoch2str( int(self.start), '%m'))
        self.end_year = int(stock.epoch2str( int(self.end), '%Y'))
        self.end_month = int(stock.epoch2str( int(self.end), '%m'))

        logger( 'start_year: %s    start_month:%s' % (self.start_year, self.start_month) )
        logger( 'end_year: %s    end_month:%s' % (self.end_year, self.end_month) )

        for year in range(self.start_year, self.end_year+1 ):
            for month in range(1, 13):

                if year == self.start_year and  month < int(self.start_month): continue
                if year == self.end_year and  month > int(self.end_month): continue

                self.time_array.append(  ( month, year ) )
                #self.time_array.append(  self.get_start_end_epoch( year, month ) )

                #logger( 'Adding time window: %s - %s' % \
                #        (stock.strdate(self.time_array[-1][0]),
                #            stock.strdate(self.time_array[-1][1])) )


    def get_data(self, url):

        logger( 'get_data( %s )' % url )

        self.url = url

        try:
            response = urllib.urlopen(self.url)
            self.data = json.loads(response.read(), object_hook=_decode_dict)
        except Exception,e:
            logger( '%s: %s' % (Exception,e) )
            sys.exit( 'Cannot find station data on %s' % self.url )

        if not self.data:
            logger( 'data: %s' % self.data )
            sys.exit( 'No data from URL: %s' % self.url )
        else:
            logger( 'Total sites in data object: %s' % len(self.data) )

    def get_start_end_epoch( self, year, month ):

        #logger( 'get_start_end_epoch(%d,%d)' % (year, month) )
        start = stock.str2epoch( "%d/1/%d" % (month,year) )

        if month == 12:
            year += 1
            month = 1
        else:
            month += 1

        end = stock.str2epoch( "%d/1/%d" % (month,year) )

        return start, end



    def clean( self ):

        while (self.icons):
            icon = self.icons.pop()
            try:
                icon.remove()
            except Exception,e:
                sys.exit('Problem %s: %s' % ( Exception,e) )

        try:
            self.lgnd.remove()
        except:
            pass
        try:
            self.time_box.remove()
        except:
            pass

        # This will also remove map background items
        #for item in self.ax.collections :
        #    item.remove()
        #del self.ax.collections[:]

        # Clean variables.
        self.valid_snets = {}
        self.icon_list = {}
        self.stations = {}



    def add_stations( self, start, end ):


        for station in self.data:

            logger( "Test: %s" % station['id'] )

            if 'lat' in station and 'lon' in station:

                # fix endtime value for site
                if not 'endtime' in station or station['endtime'] == '-':
                    station['endtime'] = stock.now()

                # Not valid station
                if not 'time' in station or station['time'] == '-': continue

                active = True

                if start:
                    if start > int(station['endtime']):
                        logger('%s out of time window' % stock.strdate(station['endtime']) )
                        active = False
                        #continue

                if end:
                    if end < int(station['time']):
                        logger('%s out of time window' % stock.strdate(station['time']) )
                        active = False
                        #continue

                logger( "Add: %s" % station['id'] )

                snet = station['snet'].lower()

                # overwrite endtime
                if self.plotall:
                    active = True

                if active:
                    markeredgecolor = '#'+self.networks[ snet ][ 'color' ]
                    markerfacecolor = '#'+self.networks[ snet ][ 'color' ]
                    markeredgewidth = .5
                    alpha = 1.
                    zorder = 2
                else:
                    markeredgecolor = '#'+self.networks[ snet ][ 'color' ]
                    markerfacecolor = 'lightgray'
                    markeredgewidth = .5
                    alpha = .6
                    zorder = 1

                if not active and not self.cumulative:
                    logger('%s not active' % station['id'] )
                    continue

                self.icons.append( self.basemap.plot( station['lon'],  station['lat'], linestyle="none",
                        marker='D', markerfacecolor=markerfacecolor, latlon=True,
                        markeredgecolor=markeredgecolor, zorder=zorder,
                        alpha=alpha, markeredgewidth=markeredgewidth,
                        path_effects=[path_effects.withSimplePatchShadow()])[0] )


                if snet in self.valid_snets:
                    self.valid_snets[ snet ] += 1
                else:
                    self.valid_snets[ snet ] = 1

                # track icons for legend
                self.icon_list[ snet ] = self.icons[-1]

                logger( "Now %s stations plotted" % len(self.icons) )

    def save_to_file( self, filename, year=False, month=False, show=False):
        #Save Image

        if not self.basemap:
            sys.exit('Missing map before saving plot to file')

        if filename:
            # split list of filenames by commas
            for f in options.outputfile.split(','):

                if self.cumulative:
                    ftype = 'cumulative'
                else:
                    ftype = 'rolling'

                f = '%s_%s' % ( ftype, f )

                if year and month:
                    f = '%04d_%02d_%s' % (year,month,f)

                logger('Save to file [%s]' % f , True )
                self.fig.savefig( f, dpi=self.dpi, frameon=None,
                            bbox_inches='tight', pad_inches=.0 )


            if show:
                process = Popen(['display', f])

    def make_movie( self ):

        if self.videofile:

            logger('Save movie [%s]' % self.videofile , True)
            self.writer.finish()


    def plot_map( self, outputfile=False , plotall=False, verbose=False ):

        self.plotall = plotall

        for segment in self.time_array:

            self.plot_map_single( *segment )

            if outputfile:
                self.save_to_file( outputfile, year=segment[1],
                        month=segment[0], show=verbose )

        # Make movie if variable is set
        self.make_movie()


    def plot_map_single( self, month, year ):

        if not self.basemap:
            sys.exit('Missing map before plotting call')

        s, e =  self.get_start_end_epoch( year, month )

        logger( 'Time: %s    Endtime:%s' % (stock.strdate(s), stock.strdate(e)) )

        self.clean()

        self.add_stations( s, e )


        if not len(self.icons):
            logger('No stations plotted from object.')
            sys.exit('Something wrong with plotting of sites.')



        # Create a legend with only labels
        self.lgnd = self.ax.legend([ self.icon_list[x] for x in sorted(self.icon_list)],
                        [self.network_name(x) for x in sorted(self.icon_list)],
                        fancybox=True, shadow=True, numpoints=1, borderpad=1.3,
                        markerscale=1.4, loc=6, prop={'size':9, 'family': 'monospace'})
        self.lgnd.get_frame().set_alpha(.3)
        self.lgnd.get_frame().set_color('#C4CED5')

        # Add time tags

        # these are matplotlib.patch.Patch properties

        # place a text box in upper left in axes coords
        self.time_box = self.ax.text(0.8, 0.05, '%2s/%4s' % (month,year),
                    transform=self.ax.transAxes, fontsize=24,
                    bbox={'boxstyle':'round,pad=0.4', 'facecolor':'white', 'alpha':1} )

        plt.draw()

        # for movie
        if self.videofile:
            for x in range(self.fps):
                self.writer.grab_frame()

# Change to work directory
logger('Change to work directory %s' % options.directory )
os.chdir( options.directory )
logger('Now working on [%s]' % os.getcwd(), True )

raw_map = DeploymentMap( videofile=options.movie, cumulative=options.cumulative )

# Make monthly maps
raw_map.set_time( start=options.time, end=options.endtime )
raw_map.get_data( options.url )
raw_map.plot_map( options.outputfile, plotall=options.all, verbose=options.verbose )

# Test if we need a picture of current state
#if options.time or options.endtime:
#    raw_map.set_time()
#    raw_map.plot_map( options.outputfile, options.verbose )
#
