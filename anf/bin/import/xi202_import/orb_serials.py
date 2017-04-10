#
# How to use...

#q330units = ORBserials( [:orbs] )
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
    import antelope.orb as orb
    import antelope.Pkt as Pkt
except Exception, e:
    raise ImportError("Problems loading ANTELOPE libraries. %s(%s)" % (Exception, e))


try:
    from xi202_import.logging_class import getLogger
except Exception, e:
    raise ImportError("Problem loading logging_class. %s(%s)" % (Exception, e))



class ORBserials():
    """Implementation of perl's autovivification feature."""
    def __init__(self, orblist=[], orbselect='.*' ):

        self.logging = getLogger('ORBserials')

        self.update_frequency = 3600
        self.last_update = 0

        self.orb_select = orbselect
        self.serials = {}
        self.orblist = []
        self.add( orblist )
        self.update()



    def update( self ):
        self.logging.info( 'Update orb serials' )

        if isinstance(self.orblist, collections.Iterable):
            for orb in self.orblist:
                self._get_orb_data( orb )

            self.last_update = int( stock.now() )

        else:
            self.logging.error( 'ORBLIST not iterable: ' + str(self.orblist) )

    def add( self, new_orbs ):

        self.logging.debug( 'add to orb configuration: ' + str(new_orbs) )

        if not new_orbs: return

        if isinstance(new_orbs, collections.Iterable):
            orbs = new_orbs
        elif isinstance(new_orbs, basestring):
            orbs = [ new_orbs ]
        else:
            self.logging.error( 'Need ORB to be string or iterable collection [%s]' % new_orbs )

        self.orblist.extend( orbs )

    def _parse_pf(self, line):

        parts = line.split()
        new_serial = parts[3]

        if  new_serial in self.serials and self.serials[ new_serial ]['dlname'] == parts[0]:
            self.logging.debug( 'New entry for %s: %s => %s' % \
                    ( new_serial, self.serials[ new_serial ]['dlname'], parts[0]) )
        elif  new_serial in self.serials:
            self.logging.warning( 'Updating value for %s: %s => %s' % \
                    ( new_serial, self.serials[ new_serial ]['dlname'], parts[0]) )
        else:
            self.logging.info( 'New serial %s: %s ' % ( parts[0], new_serial ) )

        self.serials[ new_serial ] = {
                    'dlname': parts[0],
                    'sta': parts[2],
                    'snet': parts[1]
                }

    def _get_orb_data(self, orbname ):
        """
        Look into every ORB listed on configuration
        and get list of dataloggers.
        """

        self.logging.debug( orbname )
        self.logging.debug( "Read STASH_ONLY on %s" % orbname )

        if not orbname or not isinstance(orbname, str):
            self.logging.warning( "Not valid: %s" % (orbname) )
            return

        self.logging.debug( "%s" % (orbname) )

        temp_orb = orb.Orb( orbname )

        try:
            self.logging.debug("connect to orb(%s)" % orbname )
            temp_orb.connect()
            temp_orb.stashselect(orb.STASH_ONLY)

        except Exception,e:
            raise self.logging.error("Cannot connect to ORB: %s %s" % (orbname, e))

        else:
            temp_orb.select( self.orb_select )
            temp_orb.reject( '.*/log' )

            self.logging.debug( "orb.after(0.0)" )
            temp_orb.after( 0.0 ) # or orb.ORBOLDEST

            try:
                sources = temp_orb.sources()[1]
            except:
                sources = []

            self.logging.debug( sources )

            for source in sources:
                srcname = source['srcname']
                self.logging.debug( 'sources: %s' % srcname )

                # Get stash for each source
                try:
                    pkttime, pktbuf = temp_orb.getstash( srcname )

                except Exception,e:
                    self.logging.info( '%s %s:%s' % (srcname,Exception,e) )

                else:
                    pkt = Pkt.Packet( srcname, pkttime, pktbuf )
                    temp_pf = stock.ParameterFile()
                    temp_pf.pfcompile( pktbuf.rstrip('\x00').lstrip('\xff') )

                    if temp_pf.has_key('q3302orb.pf'):

                        temp_list = temp_pf['q3302orb.pf']['dataloggers']
                        self.logging.debug( temp_list )

                    else:
                        self.logging.warning( 'No information in stash packet for %s' % srcname )
                        temp_list = []

                    for x in temp_list:
                        self.logging.debug( "Parse: [%s]" % x )
                        self._parse_pf( x )

                    else:

                        self.logging.debug("dataloggers missing from Pkt %s" % srcname )


        try:
            self.logging.debug("close orb(%s)" % orbname )
            temp_orb.close()
        except:
            pass

    def _verify_cache(self):

        if (self.last_update + self.update_frequency ) < int( stock.now() ):
            self.logging.info( 'Need to update cache.' )
            self.update()

    def __str__(self):

        return 'ORBSERVERS: %s' % str( join( ', ', self.orblist ) )


    def __call__(self, serial):

        self._verify_cache()

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

        self._verify_cache()

        if serial in self.serials:
            return self.serials[ serial ]
        else:
            return None


    def __iter__(self):

        return iter( self.serials.keys() )
