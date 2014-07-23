'''
Use multiprocessing and subprocess and Beej's
Python Flickr API to search & retrieve station photos

@notes    1. Cannot use multiprocessing.Lock() due to Python
             issue 3770. Will result in the following output:
             'ImportError: This platform lacks a functioning
             sem_open implementation, therefore, the required
             synchronization primitives needed will not
             function, see issue 3770.'
          2. Update to use the $ANF/lib/python version of the
             Flickr API, which is 1.4.2
'''

# Import modules
import glob
import time
import json
import urllib2
import smtplib
import subprocess
import multiprocessing
from pprint import pprint
from optparse import OptionParser
from email.mime.text import MIMEText

try:
    import flickrapi
except ImportError:
    sys.exit('Import Error: Do  you have the Python Flickr API module '\
            'installed correctly?')

try:
    import antelope.datascope as datascope
    import antelope.stock as stock
except Exception,e:
    sys.exit('Problems loading Antelope. %s' % e)

try:
    pf = stock.pfread('common.pf')
except Exception,e:
    sys.exit('Cannot read %s => %s' % ('common.pf',e))


# Global flags
dry = False
verbose = False
inThread = False
threadLog = '\n'
globalLog = ''

def logfmt(message):

    if message is None: return

    global inThread
    global threadLog
    global globalLog

    if inThread:
        #msg = '%s\t%s' % (stock.strtime(stock.now()), message)
        msg = '    %s' % (message)
        threadLog += msg + '\n'
        #print msg
    else:
        msg = '%s %s' % (stock.strtime(stock.now()), message)
        globalLog += msg + '\n'
        print msg


def configure():
    """Parse command line arguments

    """

    global verbose
    global dry

    usage = "Usage: %prog [options]"
    parser = OptionParser(usage=usage)
    parser.add_option("-n", "--none", action="store_true", dest="none",
                      help="dry run", default=False)
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose",
                      help="verbose output", default=False)
    parser.add_option("-s", "--station", action="store", dest="station_override",
                      help="station override", default=False)
    parser.add_option("-p", "--pf", action="store", dest="pf",
                        default='', type="string", help="parameter file path")
    (options, args) = parser.parse_args()

    # Default pf file
    for p in  list(stock.pffiles('flickrdownload')):
        if os.path.isfile(p):
            pfname = p

    if options.pf:
        if os.path.isfile(options.pf):
            pfname = options.pf
        else:
            sys.exit("Command line defined parameter file '%s' does not exist" % options.pf)

    verbose = options.verbose
    dry = options.none

    return options.station_override, pfname


def parse_pf(pfname):
    """Parse parameter file

    """
    from antelope.stock import PfReadError

    parsed_pf = {}

    try:
        pf = stock.pfread(pfname)
    except PfReadError,e:
        sys.exit('Cannot read %s => %s' % (pfname,e))

    parsed_pf['net_code'] = pf.get('net_code')
    parsed_pf['api_key'] = pf.get('api_key')
    parsed_pf['api_secret'] = pf.get('api_secret')
    parsed_pf['token'] = pf.get('token')
    parsed_pf['myid'] = pf.get('myid')
    dbmaster_key = pf.get('dbmaster_key')
    parsed_pf['all_tags'] = pf.get('all_tags')
    parsed_pf['flickr_url_path'] = pf.get('flickr_url_path')
    parsed_pf['tester_tags'] = pf.get('tester_tags')
    parsed_pf['sendmail'] = pf.get('sendmail')
    parsed_pf['recipients'] = pf.get('recipients')

    # Get generalized config parameter file vars
    try:
        pf = stock.pfread('common.pf')
    except PfReadError,e:
        sys.exit('Cannot read %s => %s' % ('common.pf',e))

    cache_json = pf.get('CACHEJSON')
    parsed_pf['dbmaster'] = pf.get(dbmaster_key)
    parsed_pf['photo_path'] = pf.get('CACHE_TOP_PICK')
    parsed_pf['json_file_path'] = '%s/stations/stations.json' % cache_json
    parsed_pf['num_processes'] = int(multiprocessing.cpu_count()/3) # Be nice & only use a third of available processors
    parsed_pf['then'] = stock.now() - 604800 # Within the last week ago

    return parsed_pf


def build_stalist(json_dict, params):
    """Parse the JSON file dict and
    return list of all stations in reverse
    order for the pop() later

    """

    global verbose
    sta_list = []

    for sta_type in json_dict:
        for sta_name in json_dict[sta_type]:
            if json_dict[sta_type][sta_name]['snet'] == params['net_code']:
                sta_list.append(sta_name)
                #if verbose: logfmt( "%s" % sta_name )

    sta_list.sort(reverse=True)
    if verbose: logfmt( "List: %s" % sta_list )

    return sta_list


def json_stalist(json_file, params, overwrite):
    """Get a list of stations
    from the JSON file specified

    """

    file_pointer = open(json_file,'r').read()
    my_json_obj = json.loads(file_pointer)
    json_sta_list = build_stalist(my_json_obj, params)

    if len(overwrite):
        temp = []
        for sta in overwrite:
            if sta in json_sta_list:
                temp.append(sta)
        json_sta_list = temp

    return json_sta_list


def per_sta_query(flickr, staname, params, conn):
    """Create a subprocess
    for the selected station

    """

    global inThread
    global threadLog

    inThread = True

    logfmt("Start %s at %s" % (staname,stock.strtime(stock.now())) )

    try:
        conn.send( flickr_photo_retrieval(flickr, staname, params) )
    except Exception, e:
        conn.send( "    %s execution failed: %s: %s" % (staname,Exception,e) )


    try:
        conn.send( threadLog )
        conn.close()
    except:
        pass



def flickr_tag_precedence(flickr, tag, sta, params):
    """Search photos tagged in Flickr
    and return in order of precedence

    """

    global verbose

    result_tags = {}
    for k,v in params['tester_tags'].iteritems():
        tag1_suffix = v[0]
        tag2_prefix = v[1]
        final_tags = tag+tag1_suffix+', '+tag2_prefix+sta

        try:
            search = flickr.photos_search(user_id=params['myid'],
                    tags=final_tags, tag_mode='all', per_page='10')
        except Exception, e:
            logfmt("Exception: %s: %s" % (final_tags,e))
            time.sleep(5)

        if len(search.find('photos')) > 0:
            #result_tags[k] = (tag1_suffix, tag2_prefix)
            result_tags[k] = (tag1_suffix, tag2_prefix)
            if verbose:
                logfmt("Tagged '%s%s, %s%s': MATCH" % (tag, tag1_suffix, tag2_prefix, sta))
            return [ tag+tag1_suffix, tag2_prefix+sta, search]
        else:
            if verbose:
                logfmt("Tagged '%s%s, %s%s': FAILED" % (tag, tag1_suffix, tag2_prefix, sta))

    # Precedence
    #if 'before' in result_tags:
    #    return [ tag+result_tags['before'][0], result_tags['before'][1]+sta ]
    #elif 'after' in result_tags:
    #    return [ tag+result_tags['after'][0], result_tags['after'][1]+sta ]
    #elif 'simple' in result_tags:
    #    return [ tag+result_tags['simple'][0], result_tags['simple'][1]+sta ]
    #elif 'none' in result_tags:
    #    return [ tag+result_tags['none'][0], result_tags['none'][1]+sta ]
    #else:
    #    logfmt('CRITICAL:    *** No matching photos for any of the tag selections. ***')
    #    raise SystemExit

    logfmt('CRITICAL:    *** No matching photos for any of the tag selections. ***')
    raise Exception

def delete_local_flickr_img(img_path, img_id, params):
    """Use glob to delete any pre-existing file for
    this image that does not match the one about to
    be downloaded

    """

    for entry in glob.glob(img_path):
        # identify img_id in entry...
        if(entry.count(img_id) == 0 ):
            logfmt("Warning: Pre-existing file %s that is no longer valid. Deleting...\n" % entry)
            try:
                os.remove(entry)
            except OSError, e:
                logfmt("Error: %s occurred when trying to delete the file %s\n" % (e.errno, entry))
        else:
            statinfo = os.stat(entry)
            if( statinfo.st_size < 1 ):
                logfmt("Warning: Pre-existing file %s has a file size of zero! Deleting...\n" % entry)
                try:
                    os.remove(entry)
                except OSError, e:
                    logfmt("Error: %s occurred when trying to delete the file %s\n" % (e.errno, entry))
    return


def download_flickr_img(img_path, photo, params):
    """Attempt to download the photo from
    Flickr to a local file system

    """

    global verbose

    if verbose:
        logfmt('Test for %s' % img_path )

    if not os.path.exists(img_path):
        my_file = params['flickr_url_path'] % (photo.attrib['farm'],
                photo.attrib['server'], photo.attrib['id'], photo.attrib['secret'])

        if verbose:
            logfmt('%s' % my_file )

        try:
            downloaded = urllib2.urlopen(my_file).read()
        except Exception,e:
            logfmt('%s while saving image for %s' % (e,my_file))
        else:
            save = open(img_path, 'wb')
            savestr = str(downloaded)
            save.write(savestr)
            save.close()
            logfmt('Saving photo: %s' % my_file )

    if verbose:
        logfmt('Image %s already exists' % img_path )

    return


def flickr_photo_retrieval(flickr, sta, params):
    """Grab the matching photo
    from Flickr

    """

    global dry
    global verbose

    for i in range(len(params['all_tags'])):
        try:
            the_auth_tag, the_sta_tag, search = flickr_tag_precedence(flickr, params['all_tags'][i], sta, params)
        except:
            logfmt('No photo for %s: %s.' % (sta, params['all_tags'][i]) )
            continue

        if verbose:
            logfmt("Using tags '%s, %s'" % (the_auth_tag, the_sta_tag))

        mytags = "%s, %s" % (the_sta_tag, the_auth_tag)

        #try:
        #    search = flickr.photos_search(user_id=params['myid'],
        #            tags=mytags, tag_mode='all', per_page='10')
        #except:
        #    try:
        #        search = flickr.photos_search(user_id=params['myid'],
        #                tags=mytags, tag_mode='all', per_page='10')
        #    except Exception, e:
        #        logfmt("Cannot do final search for %s :%s " (mytags,e) )
        #        continue

        if len(search.find('photos').findall('photo')) > 1:
            multiple_photos = len(search.find('photos').findall('photo'))
            logfmt("Warning: %d different photos match the tag query %s." % (multiple_photos, mytags) )

        # Grab all matching photos
        try:
            photo = search.find('photos').findall('photo')[0]
        except:
            photo = False
            logfmt('ERROR: Problem getting name of photo for tag: %s' % mytags)
            continue


        if dry:
            logfmt('*** Dry run. Avoid downloads of images. ***')
        else:
            img = '%s/%s_%s_%s.jpg' % (params['photo_path'], sta, params['all_tags'][i], photo.attrib['id'])
            if verbose: logfmt("Search for img: %s" % img)
            greedy_file_search = '%s/%s*_%s_*.jpg' % (params['photo_path'], sta, params['all_tags'][i])
            if verbose: logfmt("Search for greedy_file_search: %s" % greedy_file_search)
            delete_local_flickr_img(greedy_file_search, photo.attrib['id'], params)
            download_flickr_img(img, photo, params)


    return


def main():
    """Grab & parse station list
    then run subprocesses to
    grab photos from Flickr

    """

    global verbose
    global globalLog

    station, pfname = configure()

    params = parse_pf(pfname)

    if verbose: pprint(params)

    flickr = flickrapi.FlickrAPI(params['api_key'],
            params['api_secret'], token=params['token'])

    if station:
        file_sta_list = json_stalist(params['json_file_path'], params,
                                     station.split(','))
    else:
        file_sta_list = json_stalist(params['json_file_path'], params, [])

    if verbose:
        logfmt('Flickr Python Photo Downloader started')
        logfmt('Checking %s stations...' % params['net_code'])
        logfmt('Email will be sent to: %s' % ', '.join(params['recipients']))
        logfmt('Number of processes: %s' % params['num_processes'])
        logfmt('Number of stations to process: %s' % len(file_sta_list))

    logfmt('Flickr Python Photo Downloader started')
    logfmt('Checking %s stations...' % params['net_code'])

    threads = []
    while len(multiprocessing.active_children()) or len(file_sta_list) > 0:
        if ( len( multiprocessing.active_children() ) < params['num_processes']) and len(file_sta_list) > 0:
            mysta = file_sta_list.pop()

            if verbose: logfmt('New Process: %s' % mysta)

            parent_conn, child_conn = multiprocessing.Pipe()
            p = multiprocessing.Process(target=per_sta_query, args=[flickr, mysta, params, child_conn])
            p.start()
            threads.append(parent_conn)

        for thread in threads:
            try:
                if thread.poll():
                    logfmt( thread.recv() )
            except:
                thread.close()
                pass

    logfmt('All %s stations checked. Goodbye..' % params['net_code'])
    logfmt('Flickr Photo Downloader finished')


    if params['recipients'] and params['recipients'][0]:
        logfmt('Sending email to %s' % params['recipients'])
        msg = MIMEText(globalLog, 'plain')
        msg_from = 'rt@anfwebproc.ucsd.edu'
        msg['Subject'] = 'Flickr photo archive retrieval output'
        msg['From'] = msg_from
        msg['To'] = ','.join(params['recipients'])

        sm = smtplib.SMTP('localhost')
        sm.sendmail(msg_from, params['recipients'],  msg.as_string())
        sm.quit()


    return 0

if __name__ == '__main__':
    sys.exit( main() )
