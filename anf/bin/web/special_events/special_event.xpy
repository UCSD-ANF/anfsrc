
import re
import json
import string
import socket
import pprint
import operator
from subprocess import call
from collections import defaultdict
from datetime import datetime, timedelta
from optparse import OptionParser

import pylab as pylab

try:
    from antelope.elog import init as init
    from antelope.elog import notify as log
    from antelope.elog import notify as notify
    from antelope.elog import complain as complain
    from antelope.elog import die as die
    import antelope.stock as stock
    import antelope.datascope as datascope
except Exception,e:
    sys.exit('Problems loading Antelope libs: %s' % e )

import locale
locale.setlocale(locale.LC_ALL, 'en_US')

init(sys.argv[0])

def flip_angle(angle):
    angle = angle - 180
    if angle < 0: angle += 360
    return angle

def no_output(msg=''):
    '''
    Just a simple way to silence log
    if needed.
    '''
    pass


def yes_no(question, default="yes"):
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    prompt = " [y/n] "

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")

def _get_plots(dbname,time,evid,subset,filename,start=False,end=False,maxt=False,sta=False,jump=False,filterdata=False):

    try:
        os.remove(filename)
    except:
        pass

    cmd = 'plot_traces -e %s -a -o ' % evid
    cmd = cmd + ' -n "%s"' % filename
    if sta:
        cmd = cmd + ' -s "sta =~/%s/ && %s"' % (sta,subset.strip('"'))
    else:
        cmd = cmd + ' -s "%s"' % subset.strip('"')
    if filterdata: cmd = cmd + ' -f "%s"' % filterdata
    if maxt: cmd = cmd + ' -m %s' % maxt
    if jump: cmd = cmd + ' -j %s' % jump
    cmd = cmd + ' %s' % dbname
    if start and end: cmd = cmd + ' %s %s' % (start,end)

    notify('get_plots() => %s' % cmd)

    if call( cmd, shell=True):
        notify('SOME ERROR ON THIS: %s' % cmd )

    return cmd

def check_value(value=0):
    value = float(value)
    if value > 0.000: return True
    return False

def parse_filter(name=False):

    parts = name.split()

    if not name: return "Not filtered."

    if parts[0] == 'BW':
        if check_value(parts[1]) and check_value(parts[3]):
            string = "%s to %s Hz bandpass Butterworth filter" % \
                    (parts[1],parts[3])

        elif check_value(parts[1]):
            string = "%s Hz highpass Butterworth filter" % parts[1]

        else:
            string = "%s Hz lowpass Butterworth filter" % parts[3]
    else:
        string = "Filter %s" % name

    string += " has been applied to data."

    return string



def parse_cities(name,distance,angle):

      log( "name:%s distance:%s angle:%s" % (name,distance,angle) )

      bearings = ["NE", "E", "SE", "S", "SW", "W", "NW", "N"]

      cities = {}

      if angle < 0: angle += 360

      index = int(float(angle) / 45)
      b = bearings[index]

      dist = abs(int(float(distance)))
      #dist = locale.format("%d", distance, grouping=True)

      log( "%s km to %s" % (dist,name) )

      cache = {}
      cache[b] = name

      return ( dist, b, int(angle), "%s km to %s" % (dist, name) )


def get_cities(lat,lon,filename,maxplaces=1):
    '''
    Make a list of populated place close to event
    '''

    log('get_cities(%s,%s,%s)' % (lat,lon,maxplaces))

    cities = {}

    # Database in /anf/shared/maps/worldcities/world_cities.places
    dbname = '/anf/shared/maps/worldcities/world_cities'
    log( 'Getting %s' % dbname )

    with datascope.closing(datascope.dbopen( dbname , 'r' )) as db:

        dbview = db.lookup(table='places')

        if not dbview.record_count:
            log('No cities in db ')
            return {}

        for temp in dbview.iter_record():
            azimuth  = float(temp.ex_eval( 'azimuth(lat,lon,%s,%s)' % (lat, lon) ) )
            distance = float(temp.ex_eval( 'distance(lat,lon,%s,%s)' % (lat, lon) ) )
            distance = float(temp.ex_eval( 'deg2km(%s)' % distance ) )

            cities[ temp.getv('place')[0] ] = [distance,azimuth]

    cities = sorted(cities.items(), key=operator.itemgetter(1))

    cache = {"NE":{},
             "E":{},
             "SE":{},
             "S":{},
             "SW":{},
             "W":{},
             "NW":{},
             "N":{}
             }

    for city in cities[0:maxplaces]:
        log( '%s => %s' % (city[0],city[1]) )

    alldist = []
    maxdist = 0
    mindist = 999999999
    for x in cities:
        #log('x:[%s]' % json.dumps(x) )
        dist, az, angle, string = parse_cities(x[0],x[1][0],x[1][1])
        log('distance:%s angle:%s azimuth:%s, string:%s' % (dist,angle,az,string))
        if len(cache[az]) >= maxplaces: continue
        alldist.append( dist )
        #cache[b].append( string )
        cache[ az ][ dist ] = (angle,string)
        if dist < mindist: mindist = dist
        if dist > maxdist: maxdist = dist

    stddev = pylab.std( alldist )
    mean = pylab.mean( alldist )

    #mindev = mean - stddev
    #maxdev = mean + stddev
    mindev = 0
    maxdev = stddev

    #######    PLOT CITIES ON POLAR SYSTEM  #########
    log('min:%s max:%s' % (mindist,maxdist))
    fig = pylab.figure()
    #ax = fig.add_subplot(111, polar=True,axisbg='#d5de9c')
    ax = fig.add_subplot(111, polar=True)
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    pl = pylab.gcf()
    pylab.thetagrids([0, 90, 180, 270],
        labels=['N', 'E', 'S', 'W'])


    for c in cache:
        for dist in cache[c]:
            if dist > maxdev: continue
            if dist < mindev: continue
            angle,string = cache[c][dist]
            angle = flip_angle(angle)
            log('distance:%s angle:%s group:%s' % (dist,angle,c))
            ax.plot([angle/180.*pylab.pi], [dist], 'o')
            if angle > 0 and angle <= 90:
                textangle = 25
                ha='left'
                va='bottom'
            elif angle > 90 and angle <= 180:
                textangle = -25
                ha='left'
                va='top'
            elif angle > 180 and angle <= 270:
                textangle = 25
                ha='right'
                va='top'
            else:
                textangle = -25
                ha='right'
                va='bottom'

            # need to convert angle to radians!!!
            ax.annotate(string,
                    xy=(angle/180.*pylab.pi, 1 + dist),
                    horizontalalignment=ha,
                    verticalalignment=va,
                    rotation=textangle)

            # need to convert angle to radians!!!
            pylab.arrow(angle/180.*pylab.pi, 0, 0, dist, alpha = 0.5,
                            edgecolor = 'k', facecolor = 'k', lw = 1)

    pylab.savefig(filename,bbox_inches='tight', facecolor=pl.get_facecolor(), edgecolor='none',
            pad_inches=0.5,dpi=100)

    #pylab.show()

    return filename


def _get_sta_list(db,time,lat, lon, subset=False):
    '''
    Make a list of stations that recorded the event
    '''

    log('get_display_list(%s,%s,%s)' % (time,lat,lon))

    results = {}

    yearday = stock.yearday(time)

    steps = ['dbopen site']

    snetsta_table = db.lookup(table='snetsta')
    if snetsta_table.query(datascope.dbTABLE_PRESENT):
        steps.extend(['dbjoin snetsta'])

    steps.extend(['dbsubset (ondate < %s) && ( offdate == NULL || offdate > %s)' % \
            (yearday,yearday)] )

    if subset:
        steps.extend(['dbsubset %s' % subset.strip('"')] )

    log( ', '.join(steps) )

    with datascope.freeing(db.process( steps )) as dbview:

        if not dbview.record_count:
            log('No stations for time [%s]' % yearday)
            return results

        for temp in dbview.iter_record():
            distance = temp.ex_eval( 'distance(lat,lon,%s,%s)' % (lat, lon) )
            distance = temp.ex_eval( 'deg2km(%s)' % distance )

            results[ temp.getv('sta')[0] ] = distance

    results = sorted(results.items(), key=operator.itemgetter(1))

    for sta in results[0:5]:
        log( '%s => %s' % (sta[0],sta[1]) )
    log('...')
    for sta in results[-5:-1]:
        log( '%s => %s' % (sta[0],sta[1]) )

    return [(x[0],locale.format("%0.1f", x[1], grouping=True)) for x in results]
    return results

def _get_start_end(time,arrivals,multiplier=1):

    start = 2*time
    end = 0

    log('event time: %s' % time )

    for a in arrivals:
        log('arrival time: %s' % a['time'] )
        delta = (a['time'] - time) * multiplier
        log('delta: %s' % delta )
        new_start = int(a['time']) - int(delta/2)
        new_end = int(a['time']) + (delta )
        log('new_start: %s' % new_start )
        log('new_end: %s' % new_end )
        if start > new_start: start = new_start
        if end < new_end: end = new_end

    log('start: %s end: %s' % (start,end))

    if (end - start) < 240:
        start, end = _get_start_end(time,arrivals,multiplier+1)

    return (start,end)



def _get_arrivals(db,orid,subset=False):
    '''
    Lets try to find the last evid/orid
    on the db before returning the error.
    '''

    log('get_arrivals(%s,%s)' % (orid,subset))
    results = []

    steps = ['dbopen assoc']
    steps.extend(['dbsubset orid==%s' % orid])
    steps.extend(['dbjoin arrival'])
    steps.extend(['dbjoin site'])

    snetsta_table = db.lookup(table='snetsta')
    if snetsta_table.query(datascope.dbTABLE_PRESENT):
        steps.extend(['dbjoin snetsta'])

    if subset:
        steps.extend(['dbsubset %s' % subset.strip('"')] )

    log( ', '.join(steps) )

    with datascope.freeing(db.process( steps )) as dbview:

        if not dbview.record_count:
            log('No arrivals for orid [%s]' % orid)
            return results

        dbview = dbview.sort('delta')

        for temp in dbview.iter_record():
            (arid,sta,chan,phase,delta,seaz,timeres,
                vmodel,time,snr,amp,auth) = \
                temp.getv('arid','sta','chan',
                'phase','delta','seaz','timeres',
                'vmodel','time','snr','amp','auth')

            results.append( {'arid':arid,
                'sta':sta,'chan':chan,
                'phase':phase,'delta':delta,
                'seaz':seaz,'timeres':timeres,
                'vmodel':vmodel,'time':time,
                'snr':snr,'amp':amp,'auth':auth} )

            log('New arrival: %s' % results[-1] )


    return results

def _get_magnitudes(db,orid):

    mags = {}

    log('Get magnitudes ' )

    steps = ['dbopen netmag', 'dbsubset orid==%s' % orid]

    with datascope.freeing(db.process( steps )) as dbview:

        log('Got %s mags from file' % dbview.record_count )

        for record in dbview.iter_record():

            [orid, magid, magnitude, magtype,
                auth, uncertainty, lddate ] = \
                record.getv('orid', 'magid', 'magnitude',
                'magtype', 'auth','uncertainty', 'lddate')

            try:
                printmag = '%0.1f %s' % ( float(magnitude), magtype )
            except:
                printmag = '-'

            mags[magid] = {'magnitude':magnitude, 'printmag':printmag,
                    'lddate':lddate, 'magtype':magtype, 'auth':auth,
                    'uncertainty':uncertainty, 'magid':magid }
            log("%s" % mags[magid])

    return mags


def main():
    """
    Extract 1 event from database and
    format information as json file.
    """
    global log

    """
    Parse command line vars
    """
    usage = "Usage: %prog [options] project event_number"
    parser = OptionParser(usage=usage)
    parser.add_option("-o", action="store_true", dest="orid",
            help="id is an orid", default=False)
    parser.add_option("-e", action="store_true", dest="evid",
            help="id is an evid", default=False)
    parser.add_option("-n", action="store_true", dest="noimage",
            help="skip new images", default=False)
    parser.add_option("-v", action="store_true", dest="verbose",
            help="verbose output", default=False)
    parser.add_option("-p", action="store", dest="pf",
            help="parameter file", default="special_event.pf")
    parser.add_option("-d", action="store", dest="directory",
            help="specify output directory", default=False)
    parser.add_option("-f", action="store", dest="filterdata",
            help="filter traces", default="")
    (options, args) = parser.parse_args()


    if len(args) != 2 or not str(args[0] or not int(args[1]) ):
        parser.print_help()
        die("\nNeed EVENT number or ORIGIN number to run. Also need PROJECT name.\n")

    project = str(args[0])
    myid = int(args[1])

    verbose = options.verbose
    forced_dir = options.directory
    pf = options.pf


    if not verbose:
        log = no_output

    json_dict = {}

# Read parameters
    try:
        log( 'Read %s for parameters' % pf)
        pffile = stock.pfread(pf)
    except OSError:
        die("Cannot open parameter file [%s]" % (pf))

    try:
        log( 'Get network type %s from parameter file' % project)
        profileref = pffile[ project ]
        if not len(profileref): raise
    except Exception,e:
        die("\nCannot find project [%s] on configuration file [%s]\n" % (project,options.pf))


    timezone = pffile['timezone']
    timeformat = pffile['timeformat']
    dbname = profileref['dbname']
    webdir = profileref['webdir']
    website = profileref['website']
    closest = profileref['closest']
    subset = profileref['subset']
    list_subset = profileref['list_stations']['subset']
    list_jump = profileref['list_stations']['jump']


    log('Pf: timezone = %s' % timezone)
    log('Pf: timeformat = %s' % timeformat)
    log('Pf: dbname = %s' % dbname)
    log('Pf: webdir = %s' % webdir)
    log('Pf: website = %s' % website)
    log('Pf: closest = %s' % closest)
    log('Pf: subset = %s' % subset)
    log('Pf: list_subset = %s' % list_subset)
    log('Pf: list_jump = %s' % list_jump)


    if forced_dir:
        webdir = forced_dir
        notify('forcing dir to be [%s]' % webdir)


    results = {}

    with datascope.closing(datascope.dbopen( dbname , 'r' )) as db:

        if options.evid:
            steps = ['dbopen event']
            steps.extend(['dbjoin origin'])
            steps.extend(['dbsubset (evid==%s && prefor==orid)' % (myid)])
        elif options.orid:
            steps = ['dbopen origin']
            steps.extend(['dbsubset orid==%s' % myid])
        else:
            event_table = db.lookup(table='event')

            if event_table.query(datascope.dbTABLE_PRESENT):
                steps = ['dbopen origin']
                steps.extend(['dbjoin -o event'])
                steps.extend(['dbsubset (evid==%s && prefor==orid) || orid==%s' % (myid,myid)])
            else:
                steps = ['dbopen origin']
                steps.extend(['dbsubset orid==%s' % myid])


        log( ', '.join(steps) )

        with datascope.freeing(db.process( steps )) as dbview:

            notify( 'Found (%s) events with id [%s]' % (dbview.record_count,myid) )

            if not dbview.record_count:
                die('Nothing to work for id %s' % myid)

            if dbview.record_count != 1:
                complain( 'Too many (%s) events with id [%s]' % (dbview.record_count,myid) )
                msg = 'Shall I continue?'
                if not yes_no(msg): die('End')

            #we should only have 1 here
            for temp in dbview.iter_record():

                (goodevid,orid,time,lat,lon,depth,auth,nass,ndef,review) = \
                        temp.getv('evid','orid','time','lat','lon','depth',
                                'auth','nass','ndef','review')

                if int(goodevid) > 0:
                    evid = goodevid
                log( "new (%s,%s)" % (evid,orid) )

                # We need a directory for this event:
                dir = os.path.dirname("%s/%s/" % (webdir,evid))
                if not os.path.exists(dir):
                    os.makedirs(dir)

                notify( '\nSaving work on directory [%s/%s]\n\n' % (webdir,dir) )

                arrivals = _get_arrivals(db,orid,subset)
                sta_list = _get_sta_list(db,time,lat,lon,list_subset)

                start,end = _get_start_end( time,[arrivals[0]] )
                singlefilename = '%s/%s_single.png' % (evid,evid)
                if not options.noimage:
                    singleplot = _get_plots(dbname,time,evid,closest,singlefilename,
                                    filterdata=options.filterdata, start=start,end=end,sta=arrivals[0]['sta'])

                start,end = _get_start_end( time,arrivals )
                multifilename = '%s/%s_multi.png' % (evid,evid)
                if not options.noimage:
                    multiplot = _get_plots(dbname,time,evid,subset,multifilename,jump=list_jump,
                            filterdata=options.filterdata, start=start,end=end,maxt=15)

                # Get magnitudes
                allmags = []
                mag = '-'
                magtype = '-'
                magnitude = '-'
                maglddate = 0

                citiesplot = '%s/%s_cities.png' % (evid,evid)

                mags = _get_magnitudes(db,orid)
                for o in mags:
                    allmags.append(mags[o])
                    if mags[o]['lddate'] > maglddate:
                        mag = mags[o]['magnitude']
                        magtype = mags[o]['magtype']
                        magnitude = mags[o]['printmag']
                        maglddate = mags[o]['lddate']


                # Geo Name and Seismic Name
                srname = '-'
                grname = '-'
                try:
                    srname = string.capwords(stock.srname(lat,lon))
                    grname = string.capwords(stock.grname(lat,lon))
                except Exception,e:
                    die('Problems with (s/g)rname for orid %s: %s' % (orid,lat,lon,e))


                results['evid'] = evid
                results['orid'] = orid
                results['lat'] = lat
                results['lon'] = lon
                results['depth'] = depth
                results['time'] = time
                results['UTCtime'] = stock.epoch2str(time, timeformat, 'UTC')
                results['month'] = stock.epoch2str(time, '%m', timezone)
                results['year'] = stock.epoch2str(time, '%Y', timezone)

                results['mag'] = mag
                results['allmags'] = allmags
                results['magnitude'] = magnitude
                results['mag_type'] = magtype

                results['srname'] = srname
                results['grname'] = grname

                results['nass'] = nass
                results['ndef'] = ndef
                results['auth'] = auth
                results['reviewed'] = review

                results['sta_list'] = sta_list
                results['arrivals'] = arrivals

                results['cities'] = get_cities(lat,lon,citiesplot,1)

                results['filter'] =   parse_filter(options.filterdata)
                results['singleplot'] = singlefilename
                results['multiplot'] = multifilename
                if not options.noimage:
                    results['multiplotcmd'] = multiplot
                    results['singleplotcmd'] = singleplot

                results['usgs_page'] = "http://earthquake.usgs.gov/earthquakes/eventpage/usb000tp5q#general_summary"

    #log("%s" % results)

    #os.chdir( dir )
    output_file = "%s/%s.json" % (evid,evid)

    notify( '\nWriting resutls to %s\n\n' % output_file )

    with open(output_file, 'w') as outfile:
        json.dump(results, outfile, indent=4)

    return "\n\n\tNEED TO ADD THIS TO LIST: %s?event=%s\n\n" % (website,evid)

if __name__ == '__main__':
    print main()
    sys.exit()






