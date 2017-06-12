#
# Some generic Python function
# to make PF file operations easy
# to implement and speed up the
# development process.
#
# Juan Reye
# reyes@ucsd.edu
#

if __name__ == "__main__":
    raise ImportError( "\n\n\tANF Python library. Not to run directly!!!! \n" )

import sys
import logging_helper
import inspect

try:
    import antelope.stock as stock
except Exception,e:
    raise ImportError("[%s] Do you have Antelope installed?" % e)

def open_verify_pf(pf,mttime=False):
    '''
    Open the PF file and return a ParameterFile object

    Verify that we can get the file and check
    the value of PF_MTTIME if needed.
    '''

    from logging_helper import getLogger
    logging = getLogger( inspect.stack()[0][3] )

    logging.debug( 'Look for parameter file: %s' % pf )

    if mttime:
        logging.debug( 'Verify that %s is newer than %s' % (pf,mttime) )

        PF_STATUS = stock.pfrequire(pf, mttime)
        if PF_STATUS == stock.PF_MTIME_NOT_FOUND:
            logging.warning( 'Problems looking for %s. PF_MTTIME_NOT_FOUND.' % pf )
            logging.error( 'No MTTIME in PF file. Need a new version of the %s file!!!' % pf )
        elif PF_STATUS == stock.PF_MTIME_OLD:
            logging.warning( 'Problems looking for %s. PF_MTTIME_OLD.' % pf )
            logging.error( 'Need a new version of the %s file!!!' % pf )
        elif PF_STATUS == stock.PF_SYNTAX_ERROR:
            logging.warning( 'Problems looking for %s. PF_SYNTAX_ERROR.' % pf )
            logging.error( 'Need a working version of the %s file!!!' % pf )
        elif PF_STATUS == stock.PF_NOT_FOUND:
            logging.warning( 'Problems looking for %s. PF_NOT_FOUND.' % pf )
            logging.error( 'No file  %s found!!!' % pf )

        logging.debug( '%s => PF_MTIME_OK' % pf )

    logging.info( 'Found parameter file: %s' % pf )

    try:
        return stock.pfupdate( pf )
    except Exception,e:
        logging.error( 'Problem looking for %s => %s' % ( pf, e ) )
        raise Exception(e)


def safe_pf_get(pf,field,defaultval=False):
    '''
    Safe method to extract values from parameter file
    with a default value option.
    '''


    from logging_helper import getLogger
    logging = getLogger( inspect.stack()[0][3] )

    logging.debug( 'Save get value %s from PF file' % field )

    if not isinstance(pf, stock.ParameterFile ):
        logging.error( "%s not a real antelope.stock.ParameterFile" % pf )

    value = defaultval

    if pf.has_key(field):
        try:
            value = pf.get(field,defaultval)
        except Exception,e:
            logging.warning('Problems safe_pf_get(%s,%s)' % (field,e))
            pass

    logging.info( "pf.get(%s,default=%s) => %s" % (field,defaultval,value) )

    return value
