import re
import json
import string
import socket
import pprint
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

init(sys.argv[0])

def no_output(msg=''):
    '''
    Just a simple way to silence log
    if needed.
    '''
    pass

def _get_display_list(db,orid,subset=False,jump=1):
    '''
    Make a list of stations that recorded the event
    '''

    log('get_display_list(%s,%s,%s)' % (orid,subset,jump))

    results = []

    steps = ['dbopen assoc']
    steps.extend(['dbsubset orid==%s' % orid])
    steps.extend(['dbjoin arrival'])
    if subset:
        steps.extend(['dbsubset %s' % subset] )

    log( ', '.join(steps) )

    with datascope.freeing(db.process( steps )) as dbview:

        if not dbview.record_count:
            log('No arrivals for orid [%s]' % orid)
            return results

        dbview = dbview.sort('delta')

        for temp in dbview.iter_record():
            sta = temp.getv('sta')[0]

            if not sta in results:
                log( "add display sta %s" % sta )
                results.append( sta )

    if not int(jump):
        jump = 1

    return results[0::int(jump)]


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
        steps.extend(['dbsubset %s' % subset] )

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



def _fail_event_query(db,evid,use_orid=False):
    '''
    Lets try to find the last evid/orid
    on the db before returning the error.
    '''

    if use_orid:
        steps = ['dbopen event']
        steps.extend(['dbjoin origin'])
        steps.extend(['dbsubset orid==prefor'])
    else:
        steps = ['dbopen origin']
    with datascope.freeing(db.process( steps )) as dbviewlast:

        try:
            dbviewlast = dbviewlast.sort('time')
            dbviewlast.record = dbviewlast.record_count - 1
            lastorid = dbviewlast.getv('orid')[0]
        except:
            lastorid = '-'
        try:
            lastevid = dbviewlast.getv('evid')[0]
        except:
            lastevid = '-'
        die('last EVID [%s] last ORID [%s]' % (lastevid,lastorid))

    die('Not valid EVID nor ORID [%s]' % evid)

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
    parser.add_option("-o", action="store_true", dest="orid",
            help="use origin instead", default=False)
    parser.add_option("-p", action="store", dest="pf",
            help="parameter file", default="special_event.pf")
    parser.add_option("-t", action="store", dest="event_network",
            help="usarray, ceusn or anza", default="usarray")
    parser.add_option("-d", action="store", dest="directory",
            help="specify output directory", default=False)
    (options, args) = parser.parse_args()


    if len(args) != 1 or not int(args[0]):
        parser.print_help()
        die("\nNeed EVENT number or ORIGIN number to run.\n")

    evid = int(args[0])

    verbose = options.verbose
    use_orid = options.orid
    event_network = options.event_network
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
        log( 'Get network type %s from parameter file' % event_network)
        profileref = pffile[event_network]
    except:
        die("Cannot open network type [%s] on file [%s]" % (event_network,pf))


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

    with datascope.closing(datascope.dbopen( dbname , 'r' )) as db:
        if use_orid:
            steps = ['dbopen origin']
            steps.extend(['dbsubset orid==%s' % evid])
        else:
            steps = ['dbopen event']
            steps.extend(['dbsubset evid==%s' % evid])
            steps.extend(['dbjoin origin'])
            steps.extend(['dbsubset orid==prefor'])


        log( ', '.join(steps) )

        with datascope.freeing(db.process( steps )) as dbview:

            notify( 'Found (%s) events with id [%s]' % (dbview.record_count,evid) )

            if not dbview.record_count:
                # This failed. Lets see what we have in the db
                _fail_event_query(db,evid,use_orid)

            if subset:
                dbview = dbview.subset(subset)
                if not dbview.record_count:
                    die('Nothing to work after subset %s' % subset)


            #we should only have 1 here
            for temp in dbview.iter_record():

                (orid,time,lat,lon,depth,auth,nass,ndef,review) = \
                        temp.getv('orid','time','lat','lon','depth',
                                'auth','nass','ndef','review')

                log( "new (%s,%s)" % (evid,orid) )

                mags = _get_magnitudes(db,orid)
                arrivals = _get_arrivals(db,orid,subset)
                display_list = _get_display_list(db,orid,list_subset,list_jump)

                allmags = []
                magnitude = '-'
                maglddate = 0


                try:
                    srname = stock.srname(lat,lon)
                    grname = stock.grname(lat,lon)
                except Exception,e:
                    error('Problems with (s/g)rname for orid %s: %s' % (orid,lat,lon,e))
                    srname = '-'
                    grname = '-'

                srname = string.capwords(srname)
                grname = string.capwords(grname)

                for o in mags:
                    allmags.append(mags[o])
                    if mags[o]['lddate'] > maglddate:
                        mag = mags[o]['magnitude']
                        magtype = mags[o]['magtype']
                        magnitude = mags[o]['printmag']
                        maglddate = mags[o]['lddate']


                results['evid'] = evid
                results['orid'] = orid
                results['lat'] = lat
                results['lon'] = lon
                results['depth'] = depth

                results['time'] = time
                results['localtime'] = stock.epoch2str(time, timeformat, timezone)
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

                results['display_list'] = display_list
                results['arrivals'] = arrivals

                results['location'] = "%s, %s" % (srname,grname)

                closest = arrivals[0]

                results['near_station'] = closest['sta']
                results['near_distance'] = "%s km ( %s degrees)" % (( 111 * closest['delta']),
                                                                closest['delta'])
                results['population'] = ["??km (??mi) SE of town, country","??km (??mi) SE of town, country"]

                results['usgs_page'] = "http://earthquake.usgs.gov/earthquakes/eventpage/usb000tp5q#general_summary"

    log("%s" % results)

    output_file = "%s/%s.json" % (webbase,evid)

    notify( '\nWriting resutls to %s\n\n' % output_file )

    try:
        os.remove(output_file)
    except:
        pass

    with open(output_file, 'w') as outfile:
        json.dump(results, outfile, indent=4)


if __name__ == '__main__':
    sys.exit( main() )

