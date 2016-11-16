'''
EOL images are produced on Matlab code called
by this script. Get the list of stations from
web API call and make a system call for each
valid site.
The code will try to keep a virtual desktop
environment for Matlab to use. The code should
kill this virtual environment at the end.

Juan Reyes
reyes@ucsd.edu

'''

import re
import json
import urllib
import socket
import pprint
import smtplib
import getpass
import subprocess
from optparse import OptionParser
from email.mime.text import MIMEText

# Global flags
verbose = False
globalLog = ''


'''
Functions to help process EOL reports
'''


try:
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

    global globalLog
    global verbose

    if not forced and not verbose: return

    if not isinstance(message, basestring):
        print type(message)
        message = '\n%s\n' % pprint.pformat(message, indent=4)

    #globalLog = '%s\n%s %s' % (globalLog,stock.strtime(stock.now()), message)
    globalLog += '%s %s\n' % (stock.strtime(stock.now()), message)
    print '%s %s' % (stock.strtime(stock.now()), message)

#def dump_log():
#    global globalLog
#    return globalLog

def parse_pf(pfname):
    """Parse parameter file

    """
    parsed_pf = {}

    try:
        pf = stock.pfread(pfname)
    except Exception,e:
        sys.exit('Cannot read %s => %s' % (pfname,e))

    parsed_pf['ev_database'] = pf.get('ev_database')
    parsed_pf['ev_clustername'] = pf.get('ev_clustername')
    parsed_pf['wf_database'] = pf.get('wf_database')
    parsed_pf['wf_clustername'] = pf.get('wf_clustername')
    parsed_pf['imagedir'] = pf.get('imagedir')
    parsed_pf['image_regex'] = pf.get('image_regex')
    parsed_pf['sendmail'] = pf.get('sendmail')
    parsed_pf['convert_exec'] = pf.get('convert_exec')
    #parsed_pf['archive'] = pf.get( 'archive' )
    parsed_pf['recipients'] = pf.get('recipients')
    parsed_pf['json_api'] = pf.get( 'json_api' )
    parsed_pf['xvfb'] = pf.get( 'xvfb' )
    parsed_pf['matlab'] = pf.get( 'matlab' )
    parsed_pf['matlab_flags'] = pf.get( 'matlab_flags' )
    parsed_pf['topomaps'] = pf.get( 'topomaps' )

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


def per_sta_query( net, sta, chans, lat, lon, time, endtime, code, params):
    '''
    Set virtual display if needed
    '''

    logmsg( "START Matlab script for %s_%s" % (net, sta))

    variables = ''
    variables += "ev_database='%s'; " % params['ev_database']
    variables += "ev_clustername='%s'; " % params['ev_clustername']
    variables += "wf_database='%s'; " % params['wf_database']
    variables += "wf_clustername='%s'; " % params['wf_clustername']
    variables += "img_dir='%s'; " % params['imagedir']
    variables += "topomaps='%s'; " % params['topomaps']
    variables += "convert_exec='%s'; " % params['convert_exec']
    variables += "chans=%s; " % chans
    variables += "net='%s'; " % net
    variables += "sta='%s'; " % sta
    variables += "time='%s'; " % time
    variables += "endtime='%s'; " % endtime
    variables += "lat=%s; " % lat
    variables += "lon=%s; " % lon

    cmd = "%s %s -r \"%s\" < %s/%s" % \
                        (params['matlab'], params['matlab_flags'],
                        variables, os.environ['ANF'] + "/data/matlab/eol_images/", code)

    logmsg( cmd )

    output = os.system( cmd )

def setup_display( xvfb_path=None ):
    '''
    Set virtual display if needed
    '''
    if xvfb_path:
        """
        Open virtual display. Running Xvfb from Python
        """

        pid = os.getpid()
        cmd = '%s :%s -fbdir /var/tmp -screen :%s 1600x1200x24' % (xvfb_path, pid, pid)

        lognotify( " - Start virtual display: %s" % cmd  )

        xvfb = subprocess.Popen( cmd, shell=True)

        if xvfb.returncode:
            stdout, stderr = xvfb.communicate()
            lognotify( " - xvfb: stdout: %s" % stdout  )
            lognotify( " - xvfb: stderr: %s" % stderr  )
            sys.exit('Problems on %s ' % cmd )

        os.environ["DISPLAY"] = ":%s" % pid

        lognotify( " - xvfb.pid: %s" % xvfb.pid  )
        lognotify( " - $DISPLAY => %s" % os.environ["DISPLAY"]  )
        return xvfb

    else:
        return None


def kill_display( xvfb ):

    if xvfb:
        lognotify( "xvfb.kill: %s" % xvfb.terminate() )

def main():

    global globalLog

    usage = 'Usage: %prog [options]'
    parser = OptionParser(usage=usage)
    parser.add_option('-a', action='store_true', dest='all',
                      help='process all', default=False)
    parser.add_option('-n', action='store', dest='snet',
                      help='network subset', default=False)
    parser.add_option('-d', action='store_true', dest='display',
                      help='local display', default=False)
    parser.add_option('-v', action='store_true', dest='verbose',
                      help='verbose output', default=False)
    parser.add_option('-s', action='store', dest='sta',
                      help='station subset', default=False)
    parser.add_option('-p', action='store', dest='pfname',
                      help='parameter file path', default='eol_images.pf' )
    (options, args) = parser.parse_args()

    global verbose
    verbose = options.verbose

    lognotify('EOL images started')

    params = parse_pf(options.pfname)

    if not options.display:
        xvfb = setup_display( params['xvfb'] )
    else:
        xvfb = None

    file_sta_list = json_stalist( params['json_api'],
                            snet=options.snet,
                            sta=options.sta,
                            all=options.all )

    logmsg('Email: %s' % ', '.join(params['recipients']))
    logmsg('Number of stations to process: %s' % len(file_sta_list))


    while len(file_sta_list) > 0:
        stainfo = file_sta_list.pop()
        net = stainfo['snet']
        sta = stainfo['sta']
        lat = stainfo['lat']
        lon = stainfo['lon']
        time = stainfo['time']
        endtime = stainfo['endtime']

        regex = params['image_regex']
        chan_regex = re.compile( regex )


        try:
            channels = stainfo['channels'].keys()
            channels = filter(chan_regex.match, channels)
            channels.sort()

            logmsg( channels )
            if len(channels) > 2:
                chans = "{'%s', '%s', '%s'}" % ( channels[0], channels[1], channels[2] )
            else:
                chans = "{'LHZ', 'LHE', 'LHN'}"

        except:
            chans = "{'LHZ', 'LHE', 'LHN'}"

        logmsg( 'Start Matlab on [%s] [%s]' % (net,sta) )

        per_sta_query( net, sta, chans, lat, lon, time, endtime, 'eol_reports.m', params  )


    lognotify( 'EOL images finished' )

    if xvfb:
        kill_display( xvfb )

    if params['recipients'] and params['recipients'][0]:
        logmsg('Sending email to %s' % ','.join(params['recipients']) )
        #msg = MIMEText( dump_log(), 'plain')
        msg = MIMEText( globalLog, 'plain')
        msg_from = '%s@%s' % (getpass.getuser(),socket.gethostname())
        msg['Subject'] = 'EOL image production output'
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
