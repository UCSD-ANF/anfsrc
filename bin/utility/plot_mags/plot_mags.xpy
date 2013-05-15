##############################################################################
# Name          : plot_mags.xpy
# Purpose       : 
# Inputs        : 
# Pf file       : none
# Returns       : none
# Flags         : -v -p -s
# Author        : Juan Reyes
# Email         : reyes@ucsd.edu
# Date          : 5/14/2013
##############################################################################


"""
    Alternativ of subsets for Auth fields...

        a) Southern California Seismic Network  == SCSN.*|PAS  #  ml|mw
        b) Northern California Seismic Network  == NCSN.*|NC|BRK|UCMT #  ml|mw|md
        c) Pacific Northwest Seismic Network    ==  PNSN.*|SEA # ml|md
        d) Montana Tech                         ==  MTECH.*|BUT|ESO   #ml|md|M
        e) Utah University Seismic System       == UUSS|SLC|SLM  # ml
        f) University of Nevada Reno            == UNR_NBE|NBE|REN|RMT   #  ml|md|ml|mw
        g)  Center of Earthquake Research Institute  ==  CERI    # ml|md|mblg
        h)  Lamont-Doherty Columbia Seismic Network == LCSN|PAL   # ml
        i)   Geological Survey of Canada        == GSC|OTT|OGSO # M|md|mblg
        j)  Pacific Geoscience Center           == PGC    # ml|mw|M|Mw
        k) North East Seismic Network           == NESN
        l)  South East Seismic Network          == SESN
        m)  Alaska Seismic Network              == ???? 


    Calculating the total number of plots. 
        1. Get the list of magtypes for the primary network
        2. Get the list of magtypes for the secondary network.
        3. Get the Direct Product of the 2 groups.
        Direct Product...
        The elements of G x H are ordered pairs (g, h), 
        where g is element of G and h is element of H. That is, the set of elements 
        of G x H is the Cartesian product of the sets G and H.

"""


import re
import pylab
from optparse import OptionParser

try:
    import antelope.datascope as datascope
    import antelope.stock as stock
except Exception,e:
    sys.exit( 'Problem importing Antelope libraries: %s ' % e )

def main():
    """ Plot for the same evid magnitudes from two different 
    authors.
    """
    usage = '\nUSAGE:\n\t%s [-v] [-x x_label] [-y y_label] [-p primary] [-s secondary ] database\n\n' % __file__


    parser = OptionParser()
    parser.add_option("-v", "--verbose", dest="verbose", action="store_true")
    parser.add_option("-p", "--primary", dest="primary", action="store", default='dbevproc')
    parser.add_option("-s", "--secondary", dest="secondary", action="store", default='CERI')
    parser.add_option("-x", "--x_label", dest="x_label", action="store", default='')
    parser.add_option("-y", "--y_label", dest="y_label", action="store", default='')

    (options, args) = parser.parse_args()

    primary = options.primary
    secondary = options.secondary

    if not primary:
        sys.exit( '\n\tProblem selecting primary author.\n\n' )

    if not secondary:
        sys.exit( '\n\tProblem selecting secondary author.\n\n' )

    if options.verbose:
        verbose = True
    else:
        verbose = False

    if options.x_label:
        x_label = options.x_label
    else:
        x_label = primary

    if options.y_label:
        y_label = options.y_label
    else:
        y_label = secondary

    if len(args) != 1:
        sys.exit(usage)

    # Get options from command-line
    database = os.path.abspath(args[0])

    if not database:
        print "Problem with database provided. '%s'" % database
        sys.exit(usage)

    if verbose: 
        print "\n%s" % __file__
        print "Primary author:   %s" % primary
        print "Secondary author: %s" % secondary
        print "Using database:   %s" % database


    evid_list = {}

    " Open database and tables needed. " 
    try:
        db = datascope.dbopen(database,"r+")
    except: 
        sys.exit( 'Problems opening database "%s": %s' % (database,e) )

    #try:
    #    if not db.query(datascope.dbDATABASE_IS_WRITABLE):
    #        sys.exit( 'Problems opening database "%s": \n %s' % (database,database) )
    #except Exception,e:
    #    sys.exit( 'Problems testing database write permissions. %s \n %s' % (e,database) )


    " Open each table needed. "
    try:
        netmag = db.lookup (table = 'netmag')
    except Exception,e:
        sys.exit( 'Problems opening netmag table. %s \n %s' % (e,db) )

    #try:
    #    origin = db.lookup (table = 'origin')
    #except Exception,e:
    #    sys.exit( 'Problems opening origin table. %s \n %s' % (e,db) )

    #try:
    #    assoc = db.lookup (table = 'assoc')
    #except Exception,e:
    #    sys.exit( 'Problems opening assoc table. %s \n %s' % (e,db) )

    #try:
    #    arrival = db.lookup (table = 'arrival')
    #except Exception,e:
    #    sys.exit( 'Problems opening arrival table. %s \n %s' % (e,db) )

    #try:
    #    site = db.lookup (table = 'site')
    #except Exception,e:
    #    sys.exit( 'Problems opening site table. %s \n %s' % (e,db) )

    " Verify previous entries on the netmag  table. " 
    if netmag.query('dbRECORD_COUNT') < 1:
        sys.exit( 'Empty netmag table. %s' % netmag.query('dbRECORD_COUNT') )




    #try:
    #    schanloc = db.lookup (table = 'schanloc')
    #except Exception,e:
    #    sys.exit( 'Problems opening schanloc table. %s \n %s' % (e,db) )

    #" Get list of previous orids in database. "
    #for i in range(origin.query('dbRECORD_COUNT')):

    #    origin.record = i
    #    origin_list[origin.getv('orid')] = 1

    #" Get list of previous arrivals in database. "
    #for i in range(arrival.query('dbRECORD_COUNT')):

    #    arrival.record = i
    #    arrival_list[arrival.getv('arid')] = 1



    " Get list of magtypes for primary network."
    if verbose: print "Get list of magtypes for primary"
    temp_mags = netmag.subset("auth =~ /%s/" % primary)
    temp_mags = temp_mags.sort("magtype",unique=True)
    " Verify table after subset " 
    if temp_mags.query('dbRECORD_COUNT') < 1:
        sys.exit( 'ERROR after unique sort on primary magtypes')
    p_mags = []
    for i in range(temp_mags.query('dbRECORD_COUNT')):
        temp_mags.record = i
        p_mags.append(temp_mags.getv('magtype')[0].lower())
    if verbose: print "Got magtypes for primary: %s" % p_mags



    " Get list of magtypes for secondary network."
    temp_mags = netmag.subset("auth =~ /%s/" % secondary)
    temp_mags = temp_mags.sort("magtype",unique=True)
    " Verify table after subset " 
    if temp_mags.query('dbRECORD_COUNT') < 1:
        sys.exit( 'ERROR after unique sort on secondary magtypes')
    s_mags = []
    for i in range(temp_mags.query('dbRECORD_COUNT')):
        temp_mags.record = i
        s_mags.append(temp_mags.getv('magtype')[0].lower())
    if verbose: print "Got magtypes for secondary: %s" % s_mags


    " Subset for valid entries only."
    netmag = netmag.subset("auth =~ /%s|%s/" % (primary,secondary))
    netmag = netmag.sort("lddate")
    " Verify table after subset " 
    if netmag.query('dbRECORD_COUNT') < 1:
        sys.exit( 'No events after subset auth=~/%s|%s/' % (primary,secondary))


    " Get list of evids in database. "
    if verbose: print "Get list of evids"
    for i in range(netmag.query('dbRECORD_COUNT')):

        netmag.record = i
        (magid,evid,orid,magnitude,magtype,auth) = netmag.getv('magid','evid','orid','magnitude','magtype','auth')

        # Fix magtype value
        magtype = magtype.lower()

        if verbose: print "\t%s %s %s %s %s" % (evid,orid,magnitude,magtype,auth)

        if re.match(primary,auth):
            atype = 'p'
        else:
            atype = 's'

        if not evid in evid_list: evid_list[evid] = {}
        evid_list[evid][orid] = {'atype':atype,'auth':auth,'magnitude':magnitude,'magtype':magtype}


    #fig = pylab.figure(figsize=(10, 10))
    fig = pylab.figure(0,dpi=300)

    if verbose: print "Got magtypes for primary: %s" % p_mags
    if verbose: print "Got magtypes for secondary: %s" % s_mags
    r_p = len(p_mags)  # total plots
    c_p = len(s_mags)  # total plots
    t_p= 1  # columns for plots

    max_mag = 7
    mag_range = range(max_mag+1)

    for mp in p_mags:
        for ms in s_mags:

            x,y = get_points(evid_list,mp,ms)

            " Multiplot figure. "
            if verbose: print "Plot (%s,%s,%s)" % (r_p,c_p,t_p)
            subplot = fig.add_subplot(r_p,c_p,t_p)
            subplot.scatter(x,y)

            " Try to mark points with more than 1 total variation."
            #for xx,yy in zip(x,y):
            #    if abs(xx-yy) > 1:
            #        plt.annotate( '%s-%s' % (xx,yy),  \
            #            xy = (xx, yy), xytext = (-20, 20), \
            #            textcoords = 'offset points', ha = 'right', va = 'bottom', \
            #            bbox = dict(boxstyle = 'round,pad=0.5', fc = 'yellow', alpha = 0.5), \
            #            arrowprops = dict(arrowstyle = '->', connectionstyle = 'arc3,rad=0'))


            if len(x) > 1 and len(y) > 1:
                " least-squares solution to a linear matrix equation. "
                v = pylab.vstack([x,pylab.ones(len(x))]).T
                m,c = pylab.linalg.lstsq(v,y)[0]
                subplot.plot(mag_range,[m*i+c for i in mag_range], 'r', label='Fitted line')
                s = "y = %0.1fX + %0.1f" % (m,c)
                subplot.text(mag_range[1], mag_range[-2], s, size='5', bbox=dict(boxstyle='round', ec='0.5', facecolor='red', alpha=0.5))

                """ 
                Single plot figure. 
                Open a new buffer and 
                build an independent image
                to be saved to disk.
                """
                fig2 = pylab.figure(t_p,dpi=200)
                pylab.scatter(x,y)
                pylab.title('Compare magnitudes between %s and %s' % (x_label,y_label),fontsize=18) 
                pylab.plot(mag_range,[m*i+c for i in mag_range], 'r', label='Fitted line')
                pylab.text(mag_range[1], mag_range[-2], s, size='20', bbox=dict(boxstyle='round', ec='0.5', facecolor='red', alpha=0.5))
                pylab.ylim([1,max_mag])
                pylab.xlim([1,max_mag])
                pylab.yticks(mag_range)
                pylab.xticks(mag_range)
                pylab.xlabel('%s - %s' % (mp,x_label), fontsize=14)
                pylab.ylabel('%s - %s' % (ms,y_label), fontsize=14)
                name = "./magnitudes_%s-%s_vs_%s-%s.png" % (x_label,mp,y_label,ms)
                pylab.savefig(name,bbox_inches='tight', edgecolor='none',pad_inches=0.5,dpi=200)
                os.system( "open %s" % name )

            pylab.figure(0)
            subplot.set_ylim([1,max_mag])
            subplot.set_xlim([1,max_mag])
            subplot.set_yticks(mag_range)
            subplot.set_xticks(mag_range)
            subplot.set_xlabel('%s - %s' % (mp,x_label), fontsize=14)
            subplot.set_ylabel('%s - %s' % (ms,y_label), fontsize=14)

            t_p = t_p + 1


    """
    Set image size and title.
    """
    pl = pylab.gcf()
    #ax = pylab.gca()
    pl.suptitle('Compare magnitudes between %s and %s' % (x_label,y_label),fontsize=18) 
    #DefaultSize = pl.get_size_inches()
    #pl.set_size_inches( (DefaultSize[0]*4, DefaultSize[1]*4) )

    name = "./magnitudes_%s_vs_%s.png" % (x_label,y_label)
    pylab.savefig(name,bbox_inches='tight', edgecolor='none',pad_inches=0.5,dpi=300)
    os.system( "open %s" % name )
    #pylab.show()



def get_points(el,p_mag,s_mag):
    #sta_list[sta] = {'lat':lat,'lon':lon,'chans':list_chans}
    primary_mag = False
    secondary_mag = False

    list_x = []
    list_y = []

    for e in el:

        for o in el[e]:

            if el[e][o]['atype'] == 'p' and p_mag == el[e][o]['magtype']:
                primary_mag = el[e][o]['magnitude']
            if el[e][o]['atype'] == 's' and s_mag == el[e][o]['magtype']:
                secondary_mag = el[e][o]['magnitude']

        " Verify that we have one of each. "
        if primary_mag and secondary_mag:
            list_x.append(primary_mag)
            list_y.append(secondary_mag)

        " Clean temp variables. "
        primary_mag = False
        secondary_mag = False

    return list_x,list_y


if __name__ == '__main__':
    sys.exit(main())
else:
    raise Exception("Not a module to be imported!")
    sys.exit(1)


