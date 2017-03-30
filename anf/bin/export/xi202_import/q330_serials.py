#
# How to use...

#q330units = Q330serials( q330_pf_files )
#
#print  q330units( '0100000A27B19B6A' )
# >> TA_O53A

#print  q330units.info( '0100000A27B19B6A' )
# >> {'snet': 'TA', 'sta': 'O53A', 'dlname': 'TA_O53A'}

#print q330units( '00000' )
# >> False

#print q330units( None )
# >> False
#


try:
    import re
    import os
    import sys
    import datetime
    import collections
except Exception, e:
    raise ImportError("Problems importing libraries.%s %s" % (Exception, e))

try:
    import antelope.stock as stock
except Exception, e:
    raise ImportError("Problems loading ANTELOPE libraries. %s(%s)" % (Exception, e))


try:
    from xi202_import.logging_class import getLogger
except Exception, e:
    raise ImportError("Problem loading logging_class. %s(%s)" % (Exception, e))



class Q330serials():
    """Implementation of perl's autovivification feature."""
    def __init__(self, pf_files=[] ):

        self.logging = getLogger('Q330serials')

        self.serials = {}
        self.add( pf_files )


    def add( self, pf_files ):

        self.logging.debug( 'add to pf file configuration: ' + str(pf_files) )

        if not pf_files: return

        if isinstance(pf_files, collections.Iterable):
            self.q330_pf_files = pf_files
        elif isinstance(var, basestring):
            self.q330_pf_files = [ pf_files ]
        else:
            self.logging.error( 'Need pf_files to be string or iterable collection [%s]' % pf_files )

        #self.logging.debug( str( self ) )

        # remove empty strings
        self.q330_pf_files = [t for t in self.q330_pf_files if t]

        for pf in self.q330_pf_files:
            self._read_pf( pf )

    def _read_pf(self, pf):

        self.logging.info('Read values from pf file %s' % pf)

        temp = stock.pfread( pf )

        dataloggers = temp.get('dataloggers')

        if not dataloggers:
            self.logging.warning( 'Nothing in the dataloggers parameter for %s' % pf )
        else:
            #self.logging.debug( dataloggers )
            pass


        for line in dataloggers:

            parts = line.split()
            new_serial = parts[3]

            if  new_serial in self.serials:
                self.logging.info( 'Updating value for %s: %s => %s' % \
                        ( new_serial, self.serials[ new_serial ]['dlname'], parts[0]) )
            else:
                self.logging.info( 'New serial %s: %s ' % ( parts[0], new_serial ) )

            self.serials[ new_serial ] = {
                        'dlname': parts[0],
                        'sta': parts[2],
                        'snet': parts[1]
                    }

    def __str__(self):

        return 'q3302orb.pf file list: %s' % str( self.q330_pf_files )


    def __call__(self, serial):

        if serial in self.serials:
            return self.serials[ serial ][ 'dlname' ]
        else:
            return None

    def info(self, serial):

        if serial in self.serials:
            return self.serials[ serial ]
        else:
            return None

    def __getitem__(self, serial):

        if serial in self.serials:
            return self.serials[ serial ]
        else:
            return None


    def __iter__(self):

        return iter( self.serials.keys() )
