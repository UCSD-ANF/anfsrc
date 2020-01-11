
"""
plot_beachballs.xpy

Example 1:
Plot events from mt table in usarray_2016 that are within the given location (-l) and time (-t)
    plot_beachballs -i "TA early2016" -l "-175, -125, 45, 75" -t "01/01/2016, 05/01/2016" usarray_2016

Example 2:
Plot all events in the database
    plot_beachballs -i "TA 2016" usarray_2016
"""

import os, sys

from datetime import datetime
from optparse import OptionParser
from mpl_toolkits.axes_grid1 import make_axes_locatable
from mpl_toolkits.basemap import Basemap
from obspy.imaging.mopad_wrapper import beach as beachball

import antelope.stock as stock

import numpy
from six import unicode

# Matplotlib
from matplotlib import pyplot

from .util import \
        Origin, strs2floats, distance, myround, mt_comp, convert_to_rgb


"""
Configure parameters from command-line.
"""

usage = "\n\tUsage:\n"
usage += "\t\tplot_beachballs [-v] [-g] [-l location] [-t time]  database\n"

parser = OptionParser(usage=usage)

# Verbose output
parser.add_option("-v", action="store_true", dest="verbose",
        default=False, help="verbose output")

# Plot low quality moment tensor in gray
parser.add_option("-g", action="store_true", dest="gray",
        default=False, help="add low quality moment tensors in gray")

# Map location bounds
# "minlon, maxlon, minlat, maxlat"
parser.add_option("-l", action="store", dest="loc", type="string", default=None,
        help="min_lon, max_lon, min_lat, max_lat")

# Time constraint
# "mintime, maxtime" in any form that antelope database accepts
# example: "02/01/2017, 03/01/2017"
parser.add_option("-t", action="store", dest="time", type="string", default=None,
        help="min_time, max_time")

# Title name
# example: TA Feb 2017
parser.add_option("-i", action="store", dest="title", type="string",
        default=None, help="fig info")

# load command line options and arguments
(options, args) = parser.parse_args()

# If we don't have 1 arguments then exit.
if len(args) != 1:
    sys.exit( usage );

# set databasename
databasename = args[0]

"""

 EXTRACT RESULTS FROM DATABASE

"""

# load origin class
origin = Origin(databasename, options)

# grab moment tensor and origin info for all events that satisfy time and location constraints if given
results = origin.moment_array()

# if dbmoment was run on the same orid with different model, non-unique orids will be presemt
# use SOCAL model as preferred and remove others (in general, I use SOCAL model)
# check for multiple orids and remove extras from results array (NOT FROM DATABASE)
orids = results[:,0]
uniq = [x for n,x in enumerate(orids) if x not in orids[:n]]
for orid in uniq:
    inds = numpy.where(orids == orid)
    if len(inds[0]) > 1:
        results = results[numpy.logical_not(numpy.logical_and(results[:,0]==orid, results[:,2]!='mt.SOCAL_MODEL'))]

# sometimes dbmoment was run on multiple orids with single evid, in this case:
# check for multiple evids -- select the prefor origin if multiple
evids = results[:,1]
uniq = [x for n,x in enumerate(evids) if x not in evids[:n]]
for evid in uniq:
    inds = numpy.where(evids == evid)
    if len(inds[0]) > 1:
        prefor = results[inds,3][0][0]
        orids = results[inds,0][0][0]
        if prefor == evid:
            results = results[numpy.logical_not(numpy.logical_and(results[:,1]==evid,
                    results[:,0]!=prefor))]
        else:
            results = results[numpy.logical_not(numpy.logical_and(results[:,1]==evid,
                    results[:,0]!=orids))]
        evids = results[:,1]

"""

GENERATE FIGURE

"""
# initialize figure
hei = 10
wid = 10
fig = pyplot.figure(figsize=(hei, wid))

fig_height = hei * fig.dpi
fig_width = wid * fig.dpi

# set axis 1
ax = fig.add_subplot(10 ,1, (1,9))

# alternative to length -- scales to axis box instead of entire figure
# either works since both will be the same no matter what database being use.
bbox = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
axis_width, axis_height = bbox.width, bbox.height
axis_width *= fig.dpi
axis_height *= fig.dpi

# set map boundaries

# set map boundaries

# grab lat/lon of events from results
lons = strs2floats(results[:,5])
lats = strs2floats(results[:,4])

# calculate min/max of lat/lon
minlon = numpy.min(lons)
maxlon = numpy.max(lons)
minlat = numpy.min(lats)
maxlat = numpy.max(lats)

# calculate the midpoint for lat/lon
mid_lon = minlon + (maxlon-minlon)/float(2)
mid_lat = minlat + (maxlat-minlat)/float(2)

# calculate distance between events
dist = []
for i in range(len(lons)-1):
    dist.append(distance(lons[i], lons[i+1], lats[i], lats[i+1]))

# get the maximum distance between events
maxdist = max(dist) * 1000

# set the width and height of map in m
width = maxdist * 3/2
height = maxdist * 3/2

# set map with lambert conformal projection centered at the mid_lon, mid_lat
map = Basemap(ax=ax, projection='lcc', resolution='f', width=width, height=height,
        lon_0=mid_lon, lat_0=mid_lat)

# add map data
map.drawcoastlines(linewidth=0.05)
map.drawcountries(linewidth=1)
map.drawstates(linewidth=0.5)
map.shadedrelief()

# measurements of figure in data units
data_height = numpy.diff([map.llcrnrlat, map.urcrnrlat])[0]
data_width = numpy.diff([map.llcrnrlon, map.urcrnrlon])[0]

# draw lat/lon grids
# depending on scale of map, set grid intervals differently

parallels_interval = myround(x=data_height/float(2), base=5)
meridians_interval = myround(x=data_width/float(2), base=5)

if parallels_interval == 0: parallels_interval = 5
if meridians_interval == 0: meridians_interval = 5

map.drawparallels(numpy.arange(0, 90, parallels_interval), linewidth=0.25,
        dashes=[4,2], zorder=2, labels=[True, False, False, False])
map.drawmeridians(numpy.arange(0, 360, meridians_interval), linewidth=0.25,
        dashes=[4,2], zorder= 2, labels = [False, False, False, True])


# add beachballs to plot

# set color bar
cm = pyplot.cm.jet

# sort results by magnitudes
# this will allow us to plot larger magnitudes behind smaller magnitudes
results = results[results[:,7].argsort()]

# set zorder - placement of object on figure from 0 (at back) to N (up front)
# 11 is arbitrary, it is greater than number of objects already plotted
z = 11 + len(results)

# for each row in results, grab data and plot
for row in results:
    # grab location
    lat = float(row[4])
    lon = float(row[5])

    # grab mag and depth
    mag = row[7]
    dep = row[6]

    # grab quality
    stat = row[16]

    # get x,y location
    x, y = map(lon, lat)

    # get moment tensor components and divide by scalr moment using mt_comp function
    mxx = mt_comp(row, 9)
    myy = mt_comp(row, 10)
    mzz = mt_comp(row, 11)
    mxy = -1 * mt_comp(row, 12)
    mxz = mt_comp(row, 13)
    myz = -1* mt_comp(row, 14)

    # size of beachball - tried to scale this so that the same size magnitude will look same on each plot
    # not quite there but does plot nicely on all maps
    factor = 400000
    width = factor * float(mag) * (numpy.mean([data_height, data_width])/float(fig_height))
    if stat=="Quality: 3" or stat=="Quality: 4" or stat=="Quality: 2":
        # color for beachball on colorscale based on depth
        color = convert_to_rgb(minval=numpy.min(strs2floats(results[:,6])),
                maxval=numpy.max(strs2floats(results[:,6])), val=float(dep), colors=cm)

        # moment tensor list
        mt = [mxx, myy, mzz, mxy, mxz, myz]

        # initiate beachball
        bb = beachball(mt, xy=(x,y), mopad_basis='NED', linewidth=1,
                alpha = 0.8, width=width, facecolor=color)

        # set zorder placement
        bb.set_zorder(z)

        # add beachball to plot
        ax.add_collection(bb)

        z = z - 1

    # plot low quality events in gray if -g flag present
    if options.gray and (stat=="Quality: 0" or stat=="Quality: 1"):
        mt = [mxx, myy, mzz, mxy, mxz, myz]
        bb = beachball(mt, xy=(x,y), mopad_basis='NED', linewidth=1, alpha=0.8,
                width=width, facecolor="gray")
        bb.set_zorder(5)
        ax.add_collection(bb)

# scale bar only extends to edge of plot
divider = make_axes_locatable(ax)
cax = divider.append_axes("right", size="5%", pad=0.05)
sm = pyplot.cm.ScalarMappable(cmap=cm, norm=pyplot.Normalize(vmin=numpy.min(strs2floats(results[:,6])),
        vmax=numpy.max(strs2floats(results[:,6]))))
sm._A = []
cb = pyplot.colorbar(sm, ax=ax, cax=cax)
cb.ax.invert_yaxis()
cb.set_label("Depth(km)", labelpad=10)

# info/title box
# grab start and end times
time = strs2floats(results[:,15])
stime = datetime.fromtimestamp(numpy.min(time)).strftime("%m/%d/%Y")
etime = datetime.fromtimestamp(numpy.max(time)).strftime("%m/%d/%Y")

# use -i flag option if present
if options.title: st = options.title

# otherwise database name and start/end time
else: st = " ".join([databasename, stime, "-", etime])

# add to plot
box = dict(boxstyle='square', facecolor='white')
ax.annotate(st, xy = (0.01,0.01), zorder=12, xycoords = 'axes fraction', xytext=(5,5),
        textcoords='offset points', bbox=box, size=20, ha='left', va='bottom')

# extra info panel
# initiate new axis
ax = fig.add_subplot(10, 1, 10, frameon=False)
ax.xaxis.set_visible(False)
ax.yaxis.set_visible(False)
ax.patch.set_alpha(0.0)

# add command line argument to plot
text = "%s\n" % ' '.join( sys.argv )
text += "Generated at %s" % stock.strtime(stock.now())
ax.annotate(unicode(text, "utf-8"), (1,0), xycoords="axes fraction", va="bottom",
        ha="right", fontsize=8, bbox=dict(edgecolor='gray', boxstyle='round, pad=0.5', fc="w"))

# folder to store figure
folder = "./dbmoment_images"

# if dbmoment_images does not exist, create directory
directory = os.path.dirname(folder)
if not os.path.exists(directory):
    os.mkdir(directory)

if options.title:
    title = options.title.replace(" ", "-")
    filename = "%s/%s_mt_results.png" % (folder, title)
else:
    filename = "%s/%s_%sl_%sr_%sb_%st_mt_results.png" % (folder, databasename,
            round(minlon), round(maxlon), round(minlat), round(maxlat))

pyplot.savefig(filename, edgcolor='none', pad_inches=0.5, dpi=100)

