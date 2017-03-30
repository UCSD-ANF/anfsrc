#
# How to use...

#imei = IMEIbuffer()
#
#imei( imei='300234062061770', serial='0100000A27B19B6A')

#print  imei( '300234062061770' )
# >> '0100000A27B19B6A'

#print imei( '00000' )
# >> False

#print imei( None )
# >> False
#


try:
    import os
    import sys
except Exception, e:
    raise ImportError("Problems importing libraries.%s %s" % (Exception, e))

try:
    from xi202_import.logging_class import getLogger
except Exception, e:
    raise ImportError("Problem loading logging_class. %s(%s)" % (Exception, e))



class IMEIbuffer():
    def __init__( self ):

        self.logging = getLogger('Q330serials')

        self.cache = {}


    def add( self, imei=None, serial=None ):

        self.logging.debug( 'add %s to cache with value %s ' % ( imei, serial ) )

        if not imei:
            self.logging.warning( 'Need valid value for IMEI: [%s]' % imei )

        if not serial:
            self.logging.warning( 'Need valid value for serial: [%s]' % serial )

        try:
            if int( serial ) < 1:
                self.logging.warning( 'NULL serial: [%s]' % serial )
                return False
        except:
            pass


        if  imei in self.cache:
            self.logging.info( 'Updating value for %s: %s => %s' % \
                    ( imei, self.cache[ imei ], serial) )
        else:
            self.logging.info( 'New imei %s: %s ' % ( imei, serial ) )

        self.cache[ imei ] = serial

        return True


    def __str__(self):

        return 'IMEIbuffer: %s' % str( self.cache )


    def __call__(self, imei):

        if imei in self.cache:
            return self.cache[ imei ]
        else:
            return None


    def __getitem__(self, imei):

        if imei in self.cache:
            return self.cache[ imei ]
        else:
            return None


    def __iter__(self):

        return iter( self.cache.keys() )
