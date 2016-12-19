"""
Create zipped tarballs of databases
"""

import sys
import os
import string
import tarfile
import gzip
import filecmp
import subprocess
import shutil
import json
import tempfile
import shutil

from optparse import OptionParser
from time import time
from datetime import date, timedelta, datetime

from subprocess import call

from pprint import pprint
import logging

# Helper function to handle databases
from db2tarball.dbcentral import Dbcentral
from db2tarball.db2tarball_funcs import *

try:
    import antelope.datascope as datascope
    import antelope.stock as stock
except Exception, e:
    sys.exit("\n\tProblems loading ANTELOPE libraries. %s(%s)\n" % (Exception, e))


logging.basicConfig()
logger=logging.getLogger('db2tarball')

#
# Configure script with command-line arguments
#
usage = "Usage: %prog [options]"
parser = OptionParser(usage=usage)
parser.add_option("-d", "--debug", action="store_true", dest="debug",
                    default=False, help="debug output")
parser.add_option("-v", "--verbose", action="store_true", dest="verbose",
                    default=False, help="verbose output")
parser.add_option("-p", "--pf", action="store", type="string", dest="pf",
                    default='db2tarball.pf', help="parameter file path")
(options, args) = parser.parse_args()


if options.verbose:
    logger.setLevel(logging.DEBUG)

logger.info( stock.strtime(stock.now()) )

# Get PF file values
logger.debug('Read parameters from pf file %s' % options.pf)
pf = stock.pfread( options.pf )

archive = pf['archive']
database_list = pf['database_list']
tables = pf['tables']


for k,v in database_list.iteritems():
    logger.debug( 'Init DB: From PF %s => %s' % (k,v) )

    db = parse_pf_db( v )

    #
    # Open db using Dbcentral CLASS
    #
    logger.debug( "Init DB: Create Dbcentral object with database(%s, %s)." % (db['db'],db['nickname']) )
    dbcentral = Dbcentral( db['db'], db['nickname'], options.debug )

    if options.verbose: dbcentral.info()

    for tmpdb in dbcentral.list():

        # Make a name for my tar archive
        db_original_name =  tmpdb.split('/')[-1]
        archive_name =  "%s_%s" % ( db['name'], db_original_name )
        logger.info( 'Archive: %s' % archive_name )

        # Wee need a clean temp directory to work with...
        workdir = tempfile.mkdtemp()
        logger.info( 'Temp directory: %s' % workdir )
        os.chdir( workdir )

        # Make folder structure
        os.mkdir( archive_name )
        os.chdir( archive_name )
        last_mtime = 0

        if len(tables) > 0:
            for t in tables:
                # Copy database to local folder
                logger.info('Make copy of %s.%s in %s/%s' % ( tmpdb, t, workdir, archive_name) )
                call(['dbcp', "%s.%s" % (tmpdb,t), './'])
		try:
                    shutil.copystat( "%s.%s" % (tmpdb, t), "%s/%s/%s.%s" % (workdir, archive_name, db_original_name, t) )
                    mtime = os.path.getmtime( "%s.%s" % (tmpdb, t) )
                    logger.info( 'mtime of %s.%s => %s' % (tmpdb, t, mtime) )
                    if mtime > last_mtime:
                        last_mtime = mtime

                except Exception, e:
                    logger.info( "%s %s" % (Exception, e) ) 
                    logger.info( "Cannot set permissions of %s/%s/%s.%s" % (workdir, archive_name,db_original_name,  t) ) 
        else:
            logger.info('Make copy of %s in %s/%s' % ( tmpdb, workdir, archive_name) )
            call(['dbcp', tmpdb, './'])

        # Go back to work dir
        os.chdir( workdir )

        logger.info('Make zipped tarball of %s/%s' % ( workdir, archive_name) )
        tarball = zipped_tarball( archive_name )
        logger.info('Got new tarball: %s/%s' % (workdir,tarball) )

        if not tarball:
            logger.erro( 'Problems generating new tarball %s/%s' % (workdir,archive_name) )
            sys.exit(2)

        logger.info('Compare: %s <=> %s/%s.tar.gz' % (tarball, archive, archive_name) )
        if not filecmp.cmp(tarball, "%s/%s.tar.gz" % (archive, archive_name)):
            logger.info('Move tarball: %s => %s/%s.tar.gz' % (tarball, archive, archive_name) )
            shutil.move( tarball, "%s/%s.tar.gz" % (archive, archive_name)  )
            if last_mtime:
                logger.info( 'Set time of %s/%s.tar.gz to %s' % (archive,archive_name, last_mtime) )
                os.utime ("%s/%s.tar.gz" % (archive,archive_name), (-1, last_mtime))

        else:
            logger.info( 'No changes to archive %s/%s' % (workdir,archive_name) )

        logger.info('Remove temp folder: %s' % workdir )
        shutil.rmtree( workdir )
