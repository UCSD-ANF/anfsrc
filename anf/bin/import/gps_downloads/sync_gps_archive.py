
# coding: utf-8

# # SYNC_GPS_ARCHIVE 

# ## Code to download data from Trimble GPS units and keep a local archive.
# 
# The code will download raw T00 files and there is no conversion for now.
#    
#     Info: 172.16.153.231 - previous SIO test 
#     Info: 139.78.120.60  - current okstate IP address
#     Info: 139.78.120.60  /ags/data/seismogps/2017.234_ok 2017-08-22
# 
# EXAMPLE:
# 
#         sync_gps_archive.py -v --maxfiles=2 139.78.120.60 ~/repos/temp
# 
# Juan Reyes reyes@ucsd.edu
# 11/21/2017

# In[1]:


import os, sys, time, re
import glob
from datetime import datetime,timedelta
import collections
import argparse
try:
    set
except NameError:
    from sets import Set as set

from ftplib import FTP

verboseFlag = False
debugFlag = False

'''
If we are running in Jupyter Notebook then fake command line arguments.
Run this if the module is running in IPython kernel,
'''
if  'ipykernel' in sys.modules:
    args = ['sync_gps_archive', '--agelimit=1weeks', '--maxfiles=6',
            '--maxattempts=2', '--datelimit=2017/11/18','--blocksize=2500',
            '139.78.120.60', '/notebooks/temp']
else:
    args = sys.argv


# In[2]:


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


# In[3]:


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

Tool to keep Trimble FTP archive in sync to a local repo. Defaults to
files ending in .T00 but you can change this in the flags. It will keep
the directory structure encounter at the remote site. Files will problems
will be appended with a string "_trash_" and a number. There is a default
of 6 attempts per file. After this, the file will be ignored. You can also
set the number of files to download on a single run or the maximum data
that can be downloaded on a  single attempt.

The list of files could be limited by a set date with a flag --datelimit
and no files older than that date will be downloaded. The format is
"2017/12/31".  There is  also a  time window limit if you only want to
download files within a rolling time window from realtime. This is done
with the flag --agelimit and the format is a number and a string from the
list  [days, weeks,  months,  years](with or  without the  s at the end)
without spaces. i.e. "2weeks" or "90days".

There is a flag to remove files from the remote archive after a successful
download to the local archive. This is verified by looking at the size of
the local file and the reported size from the FTP server. All file size
metrics are reported in bytes. The --maxbytes flag also uses bytes to limit
the total bandwidth used for each run.

'''

epilog = '''
PROCESS:
    The algorithm is the following:
        1. input ftp site

        2. creates daily directories for raw and rinex files in top_folder

        3. retrieves RINEX T00 trimble native format file

        4. deletes the intermediate trimble dat files

    Program should run automatically once a day using crontab
    
MISSING:
    Converts trimble data files to RINEX files (.17o)
    
    Run teqc to create a qc report (.17S)
    
    Run hatanaka compresses then unix compresses the rinex .17o files
    
EXAMPLE:
    sync_gps_archive -v --maxfiles=2 139.78.120.60 ~/repos/temp
    
HELP:
    sync_gps_archive -h


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
parser = argparse.ArgumentParser( prog='sync_gps_archive',
                    formatter_class=argparse.RawTextHelpFormatter,
                    description=description, epilog=epilog)

parser.add_argument('-V', '--version', action='version', version=version)

parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', default=False,
                    help='Run in verbose mode.(default: %(default)s)')

parser.add_argument('-d', '--debug', action='store_true', dest='debug', default=False,
                    help='Run FTP connection in debug mode.(default: %(default)s)')

parser.add_argument('--demo', action='store_true', dest='demo', default=False,
                    help='DEMO or NULL run. Just show corrections.(default: %(default)s)')

parser.add_argument('--delete', action='store_true', dest='delete', default=False,
                    help='Set if you want to clean out the remote directory.(default: %(default)s)')

parser.add_argument('--user', action='store', dest='user', default=None,
                    help='FTP username.(default: %(default)s)')

parser.add_argument('--password', action='store', dest='password', default=None,
                    help='FTP password.(default: %(default)s)')

parser.add_argument('--maxattempts', action='store', dest='maxAttempts', default=6, type=int,
                    help='Limit the amount of times to retry a single file.(default: %(default)s)')

parser.add_argument('--maxfiles', action='store', dest='maxFiles', default=None, type=int,
                    help='Limit the amount of files to downlaod.(default: %(default)s)')

parser.add_argument('--maxbytes', action='store', dest='maxBytes', default=None, type=int,
                    help='Limit the amount of bytes to downlaod.(default: %(default)s)')

parser.add_argument('--blocksize', action='store', dest='blocksize', default=8192, type=int,
                    help='Maximum chunk size to read on the low-level FTP socket.(default: %(default)s)')

parser.add_argument('--filter', action='store', dest='filter', default=r'.*T00$',
                    help='Filter for data files. Default to ".*T00$".(default: %(default)s)')

parser.add_argument('--agelimit', action='store', dest='agelimit', default=None,
                    help='Avoid older than a set timewindow. ie. "1month", "4weeks" or "60days".(default: %(default)s)')

parser.add_argument('--datelimit', action='store', dest='datelimit', default=None,
                    help='Only files after this date. ie. "2017/11/03". (default: %(default)s)')

# positional arguments
parser.add_argument('ftpServer', type=str, help='FTP server')

parser.add_argument('archive', type=str, help='Local archive')


'''
Parse command line arguments. Save values to variable "args".
'''
config = parser.parse_args( args[1:] )
args_dict = vars( config )


if not config.ftpServer or not config.archive:
    parser.print_help()
    exit(-1)
    
if (config.verbose):
    verboseFlag = config.verbose
    
if (config.debug):
    verboseFlag = config.debug
    debugFlag = config.debug


# In[4]:


'''
Nice print of command-line options 
'''
notify( (' ').join(args) )
for x in args_dict:
    log( '\t%s: %s' % (x.upper(), args_dict[x]) )
    

'''
Verify local archive
'''
if not os.path.exists( config.archive ):
    log( 'Making new directory: [%s]' % config.archive )
    
    try:
        os.makedirs( config.archive )
    except Exception,e:
        error('Cannot create archive folder [%s] %s:%s' %               ( config.archive, Exception,e))

try:
    os.stat( config.archive )
except Exception,e:
    error('Cannot create archive folder [%s] %s:%s' %           ( config.archive, Exception,e))
    
log( 'Working on archive: [%s]' % config.archive)


# In[5]:


def makePath( path, cache ):
    '''
    makePath:
    
    Traverse the dictionary structure and build full paths.
    Since each key is a portion of the path until the last
    key with a NULL value. That is the filename.
    '''
    
    pathList = []
    
    for k,v in cache.iteritems():
        
        if not v:
            pathList.append( '%s/%s' % (path,k) )
        else:
            pathList += makePath( '%s/%s' % (path,k), v )
            
    return pathList


# In[6]:


def subsetFiles( fileList ):
    '''
    subsetFiles:
    
    From all files found filter the ones that
    match the config.filter regex.
    
    '''
    log( 'Make full paths of each file' )
    
    log( 'Total files [%s]' % len(fileList) )

    if config.filter:
        log( 'Make regex filter for files [%s]' % config.filter )
        regex = re.compile( config.filter )

        fileList = filter(regex.search, fileList)
        log( 'Total files after subset[%s]' % len(fileList) )

    log( 'Final file list' )
    log( fileList ) 
    
    return fileList


# In[7]:


def traverse( ftp ):
    """
    traverse:
    
    return a recursive listing of an ftp server contents

    listing is returned as a recursive dictionary, where each key
    contains a contents of the subdirectory or None if it corresponds
    to a file.
    """
    level = {}
    dirList = []
    ftp.dir(dirList.append)
    
    for each in (path for path in dirList[1:] if path not in ('.', '..')):
        #log( 'traverse: [%s]' % each )
        name = each.strip().split(' ')[-1]
        #'drwxrwxrwx  11 5000     5000         4096 Nov 20 23:54 201711'
        
        try:
            ftp.cwd( name )
            level[name] = traverse( ftp )
            ftp.cwd( '..' )
        except:
            level[name] = None
    return level


# In[8]:


def traverseLocal( folder ):
    '''
    traverseLocal:
    
    return a recursive listing of a directory structure

    listing is returned as a recursive dictionary, where each key
    contains a contents of the subdirectory or None if it corresponds
    to a file.
    '''
    level = {}
    
    dirList = []
    
    #log( 'Traverse Local Folder: [%s]' % folder )
    
    #cwd = os.getcwd()
    #os.chdir( folder )
    
    #for each in (path for path in  os.listdir('.') if path not in ('.', '..')):
    for each in (path for path in  os.listdir( folder ) if path not in ('.', '..')):
        fullname = '%s/%s' % (folder, each)
        #log( 'traverse: [%s]' % fullname )
        
        if os.path.isfile( fullname ):
            level[each] = None
        else:
            level[each] = traverseLocal( fullname )

    #os.chdir( cwd )
    
    return level


# In[9]:


def fileDate( filename ):
    '''
    fileDate:
    
    Parse file name into file date object
        # EXAMPLE:    KERG201711172100a.T00
    '''
    
    try:
        m = re.search( r'^.*(\d{4})(\d{2})(\d{2})(\d{2})(\d{2}).*$', filename)
        #log( 'regex: %s/%s/%s %s:%s' % (m.group(1),m.group(2),m.group(3),m.group(4),m.group(5)) )
        testdate = datetime( int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5)) )
    except Exception, e:
        log( '%s: %s' % (Exception,e) )
        yr = int( filename[4:8] )
        mt = int( filename[8:10] )
        dy = int( filename[10:12] )
        hr = int( filename[12:14] )
        mn = int( filename[14:16] )
        #log( 'simple: %s/%s/%s %s:%s' % (yr,mt,dy,hr,mn) )
        testdate = datetime( yr, mt, dy, hr, mn )
        
    if testdate < datetime(2000, 1, 1) or datetime(2100, 1, 1)< testdate:
        notify( '%s' % filename )
        error( 'Date is not valid in filename!!!' )
        
    log( '\tNew time: %s' % testdate )
    
    return testdate


# In[10]:


def dateLimit( conf ):
    '''
    dateLimit:
    
    Calculate date limit of files that we want to
    download. Based on command-line flags.
        - age limit: No more than X weeks or Y months
        - date limit: Not older than day X
    '''
    
    now = datetime.now()
    
    limit = datetime( 2000, 1, 1 )
    
    # maybe we have a timewindow
    if conf.agelimit:
        
        log( 'Parse age limit of files [%s]' % conf.agelimit )
        try:
            m = re.search( r'^(\d+)(\w+)$', conf.agelimit)
            digit = int( m.group(1) )
            string = m.group(2)
            log( 'Limit to %s %s' % (digit, string) )
            
            if re.match( r'month.?', string ):
                m, y = (now.month+digit) % 12, now.year + ((now.month)+digit-1) // 12
                if not m: m = 12
                d = min(now.day, [31,
                    29 if y%4==0 and not y%400==0 else 28,31,30,31,30,31,31,30,31,30,31][m-1])
                limit = now.replace(day=d,month=m, year=y)
            elif re.match( r'week.?', string ):
                limit = now - timedelta( weeks=digit )
            elif re.match( r'day.?', string ):
                limit = now - timedelta( days=digit )
            else:
                error( 'Cannot parse age limit string: [%s]' % string)
                
        except Exception,e:
            error( 'Problem parsing age limit %s %s' % (Exception, e) )
            
            
    # maybe we have a date limit
    if conf.datelimit:
        
        log( 'Parse date limit of files [%s]' % conf.datelimit )
        dateparts = conf.datelimit.split('/')
        
        try:
            log( 'date limit: %s/%s/%s' % (dateparts[0],dateparts[1],dateparts[2]) )
            limit = datetime( int(dateparts[0]), int(dateparts[1]), int(dateparts[2]) )
        except Exception,e:
            error( 'Problem parsing date limit %s %s' % (Exception, e) )
            
    if limit > datetime( 2000, 1, 1 ):
        log( 'Limit on age of files found to be: %s' % limit )
    else:
        log( 'No limit on age of files')
        
    return limit
            


# In[11]:


def trashFile( filename ):
    '''
    trashFile:
    
    Move file to trash mode.
    In case of partial download then move to the side and
    append _trash_# for each extra version.
    '''
    notify( 'Move file to trash structure: %s' % filename )
    
    otherFiles = glob.glob( filename + '*' )
    
    if len(otherFiles):
        notify( 'Found %s other files for it.' % len(otherFiles) )
        for each in otherFiles:
            notify( '\t%s %s bytes' % (each,os.path.getsize(each)) )
    else:
        notify( 'No other trahs files for it.' )
        
    newName = filename + '_trash_' + str(len(otherFiles))
    try:
        os.rename( filename, newName )
    except Exception,e:
        error( 'Cannot move %s to %s trash structure: %s %s' % (filename, newName, Exception,e) )


# In[12]:


def downloadFTP( ftp, remoteFile, localFile, delete=False, blocksize=8192 ):
    '''
    downloadFTP:
    
    Download file from FTP server.
        - Verify if we have directory ready
        - Download the file
        - Verify final size of local file
        - Move to "trash" mode if different size
        - Remove remote if needed
    '''
    
    (localDir, localName)= os.path.split(localFile)
    success = False
    totalFiles = 0
    totalDeleted = 0
    
    # Verify local archive
    log( '\tOpen pointer to local file: %s' % localFile )
    try:
        if not os.path.isdir( localDir ):
            os.makedirs( localDir )
        fileObj = open(localFile, 'wb')
    except Exception,e:
        error( '\tProblem creating new file: %s %s' % (Exception,e))
        
    # Download the file a chunk at a time using RETR
    ftp.retrbinary('RETR ' + remoteFile, fileObj.write, blocksize)
    
    # Close the file
    fileObj.close()
    
    fileSize = ftp.size( remoteFile )
    log( '\tFile size: %s bytes' % fileSize )
    
    localFileSize = os.path.getsize(localFile)
    log( '\tLocal File: %s bytes' % localFileSize )
    
    if localFileSize == fileSize:
        log( '\tSuccess in download of file.')
        notify( 'Downloaded: %s' % localName )
        success = True
        totalFiles += 1
    else:
        notify( 'ERROR in download. Remove local file.')
        notify( 'remote:[%s bytes] local:[%s bytes]' % (fileSize, localFileSize) )
        try:
            trashFile( localFile )
        except Exception,e:
            error( '\tCannot remove partial local file: %s [%s:%s]' %                   (localFile, Exception, e) )

    if delete:
        notify( 'Delete remote file:%s' % remoteFile )
        ftp.delete( remoteFile )
        totalDeleted += 1
            
            
    return {
        'success': success,
        'size':localFileSize,
        'localDir':localDir,
        'localName':localName,
        'totalFiles':totalFiles,
        'totalDeleted':totalDeleted,
        'downloaded':fileSize
    }


# In[13]:


def syncFTP( conf ):
    '''
    syncFTP: Coordinate the download of the files:
    
    - Read the remote folder
    - Read the local folder
    - Compile list of missing files
    - Connect to an FTP server and bring down files to the local directory
    
    '''
    
    try:
        notify( 'Connect to %s' % conf.ftpServer )
        ftpSite = FTP( conf.ftpServer )
        
        #if conf.verbose:
        #    ftpSite.set_debuglevel( 1 )
            
        if conf.debug:
            ftpSite.set_debuglevel( 2 )
            
    except:
        error( 'Cannot find server %s' % conf.ftpServer )
        
    notify( 'Connecting...' )
    if conf.user and conf.password:
        log( 'login( %s, %s )' % (conf.user,conf.password) )
        ftpSite.login(conf.user,conf.password)
    else:
        ftpSite.login()
        
    ftpSite.cwd( '/' )
    
    
    notify( 'Read remote folder structure...' )
    
    try:
        remoteFiles = subsetFiles( makePath( '', traverse( ftpSite ) ) )
    except:
        error( 'Remote directory listing ERROR - ' )
    
    localFiles = subsetFiles( makePath( '', traverseLocal( conf.archive ) ) )
    
    transferList = list(set(remoteFiles) - set(localFiles))
    notify( 'Missing %s files' % len(transferList) )
    
    try:
        filesMoved = 0
        totalBytes = 0
        totalFiles = []
        totalMissed = []
        dateFileLimit = dateLimit( conf ) 
        
        for fl in sorted(transferList, reverse=False):
            
            fileDateObject = fileDate( fl )
            log( 'File: %s Date: %s' % (fl, fileDateObject) )
            
            if fileDateObject < dateFileLimit:
                log( '\tFile too old. Skip.')
                continue
                
            localFile =  os.path.abspath('%s/%s' % (conf.archive, fl) )
            
            if conf.maxAttempts:
                otherFiles = glob.glob( localFile + '*' )
                
                if len(otherFiles) >= 1:
                    log( '\tAlready have %s attempts to this file' % len(otherFiles) )
                    for each in otherFiles:
                        modified = datetime.fromtimestamp(os.path.getmtime(each))
                        log( '\t%s %s bytes on %s' % (each,os.path.getsize(each),modified) )
                
                if len(otherFiles) >= conf.maxAttempts:
                    notify( '\tSkip. Max attempts on: %s' % len(otherFiles) )
                    log( '\t%s' % (otherFiles) )
                    continue
            
            log( '\tStart work on: %s' % fl )
            
            if conf.demo:
                log( '\tDEMO RUN. Skip' )
                continue
              
            
            results = downloadFTP( ftpSite, fl, localFile,
                                  delete=conf.delete,
                                  blocksize=conf.blocksize )
            #{
            #    'success': success,
            #    'size':localFileSize,
            #    'localDir':localDir,
            #    'localName':localName,
            #    'totalFiles':totalFiles,
            #    'totalDeleted':totalDeleted,
            #    'downloaded':fileSize
            #}
            
            if results['success']:
                totalFiles.append( results['localName'] )
                filesMoved += results['totalFiles']
            else:
                totalMissed.append( results['localName'] )
                
            totalBytes += results['downloaded']
            
            if conf.maxFiles:
                log( '\t%s/%s max files allowed' % (filesMoved,conf.maxFiles) )
                if filesMoved >= conf.maxFiles:
                    notify( '\tGot to limit on total files: %s' % conf.maxFiles )
                    break
                    
            if conf.maxBytes:
                log( '\t%s/%s max bytes allowed' % (totalBytes,conf.maxBytes) )
                if totalBytes >= conf.maxBytes:
                    notify( '\tGot to limit on total bytes: %s' % conf.maxBytes )
                    break
            
        notify( 'Downloaded %s Files with %s bytes' %  (filesMoved, totalBytes) )
        for each in totalFiles:
            log( 'Downloaded: %s' % each )
        
        if len( totalMissed ):
            notify( 'Error on %s files' %  totalMissed )
            notify(  totalMissed )
        else:
            notify( 'No errors on any download.' )
        
    except Exception, e:
        error( 'Download Error %s: %s' % ( Exception, e) )
        
    ftpSite.close() # Close FTP connection
    ftpSite = None
    
    return len(totalMissed)


# In[14]:


'''
Start download of the data files
'''
log( 'Retreiving Files' )

if 'ipykernel' in sys.modules:
    # Run this if inside Jupyter Notebook
    syncFTP(config)
else:
    sys.exit( syncFTP(config) )


# In[15]:


#   # make files writeable by owner and group
#   # chmod ug+w *
#   echo 'converting .T00 files to .dat files'
#   foreach f ($daily_raw/*.T00)
#      runpkr00 -d $f
#   end
#   echo 'Converted .T00 files to .DAT files'
#   
#   
#   # Making rinex files using teqc
#   cd $daily_rinex
#   foreach datfile ( $daily_raw/*.dat )
#     set fname = `basename -s .dat $datfile`
#     teqc ++err translate_${doy}.err -tr d $datfile > $fname.${yr}o 
#   end
#   
#   # qc data
#   # get all 4 char site names from the list of files 
#   ls *.${yr}o | awk '{print substr($1,1,4)}' | sort | uniq > tmp_sitelist.txt
#   foreach site (`cat tmp_sitelist.txt`)
#     echo 'GPS DATA QC in progress'
#     # teqc +qc *.${yr}o > $qcname.${yr}S
#     teqc +qc $site*.${yr}o  > /dev/null
#   end
#   echo $daily_qc
#   mv *.${yr}S $daily_qc
#   mv translate_${doy}.err $daily_qc
#   
#   foreach rinex_file ( *.${yr}o )
#     rnx2crx $rinex_file
#     rm $rinex_file
#   end
#   compress *.${yr}d
#   
#   # Clean up 
#   rm tmp_sitelist.txt
#   cd $daily_raw
#   rm *.dat
#   compress *.T00
#   
#   cd $current_dir
#   
#   echo "get_gpsdata complete for $year $doy = $year-$month-$day"
#   # when using cron, may have to change the doy variable....depends on when cron job takes
#   # place.
#   # still need to find out about t02 to rinex....
#   #  annnnnnd break...

