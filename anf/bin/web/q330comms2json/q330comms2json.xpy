import json
import gzip

# Load datascope functions
from antelope.datascope import *
from antelope.stock import *
from time import time

from optparse import OptionParser

def logfmt(message):
    """
    Output a log message with a timestamp
    """
    if verbose:
        print "%s %s" %( strtime(time()), message )

usage = "Usage: %prog [options]"
parser = OptionParser(usage=usage)
parser.add_option("-v", action="store_true", dest="verbose", help="verbose output", default=False)
(options, args) = parser.parse_args()

verbose = False
if options.verbose:
    verbose = True

def main():

    pf = pfread('pf/common.pf')
    cache_json = pf['CACHEJSON']
    json_path = '%s/stations' % cache_json
    file_path = '%s/q330comms.json' % json_path

    q330_dict = {}
    q330_fields = [
        'dlsta',
        'inp',
        'ssident',
        'idtag',
        'lat',
        'lon',
        'elev',
        'thr'
    ]

    dbmaster = pf['USARRAY_DBMASTER']
    logfmt("Opening up usarray dbmaster database: %s" % dbmaster)
    db = dbopen(dbmaster, 'r')
    db = db.lookup(table='q330comm')
    db = db.subset('endtime == NULL')
    db = db.sort('dlsta')

    logfmt("Looping over %s records" % db.record_count)

    for i in range(db.record_count):
        db.record = i
        q330_dict[i] = {}
        for f in q330_fields:
            val = db.getv(f)[0]
            q330_dict[i][f] = val

            if f == 'time':
                val = epoch2str( val,'%m/%d/%Y %H:%M:%S %Z' )
                q330_dict[i]['readable_time'] = val
            elif f == 'inp':
                tcp_udp, ip, port, lport, acq, null1, null2 = val.split(':')
                q330_dict[i]['tcp_udp'] = tcp_udp
                q330_dict[i]['ip'] = ip
                q330_dict[i]['port'] = port
                q330_dict[i]['logical_port'] = lport

    logfmt("Dumping JSON file: %s" % file_path)
    output_file_path = '%s+' % file_path
    f = open(output_file_path, 'w') 
    json.dump(q330_dict, f, sort_keys=True, indent=2)
    f.flush()

    try:
        os.rename(output_file_path, file_path)
    except Exception, e:
        logfmt('%s: %s' % (Exception, e))

    logfmt("Create gzip file: %s" % file_path+'.gz')

    f_in = open(file_path, 'rb')
    f_out = gzip.open(file_path+'.gz', 'wb')
    f_out.writelines(f_in)
    f_out.close()
    f_in.close()

    return 0

if __name__ == '__main__':
    sys.exit( main() )
