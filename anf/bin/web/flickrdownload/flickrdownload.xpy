'''
Use multiprocessing and subprocess and Beej's
Python Flickr API to search & retrieve station photos
'''

import glob
import time
import json
import urllib2
import urllib
import smtplib
import getpass
import socket
import subprocess
import multiprocessing
import pprint
from optparse import OptionParser
from email.mime.text import MIMEText

# Global flags
verbose = False

try:
    import flickrapi
except Exception,e:
    print "%s: %s" % (Exception,e)
    sys.exit('Import Error: Do  you have the Python Flickr API module '\
            'installed correctly?')

try:
    from flickrdownloads.flickrfunctions import *
except Exception, e:
    print "%s: %s" % (Exception,e)
    sys.exit('Import Error: Do  you have ANF contrib installed correctly?')

try:
    import antelope.datascope as datascope
    import antelope.stock as stock
except Exception,e:
    print "%s: %s" % (Exception,e)
    sys.exit('Problems loading Antelope. %s' % e)


def main():
    '''Grab & parse station list
    then run subprocesses to
    grab photos from Flickr

    '''

    global verbose

    parser = OptionParser()
    parser.add_option('-a', action='store_true', dest='all',
                      help='get all', default=False)
    parser.add_option('-n', action='store', dest='snet',
                      help='network subset', default=False)
    parser.add_option('-v', action='store_true', dest='verbose',
                      help='verbose output', default=False)
    parser.add_option('-s', action='store', dest='sta',
                      help='station subset', default=False)
    parser.add_option('-p', action='store', dest='pf',
                      help='parameter file path', default='flickrdownload.pf')
    (options, args) = parser.parse_args()

    if os.path.isfile(options.pf):
        pfname = options.pf
    else:
        sys.exit('Command line defined parameter file [%s] does not exist' % options.pf)

    verbose = options.verbose

    try:
        params = parse_pf(pfname)
    except Exception, e:
        sys.exit('Cannot read %s => %s' % (pfname,e))

    # This will put the Flicker IDs in the email
    #logmsg( params )

    flickr = flickrapi.FlickrAPI(params['api_key'],
            params['api_secret'], token=params['token'])

    try:
        file_sta_list = json_stalist( params['json_api'],
                                     snet=options.snet,
                                     sta=options.sta,
                                     all=options.all )
    except Exception,e:
        logerror('Cannot get list of stations')
        sys.exit( "%s => %s" % (json_api, e) )


    lognotify('Flickr Python Photo Downloader started')
    logmsg('Email will be sent to: %s' % ', '.join(params['recipients']))
    logmsg('Number of stations to process: %s' % len(file_sta_list))


    while len(file_sta_list) > 0:
        stainfo = file_sta_list.pop()
        mysta = stainfo['id']

        logmsg('New Process: %s' % mysta)

        per_sta_query( flickr, mysta, params['all_tags'], params['myid'],
                    params['archive'], params['flickr_url_path'])


    logmsg('Flickr Photo Downloader finished')


    if params['recipients'] and params['recipients'][0]:
        logmsg('Sending email to %s' % ','.join(params['recipients']) )
        msg = MIMEText( dump_log(), 'plain')
        msg_from = '%s@%s' % (getpass.getuser(),socket.gethostname())
        msg['Subject'] = 'Flickr photo archive retrieval output'
        msg['From'] = msg_from
        msg['To'] = ','.join(params['recipients'])

        try:
            sm = smtplib.SMTP('localhost')
            sm.sendmail(msg_from, params['recipients'],  msg.as_string())
            sm.quit()
        except Exception, e:
            logerror( 'Cannot send email. %s' % e )


    return 0

if __name__ == '__main__':
    sys.exit( main() )
