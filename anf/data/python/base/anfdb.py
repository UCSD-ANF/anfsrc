#
# Some generic Python function
# to make database operations easy
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
    import antelope.datascope as datascope
except Exception,e:
    raise ImportError("[%s] Do you have Antelope installed?" % e)


def get_all_fields( dbpointer , nulls={}):
    '''
    At a given database pointer to a particular record query for valid
    table fields and pull all values.

    Return a dictionary (key=>value) with the values.
    '''

    import antelope.datascope as datascope
    from anfstock import eval_null
    from logging_helper import getLogger
    logging = getLogger( inspect.stack()[0][3] )

    logging.debug( 'Extract all values from db view ' )

    results = {}

    if not dbpointer:
        logging.warning('NULL or NONE dbpointer')
        return results


    logging.warning('%s records found' % dbpointer.query( datascope.dbFIELD_COUNT ) )
    #if not dbpointer.query(datascope.dbTABLE_PRESENT):
    #    logging.warning('No table in view. No records extracted.')
    #    return results


    for x in range( dbpointer.query( datascope.dbFIELD_COUNT )):

        dbpointer.field = x

        table = dbpointer.query( datascope.dbFIELD_BASE_TABLE )
        field = dbpointer.query( datascope.dbFIELD_NAME )

        test = "%s.%s" % (table,field)
        logging.debug( 'Extract field %s' % test )

        value = dbpointer.getv( test )[0]

        # Verify value with NULL options for those fields.
        if nulls and test in nulls:
            #logging.debug( 'verify null on: [%s] == [%s] ' % (value,nulls[test]) )
            if eval_null( value, nulls[ test ] ):
                logging.debug( 'AVOID NULL VALUE: [%s] ' % value )
                continue
        else:
            #logging.debug( 'Save value for NULL [%s] on %s' % (value,test) )
            pass

        results[ test ] = value

        #if nulls:
        #    logging.debug( '%s => %s' % ( test, results[test]) )

    #logging.debug( results )

    return results


def verify_table(db, tablename):
    '''
    Open a database (or database pointer) and verify a table

    On multiple instances we perform the same process
    of verifying the presence of a table before we get to
    interact with it. This will make that process easy since
    you can get to that point either from a database name
    or from a database pointer. The function will return
    the database pointer that you are responsible for
    cleaning later. The local view of the table will be
    freed.

    Remember to free the return pointer later!!!
    '''

    import antelope.datascope as datascope
    from logging_helper import getLogger
    logging = getLogger( inspect.stack()[0][3] )

    logging.debug( 'Verify table [%s]' % tablename )

    # Verify if we have a string or a pointer DB object
    if isinstance( db, datascope.Dbptr ):
        dbview = db
    else:
        logging.debug( 'dbopen( %s )' % db )
        dbview = datascope.dbopen( db, "r+" )


    # Verify if we have a table or if we should open it
    try:
        if dbview.query(datascope.dbTABLE_PRESENT):
            tableview = dbview
        else:
            raise
    except:
        logging.debug( 'Lookup table: %s' % tablename )
        tableview = dbview.lookup(table=tablename)


    logging.debug( 'dbTABLE_PRESENT => %s' % \
            tableview.query(datascope.dbTABLE_PRESENT))

    # Check if we don't have anything to continue
    if not tableview.query(datascope.dbTABLE_PRESENT):
        logging.warning( 'Missing table [%s] in db view.' % tablename )
        return False

    if not tableview.record_count:
        logging.warning( 'EMPTY table %s' % tablename )

    # Return valid view if table is present
    return tableview
