'''
Functions to help download images from Flickr into
ANF's local archive

Juan Reyes
reyes@ucsd.edu
'''

import os
import glob
import sys
import json
import urllib
import urllib2
import pprint

globalLog = ''

try:
    import antelope.datascope as datascope
    import antelope.stock as stock
except Exception,e:
    sys.exit('Problems loading Antelope. %s' % e)


def lognotify(message):
    logmsg( message, forced=True)

def logerror(message):
    if not isinstance(message, basestring):
        message = pprint.pformat(message, indent=4)

    logmsg('*** %s ***' % message, forced=True)

def logmsg(message, forced=False):

    if message is None: message = ''

    from __main__ import verbose
    global globalLog

    if not forced and not verbose: return

    if not isinstance(message, basestring):
        print type(message)
        message = '\n%s\n' % pprint.pformat(message, indent=4)

    #globalLog = '%s\n%s %s' % (globalLog,stock.strtime(stock.now()), message)
    globalLog += '%s %s\n' % (stock.strtime(stock.now()), message)
    print '%s %s' % (stock.strtime(stock.now()), message)

def dump_log():
    global globalLog
    return globalLog

def parse_pf(pfname):
    """Parse parameter file

    """
    parsed_pf = {}

    try:
        pf = stock.pfread(pfname)
    except Exception,e:
        sys.exit('Cannot read %s => %s' % (pfname,e))

    parsed_pf['api_key'] = pf.get('api_key')
    parsed_pf['api_secret'] = pf.get('api_secret')
    parsed_pf['token'] = pf.get('token')
    parsed_pf['myid'] = pf.get('myid')
    parsed_pf['all_tags'] = pf.get('all_tags')
    parsed_pf['flickr_url_path'] = pf.get('flickr_url_path')
    parsed_pf['sendmail'] = pf.get('sendmail')
    parsed_pf['recipients'] = pf.get('recipients')
    parsed_pf['json_api'] = pf.get( 'json_api' )
    parsed_pf['archive'] = pf.get( 'archive' )

    return parsed_pf


def json_stalist(json_api, snet=False, sta=False, all=False):
    """
    Get a list of stations from the web API

    snet is a subset of SNET values
    sta is a subset of STA values
    all is a flag to add decommissioned sites

    """

    if snet:
        json_api += "&snet=%s" % snet
    if sta:
        json_api += "&sta=%s" % sta
    if all:
        json_api += "&all=true"

    logmsg( json_api )

    try:
        response = urllib.urlopen( json_api )
        data = json.loads( response.read() )
    except Exception,e:
        logerror('Cannot get list of stations')
        sys.exit( "%s => %s" % (json_api, e) )

    lognotify( 'Got [%s] stations' % len( data ) )

    logmsg(data)

    return data


def per_sta_query(flickr, staname, tags, myid, archive, url_path):
    """Create a subprocess
    for the selected station

    """


    logmsg("Start %s at %s" % (staname,stock.strtime(stock.now())) )

    try:
        flickr_photo_retrieval(flickr, staname, tags, myid, archive, url_path)
    except Exception, e:
        logerror( "%s execution failed: %s" % (staname,e) )



def flickr_tag_precedence(flickr, tag, sta, myid):
    """Search photos tagged in Flickr
    and return in order of precedence

    """

    logmsg('Start flickr_tag_precedence [%s] [%s]' % (sta, tag) )


    # Search name with underline
    tags = '%s, %s' % (tag,sta)
    logmsg('Search for %s [%s].' % (sta, tags) )

    try:
        search = flickr.photos_search(user_id=myid,
                tags=tags, tag_mode='all', per_page='10')
        if len(search.find('photos').findall('photo')) < 1:
            logmsg('No matching photos for %s %s.' % (sta, tags) )
        else:
            return search

    except Exception, e:
        logerror("Exception: %s: %s" % (tags,e))
        time.sleep(1)


    # Search name with period
    tags = '%s, %s' % ( tag, sta.replace('_', '.') )
    logmsg('Search for %s [%s].' % (sta, tags) )

    try:
        search = flickr.photos_search(user_id=myid,
                tags=tags, tag_mode='all', per_page='10')
        if len(search.find('photos').findall('photo')) < 1:
            logmsg('No matching photos for %s %s.' % (sta, tags) )
        else:
            return search

    except Exception, e:
        logerror("Exception: %s: %s" % (tags,e))
        time.sleep(1)


    # Search split name
    try:
        tags =  tag
        splitname = sta.split('_')
        if len(splitname) > 1:

            for s in splitname:
                tags += ', %s' % s

            logmsg('Search for %s [%s].' % (sta, tags) )

            search = flickr.photos_search(user_id=myid,
                    tags=tags, tag_mode='all', per_page='10')

            if len(search.find('photos').findall('photo')) < 1:
                logmsg('No matching photos for %s %s.' % (sta, tags) )
            else:
                return search

    except Exception, e:
        logerror("Exception: %s: %s" % (tags,e))
        time.sleep(1)


    return []


def delete_local_flickr_img(img_path, img_id):
    """Use glob to delete any pre-existing file for
    this image that does not match the one about to
    be downloaded

    """

    for entry in glob.glob(img_path):
        # identify img_id in entry...
        if(entry.count(img_id) == 0 ):
            lognotify("Warning: Pre-existing file %s that is no longer valid. Deleting...\n" % entry)
            try:
                os.remove(entry)
            except Exception, e:
                logerror("Error: %s occurred when trying to delete the file %s\n" % (e, entry))
        else:
            statinfo = os.stat(entry)
            if( statinfo.st_size < 1 ):
                lognotify("Warning: Pre-existing file %s has a file size of zero! Deleting...\n" % entry)
                try:
                    os.remove(entry)
                except Exception, e:
                    logerror("Error: %s occurred when trying to delete the file %s\n" % (e, entry))
    return


def download_flickr_img(img_path, photo, url_path):
    """Attempt to download the photo from
    Flickr to a local file system

    """


    logmsg('Test for %s' % img_path )

    if not os.path.exists(img_path):
        my_file = url_path % (photo.attrib['farm'],
                photo.attrib['server'], photo.attrib['id'], photo.attrib['secret'])

        logmsg('%s' % my_file )

        try:
            downloaded = urllib2.urlopen(my_file).read()
        except Exception,e:
            logmsg('%s while saving image for %s' % (e,my_file))
        else:
            save = open(img_path, 'wb')
            savestr = str(downloaded)
            save.write(savestr)
            save.close()
            logmsg('Saving photo: %s' % my_file )

    else:
        logmsg('Image %s already exists' % img_path )

    return


def flickr_photo_retrieval(flickr, sta, tags, myid, archive, url_path):
    """Grab the matching photo
    from Flickr

    """


    for i in range(len(tags)):
        try:
            search = flickr_tag_precedence(flickr, "-avoid, %s" % tags[i], sta, myid)

            # try with old tag style: _after
            if not len(search):
                search = flickr_tag_precedence(flickr, "-avoid, %s_after" % tags[i], sta, myid)

            #if len(search.find('photos').findall('photo')) < 1:
            if not len(search):
                logerror('No matching photos for %s %s.' % (sta, tags[i]) )
                continue

            if len(search.find('photos').findall('photo')) > 1:
                multiple = len(search.find('photos').findall('photo'))
                logerror('Multiple [%s] photos for %s %s.' % (multiple, sta, tags[i]) )

        except Exception,e :
            logmsg('%s => %s' % (Exception, e) )
            logerror('No photo for %s: %s.' % (sta, tags[i]) )
            continue


        # Grab all matching photos
        try:
            photo = search.find('photos').findall('photo')[-1]
        except:
            logerror('Problem in FIND() for photo for %s %s.' % (multiple, sta, tags[i]) )
            continue

        logmsg( 'Photo: %s' % photo.attrib['id'] )

        img = '%s/%s_%s_%s.jpg' % (archive, sta, tags[i], photo.attrib['id'])

        logmsg("Search for img: %s" % img)
        greedy_file_search = '%s/%s*_%s_*.jpg' % (archive, sta, tags[i])
        logmsg("Search for greedy_file_search: %s" % greedy_file_search)
        delete_local_flickr_img(greedy_file_search, photo.attrib['id'])

        download_flickr_img(img, photo, url_path)


    return


