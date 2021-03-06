"""

@author     Juan Reyes
@modified   25/07/2014 - Malcolm White
@notes      Updated to run under 5.4 of Antelope.

"""

import sys
import os
from shutil import move
import tempfile
from optparse import OptionParser
from subprocess import call, check_call
# Load datascope functions
#sys.path.append(os.environ['ANTELOPE'] + '/data/python')

import antelope.datascope as antdb
import  antelope.stock as stock

from time import time, gmtime, strftime
import datetime

# return the first year that data is available for a given project
def get_start_year():
  return 2004

def parse_args():
    """
    Return a 6-tuple: (verbosity, year, month, maptype, deploytype, size).
    """
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('deploytype',  type=str,
            help='type of deployment  to plot')
    parser.add_argument('maptype', type=str,
            help='type of map to plot')
    parser.add_argument('-v', '--verbose', action='store_true',
            help='verbose output')
    parser.add_argument('-x', '--debug', action='store_true',
            help='debug script')
    parser.add_argument('-s', '--size', type=str,
            help='generate different sizes')
    parser.add_argument('-t', '--time', type=int, nargs=2,
            help='year and month to plot')
    parser.add_argument('-m', '--maptype', type=str,
            help='type of map to produce (cumulative, rolling, both)')
    parser.add_argument('-p', '--parameter_file', type=str,
            help='parameter file')

    maptypes = ['cumulative', 'rolling']
    deploytypes = ['seismic', 'inframet']

    args = parser.parse_args()

    if not args.deploytype in deploytypes:
        print "Your deployment type ('%s') must be either '%s' or '%s'. "\
                "Goodbye." % (args.deploytype, deploytypes[0], deploytypes[1])
        exit()


    if not args.maptype in maptypes:
        if args.maptype != 'both':
            print "Your map type ('%s') must be either '%s' or '%s'. Goodbye" \
                    % (args.maptype, maptypes[0], maptypes[1])
            exit()
        else:
            args.maptype = maptypes

    if args.time:
        year = args.time[0]
        month = args.time[1]
        if year < get_start_year():
            print "Your year integer (%d) must be greater than %d. Goodbye." \
                    % (year, get_start_year())
            exit()
        if 12 < month < 1:
            print "Month must be in range [1, 12]. Goodbye."
            exit()
    else:
        today = datetime.date.today()
        m = today.month
        y = today.year
        year, month = (y - 1, 12) if m == 1 else (y, m - 1)
        print "Using default value of last whole month, which is %d %02d" \
                % (year, month)
        print "Use '-t' option to specify specific year and month."

    if args.parameter_file and not os.path.exists(args.parameter_file):
        print "Parameter file specified ('%s') does not exist. Goodbye."\
                % args.parameter_file
        exit()

    return args.verbose,\
           args.debug,\
           year,\
           month,\
           args.maptype,\
           args.deploytype,\
           args.size,\
           args.parameter_file

def parse_parameter_files(parameter_file):
    if parameter_file:
        parameter_file = stock.pfin(parameter_file)
    else:
        parameter_file = stock.pfread('usarray_deploy_map')
    common_pf = stock.pfin(parameter_file['common_pf'])
    stations_pf = stock.pfin(parameter_file['stations_pf'])
    return common_pf, stations_pf, parameter_file

def process_command_line(argv):
    """Return a 6-tuple: (verbosity, year, month, maptype, deploytype, size).
    'argv' is a list of arguments, or 'None' for ''sys.argv[1:]''.
    """

    if argv is None:
        argv = sys.argv[1:]

    # Limit the choices to two
    maptypes = ['cumulative', 'rolling']
    deploytypes = ['seismic', 'inframet']

    # Initialize the parser object
    usage = "Usage: %prog [options] YYYY MM"
    parser = OptionParser(usage=usage)
    parser.add_option("-v", action="store_true", dest="verbose", help="verbose output", default=False)
    parser.add_option("-x", action="store_true", dest="debug", help="debug script", default=False)
    parser.add_option("-d", "--deploytype", action="store", type="string", dest="deploytype", help="type of deployment to plot", default="seismic")
    parser.add_option("-t", "--type", action="store", type="string", dest="maptype", help="type of map to plot", default=False)
    parser.add_option("-s", "--size", action="store", type="string", dest="size", help="generate different sizes", default=False)
    parser.add_option("-p", "--parameter_file", action="store", type="string", dest="parameter_file", help="parameter file", default=None)
    options, args = parser.parse_args(argv)

    if options.verbose:
        verbose = True
    else:
        verbose = False

    if options.debug:
        debug = True
    else:
        debug = False

    if options.deploytype:
        deploytype = options.deploytype
        if not deploytype in deploytypes:
            print "Your deployment type ('%s') must be either '%s' or '%s'. Goodbye" % (deploytype, deploytypes[0], deploytypes[1])
            exit()
    else:
        print "You have not defined a deploytype to plot, exiting"
        exit()

    if options.maptype:
        maptype = options.maptype
        if not maptype in maptypes:
            print "Your map type ('%s') must be either '%s' or '%s'. Goodbye" % (maptype, maptypes[0], maptypes[1])
            exit()
        maptype = [maptype]
    else:
        print "You have not defined a maptype to plot, so both types will be created"
        maptype = maptypes

    if options.size:
        size = options.size
    else:
        size = False

    if len(args) < 2:
        today = datetime.date.today()
        m = today.month
        y = today.year
        if m == 1:
          m = 12
          y -= 1
        else:
          m -= 1
        month = m
        year = y
        print "You have not specified a year and/or month."
        print "Using default value of last whole month, which is %d %02d" % (year, month)
    else:
        year = int(args[0])
        month = int(args[1])
        if year < get_start_year():
            print "Your year integer ('%s') must be four characters. Goodbye." % year
            exit()
        if 12 < month < 1:
            print "Bad month number ('%d') specified. Goodbye." % month
            exit()
#    if options.parameter_file:
#        if not os.path.exits(options.parameter_file):
#            print "Parameter file %s does not exist. Goodbye." % options.parameter_file
#            exit()
#        else:
#            parameter_file = options.parameter_file
#    else:
#        parameter_file = 'usarray_deploy_map'

#    return verbose, debug, year, month, maptype, deploytype, size, parameter_file
    return verbose, debug, year, month, maptype, deploytype, size

def generate_times(year, month):
    """Generate start and end time unix timestamps for dbsubsets """

    print "month:%s" % month
    print "year:%s " % year
    month=int(month)
    year=int(year)
    next_year = year
    next_month = month + 1
    if next_month > 12:
        next_month = 1
        next_year = next_year + 1

    print "next_month:%s" % next_month
    print "next_year:%s " % next_year

    start_time = stock.str2epoch('%02d/01/%4d 00:00:00' % (month, year))
    end_time = stock.str2epoch('%02d/01/%4d 00:00:00' % (next_month, next_year))
    print "START:%s => %s" % (start_time,stock.strdate(start_time))
    print "END:%s => %s" % (end_time,stock.strdate(end_time))

    return start_time, end_time

def generate_inframet_locations(db, mtype, deploytype, year, month, imap=False, verbose=False, debug=False):
    """Generate inframet locations for specific
    periods in time and write out to xy files 
    suitable for GMT
    """
    # Build the Datascope query str. 
    # For some reason this list comprehensions 
    # has to be at the top of a function?
    # Cannot reproduce in independent tests?

    qstr = '|'.join([ '|'.join(v) for k,v in imap.iteritems()])
    start_time, end_time = generate_times(year, month)

    if verbose or debug:
        print "  - generate_inframet_locations(): Infrasound: Searching sitechan table for chans that match: %s" % qstr

    with antdb.closing(antdb.dbopen(db, 'r')) as infraptr:
        process_list = [
            'dbopen sitechan',
            'dbjoin deployment',
            'dbjoin site',
            'dbsubset deployment.time <= %s' % end_time,
            'dbsubset chan=~/(%s)/' % qstr
        ]
            #'dbsubset ondate <= %s' % end_time # Remove future deployed stations

        if mtype == 'rolling':
            #process_list.append('dbsubset endtime >= %s' % start_time) # No decommissioned stations for rolling plot
            process_list.append('dbsubset deployment.endtime >= %s' % start_time) # No decommissioned stations for rolling plot
        elif mtype != 'cumulative':
            print "generate_inframet_locations(): Inframet Error: Map type ('%s') is not recognized" % mtype
            exit()

        process_list.append('dbsort sta ondate chan time')

        try:
            infraptr = infraptr.process(process_list)
        except Exception,e:
            print "  - generate_inframet_locations(): Dbprocessing failed with exception: %s" % e
            sys.exit(1)
        else:
            all_stations = {}

            infra_tmp_all = tempfile.mkstemp(suffix='.xy',
                                            prefix='deployment_list_inframet_ALL_')

            infra_tmp_ncpa = tempfile.mkstemp(suffix='.xy',
                                            prefix='deployment_list_inframet_NCPA_')

            infra_tmp_setra = tempfile.mkstemp(suffix='.xy',
                                            prefix='deployment_list_inframet_SETRA_')

            infra_tmp_mems = tempfile.mkstemp(suffix='.xy',
                                            prefix='deployment_list_inframet_MEMS_')

            file_list = {'complete':infra_tmp_all[1], 'ncpa':infra_tmp_ncpa[1],
                        'setra':infra_tmp_setra[1], 'mems':infra_tmp_mems[1]}

            counter = {'complete':0, 'ncpa':0, 'setra':0, 'mems':0}

            if mtype == 'cumulative':
                infra_tmp_decom = tempfile.mkstemp(
                suffix='.xy',
                prefix='deployment_list_inframet_DECOM_'
                )
                # Add the DECOM by hand as it is a manufactured
                # file, not a snet per se. Call it _DECOM to force
                # it to plot first
                file_list['1_DECOM'] = infra_tmp_decom[1]
                counter['decom'] = 0
            try:
                infraptr_grp = infraptr.group('sta')
            except Exception,e:
                print "  - generate_inframet_locations(): Dbgroup failed with exception: %s" % e
                sys.exit(1)
            else:
                with antdb.freeing(infraptr_grp):
                    # Get values into a easily digestible dict
                    for record in  infraptr_grp.iter_record():
                        sta, [db, view, end_rec, start_rec] = \
                            record.getv('sta', 'bundle')
                        all_stations[sta] = {'sensors': {'MEMS':False, 'NCPA':False,
                                                        'SETRA':False},
                                            'location': {'lat':0, 'lon':0}}
                        for j in range(start_rec, end_rec):
                            infraptr.record = j
                            # Cannot use time or endtime as that applies to the station, not to the inframet sensor
                            ondate, offdate, chan, lat, lon = \
                                infraptr.getv('ondate', 'offdate', 'chan', 'lat', 'lon')
                            all_stations[sta]['location']['lat'] = lat
                            all_stations[sta]['location']['lon'] = lon

                            ondate = stock.epoch(ondate)

                            if offdate > 0:
                                offdate = stock.epoch(offdate)
                            else:
                                offdate = 'NULL'

                            if chan == 'LDM_EP':
                                if ondate <= end_time and (offdate == 'NULL' or offdate >= start_time):
                                    all_stations[sta]['sensors']['MEMS'] = True
                            elif chan == 'BDF_EP' or chan == 'LDF_EP':
                                if ondate <= end_time and (offdate == 'NULL' or offdate >= start_time):
                                    all_stations[sta]['sensors']['NCPA'] = True
                            elif chan == 'BDO_EP' or chan == 'LDO_EP':
                                if ondate <= end_time and (offdate == 'NULL' or offdate > start_time):
                                    all_stations[sta]['sensors']['SETRA'] = True
                            else:
                                print "   - ***Channel %s not recognized***" % chan
                    #
                    if debug:
                        print all_stations
                    # Process dict
                    for sta in sorted(all_stations.iterkeys()):
                        if verbose or debug:
                            print "   - Working on station %s" % sta
                        lat = all_stations[sta]['location']['lat']
                        lon = all_stations[sta]['location']['lon']
                        sensors = all_stations[sta]['sensors']
                        if mtype == 'rolling':
                            if sensors['MEMS'] and sensors['NCPA'] and sensors['SETRA']:
                                os.write(infra_tmp_all[0], "%s    %s    # %s \n" % (lat, lon, sta))
                                counter['complete'] += 1
                            elif sensors['MEMS'] and sensors['NCPA']:
                                os.write(infra_tmp_ncpa[0], "%s    %s    # %s \n" % (lat, lon, sta))
                                counter['ncpa'] += 1
                            elif sensors['MEMS'] and sensors['SETRA']:
                                os.write(infra_tmp_setra[0], "%s    %s    # %s \n" % (lat, lon, sta))
                                counter['setra'] += 1
                            elif sensors['MEMS']:
                                os.write(infra_tmp_mems[0], "%s    %s    # %s \n" % (lat, lon, sta))
                                counter['mems'] += 1
                        elif mtype == 'cumulative':
                            if not sensors['MEMS'] and not sensors['NCPA'] and not sensors['SETRA']:
                                os.write(infra_tmp_decom[0], "%s    %s    # DECOM %s \n" % (lat, lon, sta))
                                counter['decom'] += 1
                            else:
                                if sensors['MEMS'] and sensors['NCPA'] and sensors['SETRA']:
                                    os.write(infra_tmp_all[0], "%s    %s    # %s \n" % (lat, lon, sta))
                                    counter['complete'] += 1
                                elif sensors['MEMS'] and sensors['NCPA']:
                                    os.write(infra_tmp_ncpa[0], "%s    %s    # %s \n" % (lat, lon, sta))
                                    counter['ncpa'] += 1
                                elif sensors['MEMS'] and sensors['SETRA']:
                                    os.write(infra_tmp_setra[0], "%s    %s    # %s \n" % (lat, lon, sta))
                                    counter['setra'] += 1
                                elif sensors['MEMS']:
                                    os.write(infra_tmp_mems[0], "%s    %s    # %s \n" % (lat, lon, sta))
                                    counter['mems'] += 1
                    os.close(infra_tmp_all[0])
                    os.close(infra_tmp_mems[0])
                    if mtype == 'cumulative':
                        os.close(infra_tmp_decom[0])
    return file_list, counter
 
def generate_sta_locations(db, mtype, deploytype, year, month, verbose=False, debug=False):
    """Generate station locations for specific
    periods in time and write out to xy files 
    suitable for GMT
    """
    start_time, end_time = generate_times(year, month)

    # Define dbops
    process_list = [
        'dbopen site', 
        'dbjoin snetsta', 
        'dbjoin deployment', 
        'dbsubset deployment.time <= %s' % end_time,
        'dbsort snet sta'
    ]
    with antdb.closing(antdb.dbopen(db, 'r')) as dbptr:
        dbptr = dbptr.process(process_list)

        # Get networks
        snetptr = dbptr.sort('snet', unique=True)
        usnets = []
        try:
            with antdb.freeing(snetptr):
                for record in snetptr.iter_record():
                    mysnet = record.getv('snet')[0]
                    usnets.append(mysnet)
                    print "Adding snet:%s" % mysnet
        except Exception, e:
            print "generate_sta_locations(): Exception occurred: %s" % e
            sys.exit(1)


        # If we don't want to plot cumulative then remove old stations
        if mtype == 'rolling':
            dbptr = dbptr.subset('deployment.endtime >= %s' % start_time)
        else:
            this_decom_counter = 0



        file_list = {}
        counter = {}

        dfile = tempfile.mkstemp(suffix='.xy', prefix='deployment_list_DECOM_')
        decom_ptr = dfile[0]
        decom_name = dfile[1]

        # Loop over unqiue snets
        for s in usnets:

            if verbose:
                print "generate_sta_locations(): Working on network: %s" % s

            try:
                dbptr_snet = dbptr.subset('snet=~/%s/' % s )
            except Exception, e:
                print "Error occurred: %s" % e
                sys.exit(1)

            if dbptr_snet.query( 'dbRECORD_COUNT' ) < 1:
                continue

            stmp = tempfile.mkstemp(suffix='.xy',
                                    prefix='deployment_list_%s_' % s)
            file_ptr = stmp[0]
            file_name = stmp[1]

            this_counter = 0
            for record in dbptr_snet.iter_record():
                if mtype == 'rolling':
                    sta, lat, lon, snet = record.getv('sta', 'lat', 'lon', 'snet')
                    os.write(file_ptr, "%s    %s    # %s %s\n" % (lat, lon,
                                                                    snet, sta))
                    this_counter = this_counter + 1
                elif mtype == 'cumulative':
                    sta, lat, lon, snet, sta_time, sta_endtime = record.getv(
                        'sta', 'lat', 'lon', 'snet', 'time', 'endtime')
                    if sta_endtime >= start_time:
                        os.write(file_ptr, "%s    %s    # %s %s\n" %
                                    (lat, lon, snet, sta))
                        this_counter = this_counter + 1
                    else:
                        os.write(decom_ptr, "%s    %s    # DECOM %s\n" %
                                    (lat, lon, sta))
                        this_decom_counter = this_decom_counter + 1
            counter[s] = this_counter
            os.close(file_ptr)
            file_list[s] = file_name

        if mtype == 'cumulative':
            counter['decom'] = this_decom_counter

    # Add the DECOM by hand as it is a manufactured 
    # file, not a snet per se. Call it _DECOM to force
    # it plot first
    file_list['1_DECOM'] = decom_name
    os.close(decom_ptr)

    return file_list, counter

def set_gmt_params(paper_orientation, paper_media):
    """ Calls gmtset to configure various GMT parameters just for this script """

    # Leaving on shell=True just in case Rob had some magic environment 
    # set up that this script doesn't define explicily

    # Plot media
    retcode = check_call( " ".join([ "gmtset",
    "PAGE_COLOR", "255/255/255",
    "PAGE_ORIENTATION", paper_orientation,
    "PAPER_MEDIA", paper_media ]), shell=True )

    # Basemap Anotation Parameters
    retcode = check_call( " ".join([
                "gmtset",
                "ANNOT_OFFSET_PRIMARY", "0.2c",
                "ANNOT_OFFSET_SECONDARY", "0.2c",
                "LABEL_OFFSET", "0.2c" ]), shell=True)

    # Basemap Layout Parameters
    retcode = check_call( " ".join([
            "gmtset",
            "FRAME_WIDTH", "0.2c",
            "MAP_SCALE_HEIGHT", "0.2c",
            "TICK_LENGTH", "0.2c",
            "X_AXIS_LENGTH", "25c",
            "Y_AXIS_LENGTH", "15c",
            "X_ORIGIN", "2.5c",
            "Y_ORIGIN", "2.5c",
            "UNIX_TIME_POS", "-0.2c/-0.2c"]), shell=True)

    # Miscellaneous
    retcode = check_call( " ".join([
                "gmtset",
                "LINE_STEP", "0.025c",
                "MEASURE_UNIT", "inch" ]), shell=True)

def gmt_fix_land_below_sealevel(regionname,
                                description,
                                region,
                                center,
                                outfile,
                                wet_rgb):
    """run psclip to fix coloring of dry areas that are below sea-level"""

    landfile = "land_only.cpt"
    grdfile = regionname + ".grd"
    gradientfile = regionname + ".grad"
    xyfile = regionname + ".xy"

   # Define a clip region
    try:
        retcode = check_call("psclip %s -R%s -JE%s -V -K -O >> %s" % (xyfile,
                    region, center, outfile), shell=True)
    except OSError, e:
        print description + " psclip execution failed"
        sys.exit(1)

    # Make area 'land-only' and put into the clipping region
    try:
        retcode = check_call("grdimage %s -V -R%s -JE%s -C%s -I%s -O -K >> %s"
                % (grdfile, region, center, landfile, gradientfile, outfile),
                shell=True)
    except OSError, e:
        print description + " grdimage execution failed"
        sys.exit(1)

    # Color the actual water areas blue
    try:
        retcode = check_call("pscoast -V -R%s -JE%s -C%s -Df -O -K >> %s" % (
                    region, center, wet_rgb, outfile), shell=True)
    except OSError, e:
        print description + " pscoast execution failed"
        sys.exit(1)

    # Close psclip
    try:
        retcode = check_call("psclip -C -K -O >> %s" % outfile, shell=True)
    except OSError, e:
        print description + " psclip execution failed"
        sys.exit(1)

def gmt_plot_wet_and_coast(region, center, wet_rgb, outfile):
    """plot wet areas and coastline"""
    try:
        # Plot wet areas (not coast)
        retcode = check_call("pscoast"+" -V -R%s -JE%s -W0.5p,%s -S%s -A0/2/4 -Df -O -K >> %s" % (region, center, wet_rgb, wet_rgb, outfile), shell=True)
        # Plot coastline in black
        retcode = check_call("pscoast"+" -V -R%s -JE%s -W0.5p,0/0/0 -Df -O -K >> %s" % (region, center, outfile), shell=True)
        # Plot major rivers
        retcode = check_call("pscoast"+" -V -R%s -JE%s -Ir/0.5p,0/0/255 -Df -O -K >> %s" % (region, center, outfile), shell=True)
        # Plot national (N1) and state (N2) boundaries
        retcode = check_call("pscoast"+" -V -R%s -JE%s -N1/5/0/0/0 -N2/1/0/0/0 -Df -O -K >> %s" % (region, center, outfile), shell=True)
    except OSError, e:
        print "A pscoast call failed: %s" % e
        sys.exit(1)

def gmt_overlay_grid(region, center, coords, legendloc, outfile):
    """Overlay the grid for a given region"""
    try:
        retcode = check_call( "psbasemap -X0 -Y0 -R%s -JE%s -V -Bg%swesn -Lf%sk+l -O -K >> %s"
                % (region, center, coords, legendloc, outfile), shell=True)
    except OSError, e:
        print "psbasemap execution failed: %s" % e
        sys.exit(1)

def gmt_add_stations(station_loc_files, symsize, rgbs, outfile):
    """Overlay the station icons"""
    for key in sorted(station_loc_files.iterkeys()):
        if key == 'IU' or key == 'US': 
            # Plots diamond symbols for US backbone stations
            symtype='d'
        else:
            symtype='t'

        try:
            retcode = check_call(
                    "psxy %s -R -JE -V -S%s%s -G%s -W -L -O -K -: >> %s"
                    % (station_loc_files[key], symtype, symsize, rgbs[key],
                        outfile), shell=True)
        except OSError, e:
            "psxy execution failed: %s" % e
            sys.exit(1)


def main(argv=None):
    """Main processing script for all maps """

    print "Start of script"

    verbose,\
            debug,\
            year,\
            month,\
            maptype,\
            deploytype,\
            size,\
            parameter_file = parse_args()
    #verbose, debug, year, month, maptype, deploytype, size = process_command_line(argv)
    common_pf, stations_pf, parameter_file = parse_parameter_files(parameter_file)
    if debug:
        print "*** DEBUGGING ON ***"
        print "*** No grd or grad files - just single color for speed ***"

    wet_rgb = '202/255/255'

    #common_pf = stock.pfin('/anf/web/vhosts/anf.ucsd.edu/conf/common.pf')
    #stations_pf = stock.pfin('/anf/web/vhosts/anf.ucsd.edu/conf/stations.pf')

    if verbose:
        print '%s' % common_pf
        print '%s' % stations_pf

    dbmaster = common_pf.get('USARRAY_DBMASTER')
    networks = stations_pf.get('network')
    infrasound = stations_pf.get('infrasound')
    colors = stations_pf.get('colors')
    # Force the tmp dir environmental variable
    tmp = common_pf.get('TMP')
    os.environ['TMPDIR'] = os.environ['TEMP'] = os.environ['TMP'] = tmp
    gmtbindir = common_pf.get('GMT_BIN')
    usa_coords = common_pf.get('USACOORDS')
    ak_coords = common_pf.get('AKCOORDS')
    web_output_dir = common_pf.get('CACHE_MONTHLY_DEPLOYMENT')
    web_output_dir_infra = common_pf.get('CACHE_MONTHLY_DEPLOYMENT_INFRA')
    infrasound_mapping = common_pf.get('INFRASOUND_MAPPING')
    output_dir = parameter_file.get('output_dir')
    sys.path.append(gmtbindir)
    if size == 'wario':
        paper_orientation = 'landscape'
        paper_media = 'b0'
        symsize = '0.3'
    else:
        paper_orientation = 'portrait'
        paper_media = 'a1'
        symsize = '0.15'

    # Make sure execution occurs in the right directory
#    cwd = os.getcwd()
#    path_parts = cwd.split('/')
#    if path_parts[-1] == 'deployment_history' and path_parts[-2] == 'bin':
#        if verbose or debug:
#            print ' - Already in the correct current working directory %s' % cwd
#    else:
#        cwd = os.getcwd() + '/data/deployment_history'
#        if verbose or debug:
#            print ' - Changed current working directory to %s' % cwd
#        os.chdir(cwd)
    if os.getcwd() != parameter_file['data_dir']:
        os.chdir(parameter_file['data_dir'])
        if verbose or debug:
            print ' - Changed current working directory to %s'\
                    % parameter_file['data_dir']

    # Make sure we set some GMT parameters for just this script
    # GMTSET
    try:
        set_gmt_params(paper_orientation, paper_media)
    except Exception, e:
        print "An error occurred setting GMT params %s"
        sys.exit(1)


    for m in maptype:
        if size == 'wario':
            ps = tempfile.mkstemp(suffix='.ps', prefix='deployment_history_map_%s_%d_%02d_%s_WARIO_' % (deploytype, year, month, m))
            png = 'PNG not created for tiled display wario. Create by hand in Photoshop'
        else:
            ps = tempfile.mkstemp(suffix='.ps', prefix='deployment_history_map_%s_%d_%02d_%s_' % (deploytype, year, month, m))
            if deploytype == 'inframet':
                finalfile = 'deploymap_%s_%d_%02d.%s.png' % (deploytype, year, month, m)
            else:
                finalfile = 'deploymap_%d_%02d.%s.png' % (year, month, m)
            png = '%s/%s' % (output_dir, finalfile)

        if verbose or debug or size:
            print ' - Working on maptype: %s' % m
            print ' - Temp postscript file: %s' % ps[1]
            print ' - Output target: %s' % png

        # Determine region of interest and center of plot
        # The lat and lon padding ensures we get full topo and bathy.
        minlon = int(usa_coords['MINLON'])
        maxlon = int(usa_coords['MAXLON'])
        minlat = int(usa_coords['MINLAT'])
        maxlat = int(usa_coords['MAXLAT'])
        region = '%s/%s/%s/%s' % (minlon, minlat, maxlon, maxlat) + 'r'
        centerlat = (maxlat - minlat)/2 + minlat
        centerlon = (maxlon - minlon)/2 + minlon

        ak_minlon = int(ak_coords['MINLON'])
        ak_maxlon = int(ak_coords['MAXLON'])
        ak_minlat = int(ak_coords['MINLAT'])
        ak_maxlat = int(ak_coords['MAXLAT'])
        ak_region = '%s/%s/%s/%s' % (ak_minlon, ak_minlat, ak_maxlon, ak_maxlat) + 'r'
        ak_centerlat = (ak_maxlat - ak_minlat)/2 + ak_minlat
        ak_centerlon = (ak_maxlon - ak_minlon)/2 + ak_minlon

        if size == 'wario':
            center = '%s/%s/%s' % (centerlon, centerlat, '44') + 'i'
            ak_center = '%s/%s/%s' % (ak_centerlon, ak_centerlat, '10') + 'i'
        else:
            center = '%s/%s/%s' % (centerlon, centerlat, usa_coords['WIDTH']) + 'i'
            ak_center = '%s/%s/%s' % (ak_centerlon, ak_centerlat, ak_coords['WIDTH']) + 'i'

        if verbose or debug:
            print ' - GMT USA region string: %s' % region
            print ' - GMT USA center location string: %s' % center
            print ' - GMT AK region string: %s' % ak_region
            print ' - GMT AK center location string: %s' % ak_center

        if deploytype == 'seismic':
            station_loc_files, counter = generate_sta_locations(dbmaster, m, deploytype, year, month, verbose, debug)
            rgbs = {'1_DECOM':'77/77/77'} # Init with the missing color and force to be first plotted
        elif deploytype == 'inframet':
            station_loc_files, counter = generate_inframet_locations(dbmaster, m, deploytype, year, month, infrasound_mapping, verbose, debug)
            rgbs = {'1_DECOM':'255/255/255'} # Init with the missing color and force to be first plotted

        snets_text = {}
        for key in sorted(station_loc_files.iterkeys()):
            if deploytype == 'seismic':
                if key in networks:
                      color = networks[key]['color']
                      rgbs[key] = colors[color]['rgb'].replace(',', '/')
                      snets_text[key] = networks[key]['abbrev'].replace(' ', '\ ')
            elif deploytype == 'inframet':
                if debug:
                    print "\tWorking on inframet key: %s" % key
                if key in infrasound:
                      color = infrasound[key]['color']
                      rgbs[key] = colors[color]['rgb'].replace(',', '/')
                      snets_text[key] = infrasound[key]['name'].replace(' ', '\ ')
        # Extra key for the decommissioned stations group
        if m == 'cumulative':
            if deploytype == 'seismic':
               color = networks['DECOM']['color']
               rgbs['decom'] = colors[color]['rgb'].replace(',', '/')
            elif deploytype == 'inframet':
               color = infrasound['decom']['color']
               rgbs['decom'] = colors[color]['rgb'].replace(',', '/')

        # Create the contiguous United States topography basemap

        # {{{ Contiguous United States

        if verbose or debug:
            print ' - Working on contiguous United States'

        if debug == True:
            try:
                retcode = check_call("pscoast -R%s -JE%s -Df -A5000 -S%s -G40/200/40 -V -X2 -Y2 -K >> %s" % (region, center, wet_rgb, ps[1]), shell=True)
            except OSError, e:
                print "pscoast for contiguous United States execution failed"
                sys.exit(2)
        else:
            try:
                retcode = check_call("grdimage usa.grd -R%s -JE%s -Cland_ocean.cpt -Iusa.grad -V -E100 -X2 -Y2 -K >> %s" % (region, center, ps[1]), shell=True)
            except OSError, e:
                print "grdimage for usa.grd execution failed"
                sys.exit(3)

        # Plot land areas below sea level correctly

        # Salton Sea co-ords -R-116.8/-115/32/34
        gmt_fix_land_below_sealevel('saltonsea', 'Salton Sea',
                region, center, ps[1], wet_rgb)

        # Death Valley co-ords -R
        gmt_fix_land_below_sealevel('deathvalley', 'Death Valley',
                region, center, ps[1], wet_rgb)

        # Plot wet areas and coastline
        gmt_plot_wet_and_coast(region, center, wet_rgb, ps[1])

        # Overlay the grid
        gmt_overlay_grid(region, center, usa_coords['GRIDLINES'],
                '-75/30/36/500', ps[1])

        # Add stations from local text files
        gmt_add_stations(station_loc_files, symsize, rgbs, ps[1])

        # }}} Contiguous United States

        if verbose or debug:
            print ' - Working on Alaska inset'

        # {{{ Alaska

        if debug == True:
            try:
                retcode = check_call("pscoast -R%s -JE%s -Df -A5000 -S%s -G40/200/40 -V -X0.1i -Y0.1i -O -K >> %s" % (ak_region, ak_center, wet_rgb, ps[1]), shell=True)
            except OSError, e:
                print "pscoast for Alaska execution failed: %s" % e
                sys.exit(4)
        else:
            try:
                retcode = check_call("grdimage alaska.grd -R%s -JE%s -Cland_ocean.cpt -Ialaska.grad -V -E100 -X0.1i -Y0.1i -O -K >> %s" % (ak_region, ak_center, ps[1]), shell=True)
            except OSError, e:
                print "grdimage for alaska.grd execution failed: %s" % e
                sys.exit(5)

        # Plot wet areas and coastline
        gmt_plot_wet_and_coast(ak_region, ak_center, wet_rgb, ps[1])

        # Overlay the grid
        gmt_overlay_grid(ak_region, ak_center, ak_coords['GRIDLINES'],
                '-145/57/60/500', ps[1])

        # Add stations from local text files
        gmt_add_stations(station_loc_files, symsize, rgbs, ps[1])

        # }}} Alaska

        # Clean up station files
        for key in sorted(station_loc_files.iterkeys()):
            os.unlink(station_loc_files[key])

        if verbose or debug:
            print ' - Working on year and month timestamp'
        # Create the text files of year & month and legend
        time_file = tempfile.mkstemp(suffix='.txt', prefix='year_month_')
        # time_file = "%syear_month.txt" % tmp
        tf = open(time_file[1], 'w')
        tf.write("-75.5    17    20    0    1    BR    %d\ %02d" % (year, month))
        tf.close()

        if verbose or debug:
            print ' - Working on copyright file'
        copyright_file = tempfile.mkstemp(suffix='.txt', prefix='copyright_')
        # copyright_file = "%scopyright.txt" % tmp
        cf = open(copyright_file[1], 'w')
        cf.write("-67    48.7    11    0    1    BR    (c)\ 2004\ -\ %s\ Array\ Network\ Facility,\ http://anf.ucsd.edu" % year)
        cf.close()

        if verbose or debug:
            ' - Working on snet files'
        snets_file = tempfile.mkstemp(suffix='.txt', prefix='snets_')
        sf = open(snets_file[1], 'w')
        if size == 'wario':
            legend_symsize = '0.3'
        else:
            legend_symsize = '0.15'
        snet_file_txt = 'G 0.06i\n'
        snet_file_txt += 'H 14 Helvetica-Bold Network Legend\n'
        snet_file_txt += 'D 0.06i 1p\n' # A horizontal line
        snet_file_txt += 'N 1\n'
        snet_file_txt += 'V 0 1p\n'
        snet_symbol = 't'
        for key in sorted(snets_text.iterkeys()):
            snet_symbol = 't'
            if verbose or debug:
                print ' -     snets: %s' % key
            if key == 'IU' or key == 'US': 
                snet_symbol = 'd'
            snet_file_txt += 'S 0.1i %s %s %s 0.25p 0.3i %s\ [%s]\n' % (snet_symbol, legend_symsize, rgbs[key], snets_text[key], counter[key])
        if m == 'cumulative':
            snet_file_txt += 'D 0.06i 1p\n' # A horizontal line
            snet_file_txt += 'S 0.1i %s %s %s 0.25p 0.3i Decommissioned\ [%s]\n' % (snet_symbol, legend_symsize, rgbs['decom'], counter['decom'])
        sf.write(snet_file_txt)
        sf.close()

        # Overlay the copyright notice
        if verbose or debug:
            print ' - Overlay the copyright notice'

        try:
            retcode = check_call("pstext %s -R%s -JE%s -V -D0.25/0.25 -S2p/255/255/255 -P -O -K >> %s"
                    % (copyright_file[1], region, center, ps[1]), shell=True)
        except OSError, e:
            print "Copyright msg plotting error: pstext execution failed"
            os.unlink(copyright_file[1])
            sys.exit(1)
        else:
            os.unlink(copyright_file[1])

        # Overlay the date legend stamp
        if verbose or debug:
            print ' - Overlay the date legend stamp'
        try:
            retcode = check_call("pstext " + time_file[1] + " -R" + region
                    + " -JE" + center + " -V -D0.25/0.25" +
                    " -W255/255/255o1p/0/0/0 -C50% -P -O -K >> " + ps[1],
                    shell=True)
        except OSError, e:
            print "Time msg plotting error: pstext execution failed"
            sys.exit(1)
        else:
            os.unlink(time_file[1])

        # Overlay the snet legend
        if verbose or debug:
            print ' - Overlay the snet legend'

        if deploytype == 'seismic':
            legend_width = '2.6'
            legend_height = '2.98'
        elif deploytype == 'inframet':
            legend_width = '4.2'
            legend_height = '1.7'
        else:
            print "unknown deploytype"
            return 1

        try:
            retcode = check_call("pslegend %s -R%s -JE%s -V -D-90/26/%si/%si/TC -F -G255/255/255 -P -O >> %s" % (snets_file[1], region, center, legend_width, legend_height, ps[1]), shell=True)
        except OSError, e:
             print "Network (snet) legend plotting error: pslegend execution failed"
             sys.exit(2)
        else:
            os.unlink(snets_file[1])

        # Run Imagemagick convert cmd on Postscript output
        if size == 'wario':
            print " - Your file for wario is ready for photoshop and is called %s" % ps[1]
        else:
            if verbose or debug:
                print " - Running Imagemagick's convert command on postscript file %s" % ps[1]
            try:
                retcode = check_call("convert -trim -depth 16 +repage %s %s" % (ps[1], png), shell=True)
            except OSError, e:
                print "Execution failed"
                sys.exit(6)
            else:
                os.unlink(ps[1])

            if deploytype == 'inframet':
                web_output_dir = web_output_dir_infra

            if verbose or debug:
                print " - Going to move %s to %s/%s" % (png,web_output_dir,finalfile)
            try:
                move(png, '%s/%s' % (web_output_dir, finalfile))
            except OSError, e:
                print "shutil.move failed"
                sys.exit(8)
            else:
                print " - Your file is ready and is called %s/%s" % (web_output_dir, finalfile)

    return 0

if __name__ == '__main__':
    status = main()
    sys.exit(status)
