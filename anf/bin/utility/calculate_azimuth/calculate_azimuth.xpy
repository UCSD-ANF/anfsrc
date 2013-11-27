"""
    Simple script to read arrivals and origins and
    calculate the azimuth. Then update the arrival
    table with the azimuth information. That will be
    the station-to-event azimuth mesured clockwise
    from north.


    Juan Reyes <reyes@ucsd.edu>

    11/2013

"""

import re

try:
        from optparse import OptionParser
except Exception,e:
        sys.exit( "Problem loading Python's json library. (%s)" % e )

try:
    import antelope.datascope as datascope
    import antelope.stock as stock
except Exception,e:
    sys.exit( 'Problem importing Antelope libraries: %s ' % e )

def main():
    """ Calculate arrivals for stations
    in site table.

    """

    usage = "Usage: calculate_azimuth [-v] [-n] database"

    parser = OptionParser(usage=usage)
    parser.add_option("-v", action="store_true",
                            dest="verbose", default=False,
                                            help="Set verbose output.")
    parser.add_option("-n", action="store_true",
                            dest="null", default=False,
                                            help="Dry run. No updates.")

    try:
        (options, args) = parser.parse_args()
    except Exception,e:
        sys.exit( "Problems parsing command-line arguments. (%s)" % e)

    verbose = options.verbose
    nullRun = options.null

    if len(args) == 1:
        database = args[0]

    else:
        print usage
        sys.exit()


    if verbose:
        print "Using database [%s]" % database

    if nullRun:
        print "\n\t****  NULL RUN. NOT UPDATING DATABASE. ****\n"

    # Verify database
    try:
        db = datascope.dbopen(database,"r+")
    except Exception,e:
        sys.exit( 'Need valid database. (%s)', e )

    if db[0] == -102:
        sys.exit('Problem opening database.')


    try:
        origin = db.lookup(table = 'origin')
    except Exception,e:
        sys.exit( 'Problems opening origin table: %s' % (database,e) )
    if not origin.query(datascope.dbTABLE_PRESENT):
        sys.exit('Problems on origin table: dbTABLE_PRESENT')

    try:
        arrival = datascope.dblookup (db, table = 'arrival')
    except Exception,e:
        sys.exit( 'Problems opening arrival table: %s' % (database,e) )



    if verbose:
        print "Got %s entries in origin." % origin.query('dbRECORD_COUNT')

    origin = origin.join( 'assoc', outer = False )
    if verbose:
        print "Got %s after assoc join." % origin.query('dbRECORD_COUNT')

    origin = origin.join( 'arrival', outer = False )
    if verbose:
        print "Got %s after arrival join." % origin.query('dbRECORD_COUNT')

    origin = origin.join( 'site', outer = False )
    if verbose:
        print "Got %s after site join." % origin.query('dbRECORD_COUNT')


    if origin.query('dbRECORD_COUNT') < 1:
        sys.exit('No entries after join with arrival table.')
    else:
        if verbose:
            print "Got %s entries." % origin.query('dbRECORD_COUNT')


    origin = origin.sort('arid')


    for s in range(origin.query('dbRECORD_COUNT')):

        # Get each station from db
        origin.record = s
        arid,orid,azimuth,originlat,originlon,stalat,stalon = origin.getv('arid','orid',
                'azimuth','origin.lat','origin.lon','site.lat','site.lon')

        if verbose:
            print ("\t%s:%s azimuth:%s site(%s,%s) event(%s,%s)" % (
                    orid,arid,azimuth,stalat,stalon,originlat,originlon))

        azimuth = datascope.dbex_eval(origin,'azimuth(site.lat,site.lon,lat,lon)')

        if azimuth > 360 or azimuth < 0:
            sys.exit('Problems calculating azimuth: %s' % azimuth)

        if verbose:
            print "\t\tAZIMUTH: %0.1f" % azimuth

        record = arrival.find('arid == %s' % arid, first=-1)

        if record > -1:

            arrival.record = record

            if verbose:
                print "\t\tGot arid:%s in record:%s" % (arid,record)


            if nullRun:
                print "\t\tNo update to database. NULL RUN!"

            else:
                # Add arrival table
                arrival.putv('azimuth',azimuth)
        else:
            sys.exit('Cannot find arrival id: %s' % arid)


    db.close()


    return 0

if __name__ == '__main__':
    sys.exit(main())

else:
    raise Exception("Not a module to be imported!")
    sys.exit()
