""" 
    The Earth Networks lightning sensor network, 
    known as the Earth Networks Total Lightning 
    Network (ENTLN), is the worlds largest 
    lightning detection network. 
    
    Once the data gets archive into css3.0 and we 
    have an origin table then we can calculate 
    theoretical arrivals on seismic stations. 
    
    
    From EarthNetworks:
        Christopher D. Sloop <CSloop@earthnetworks.com>
        Amena Ali <aali@earthnetworks.com>
    
    From ANF:
        Juan Reyes <reyes@ucsd.edu>
    
    06/2012

"""

import random, getopt, sys, math

try:
    import antelope.datascope as datascope
    import antelope.stock as stock
except Exception,e:
    sys.exit( 'Problem importing Antelope libraries: %s ' % e )


def distance_on_unit_sphere(lat1, long1, lat2, long2):
    """ Convert latitude and longitude to 
    spherical coordinates in radians.
    The distance returned is relative to 
    Earth's radius. To get the distance 
    in miles, multiply by 3960. To get the 
    distance in kilometers, multiply by 6373.

    http://www.johndcook.com/python_longitude_latitude.html

    """
#{{{
    degrees_to_radians = math.pi/180.0

    # phi = 90 - latitude
    phi1 = (90.0 - lat1)*degrees_to_radians
    phi2 = (90.0 - lat2)*degrees_to_radians

    # theta = longitude
    theta1 = long1*degrees_to_radians
    theta2 = long2*degrees_to_radians

    # Compute spherical distance from spherical coordinates.

    # For two locations in spherical coordinates 
    # (1, theta, phi) and (1, theta, phi)
    # cosine( arc length ) = 
    #    sin phi sin phi' cos(theta-theta') + cos phi cos phi'
    # distance = rho * arc length
    
    cos = (math.sin(phi1)*math.sin(phi2)*math.cos(theta1 - theta2) + 
           math.cos(phi1)*math.cos(phi2))
    arc = math.acos( cos )

    # Remember to multiply arc by the radius of the earth 
    # in your favorite set of units to get length.
    return arc
#}}}



def main():
    """ Calculate arrivals for stations
    in site table.

    """
    # {{{ main

    try:
        opts, args = getopt.getopt(sys.argv[1:], "vs:r:d:", ["verbose","select=","reject=","distance="])
    except Exception, e:
        sys.exit('Error reading command line arguments: %s' % e)

    # default values
    verbose = False
    select = ''
    reject = ''
    maxdistance = 0.0
    id = random.randint(99, 9999)
    #channels = ['BHZ','BDO_EP','BDF_EP','LDM_EP']
    channels = ['BHZ']
    speed = 0.34029  #speed of sound at sea level in km/sec

    for o, a in opts:
        if o in ("-s", "--select"):
            select = a

        elif o in ("-r", "--reject"):
            reject = a

        elif o in ("-d", "--distance"):
            maxdistance = float(a)

        else:
            assert False, "unhandled option in command line"


    # Get options from command line
    #if sys.argv[1]:
    if args:
        database = args[0]
    else:
        sys.exit( 'Need to provide source table for site and lightning databases' )


    if verbose:
        print "Using database [%s] subset:%s reject:%s" % (database, select, reject)

    # Verify database
    try:
        db = datascope.dbopen(database,"r+")
    except: 
        sys.exit( 'Need valid databse with site table and origin table with lightning strikes' )

    if db[0] == -102:
        sys.exit('Problem opening database.')


    try:
        origin = datascope.dblookup (db, table = 'origin')
    except Exception,e:
        sys.exit( 'Problems opening origin table: %s' % (database,e) )
    if not origin.query(datascope.dbTABLE_PRESENT):
        sys.exit('Problems on origin table: dbTABLE_PRESENT')

    try:
        site = datascope.dblookup (db, table = 'site')
    except Exception,e:
        sys.exit( 'Problems opening site table: %s' % (database,e) )
    if not site.query(datascope.dbTABLE_PRESENT):
        sys.exit('Problems on site table: dbTABLE_PRESENT')

    try:
        arrival = datascope.dblookup (db, table = 'arrival')
    except Exception,e:
        sys.exit( 'Problems opening arrival table: %s' % (database,e) )


    # subset site table to match command line arguments
    if select:
        site = site.subset("sta =~ /%s/" % select)
    if reject:
        site = site.subset("sta !~ /%s/" % reject)

    if not site.query(datascope.dbRECORD_COUNT):
        sys.exit( 'No stations to work with after subsets: select:%s rejects:%s' % (select,reject) )

    for s in range(site.query(datascope.dbRECORD_COUNT)):

        # Get each station from db
        site.record = s
        sta,slat,slon = site.getv('sta', 'lat', 'lon')
        if verbose: 
            print ("\t%s (%s,%s):" % (sta,slat,slon))

        # Calculate distance to each event
        for o in range(origin.query(datascope.dbRECORD_COUNT)):

            origin.record = o
            time,evid,olat,olon,type,amps = origin.getv('time','evid', 'lat', 'lon','etype','ml')
            if verbose: 
                print ("\t\t%s (%s,%s) %s" % (evid,olat,olon,time,type,amps))

            # Get distance and convert to km
            arc = distance_on_unit_sphere(slat, slon, olat, olon)
            distance = float(arc * 6373)

            if maxdistance == 0 or distance < maxdistance:
                #print "****** Got one %s km away. ******" % distance
                strtime = stock.strtime(time)
                print "%s: %0.2f km at %s [type:%s amps:%s]" % (sta,distance,strtime,type,amps)

                # calculate time for arrival
                # use speed of sound at sea level
                # of 340.29 m/sec or 0.34029 km/sec
                newtime =  time + distance/speed
                print "\t\tCalculating arrival time: %s + %s = %s" % (time,(distance/speed),newtime)

                # Add to arrival table
                for c in channels:
                    id = id + 1
                    arrival.addv('sta',sta,'chan',c,'time',newtime,'arid',id,'auth','ligthning_code','iphase',str(int(distance)))
            else:
                if verbose: 
                   print "\t\t\tToo far: %s" % distance

    db.close()


    return 0
    # }}}

if __name__ == '__main__':
    sys.exit(main())

else:
    raise Exception("Not a module to be imported!")
    sys.exit()
