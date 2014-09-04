"""
Retrieve missing IRIS Power Density Function plots

1) Verify the deplopyment table.
2) Verify if we have valid PD plots  for every channel
on each sta_chan selected. 
3)Verify if the time of the local plot is within one day
of the endtime day of station. For some stations with
multiple entries we get the time of the first entry and
the entime of the last entry. 
4) We verify the date on the dataless file for the
station and will get a new plot if the image is older
than the dataless.

Juan Reyes
reyes@ucsd.edu
"""

import pprint
import urllib2

# Load time functions
import time

from time import strftime, gmtime

# Load datascope functions
import antelope.datascope as datascope
import antelope.stock as stock

# Global variables
# Parameter file of exceptions
verbose = True
web_root          = '/anf/web/vhosts/anf.ucsd.edu'
iris_site         = "http://www.iris.washington.edu/servlet/quackquery/plotcache/"
dataless_dir      = '/anf/TA/products/dataless_sta'

common_pf         = web_root + '/conf/common.pf'
pf = stock.pfupdate(common_pf);
dbmaster          = pf.get('USARRAY_DBMASTER')
photo_path        = pf.get('CACHE_PDF')


# array to store exception names
my_exceptions = []
last = ''

# Channels
#chans = ['BHZ','BHN','BHE','LHZ','LHN','LHE']
chans = ['BHZ','BHN','BHE']
if verbose:
    print "Config:"
    print "\tcommon_pf: %s" % common_pf
    print "\tdbmaster: %s" % dbmaster
    print "\tphoto_path: %s" % photo_path
    print "\tweb_root: %s" % web_root
    print "\tiris_site: %s" % iris_site
    print "\tdataless_dir: %s" % dataless_dir


#  Datascope database operations
db = datascope.dbopen( dbmaster, "r" )
deployment = db.lookup( table='deployment' )
sub_deploy = deployment.subset( "snet =~ /TA|AZ|AK/" )
sub_deploy = sub_deploy.sort(("snet","sta"),unique=True )


#  Datascope database operations

def query(type,net,sta,chan,time,endtime):

    if verbose:
        print "query(%s,%s,%s,%s,%s,%s)" % (type,net,sta,chan,time,endtime)

    if type == 'day':
        endtime = stock.now() - (86400*2) # secs in a day time 2
        time = endtime - 86400
    elif type == 'month':
        if endtime > stock.now():
            endtime = stock.now()

        month =  int( stock.epoch2str(endtime, "%m") )
        year =  int (stock.epoch2str(endtime, "%Y") )

        endtime = stock.str2epoch("%s/01/%s" % (month,year) )

        if month == 1:
            time = stock.str2epoch("12/01/%s" % year-1 )
        else:
            time = stock.str2epoch("%s/01/%s" % \
                    (month-1,year) )

    elif type == 'year':
        if endtime > stock.now():
            endtime = stock.now()

        year =  int( stock.epoch2str(endtime, "%Y") )

        endtime = stock.str2epoch("01/01/%s" % year )

        time = stock.str2epoch("01/01/%s" % (year-1) )

    else:
        pass


    time =  stock.epoch2str(time, "%Y.%j")
    endtime =  stock.epoch2str(endtime, "%Y.%j")

    if verbose: print '\t\tType: %s Start: %s End: %s '% (type,time,endtime)

    try:
        try:
                os.stat('%s/%s' % (photo_path,sta))
        except:
                os.mkdir('%s/%s' % (photo_path,sta)) 

        file = iris_site + "pdf_S%s_E%s_c%s_l++_n%s_s%s.png" % (time,endtime,chan,net,sta)

        print '\t\tSaving file ' + file

        target = photo_path + '/%s/%s_%s_%s_%s.png' % (sta,net,sta,chan,type)

        myfile = urllib2.urlopen(file).read()

        save = open( target, 'wb' )
        savestr = str(myfile)
        save.write(savestr)
        save.close()

        print '\t\t' + target

    except Exception,e:

        print 'PDF '+sta+':'+chan+' / %s.' % e


for i in range(0,sub_deploy.query(datascope.dbRECORD_COUNT)):

    # Get name of station from global database
    sub_deploy.record = i
    sta = sub_deploy.getv( "sta" )[0]

    if last == sta:
        continue
    last = sta

    # Make a subset view with only that station
    db_subset = deployment.subset( "sta =~ /"+sta+"/" )
    db_subset = db_subset.sort( 'time' )
    n = db_subset.query(datascope.dbRECORD_COUNT)

    # Get the value of time of the first record
    db_subset.record=0
    snet = db_subset.getv( "snet" )[0]
    time = db_subset.getv( "time" )[0]

    # If we have multiple records then get 
    # the endtime of the last...
    if n > 1: db_subset.record=n-1
    endtime = db_subset.getv( "endtime" )[0]

    if endtime > stock.now(): 
        if verbose: print "%s Is Active in Database" % sta
        segments = ['day','month','year','lifetime']
    else:
        if verbose: print "%s Is Decom in Database" % sta
        segments = ['lifetime']


    if (stock.now() - endtime) > 7776000:
        if verbose: print "%s Removed more than 90 days ago. SKIPPING!" % sta
        continue

    for type in segments:
        for i in range(0,len(chans)):
            chan = chans[i]

            query(type,snet,sta,chan,time,endtime)

    db_subset.free()

if verbose: print 'All stations checked'

exit(0)
