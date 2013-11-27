##############################################################################
# Name          : Plot traces
# Purpose       : Simple scirpt to plot segments
# Inputs        : start end sta_regex chan_regex
# Pf file       : none
# Returns       : none
# Flags         : none
# Author        : Juan Reyes
# Email         : reyes@ucsd.edu
# Date          : 2/22/2013
##############################################################################

import sys
import os
import pylab
import re
from optparse import OptionParser

sys.path.append( os.environ['ANTELOPE'] + '/data/python' )

try:
    import antelope.datascope as datascope
    import antelope.stock as stock
except Exception,e:
    sys.exit("\nProblem loading Antelope libraries: %s\n" % e)

" Configure from command-line. "
#{{{

usage = '\nUSAGE:\n\t%s [-v] [-n ./file_name.png] [-f filter] [-l "lat,lon"] [-e event_time] [-s "290|300"] [-m amplitude_mulitiplier] db start end sta_regex chan_regex\n\n' % __file__


parser = OptionParser()
parser.add_option("-v", "--verbose", dest="verbose", action="store_true")
parser.add_option("-f", "--filter", dest="filter", action="store")
parser.add_option("-a", "--arrivals", dest="arrivals", action="store_true")
parser.add_option("-l", "--event_location", dest="event_location", action="store")
parser.add_option("-s", "--speed", dest="speed", action="store")
parser.add_option("-e", "--event_time", dest="event_time", action="store")
parser.add_option("-m", "--amp_mult", dest="amp_mult", action="store")
parser.add_option("-n", "--name", dest="name", action="store")
parser.add_option("-d", "--display", dest="display", action="store_true")


(options, args) = parser.parse_args()

if options.event_location:
    coords = options.event_location.split(',')
    if len(coords) != 2 :
        sys.exit("\nProblem with location: %s Format='lat,lon'\n" % options.event_location)
    d_lat = float(coords[0])
    d_lon = float(coords[1])
    event_location = True
else:
    event_location = False

if options.arrivals:
    show_arrivals = True
else:
    show_arrivals = False

if options.display:
    display = True
else:
    display = False

if options.verbose:
    verbose = True
else:
    verbose = False

if options.speed:
    speed = [float(x) for x in options.speed.split('|')]
else:
    speed = []

if options.event_time:
    event_time = stock.str2epoch(options.event_time)
else:
    event_time = False

if options.name:
    name = os.path.abspath(options.name)
else:
    name = False

if options.filter:
    filter_type = str(options.filter)
else:
    filter_type = False

if options.amp_mult:
    amp_mult = float(options.amp_mult)
else:
    amp_mult = 1

if len(args) != 5:
    sys.exit(usage)

#}}}


"""
Get options.
"""
#{{{
database = os.path.abspath(args[0])
start = stock.str2epoch(args[1])
end = stock.str2epoch(args[2])
sta = args[3]
chan = args[4]
#}}}


"""
Verify that we have what we need. 
"""
#{{{
if start > stock.now() or start < 0:
    sys.exit("\nProblem with start time: %s => %s\n" % (args[1],start))
if end > stock.now() or end < 0:
    sys.exit("\nProblem with end time: %s => %s\n" % (args[2],end))

if event_location:
    if d_lat < -90.0 or d_lat > 90.0:
        sys.exit("\nProblem with lat of event: %s => %s\n" % options.distance)
    if d_lon < -180.0 or d_lon > 180.0:
        sys.exit("\nProblem with lat of event: %s => %s\n" % options.distance)

if speed:
    if not event_time:
        sys.exit('\nWee need an event time for adding speed lines.\n')

if name:
    if not re.match('.*\.(png|eps|ps|pdf|svg)$',name):
        sys.exit('\nOnly these types of images are permited: png, pdf, ps, eps and svg.\n')

#}}}


"""
Get all the databases ready. Set the 
pointers to the tables to the objects
in variables wfdisc, arrival and site. Keep main 
pointer db open. 
"""
#{{{
db = datascope.dbopen( database, "r" )

try:
    wfdisc = db.lookup( table = "wfdisc" )
except Exception,e:
    sys.exit('\nProblem at dbopen of wfdisc table: %s\n' % e)

if event_location:
    try:
        site = db.lookup( table = "site" )
    except Exception,e:
        sys.exit('\nProblem at dbopen of site table: %s\n' % e)

if show_arrivals:
    try:
        arrival = db.lookup( table = "arrival" )
    except Exception,e:
        sys.exit('\nProblem at dbopen of arrival table: %s\n' % e)
#}}}


"""
We need to subset the wfdisc and the site tables
to verify station data and location.
"""
#{{{
" Subset our database for sta and channel" 
wfdisc = wfdisc.subset("sta =~ /%s/ && chan =~ /%s/" % (sta,chan))

" Verify table after subset." 
if wfdisc.query('dbRECORD_COUNT') < 1:
    sys.exit( 'No stations after subset sta=~/%s/ && chan =~/%s/' % (sta,chan) )

wfdisc = wfdisc.sort(["sta","chan"])
traces = wfdisc.query('dbRECORD_COUNT')
#}}}

"""
We need to calculate the distance for each station
to the event. This is done before we pull data and 
start plotting so we know the size available for 
each trace. 
"""
#{{{
distance = []
sites = {} 
diff = 0
space = 1
if event_location:
    " Subset site table for sta." 
    try: 
        site = site.join(wfdisc)
        site = site.subset("sta =~ /%s/" % sta)
    except Exception,e:
        sys.exit('\nProblem during site and wfdisc join\n')

    " Verify table after subset " 
    if site.query('dbRECORD_COUNT') < 1:
        sys.exit( 'No stations after subset sta=~/%s/ && chan =~/%s/' % (sta,chan) )

    for i in range(site.query('dbRECORD_COUNT')):
        site.record = i
        d = site.ex_eval('distance(lat,lon,%s,%s)' % (d_lat,d_lon) )
        distance.append( d )
        sites[site.getv('sta')[0]] = d 

    " Add 10% to the max min values. "
    #space = ((max(distance)-min(distance))*1.1) / traces
#}}}

""" 
Get data for our subset of stations and channels.
"""
#{{{

" Extract the data and plot it. "
done = {}
trace = 0

"""
Calculate the size of the lines
that we need to plot.
"""
if traces > 100:
    line_size = 0.4
elif traces > 60:
    line_size = 0.6
elif traces > 30:
    line_size = 0.8
else:
    line_size = 1

for i in range(traces):

    wfdisc.record = i
    s = wfdisc.getv('sta')[0]
    c = wfdisc.getv('chan')[0]
    fullname = "%s_%s" % (s,c)


    " Keep track of the stations that are done."
    if fullname in done: continue
    done[fullname] = 1

    if event_location:
        distance = sites[s]
        "Replace with full name."
        del sites[s]
        sites[fullname] = distance 
    else:
        distance = -len(done)
        sites[fullname] = distance 


    if verbose: print "GET DATA FOR: %f %f %s" % ( start, end, fullname)

    #v = wfdisc.sample(start,end,s,c,False)

    try:
        tr = datascope.trloadchan( wfdisc, start, end, s, c )
    except Exception,e:
        sys.exit('\nProblem during trloadchan of data for %s %s %s %s\n' % (start,end,s,c))

    tr[3] = 0
    #tr.filter('DEMEAN')
    nsamp = int(tr.ex_eval('nsamp'))
    samplerate = int(tr.ex_eval('samprate'))
    if verbose: print "nsamp = %s" % nsamp
    if verbose: print "samplerate = %s" % samplerate

    if not nsamp > 1: continue

    if filter_type: 
        tr.filter(filter_type)


    tr_start = tr.getv('time')[0]
    tr_end = tr.getv('endtime')[0]

    if nsamp > 4000:
        binsize = int(nsamp/4000)
    else:
        binzise = 1

    v = pylab.array(tr.databins(binsize))

    " Build a time array for our tuples."
    time_axis = pylab.arange(tr_start,tr_end,((tr_end-tr_start)/len(v)))

    tr.trfree()


    " Find the min and the max values in the tuples."
    data_max = float('-Inf') 
    data_min = float('Inf') 
    for x in v:
        for y in x:
            if y is None: continue
            if y > data_max: data_max = y
            if y < data_min: data_min = y


    data_range = (data_max - data_min)/2
    data_range_all = (data_max + data_min)/2

    timelist = []
    datalist = []
    for i in range(len(v)):
        timelist.append( ((v[i][0] - data_range_all) / data_range) * amp_mult + distance)
        timelist.append( ((v[i][1] - data_range_all) / data_range) * amp_mult + distance)

        timelist.append(None)
        datalist.append(time_axis[i])
        datalist.append(time_axis[i])
        datalist.append(None)

    pylab.plot(datalist,timelist,'#FFFE00',lw=line_size)

    if show_arrivals:
        " Look for arrivals. "
        arrivals = []
        temp_arrival = arrival.subset("sta =~ /%s/ && chan =~ /%s/ && time > %s && time < %s" % (s,c,tr_start,tr_end))
        for p in range(temp_arrival.query('dbRECORD_COUNT')):
            temp_arrival.record = p
            at = temp_arrival.getv('time')[0]
            pylab.plot([at,at],[distance-(0.5*amp_mult),distance+(0.5*amp_mult)],'r',lw=0.4)
        temp_arrival.free()
#}}}


"""
Get/Set some information about the plot.
Set size and the colors.
"""
#{{{
x1,x2,y1,y2 = pylab.axis()
ax = pylab.gca()
pl = pylab.gcf()
ax.patch.set_facecolor('#000782')
pl.set_facecolor('#D9DAE6')
DefaultSize = pl.get_size_inches()
pl.set_size_inches( (DefaultSize[0]*2, DefaultSize[1]*2) )
#}}}

" Set doted grid on plot."
#{{{

for x in ax.xaxis.get_ticklocs():
    pylab.plot([x,x],[y1,y2],'w',lw=0.3)

#}}}


"""
Add the distance to the top of the x axis. If not sorted by distance then 
set the limit of the axis by the amount of traces plotted."
"""
#{{{
if event_location:
    ay2 = ax.twinx()
    ay2.set_ylabel('Distance in degrees')
else:
    pylab.ylim([-(len(done)+1),0])
#}}}


" Add the name of the stations and channels to the plot."
#{{{
size = 10
if len(sites) > 20: size = 8
if len(sites) > 30: size = 5
if len(sites) > 50: size = 3
locations = [sites[x] for x in sites]
labels = [x for x in sites]
ax.set_yticks(locations)
ax.set_yticklabels(labels,fontsize=size)
x_ax = [stock.epoch2str(y,'%D\n%H:%M UTC') for y in ax.xaxis.get_ticklocs()]
ax.set_xticklabels(x_ax,fontsize=10)
pylab.xlim([start,end])
#}}}


" Add the velocity lines."
#{{{
for s in speed:
    " Convert from m/s to deg/s."
    ns = s/1000
    ns *= .00898311
    " Great Circle. "
    pylab.plot([(y1/ns)+event_time,(y2/ns)+event_time],[y1,y2],'k',lw=1)
    pylab.text(((y2/ns)+event_time), y2, ' %s m/s' % s, color='r', horizontalalignment='right', verticalalignment='top',
                            bbox={'facecolor':'k', 'alpha':1.0, 'pad':2}, fontsize=10)

    " Great Circle Complement. "
    c_x1 = ((360-y1)/ns)+event_time
    c_x2 = ((360-y2)/ns)+event_time
    pylab.plot([c_x1,c_x2],[y1,y2],'g',lw=1)
    pylab.text(c_x2, y2, ' %s m/s' % s, color='r', horizontalalignment='right', verticalalignment='top',
                            bbox={'facecolor':'g', 'alpha':1.0, 'pad':2}, fontsize=10)

#}}}


" Set the title of the plot."
#{{{
text = '%s [%s,%s]   ' % (database,sta,chan)
if filter_type: 
    text += ' filter:"%s"' % filter_type
else:
    text += ' filter:"NONE"'

pylab.title(text)
#}}}

" Save plot and/or open final file. "
#{{{
if name:
    pylab.savefig(name,bbox_inches='tight', facecolor=pl.get_facecolor(), edgecolor='none',pad_inches=0.5,dpi=200)
    if display: os.system( "open %s" % name )
else:
    pylab.show()
#}}}


sys.exit()


