
# coding: utf-8

# # GPS_ARCHIVE_DAEMON

# ## Wrapper for SYNC_GPS_ARCHIVE
# 
# Simple code to keep track of the sites and run the command
# to download the files. Wait until we see the ping response.
# Try to get the IP from the ANF API calls. 
# 
# 
# Juan Reyes reyes@ucsd.edu
# 11/21/2017

# In[95]:


import os, sys
import re
import time
import json
import urllib
import argparse
import subprocess
from datetime import datetime,timedelta

verboseFlag = False

'''
If we are running in Jupyter Notebook then fake command line arguments.
Run this if the module is running in IPython kernel,
'''
if  'ipykernel' in sys.modules:
    args = ['gps_archive_daemon','-v', 'P29M', 'P30M', '109C']
else:
    args = sys.argv


# In[96]:


'''
Set some generic print functions
'''
def notify( msg ):
    print '%s: %s' % (datetime.now().strftime('%D %H:%M:%S.%f'), msg) 
    
def log( msg ):
    if verboseFlag:
        notify( msg )
        
def debug( msg ):
    if debugFlag:
        notify( msg )
        
def error( msg ):
    print '%s: ERROR' % datetime.now().strftime('%D %H:%M:%S.%f')
    notify( msg )
    print '%s: EXIT' % datetime.now().strftime('%D %H:%M:%S.%f')
    if __name__ == '__main__':
        sys.exit()
    else:
        raise Exception( msg )


# In[147]:


'''
Parse command line arguments. Save values to variable "args".

Configure HELP strings for script.
You can make a manpage with this command:
    help2man -o sync_gps_archive.1  --no-discard-stderr  sync_gps_archive
    
First run of "make install" will get all files into the system. Then we can
run help2man to output the manpage.1 file. This will require a second
pass of the "make install". 

'''

description = '''

Simple wrapper around sync_gps_archive. This will run in a rtexec
and will track the state of the connection. Once the station is
responding to pings we call the command to sync the archive. Wait
some hours (24?) before a new attempt. Get the IP of the site from
the ANF API tools.

'''

epilog = '''
PROCESS:
    The algorithm is the following:
        1. Get the IP of the sites

        2. Look for positive PING response

        3. Go to sleep and retry if failure. Run sysnc_gps_archive if success.

    Program should run from rtexec.
    
MISSING:
    TBD
    
EXAMPLE:
    gps_archive_daemon
    
HELP:
    gps_archive_daemon -h


Report bugs to Juan Reyes <reyes@ucsd.edu>.
'''

version = '''
%(prog)s 1.0

Copyright (c) 2017, The Regents of the University of California
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:
 1. Redistributions of source code must retain the above copyright notice, this
    list of conditions and the following disclaimer.
 2. Redistributions in binary form must reproduce the above copyright notice,
    this list of conditions and the following disclaimer in the documentation and/or
    other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


Written by Juan Reyes <reyes@ucsd.edu>
'''
parser = argparse.ArgumentParser( prog='gps_archive_daemon',
                    formatter_class=argparse.RawTextHelpFormatter,
                    description=description, epilog=epilog)

parser.add_argument('-V', '--version', action='version', version=version)

parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', default=False,
                    help='Run in verbose mode.(default: %(default)s)')

parser.add_argument('-a', '--archive', action='store', dest='archive',
                    default='db/gps_data/okstate-gps-receiver/',
                    help='Use this folder for local archive. (default: %(default)s)')

parser.add_argument('--hours', action='store', dest='hours', default=8,
                    help='Download files every X hours. (default: %(default)s)')

parser.add_argument('stations', nargs='+', help='List of stations with FTP servers')


'''
Parse command line arguments. Save values to variable "args".
'''
config = parser.parse_args( args[1:] )
args_dict = vars( config )


if (config.verbose):
    verboseFlag = config.verbose


# In[148]:


'''
Nice print of command-line options 
'''
notify( (' ').join(args) )
for x in args_dict:
    log( '\t%s: %s' % (x.upper(), args_dict[x]) )


# In[100]:


def get_ip( sta ):
    '''
    get_ip:
    
    Get the last ip of the station from the 
    ANF API calls.
    '''
    
    log( 'GET IP FOR: %s' % sta )
    url = 'http://anf.ucsd.edu/api/ta/stations/?fields=orbcomms&snet=TA&sta=%s' % sta
    log( url )
    
    try:
        response = urllib.urlopen(url)
        data = json.loads(response.read())[0]
        print data
    except Exception,e:
        notify('Problems with ANF API:')
        notify( url )
        error( '%s: %s' % (Exception,e) )
        
    # Example
    #id : TA_109C
    #orbcomms : 
    #    inp : udp:172.23.47.21:5332:L1:startacq:0:0
    #    id : 5906286
    #    name : tadataStrays/pf/st
    #    time : 1518212588.2788
    
    #inp = data['orbcomms']['inp']
    inp = 'udp:172.23.47.21:5332:L1:listen:0:0'
    m = re.match(r"udp:(\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}):(\d{4}):.*", inp)
    
    if m:
        log('ip:   %s' % m.group(1) )
        log('port: %s' % m.group(2) )

        return m.group(1),m.group(2)
    else:
        notify('Cannot get IP from API for %s.' % sta )
        notify( url )
        notify( data )
        return False, False


# In[101]:


#ip,port = get_ip( 'P29M' )
#print ip
#print port


# In[143]:


def ping_station( ip ):
    '''
    ping_station:
    
    send ping to veirfy if station is online.
    
    '''
    log( 'ping: %s' % ip )
    
    child = subprocess.Popen(['ping', '-c3', ip], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    streamdata = child.communicate()
    log( streamdata )
    log( 'streamdata: ' + streamdata[0] )
    status = child.returncode
    log( 'returncode: ' + str( status ) )
    
    if status == 0:
        notify(str(ip) + " is UP !")
        alive = True
    else:
        log(str(ip) + " is DOWN !")
        alive = False
    
    return alive


# In[146]:


#ip, port = get_ip( 'P29M' )
#ping_station( ip )


# In[143]:


def get_data( sta, ip, archive ):
    '''
    get_data:
    
    Run command to download data.
    
    '''
    log( 'get_data: %s[%s]' % (sta,ip) )
    
    child = subprocess.Popen(['sync_gps_archive', ip, archive], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    streamdata = child.communicate()
    log( streamdata )
    log( 'streamdata: ' + streamdata[0] )
    status = child.returncode
    log( 'returncode: ' + str( status ) )
    
    if status == 0:
        log( "Success on %s" % sta )
    else:
        log( "Problems with %s[%s]" % (sta,ip) )
    
    return status


# In[150]:


'''
Start main loop
'''
notify( 'Start daemon' )

status = {}

while True:
    try:
        for sta in config.stations:
            log( 'Now work on %s' % sta )

            # Verify if we have a working local folder
            directory = '%s/%s/' % (config.archive,sta)
            log( 'Working on directory: %s' % directory )
            if not os.path.exists(directory):
                notify( 'Directory missing. Create new: %s' % directory )
                os.makedirs(directory)

            if not sta in status or                 datetime.now() - status[ sta ] > timedelta(hours=options.hours):

                ip, port = get_ip( sta )
                log( '%s:%s' % (sta,ip) )

                if ip:
                    if ping_station( ip ):
                        if get_data( sta, ip, directory ):
                            # Track last success
                            status[ sta ] = datetime.now()

        log( 'Wait for next loop')
        time.sleep(5)
        
    except KeyboardInterrupt:
        print('\n\nKeyboard interrupt. Exiting.')
        sys.exit(1)

