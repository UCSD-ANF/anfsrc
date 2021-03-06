"""
Functions to help download images from Flickr into
ANF's local archive
"""

from datetime import time
import glob
import json
import os
import pprint
import urllib
import urllib2

import antelope.stock as stock
from six import string_types

globalLog = ""

PF_REQUIRED_KEYS = [
    "api_key",
    "api_secret",
    "token",
    "myid",
    "all_tags",
    "flickr_url_path",
    "sendmail",
    "recipients",
    "json_api",
    "archive",
]


def lognotify(message):
    logmsg(message, forced=True)


def logerror(message):
    if not isinstance(message, string_types):
        message = pprint.pformat(message, indent=4)

    logmsg("*** %s ***" % message, forced=True)


def logmsg(message, forced=False):

    if message is None:
        message = ""

    from __main__ import verbose

    global globalLog

    if not forced and not verbose:
        return

    if not isinstance(message, string_types):
        message = "\n%s\n" % pprint.pformat(message, indent=4)

    globalLog += "%s %s\n" % (stock.strtime(stock.now()), message)
    print("%s %s" % (stock.strtime(stock.now()), message))


def dump_log():
    global globalLog
    return globalLog


def parse_pf(pfname, pf_keys=PF_REQUIRED_KEYS):
    """Parse parameter file, looking for explicit keys"""

    parsed_pf = {}

    pf = stock.pfread(pfname)

    for key in pf_keys:
        parsed_pf[key] = pf.get(key)

    return parsed_pf


def json_stalist(json_api, snet=False, sta=False, all=False):
    """
    Get a list of stations from the web API

    snet is a subset of SNET values
    sta is a subset of STA values
    all is a flag to add decommissioned sites

    """

    if snet:
        json_api = "%s&snet=%s" % (json_api, snet)
    if sta:
        json_api = "%s&sta=%s" % (json_api, sta)
    if all:
        json_api = "%s&all=true" % json_api

    logmsg(json_api)

    response = urllib.urlopen(json_api)
    data = json.loads(response.read())

    lognotify("Got [%s] stations" % len(data))

    logmsg(data)

    return data


def per_sta_query(flickr, staname, tags, myid, archive, url_path):
    """Create a subprocess
    for the selected station

    """

    logmsg("Start %s at %s" % (staname, stock.strtime(stock.now())))

    try:
        flickr_photo_retrieval(flickr, staname, tags, myid, archive, url_path)
    except Exception as e:
        logerror("%s execution failed: %s" % (staname, e))


def flickr_tag_precedence(flickr, tag, sta, myid):
    """Search photos tagged in Flickr
    and return in order of precedence

    """

    logmsg("Start flickr_tag_precedence [%s] [%s]" % (sta, tag))

    # Search name with underline
    tags = "%s, %s" % (tag, sta)
    logmsg("Search for %s [%s]." % (sta, tags))

    try:
        search = flickr.photos_search(
            user_id=myid, tags=tags, tag_mode="all", per_page="10"
        )
        if len(search.find("photos").findall("photo")) < 1:
            logmsg("No matching photos for %s %s." % (sta, tags))
        else:
            return search

    except Exception as e:
        logerror("Exception: %s: %s" % (tags, e))
        time.sleep(1)

    # Search name with period
    tags = "%s, %s" % (tag, sta.replace("_", "."))
    logmsg("Search for %s [%s]." % (sta, tags))

    try:
        search = flickr.photos_search(
            user_id=myid, tags=tags, tag_mode="all", per_page="10"
        )
        if len(search.find("photos").findall("photo")) < 1:
            logmsg("No matching photos for %s %s." % (sta, tags))
        else:
            return search

    except Exception as e:
        logerror("Exception: %s: %s" % (tags, e))
        time.sleep(1)

    # Search split name
    try:
        tags = tag
        splitname = sta.split("_")
        if len(splitname) > 1:

            for s in splitname:
                tags += ", %s" % s

            logmsg("Search for %s [%s]." % (sta, tags))

            search = flickr.photos_search(
                user_id=myid, tags=tags, tag_mode="all", per_page="10"
            )

            if len(search.find("photos").findall("photo")) < 1:
                logmsg("No matching photos for %s %s." % (sta, tags))
            else:
                return search

    except Exception as e:
        logerror("Exception: %s: %s" % (tags, e))
        time.sleep(1)

    return []


def delete_local_flickr_img(img_path, img_id):
    """Use glob to delete any pre-existing file for
    this image that does not match the one about to
    be downloaded

    """

    for entry in glob.glob(img_path):
        # identify img_id in entry...
        if entry.count(img_id) == 0:
            lognotify(
                "Warning: Pre-existing file %s that is no longer valid. Deleting...\n"
                % entry
            )
            try:
                os.remove(entry)
            except Exception as e:
                logerror(
                    "Error: %s occurred when trying to delete the file %s\n"
                    % (e, entry)
                )
        else:
            statinfo = os.stat(entry)
            if statinfo.st_size < 1:
                lognotify(
                    "Warning: Pre-existing file %s has a file size of zero! Deleting...\n"
                    % entry
                )
                try:
                    os.remove(entry)
                except Exception as e:
                    logerror(
                        "Error: %s occurred when trying to delete the file %s\n"
                        % (e, entry)
                    )
    return


def download_flickr_img(img_path, photo, url_path):
    """Attempt to download the photo from
    Flickr to a local file system

    """

    logmsg("Test for %s" % img_path)

    if not os.path.exists(img_path):
        my_file = url_path % (
            photo.attrib["farm"],
            photo.attrib["server"],
            photo.attrib["id"],
            photo.attrib["secret"],
        )

        logmsg("%s" % my_file)

        try:
            downloaded = urllib2.urlopen(my_file).read()
        except Exception as e:
            logmsg("%s while saving image for %s" % (e, my_file))
        else:
            save = open(img_path, "wb")
            savestr = str(downloaded)
            save.write(savestr)
            save.close()
            logmsg("Saving photo: %s" % my_file)

    else:
        logmsg("Image %s already exists" % img_path)

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
                search = flickr_tag_precedence(
                    flickr, "-avoid, %s_after" % tags[i], sta, myid
                )

            # if len(search.find('photos').findall('photo')) < 1:
            if not len(search):
                logerror("No matching photos for %s %s." % (sta, tags[i]))
                continue

            if len(search.find("photos").findall("photo")) > 1:
                multiple = len(search.find("photos").findall("photo"))
                logerror("Multiple [%s] photos for %s %s." % (multiple, sta, tags[i]))

        except Exception as e:
            logmsg("%s => %s" % (Exception, e))
            logerror("No photo for %s: %s." % (sta, tags[i]))
            continue

        # Grab all matching photos
        try:
            photo = search.find("photos").findall("photo")[-1]
        except:
            logerror(
                "Problem in FIND() for photo for %s %s." % (multiple, sta, tags[i])
            )
            continue

        logmsg("Photo: %s" % photo.attrib["id"])

        img = "%s/%s_%s_%s.jpg" % (archive, sta, tags[i], photo.attrib["id"])

        logmsg("Search for img: %s" % img)
        greedy_file_search = "%s/%s*_%s_*.jpg" % (archive, sta, tags[i])
        logmsg("Search for greedy_file_search: %s" % greedy_file_search)
        delete_local_flickr_img(greedy_file_search, photo.attrib["id"])

        download_flickr_img(img, photo, url_path)

    return
