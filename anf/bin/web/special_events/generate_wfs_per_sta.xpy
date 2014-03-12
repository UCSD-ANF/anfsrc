import sys
import os
import json

# Load datascope functions
import antelope.datascope as datascope
import antelope.stock as stock
from optparse import OptionParser
from subprocess import call

def check_orid(dbptr, orid):
    """Test the origin number
    exists in the database
    """
    dbptr.subset('orid == %s' % orid)
    if dbptr.query('dbRECORD_COUNT') > 0:
        return True
    else:
        return False

def calc_window_and_lead(d):
    """Determine the time window
    and lead time for the plots
    """
    if d < 5:
        tw = 120
        lt = 15
    elif d < 15:
        tw = 300
        lt = 30
    elif d < 45:
        tw = 1200
        lt = 100
    elif d < 90:
        tw = 3600
        lt = 300
    elif d < 120:
        tw = 5400
        lt = 450
    else:
        tw = 7200
        lt = 600
    return tw, lt

def calc_iphases(dbptr):
    """Return a string of all the
    iphases of an event
    """
    iphase_str = ''
    for i in range(dbptr.query('dbRECORD_COUNT')):
        dbptr[3] = i
        chan, iphase, delta, arr_time = dbptr.getv('chan', 'iphase', 'delta', 'arrival.time')
        iphase_str += '\t\t%s &Arr{\n' % iphase
        iphase_str += '\t\t\tchan\t%s\n' % chan
        iphase_str += '\t\t\tiphase\t%s\n' % iphase
        iphase_str += '\t\t\tarrival_time\t%d\n' % arr_time
        iphase_str += '\t\t}\n'
    return iphase_str

def main():
    """Parse command line vars
    and output the JSON and parameter files
    """
    usage = "Usage: %prog [options]"
    parser = OptionParser(usage=usage)
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose", help="verbose output", default=False)
    parser.add_option("-o", "--orid", action="store", dest="orid", help="origin number", metavar="")
    parser.add_option("-p", "--profile", action="store", dest="profile", help="snet profile", metavar="")
    parser.add_option("-t", "--type", action="store", dest="type", help="type of event", metavar="")
    parser.add_option("-w", "--window", action="store", dest="window", help="time window", metavar="")
    parser.add_option("-l", "--lead", action="store", dest="lead", help="lead time", metavar="")
    parser.add_option("-f", "--filter", action="store", dest="filter", help="filter", metavar="")
    parser.add_option("-d", "--dir", action="store", dest="outdir", help="output directory", metavar="")
    parser.add_option("-x", "--debug", action="store_true", dest="debug", help="debug flag", default=False)
    (options, args) = parser.parse_args()
    if options.verbose:
        verbose = True
    else:
        verbose = False
    if options.orid:
        orid = options.orid
    else:
        parser.error("Need an origin number to work. Exiting")
    if options.profile:
        profile = options.profile
    else:
        parser.error("Need a network profile (from the parameter file) to work. Exiting.")
    if options.type:
        type = options.type
    else:
        type = False
    if options.window:
        window = options.window
    else:
        window = False
    if options.lead:
        lead = options.lead
    else:
        lead = False
    if options.filter:
        filter = options.filter
    else:
        filter = False
    if options.outdir:
        outdir = options.outdir
    else:
        parser.error("You must provide a output directory. Exiting")
    if options.debug:
        debug = options.debug
    else:
        debug = False
    if (options.window is False and options.lead) or (options.lead is False and options.window):
        print 'You must provide either (1) neither lead time nor time window and let this script calcuate both, or (2) both lead time and window in seconds'

    matlab_exec = "/opt/antelope/4.11p/local/bin/matlab"
    pf = 'data/generate_spevent.pf'
    tmp_dir = '/var/tmp'
    spevent_images_json = '%s/spevent.json' % outdir
    wform_arrivals_pf = '%s/spwfs.pf' % tmp_dir
    json_dict = {}
    sta_list = []

    if not os.path.isdir(outdir):
        try:
            os.mkdir(outdir, 0755)
        except OSError:
            print "The output directory specificed (%s) does not exist and cannot be created. Exiting." % outdir
            os._exit(99)

    try:
        profileref = stock.pfget(pf, profile)
    except OSError:
        print "Cannot open parameter file %s" % profile
    else:
        dbpointer = profileref['dbname']
        chan_expr = profileref['chan_expr']

        if verbose:
            print "Config:\n\tPROFILE:%s\n\tDB:%s\n\tORID:%s\n" % (profile, dbpointer, orid)

        db = datascope.dbopen(dbpointer, 'r')
        db.lookup('', 'origin', '', '')

        if check_orid(db, orid):

            wformf = open(wform_arrivals_pf, 'w')
            jsonf = open(spevent_images_json, 'w')

            if verbose:
                print 'Determining station arrivals for origin (%s)' % orid

            db.join('assoc')
            db.join('arrival')
            db.join('site')
            db.join('snetsta')
            db.subset('chan =~ /%s/' % chan_expr)
            db.sort(['delta', 'sta'])
            db.group('sta')
            grp_nrecs = db.query('dbRECORD_COUNT')

            if verbose:
                print 'Number of stations that recorded arrivals for this origin: %s' % grp_nrecs

            for i in range(grp_nrecs):
                """Go through each group
                of stations (i.e. all the 
                arrivals recorded at each station)
                """
                db[3] = i
                grp_sta = datascope.dbsubset(db, 'sta =~ /%s/' % db.getv('sta')[0])
                grp_sta.ungroup()
                grp_sta.sort('time')

                """All metadata for the event is the same, 
                so use first arrival to get station metadata
                """
                grp_sta[3] = 0
                sta, snet, delta, lat, lon, depth, time, site_lat, site_lon = grp_sta.getv('sta', 'snet', 'delta', 'lat', 'lon', 'depth', 'time', 'site.lat', 'site.lon')

                """Append the relative image path 
                to the JSON dictionary using the station 
                name as the key. Order is irrelevant
                """
                json_dict[sta] = 'wfs/%s_%s.png' % (snet, sta)

                if verbose:
                    print "Working on arrivals for station %s: lat %s, lon %s" % (sta, site_lat, site_lon)

                if window is False and lead is False:
                    window, lead = calc_window_and_lead(delta)

                # Pf array for each station that recorded an arrival
                mypf_str = '%s\t&Arr{\n' % sta
                mypf_str += '\tsnet\t%s\n' % snet
                mypf_str += '\tdelta\t%s\n' % delta
                mypf_str += '\tlt\t%s\n' % lead
                mypf_str += '\ttw\t%s\n' % window
                mypf_str += '\tiphases &Arr{\n'
                # Now iterate through iphases (arrival types)
                mypf_str += calc_iphases(grp_sta)
                mypf_str += '\t}\n}\n'
                wformf.write(mypf_str)
                sta_list.append(sta)

            # Matlab needs a list of stations to iterate through
            sta_pf_arr = '\t \n'.join(sta_list)

            """Add a row with metadata for the 
            event. We can use the lat lon depth time
            from the latest iteration as they are
            all from the same event so will all be 
            the same
            """
            metadata_str = 'metadata\t&Arr{\n'
            if debug:
                print "Debugging on"
                metadata_str += '\tdebug\tTrue\n'
            metadata_str += '\torid\t%s\n' % orid
            metadata_str += '\tarr_stas\t%s\n' % grp_nrecs
            metadata_str += '\tlat\t%s\n' % lat
            metadata_str += '\tlon\t%s\n' % lon
            metadata_str += '\tdepth\t%s\n' % depth
            metadata_str += '\ttime\t%0.5f\n' % time
            metadata_str += '\toutdir\t%s\n' % outdir
            metadata_str += '\tfilter\t%s\n' % filter
            metadata_str += '\tchan_expr\t%s\n' % chan_expr
            metadata_str += '\tdbpointer\t%s\n' % dbpointer
            metadata_str += '}\n'

            # Write out the waveform parameter file
            wformf.write(metadata_str)
            wformf.write('stas\t&Tbl{\n%s\n}' % sta_pf_arr)
            wformf.close()

            # Write out JSON file
            json.dump(json_dict, jsonf, indent=2)
            jsonf.flush()
            jsonf.close()

            if verbose:
                print "Pass pf to Matlab"
            try:
                matlab_retcode = call(matlab_exec + " -nojvm -nodisplay -nosplash -r \"addpath('"+tmp_dir+"')\" < gwfps.m", shell=True)
                if matlab_retcode < 0:
                    print >>sys.stderr, "Child was terminated by signal", -matlab_retcode
                else:
                    print >>sys.stderr, "Child returned ", matlab_retcode
            except OSError, e:
                print >>sys.stderr, "Execution failed:", e

        else:
            print "No orid (%s) in the database. Please check and try again" % orid


if __name__ == '__main__':
    main()
