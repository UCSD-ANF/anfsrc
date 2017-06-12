"""
This module is in charge of pulling information from a
Datascope table ( view? ) and keep all values in memory.
We create an object with multiple methods to
interact with the databases and attributes to
keep the field information easily accessible to
the parent process.

Juan Reyes
reyes@ucsd.edu


"""

if __name__ == "__main__":
    raise ImportError( "\n\n\tANF Python library. Not to run directly!!!! \n" )

import sys
import json
import inspect
import logging_helper

try:
    import antelope.stock as stock
    import antelope.datascope as datascope
except Exception,e:
    raise ImportError("[%s] Do you have Antelope installed?" % e)


class Document():
    """
    Class for creating rows storage objects.

    Store all information of a single row from a
    datascope view. Similar to a NoSQL document in
    JSON format.

    """

    def __init__(self, *args):

        #from logging_helper import getLogger
        #self.logging = getLogger( inspect.stack()[0][3] )

        #self.logging.debug('New Document')

        self.data = args[0]

    def __str__(self):
        return "\n%s" % json.dumps( self.data)

    def __getitem__(self, name):
        try:
            return self.data[ name ]
        except:
            return ''


class Collection( Document ):
    '''
    Class for maintaining a Datascope view in memory.

    Open the database while declaring the object. You can
    specify the table of interest on the argument list and
    let the init process verify that it's valid and has
    some data. In example:
        sites = anf.Collection( database, 'site' )

    Then you can make a second call to "get_view" and extract
    all valid entries and have the cached in memory in the
    object.

    Submit a list of db operations to subset your table before
    pull the values into memory. In example:

        origins = anf.Collection( database, 'origin' )
        steps = ['dbopen origin']
        steps.extend([ 'dbsubset evid == %s' % self.evid ])

        origins.get_view( steps, key='origin.orid' )

        log.info( origins )

        for (sta, data) in origins.items():
            log.info( "%s => %s:" % (sta,data) )

    '''

    def __init__(self, database=None, table=None ):

        import antelope.datascope as datascope
        from anfdb import verify_table
        from logging_helper import getLogger

        self.logging = getLogger( inspect.stack()[0][3] )
        self.logging.debug('New Collection')

        self.documents = {}

        self.database = database    # database name
        self.table = table         # database table name

        self.db = verify_table( self.database, self.table )


    def clean(self):
        self.documents = {}

    def __str__(self):
        return self.documents.keys()

    def __iter__(self):
        return iter(self.dcouments)

    def items(self):
        return self.documents.items()

    def exists(self, name):
        try:
            return name in self.documents
        except:
            return False

    def __getitem__(self, name):
        try:
            return self.documents[ name ]
        except:
            return None

    def keys(self, reverse=False):
        return  self.documents.keys()

    def values(self, sort=False, reverse=False):
        if sort:
            return  sorted(self.documents.values(), key=lambda v: v[sort] , reverse=reverse)
        else:
            return  self.documents.values()


    def get_view(self, steps=[], key=None):
        """
        Open view, run commands and get entries.

        if 'key' is given then use that as a key for the
        final dictionary. This should be a unique key
        in the table view otherwise you will miss some
        rows. It has the form: 'origin.orid'
        If not 'key' set then it builds a sudo list. Only
        sequential numbers as keys that represent the row
        numbers from the original view.
        """

        from anfdb import get_all_fields

        self.logging.debug( ', '.join(steps) )

        if not self.db:
            self.logging.warning( 'Problems with database pointer' )
            return

        with datascope.freeing(self.db.process( steps )) as dbview:

            self.logging.debug( '%s total values in view' % dbview.record_count )

            if not dbview.record_count:
                self.logging.warning( 'No values left in view' )
                return


            # Get NULL values
            self.logging.debug( 'Extract NULL values' )
            dbview.record = datascope.dbNULL
            nulls = get_all_fields( dbview )

            self.logging.debug( 'Extract data values' )
            for r in dbview.iter_record():

                self.logging.debug( 'New document' )
                temp = get_all_fields( r,nulls )

                if key:
                    self.documents[ temp[ key ] ] = Document( temp )
                else:
                    self.documents[ len(self.documents) ] = Document( temp )


if __name__ == "__main__": raise ImportError( "\n\n\tAntelope's qml module. Not to run directly!!!! **\n" )
