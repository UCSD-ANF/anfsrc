"""
Create zipped tarballs of databases
"""

# import of os, site, and signal is done via the xpy template mechanism
import antelope.stock as stock

import shutil
import tarfile
import tempfile

from optparse import OptionParser

from subprocess import call

import logging

# Helper function to handle databases
from db2tarball.dbcentral import Dbcentral


def zipped_tarball(this_tmp_dir):
    """
    Generate and return the path to the new file
    """
    tgz_name = "%s.tar.gz" % this_tmp_dir

    tar = tarfile.open(tgz_name, "w:gz")

    tar.add(this_tmp_dir)

    tar.close()

    return tgz_name


def parse_pf_db(raw_text):
    """
    The parameter file will give us a long
    string that we need to cut into a 2-tuple
    or 3-tuple.
    Example:
    'ta-events     /anf/shared/dbcentral/dbcentral     usarray_rt'
    'ta-events     /anf/db/dbops'
    """

    obj = {}

    temp = raw_text.split()

    if len(temp) == 3:
        obj["name"] = temp[0]
        obj["db"] = temp[1]
        obj["nickname"] = temp[2]
    elif len(temp) == 2:
        obj["name"] = temp[0]
        obj["db"] = temp[1]
        obj["nickname"] = None

    return obj


logging.basicConfig()
logger = logging.getLogger("db2tarball")

#
# Configure script with command-line arguments
#
usage = "Usage: %prog [options]"
parser = OptionParser(usage=usage)
parser.add_option(
    "-d",
    "--debug",
    action="store_true",
    dest="debug",
    default=False,
    help="debug output",
)
parser.add_option(
    "-v",
    "--verbose",
    action="store_true",
    dest="verbose",
    default=False,
    help="verbose output",
)
parser.add_option(
    "-p",
    "--pf",
    action="store",
    type="string",
    dest="pf",
    default="db2tarball.pf",
    help="parameter file path",
)
(options, args) = parser.parse_args()


if options.verbose:
    logger.setLevel(logging.DEBUG)

logger.info(stock.strtime(stock.now()))

# Get PF file values
logger.debug("Read parameters from pf file %s" % options.pf)
pf = stock.pfread(options.pf)

archive = pf["archive"]
database_list = pf["database_list"]
tables = pf["tables"]


for k, v in database_list.iteritems():
    logger.debug("Init DB: From PF %s => %s" % (k, v))

    db = parse_pf_db(v)

    #
    # Open db using Dbcentral CLASS
    #
    logger.debug(
        "Init DB: Create Dbcentral object with database(%s, %s)."
        % (db["db"], db["nickname"])
    )
    dbcentral = Dbcentral(db["db"], db["nickname"], options.debug)

    if options.verbose:
        dbcentral.info()

    for tmpdb in dbcentral.list():

        # Make a name for my tar archive
        db_original_name = tmpdb.split("/")[-1]
        archive_name = "%s_%s" % (db["name"], db_original_name)
        logger.info("Archive: %s" % archive_name)

        # Wee need a clean temp directory to work with...
        workdir = tempfile.mkdtemp()
        logger.info("Temp directory: %s" % workdir)
        os.chdir(workdir)

        # Make folder structure
        os.mkdir(archive_name)
        os.chdir(archive_name)
        last_mtime = 0

        if len(tables) > 0:
            for t in tables:
                # Copy database to local folder
                logger.info(
                    "Make copy of %s.%s in %s/%s" % (tmpdb, t, workdir, archive_name)
                )
                call(["dbcp", "%s.%s" % (tmpdb, t), "./"])
                try:
                    shutil.copystat(
                        "%s.%s" % (tmpdb, t),
                        "%s/%s/%s.%s" % (workdir, archive_name, db_original_name, t),
                    )
                    mtime = os.path.getmtime("%s.%s" % (tmpdb, t))
                    logger.info("mtime of %s.%s => %s" % (tmpdb, t, mtime))
                    if mtime > last_mtime:
                        last_mtime = mtime

                except Exception as e:
                    logger.info("%s %s" % (Exception, e))
                    logger.info(
                        "Cannot set permissions of %s/%s/%s.%s"
                        % (workdir, archive_name, db_original_name, t)
                    )
        else:
            logger.info("Make copy of %s in %s/%s" % (tmpdb, workdir, archive_name))
            call(["dbcp", tmpdb, "./"])

        # Go back to work dir
        os.chdir(workdir)

        logger.info("Make zipped tarball of %s/%s" % (workdir, archive_name))
        tarball = zipped_tarball(archive_name)
        logger.info("Got new tarball: %s/%s" % (workdir, tarball))

        if not tarball:
            logger.erro(
                "Problems generating new tarball %s/%s" % (workdir, archive_name)
            )
            sys.exit(2)

        final_archive = "%s/%s.tar.gz" % (archive, archive_name)

        logger.info("Move tarball: %s => %s" % (tarball, final_archive))
        shutil.move(tarball, final_archive)

        if last_mtime:
            logger.info("Set time of %s to %s" % (final_archive, last_mtime))
            os.utime(final_archive, (-1, last_mtime))

        logger.info("Remove temp folder: %s" % workdir)
        shutil.rmtree(workdir)
