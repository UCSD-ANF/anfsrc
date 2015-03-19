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

try:
    from antelope.elog import init as init
    from antelope.elog import notify as log
    from antelope.elog import notify as notify
    from antelope.elog import die as die
    import antelope.stock as stock
    import antelope.datascope as datascope
except Exception,e:
    sys.exit('Problems loading Antelope libs: %s' % e )

import locale
locale.setlocale(locale.LC_ALL, 'en_US')

init(sys.argv[0])



def no_output(msg=''):
    '''
    Just a simple way to silence log
    if needed.
    '''
    pass


def _get_plots(dbname,time,evid,subset,filename,sta=False,jump=False):
    '''
    Porduce plots for the event

        Usage: plot_traces [options]

        Options:
        -h, --help    show this help message and exit
        -v            Verbose output
        -f FILTER     Filter data. ie. 'BW 0.1 4 3 4'
        -a            Plot arrivals on traces.
        -s SUBSET     Subset. ie. 'sta=~/AAK/ && chan=~/.*Z/'
        -e EVENT_ID   Plot traces for event: evid/orid
        -p PF         Parameter File to use.
        -m MAXTRACES  Don't plot more than this number of traces
        -n FILENAME   Save final plot to the provided name. ie. test.png
        -d            If saving to file then use -d to force image to open at the
                        end.
        -j JUMP       Avoid plotting every trace of the subset. Only use every N
                        trace.

    Example:
    ./plot_traces -e 1589065 -s 'chan=~/BHZ/' -a -j 8 -f 'BW 3 4 0 0' /anf/TA/rt/usarray/usarray
    '''

    try:
        os.remove(filename)
    except:
        pass

    cmd = './plot_traces -e %s -a ' % evid
    cmd = cmd + ' -n "%s"' % filename
    if sta:
        cmd = cmd + ' -s "sta =~/%s/ && %s"' % (sta,subset.strip('"'))
    else:
        cmd = cmd + ' -s "%s"' % subset.strip('"')
    if jump: cmd = cmd + ' -j %s' % jump
    cmd = cmd + ' %s' % dbname

    notify('get_plots() => %s' % cmd)

    if call( cmd, shell=True):
        notify('SOME ERROR ON THIS: %s' % cmd )

    return cmd

def parse_cities(name,distance,angle):

    bearings = ["NE", "E", "SE", "S", "SW", "W", "NW", "N"]

    if angle < 0: angle += 360

    index = int(angle / 45)

    b = bearings[index]

    dist = locale.format("%d", distance, grouping=True)

    return "%s km %s of %s" % (dist,b,name)


def get_cities(lat,lon,max=5):
    '''
    Make a list of populated place close to event
    '''

    log('get_cities(%s,%s,%s)' % (lat,lon,max))

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
            azimuth  = temp.ex_eval( 'azimuth(lat,lon,%s,%s)' % (lat, lon) )
            distance = temp.ex_eval( 'distance(lat,lon,%s,%s)' % (lat, lon) )
            distance = temp.ex_eval( 'deg2km(%s)' % distance )

            #cities[ temp.getv('place')[0] ] = {'distance':distance,'azimuth':azimuth}
            cities[ temp.getv('place')[0] ] = [distance,azimuth]

    cities = sorted(cities.items(), key=operator.itemgetter(1))

    for city in cities[0:max]:
        log( '%s => %s' % (city[0],city[1]) )

    #return cities[0:max]
    for city in  [ parse_cities(x[0],x[1][0],x[1][1]) for x in cities[0:max] ]:
        log( '%s' % city )

    return [ parse_cities(x[0],x[1][0],x[1][1]) for x in cities[0:max] ]

def _get_sta_list(db,time,lat, lon, subset=False):
    '''
    Make a list of stations that recorded the event
    '''

    log('get_display_list(%s,%s,%s)' % (time,lat,lon))

    results = {}

    yearday = stock.yearday(time)

    steps = ['dbopen site']

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
    usage = "Usage: %prog [options] event_number"
    parser = OptionParser(usage=usage)
    parser.add_option("-v", action="store_true", dest="verbose",
            help="verbose output", default=False)
    parser.add_option("-p", action="store", dest="pf",
            help="parameter file", default="special_event.pf")
    parser.add_option("-t", action="store", dest="event_network",
            help="usarray, ceusn or anza", default="usarray")
    parser.add_option("-d", action="store", dest="directory",
            help="specify output directory", default=False)
    (options, args) = parser.parse_args()


    if len(args) != 1 or not int(args[0]):
        notify("\nNeed EVENT number or ORIGIN number to run.\n")
        parser.print_help()

    evid = int(args[0])

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
        log( 'Get network type %s from parameter file' % options.event_network)
        profileref = pffile[options.event_network]
    except Exception,e:
        die("Cannot open network type [%s] on file [%s]" % (options.event_network,e))


    timezone = pffile['timezone']
    timeformat = pffile['timeformat']
    dbname = profileref['dbname']
    webbase = profileref['webbase']
    closest = profileref['closest']
    subset = profileref['subset']
    list_subset = profileref['list_stations']['subset']
    list_jump = profileref['list_stations']['jump']


    log('Pf: timezone = %s' % timezone)
    log('Pf: timeformat = %s' % timeformat)
    log('Pf: dbname = %s' % dbname)
    log('Pf: webbase = %s' % webbase)
    log('Pf: closest = %s' % closest)
    log('Pf: subset = %s' % subset)
    log('Pf: list_subset = %s' % list_subset)
    log('Pf: list_jump = %s' % list_jump)


    if forced_dir:
        webbase = forced_dir
        notify('forcing dir to be [%s]' % webbase)


    results = {}

    # We need a directory for this event:
    dir = os.path.dirname("%s/%s/" % (webbase,evid))
    if not os.path.exists(dir):
        os.makedirs(dir)

    notify( '\nSaving work on directory [%s/%s]\n\n' % (webbase,dir) )


    with datascope.closing(datascope.dbopen( dbname , 'r' )) as db:

        event_table = db.lookup(table='event')

        if event_table.query(datascope.dbTABLE_PRESENT):
            steps = ['dbopen origin']
            steps.extend(['dbjoin -o event'])
            steps.extend(['dbsubset (evid==%s && prefor==orid) || orid==%s' % (evid,evid)])
        else:
            steps = ['dbopen origin']
            steps.extend(['dbsubset orid==%s' % evid])


        log( ', '.join(steps) )

        with datascope.freeing(db.process( steps )) as dbview:

            notify( 'Found (%s) events with id [%s]' % (dbview.record_count,evid) )

            if not dbview.record_count:
                die('Nothing to work for %s' % evid)


            #we should only have 1 here
            for temp in dbview.iter_record():

                (orid,time,lat,lon,depth,auth,nass,ndef,review) = \
                        temp.getv('orid','time','lat','lon','depth',
                                'auth','nass','ndef','review')

                log( "new (%s,%s)" % (evid,orid) )

                arrivals = _get_arrivals(db,orid,subset)
                sta_list = _get_sta_list(db,time,lat,lon,list_subset)

                singlefilename = '%s/%s_single.png' % (evid,evid)
                singleplot = _get_plots(dbname,time,evid,closest,singlefilename,sta=arrivals[0]['sta'])

                multifilename = '%s/%s_multi.png' % (evid,evid)
                multiplot = _get_plots(dbname,time,evid,subset,multifilename,jump=list_jump)

                # Get magnitudes
                allmags = []
                mag = '-'
                magtype = '-'
                magnitude = '-'
                maglddate = 0

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
                    error('Problems with (s/g)rname for orid %s: %s' % (orid,lat,lon,e))


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

                results['cities'] = get_cities(lat,lon,5)

                results['singleplot'] = singlefilename
                results['singleplotcmd'] = singleplot
                results['multiplot'] = multifilename
                results['multiplotcmd'] = multiplot

                results['usgs_page'] = "http://earthquake.usgs.gov/earthquakes/eventpage/usb000tp5q#general_summary"

    #log("%s" % results)


    #os.chdir( dir )
    output_file = "%s/%s.json" % (evid,evid)

    notify( '\nWriting resutls to %s\n\n' % output_file )

    with open(output_file, 'w') as outfile:
        json.dump(results, outfile, indent=4)

    return "\n\n\tNEED TO ADD THIS TO LIST: http://anf.ucsd.edu/spevents/display.php?event=%s\n\n" % evid



if __name__ == '__main__':
    print main()
    sys.exit()

