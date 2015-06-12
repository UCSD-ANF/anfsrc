"""
Retrieve IRIS Power Density Function plots

Juan Reyes
reyes@ucsd.edu
"""

import urllib2
import glob

# Load time functions
import time

from time import strftime, gmtime
from optparse import OptionParser

try:
    import json
    import logging as logging
    logging.basicConfig(format='update_rrd[%(levelname)s]: %(message)s')
    logging.addLevelName(35, "NOTIFY")
    logger = logging.getLogger()

except Exception,e:
    sys.exit('Problems loading logging lib. %s' % e)

def log(msg=''):
    if not isinstance(msg, str): msg = pprint(msg)
    logger.info(msg)

def debug(msg=''):
    if not isinstance(msg, str): msg = pprint(msg)
    logger.debug(msg)

def warning(msg=''):
    if not isinstance(msg, str): msg = pprint(msg)
    logger.warning("\t*** %s ***" % msg)

def notify(msg=''):
    if not isinstance(msg, str): msg = pprint(msg)
    logger.log(35,msg)

def error(msg=''):
    if not isinstance(msg, str): msg = pprint(msg)
    logger.critical(msg)
    sys.exit("\n\n\t%s\n\n" % msg)

def pprint(obj):
    return "\n%s" % json.dumps( obj, indent=4, separators=(',', ': ') )



# Load datascope functions
import antelope.datascope as datascope
import antelope.stock as stock

# Global variables
# Parameter file of exceptions

usage = "usage: %prog [options]"
parser = OptionParser(usage=usage)
parser.add_option("-c", action="store_true", dest="clean",
        help="Clean all files in STA repo.", default=False)
parser.add_option("-a", action="store_true", dest="all",
        help="Force run on ALL sites.", default=False)
parser.add_option("-v", action="store_true", dest="verbose",
        help="verbose output", default=False)
parser.add_option("-p", action="store", dest="pf",
        help="Parameter file to use", default=sys.argv[0])
(options, args) = parser.parse_args()


if options.verbose:
    logger.setLevel(logging.INFO)
    log('Set log level to INFO')

#
# Parse parameter file
#
log('Read PF "%s"' % options.pf)
try:
    pf = stock.pfread(options.pf)
except Exception,e:
    error('Problems with PF %s' % options.pf)

IRIS_SITE = pf.get('iris_site')
DBMASTER = pf.get('dbmaster')
PHOTO_PATH = pf.get('photo_path')
STA_SUBSET = pf.get('sta_subset')
SNET_SUBSET = pf.get('snet_subset')
CHAN_SUBSET = pf.get('chan_subset')

log( "Config:" )
log( "\tIRIS_SITE: %s" % IRIS_SITE )
log( "\tDBMASTER: %s" % DBMASTER )
log( "\tPHOTO_PATH: %s" % PHOTO_PATH )
log( "\tSTA_SUBSET: %s" % STA_SUBSET )
log( "\tSNET_SUBSET: %s" % SNET_SUBSET )
log( "\tCHAN_SUBSET: %s" % CHAN_SUBSET )


def clean_dir(directory):

    files = glob.glob('%s/*' % directory)

    for f in files:
        log( "\t\t\tRemove file: %s" % f )
        try:
            os.remove(f)
        except Exception,e:
            error('Cannot remove %s => %s' % (f,e) )

def fix_date(date):
    date = str( date )
    year = date[:4]
    jday = date[4:]
    new_date = "%s.%s" % (year,jday)

    log( "\t\t\t\tfix_date(%s)=>%s" % (date,new_date) )

    return new_date


def query(type,net,sta,chan,ondate,offdate,chanid):

    log( "\t\t\tquery(%s,%s,%s,%s,%s,%s,%s)" % \
            (type,net,sta,chan,ondate,offdate,chanid) )

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

    log( '\t\t\tType: %s Start: %s End: %s '% (type,ondate,offdate) )

    try:
        try:
                os.stat('%s/%s' % (PHOTO_PATH,sta))
        except:
                os.mkdir('%s/%s' % (PHOTO_PATH,sta))

        file = IRIS_SITE + "pdf_S%s_E%s_c%s_l++_n%s_s%s.png" % (ondate,offdate,chan,net,sta)

        notify( '\t\t\tQuery file: ' + file )

        target = PHOTO_PATH + '/%s/%s_%s_%s_%s_%s.png' % (sta,net,sta,chan,type,chanid)

        myfile = urllib2.urlopen(file).read()

        save = open( target, 'wb' )
        savestr = str(myfile)
        save.write(savestr)
        save.close()

        log( '\t\t\t' + target )

    except Exception,e:

        warning( 'PDF '+sta+':'+chan+' / %s.' % e )



#  Datascope database operations
db = datascope.dbopen( DBMASTER, "r" )
log( "Opend deployment table" )

deployment = db.lookup( table='deployment' )

log( "%s entries on table" % deployment.record_count )

if STA_SUBSET:
    log( "subset on sta =~/%s/" % STA_SUBSET )
    deployment = deployment.subset( "sta =~ /%s/" % STA_SUBSET)
    log( "%s entries on table" % deployment.record_count )

if SNET_SUBSET:
    log( "subset on snet =~/%s/" % SNET_SUBSET )
    deployment = deployment.subset( "snet =~ /%s/" % SNET_SUBSET)
    log( "%s entries on table" % deployment.record_count )

log( "sort unique on snet, sta" )
deployment = deployment.sort(("snet","sta"),unique=True )
log( "%s entries on table" % deployment.record_count )

for dbrecord in deployment.iter_record():

    sta = dbrecord.getv( "sta" )[0]
    snet = dbrecord.getv( "snet" )[0]

    log( "%s %s:" % (sta, snet) )

    # Make a subset view with only that station
    log( "\tLookup sitechan" )
    sitechan = db.lookup( table='sitechan' )
    log( "\tsubset( sta =~ /%s/ && chan =~ /%s/ )" % \
            (sta,CHAN_SUBSET) )
    sitechan = sitechan.subset( "sta =~ /%s/ && chan =~ /%s/" % \
            (sta,CHAN_SUBSET) )

    if sitechan.record_count < 1:
        warning( "***** NOTHING AFTER SUBSET *****" )
        continue

    if options.clean: clean_dir("%s/%s" % (PHOTO_PATH,sta) )

    for siterecord in sitechan.iter_record():
        # Get the value of time of the first record
        chan = siterecord.getv( "chan" )[0]
        ondate = int( siterecord.getv( "ondate" )[0] )
        offdate = int( siterecord.getv( "offdate" )[0] )
        chanid = siterecord.getv( "chanid" )[0]

        today = int( stock.epoch2str(stock.now(), "%Y%j") )

        # fix offdate
        if offdate < 0 or offdate > today:
            offdate =  today

        log( "\t\tondate=%s offdate=%s chanid=%s" % \
                (ondate, offdate, chanid) )

        too_old = int( stock.epoch2str(stock.now()-7776000, "%Y%j") )

        if ( not options.all and offdate < too_old ):
            log( "\t\t offdate: %s too_old: %s" % (offdate, too_old) )
            log( "\t\t%s Removed more than 90 days ago. SKIPPING!" % sta )
            continue

        if offdate == today:
            log( "\t\t%s Is Active in Database" % sta )
            segments = ['week','month','year','lifetime']
            #offdate = stock.now() - (86400*2) # secs in a day time 2
            #offdate = int( stock.epoch2str(offdate, "%Y%j") )
        else:
            log( "\t\t%s Is Decom in Database" % sta )
            segments = ['lifetime']

        for type in segments:
            query(type,snet,sta,chan,ondate,offdate,chanid)

    sitechan.free()

log( 'All stations checked' )

exit(0)
