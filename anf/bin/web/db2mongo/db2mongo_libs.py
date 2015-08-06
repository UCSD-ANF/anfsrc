"""
Safe to use as:
    from db2web_libs import *
"""
from __main__ import *


def log(msg=''):
    if not isinstance(msg, str):
        msg = pprint(msg)
    logger.info(msg)


def debug(msg=''):
    if not isinstance(msg, str):
        msg = pprint(msg)
    logger.debug(msg)


def warning(msg=''):
    if not isinstance(msg, str):
        msg = pprint(msg)
    logger.warning("\t*** %s ***" % msg)


def notify(msg=''):
    if not isinstance(msg, str):
        msg = pprint(msg)
    logger.log(35,msg)


def error(msg=''):
    if not isinstance(msg, str):
        msg = pprint(msg)
    logger.critical(msg)
    sys.exit("\n\n\t%s\n\n" % msg)


def pprint(obj):
    return "\n%s" % json.dumps( obj, indent=4, separators=(',', ': ') )

def run(cmd,directory='./'):
    debug("run()  -  Running: %s" % cmd)
    p = subprocess.Popen([cmd], stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         cwd=directory, shell=True)
    stdout, stderr = p.communicate()

    if stderr:
        error('STDERR present: %s => \n\t%s'  % (cmd,stderr) )

    for line in iter(stdout.split('\n')):
        debug('stdout:\t%s'  % line)

    if p.returncode != 0:
        notify('stdout:\t%s'  % line)
        error('Exitcode (%s) on [%s]' % (p.returncode,cmd))

    return stdout


class event2jsonException(Exception):
    """
    Local class to raise Exceptions to the
    rtwebserver framework.
    """
    def __init__(self, msg):
        self.msg = msg
    def __repr__(self):
        return 'event2jsonException: %s' % (self.msg)
    def __str__(self):
        return repr(self)

class sta2jsonException(Exception):
    """
    Local class to raise Exceptions to the
    rtwebserver framework.
    """
    def __init__(self, msg):
        self.msg = msg
    def __repr__(self):
        return 'sta2jsonException: %s' % (self.msg)
    def __str__(self):
        return repr(self)



def find_snet(blob,sta,debug=False):
    """
    Sometimes we don't know if the snet value of a station.
    Look in the object for it's snet.
    """

    for status in blob:
        for snet in blob[status]:
            if sta in blob[status][snet]:
                log( "find_snet(%s) => %s" % (sta,snet) )
                return snet

    log("find_snet(%s) => False" % sta)
    return False

def find_status(blob,sta,debug=False):
    """
    Sometimes we don't know if the station is active or offline.
    Look in the object for it's status.
    """

    for status in blob:
        for snet in blob[status]:
            if sta in blob[status][snet]:
                log( "find_status(%s) => %s" % (sta,status))
                return status

    log("find_status(%s) => False" % sta )
    return False


def parse_time(time):
    """
    Verify that we have a valid time. Not in future.
    NULL == '-'
    """

    try:
        if int(float(time)) > stock.now(): raise
        return int(float(time))

    except:
        return '-'


def test_yesno(v):
    """
    Verify if we have true or false
    on variable.
    """
    return str(v).lower() in ("y", "yes", "true", "t", "1")


def test_table(dbname,tbl,verbose=False):
    """
    Verify that we can work with table.
    Returns path if valid and we see data.
    """


    path = False

    try:
        with datascope.freeing(datascope.dbopen( dbname , 'r' )) as db:
            db = db.lookup( table=tbl )

            if not db.query(datascope.dbTABLE_PRESENT):
                warning( 'No dbTABLE_PRESENT on %s' % dbname )
                return False

            if not db.record_count:
                warning( 'No %s.record_count' % dbname )
                return False

            path = db.query('dbTABLE_FILENAME')

    except Exception,e:
        warning("Prolembs with db[%s]: %s" % (dbname,e) )
        return False

    return path


def flatten_cache( cache ):
    """
    Need to reshape the dict
    """
    newCache = []

    for snet in cache:
        if not snet: continue
        for sta in cache[snet]:
            if not sta: continue
            oldEntry = cache[snet][sta]
            oldEntry['dlname'] = snet + '_' + sta
            newCache.append(oldEntry)

    return newCache



def index_db(collection, indexlist ):
    """
    Set index values on MongoDB
    """

    re_simple = re.compile( '.*simple.*' )
    re_text = re.compile( '.*text.*' )
    re_sparse = re.compile( '.*sparse.*' )
    re_hashed = re.compile( '.*hashed.*' )
    re_unique = re.compile( '.*unique.*' )

    debug( indexlist )
    for field, param in indexlist.iteritems():

        unique = 1 if re_unique.match( param ) else 0
        sparse = 1 if re_sparse.match( param ) else 0

        style = 1
        if re_text.match( param ):
            style = 'text'
        elif re_hashed.match( param ):
            style = 'hashed'
        elif re_simple.match( param ):
            style = 1

        try:
            expireAfter = float( param )
        except:
            expireAfter = False

        log("ensure_index( [(%s,%s)], expireAfterSeconds = %s, unique=%s, sparse=%s)" % \
                (field,style,expireAfter,unique,sparse) )
        collection.ensure_index( [(field,style)], expireAfterSeconds = expireAfter,
                unique=unique, sparse=sparse)

    collection.reindex()

    for index in collection.list_indexes():
        debug(index)



def get_md5(test_file,debug=False):
    """
    Verify the checksum of a table.
    Return False if no file found.
    """

    log('get_md5(%s) => test for file' % test_file )

    if os.path.isfile( test_file ):
        f = open(test_file)
        md5 = hashlib.md5( f.read() ).hexdigest()
        f.close()
        return md5
    else:
        raise sta2jsonException( "get_md5(%s) => FILE MISSING!!!" % test_file )


    return False

def dict_merge(a, b):
    '''recursively merges dict's. not just simple a['key'] = b['key'], if
    both a and bhave a key who's value is a dict then dict_merge is called
    on both values and the result stored in the returned dictionary.'''
    if not isinstance(b, dict):
        return b
    for k, v in b.iteritems():
        if k in a and isinstance(a[k], dict):
                a[k] = dict_merge(a[k], v)
        else:
            a[k] = v
    return a
