"""
Retrieve IRIS Power Density Function plots

Juan Reyes
reyes@ucsd.edu
"""

import pprint
import urllib2
import glob

# Load time functions
import time

from time import strftime, gmtime

# Load datascope functions
import antelope.datascope as datascope
import antelope.stock as stock

# Global variables
# Parameter file of exceptions
verbose = False
cleanup = True
get_all = False
web_root          = '/anf/web/vhosts/anf.ucsd.edu'
iris_site         = "http://www.iris.washington.edu/servlet/quackquery/plotcache/"
dataless_dir      = '/anf/TA/products/dataless_sta'

common_pf         = web_root + '/conf/common.pf'
pf = stock.pfupdate(common_pf);
dbmaster          = pf.get('USARRAY_DBMASTER')
photo_path        = pf.get('CACHE_PDF')


# array to store exception names
sta_subset = ''
snet_subset = 'TA|AZ|AK'
chan_subset = '[B|H][H|N][E|N|Z]'

# Channels
#chans = ['BHZ','BHN','BHE','LHZ','LHN','LHE']
#chans = ['BHZ','BHN','BHE','HHZ','HHN','HHE','LHZ','LHN','LHE']

if verbose:
    print "Config:"
    print "\tcommon_pf: %s" % common_pf
    print "\tdbmaster: %s" % dbmaster
    print "\tphoto_path: %s" % photo_path
    print "\tweb_root: %s" % web_root
    print "\tiris_site: %s" % iris_site
    print "\tdataless_dir: %s" % dataless_dir

def clean_dir(directory):
    files = glob.glob('%s/*' % directory)
    for f in files:
        if verbose: print "\t\t\tRemove file: %s" % f
        try:
            os.remove(f)
            pass
        except Exception,e:
            exit('Cannot remove %s => %s' % (f,e) )

def fix_date(date):
    date = str( date )
    year = date[:4]
    jday = date[4:]
    new_date = "%s.%s" % (year,jday)

    if verbose:
        print "\t\t\t\tfix_date(%s)=>%s" % (date,new_date)

    return new_date


def query(type,net,sta,chan,ondate,offdate,chanid):

    if verbose:
        print "\t\t\tquery(%s,%s,%s,%s,%s,%s,%s)" % \
                (type,net,sta,chan,ondate,offdate,chanid)

    if type == 'week':
        ondate = stock.now() - (604800) # secs in a week times 3
        ondate =  stock.epoch2str(ondate, "%Y.%j")
    elif type == 'month':
        ondate = stock.now() - (2680200) # secs in a month
        ondate =  stock.epoch2str(ondate, "%Y.%j")
    elif type == 'year':
        ondate = stock.now() - (31622400) # secs in a year
        ondate =  stock.epoch2str(ondate, "%Y.%j")
    else:
        ondate = fix_date(ondate)

    ## convert to yearday format
    #ondate =  stock.epoch2str(ondate, "%Y.%j")

    ## compare to date on database
    #if ondate < time:
    #    ondate = time

    # convert from 2014001 to 2014.001
    offdate = fix_date(offdate)

    if verbose: print '\t\t\tType: %s Start: %s End: %s '% (type,ondate,offdate)

    try:
        try:
                os.stat('%s/%s' % (photo_path,sta))
        except:
                os.mkdir('%s/%s' % (photo_path,sta))

        file = iris_site + "pdf_S%s_E%s_c%s_l++_n%s_s%s.png" % (ondate,offdate,chan,net,sta)

        print '\t\t\tSaving file ' + file

        target = photo_path + '/%s/%s_%s_%s_%s_%s.png' % (sta,net,sta,chan,type,chanid)

        myfile = urllib2.urlopen(file).read()

        save = open( target, 'wb' )
        savestr = str(myfile)
        save.write(savestr)
        save.close()

        print '\t\t\t' + target

    except Exception,e:

        print 'PDF '+sta+':'+chan+' / %s.' % e



#  Datascope database operations
db = datascope.dbopen( dbmaster, "r" )
if verbose:
    print "Opend deployment table"
deployment = db.lookup( table='deployment' )
if sta_subset:
    if verbose:
        print "subset on sta =~/%s/" % sta_subset
    deployment = deployment.subset( "sta =~ /%s/" % sta_subset)
if snet_subset:
    if verbose:
        print "subset on snet =~/%s/" % snet_subset
    deployment = deployment.subset( "snet =~ /%s/" % snet_subset)
deployment = deployment.sort(("snet","sta"),unique=True )

if verbose:
    print "%s entries on table" % deployment.query(datascope.dbRECORD_COUNT)

for i in range(0,deployment.query(datascope.dbRECORD_COUNT)):

    # Get name of station from global database
    deployment.record = i
    sta = deployment.getv( "sta" )[0]
    snet = deployment.getv( "snet" )[0]

    if verbose:
        print "%s %s:" % (sta, snet)

    # Make a subset view with only that station
    if verbose:
        print "\tLookup sitechan"
    sitechan = db.lookup( table='sitechan' )
    if verbose:
        print "\tsubset( sta =~ /%s/ && chan =~ /%s/ )" % \
            (sta,chan_subset)
    sitechan = sitechan.subset( "sta =~ /%s/ && chan =~ /%s/" % \
            (sta,chan_subset) )

    if sitechan.query(datascope.dbRECORD_COUNT) < 1:
        print "***** NOTHING AFTER SUBSET *****"
        continue

    if cleanup: clean_dir("%s/%s" % (photo_path,sta) )

    for i in range(0,sitechan.query(datascope.dbRECORD_COUNT)):
        # Get the value of time of the first record
        sitechan.record=i
        chan = sitechan.getv( "chan" )[0]
        ondate = int( sitechan.getv( "ondate" )[0] )
        offdate = int( sitechan.getv( "offdate" )[0] )
        chanid = sitechan.getv( "chanid" )[0]

        today = int( stock.epoch2str(stock.now(), "%Y%j") )

        # fix offdate
        if offdate < 0 or offdate > today:
            offdate =  today

        if verbose:
            print "\t\tondate=%s offdate=%s chanid=%s" % \
                    (ondate, offdate, chanid)

        too_old = int( stock.epoch2str(stock.now()-7776000, "%Y%j") )

        if ( not get_all and offdate < too_old ):
            if verbose:
                print "\t\t offdate: %s too_old: %s" % (offdate, too_old)
                print "\t\t%s Removed more than 90 days ago. SKIPPING!" % sta
            continue

        if offdate == today:
            if verbose: print "\t\t%s Is Active in Database" % sta
            segments = ['week','month','year','lifetime']
            #offdate = stock.now() - (86400*2) # secs in a day time 2
            #offdate = int( stock.epoch2str(offdate, "%Y%j") )
        else:
            if verbose: print "\t\t%s Is Decom in Database" % sta
            segments = ['lifetime']

        for type in segments:
            query(type,snet,sta,chan,ondate,offdate,chanid)

    sitechan.free()

if verbose: print 'All stations checked'

exit(0)
