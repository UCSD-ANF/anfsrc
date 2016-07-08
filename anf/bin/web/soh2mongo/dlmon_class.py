try:
    #import inspect
    import os
    import re
    import sys
    import json
except Exception, e:
    raise ImportError("Problems importing libraries.%s %s" % (Exception, e))


try:
    import antelope.stock as stock
except Exception, e:
    sys.exit("\n\tProblems loading ANTELOPE libraries. %s(%s)\n" % (Exception, e))


try:
    from soh2mongo.logging_class import getLogger
except Exception, e:
    raise ImportError("Problem loading logging_class. %s(%s)" % (Exception, e))



class Dlmon():
    """
    We have multiple data types and states on the packets
    that we get from the SOH streams. The realtime will send
    those multiplexed raw packets to the ORB and we need
    to read them and parse them. We want to prepare them
    for some other process. This class should handle the
    formats and the state levels of each parameter.

    For now let's work on exporting HTML strings.
    """

    def __init__(self, opt=False, html=False):

        self.logging = getLogger('Dlmon')

        self.logging.info( 'New Dlmon object' )

        self._clean()

        #self.export_format = export_format

        self.parse_opt = opt
        self.output_html = html

        self.rules = stock.pfread('dlmon_rules.pf')


    def _clean(self):
        #self.logging.debug( 'clean object' )

        self.data = {}
        self.packet = {}


    def keys(self):
        return self.data.keys().sort()


    def items(self):
        return self.data.items()


    def __getitem__(self, item):
        return self.data[item]


    def set(self, key, value):
        self.data[ key ] = value


    def dump(self):
        return  self.data


    def new( self, packet ):
        self._clean()

        #print  "\n%s" % json.dumps( packet, indent=4, separators=(',', ': ') )

        self.logging.debug( 'New Dlmon packet ' )

        # Need a dictionary with data
        if not isinstance(packet, dict) or not len(packet) : return

        self.packet = packet

        self._parse()


    def _parse(self):

        # Maybe we want to convert the string OPT into independent
        # variables and append them to object.
        if  self.parse_opt and 'opt' in self.packet:
            opt = self.packet['opt']
            # Let's expand the flags and add 0 if missing.
            self.packet[ 'acok' ] = 1 if re.match( '.*acok.*', opt ) else 0
            self.packet[ 'api' ] = 1 if re.match( '.*api.*', opt )  else 0
            self.packet[ 'isp1' ] = 1 if re.match( '.*isp1.*', opt )  else 0
            self.packet[ 'isp2' ] = 1 if re.match( '.*isp2.*', opt )  else 0
            self.packet[ 'ti' ] = 1 if re.match( '.*ti.*', opt )  else 0

        for chan in self.packet:

            self.logging.debug( 'Channel: %s' % chan )

            try:
                if self.rules[ chan ][ 'avoid']:
                    self.logging.debug( 'SKIP variable set for this channel' )
                    continue
            except:
                pass

            self.data[ chan ] = {}

            # Save original value
            self.data[ chan ][ 'original' ] =  self.packet[ chan ]
            self.data[ chan ][ 'value' ] =  str( self.packet[ chan ] )
            self.data[ chan ][ 'status' ] =  self.rules[ 'defaultstate' ]

            # Verify if we have a definition for this channel
            if chan in self.rules.keys():

                # Let's try to make a clean version of this element.
                try:
                    self.data[ chan ][ 'value' ] =  getattr( self, self.rules[ chan ][ 'transform' ] )( self.packet[ chan ] )
                except:
                    self.data[ chan ][ 'value' ] =  str( self.packet[ chan ] )


                # Verify if we have some tests to run

                if 'test' in self.rules[ chan ]:
                    self.logging.debug( 'test function: %s' % self.rules[ chan ]['test'] )
                    try:
                        # Modify value before running test
                        if 'pretest' in self.rules[ chan ]:
                            value = getattr( self, self.rules[ chan ][ 'pretest' ] )( self.packet[ chan ] )
                        else:
                            value = self.packet[ chan ]

                        self.logging.debug( 'test value: %s' % value )

                        if ( self.rules[ chan ][ 'test' ] == '_testRange' ):
                            okgt = False
                            oklt = False
                            warninglt = False
                            warninggt = False

                            if 'okgt' in self.rules[ chan ]:
                                okgt = self.rules[ chan ][ 'okgt' ]

                            if 'oklt' in self.rules[ chan ]:
                                oklt = self.rules[ chan ][ 'oklt' ]

                            if 'warninggt' in self.rules[ chan ]:
                                warninggt = self.rules[ chan ][ 'warninggt' ]

                            if 'warninglt' in self.rules[ chan ]:
                                warninglt = self.rules[ chan ][ 'warninglt' ]

                            self.data[ chan ][ 'status' ] =  \
                                getattr( self, self.rules[ chan ][ 'test' ] )( value,
                                        okgt=okgt, oklt=oklt, warninggt=warninggt,
                                        warninglt=warninglt )
                        else:

                            ok = False
                            warning = False

                            if 'ok' in self.rules[ chan ]:
                                ok = self.rules[ chan ][ 'ok' ]

                            if 'warning' in self.rules[ chan ]:
                                warning = self.rules[ chan ][ 'warning' ]

                            self.data[ chan ][ 'status' ] =  \
                                getattr( self, self.rules[ chan ][ 'test' ] )( value, ok, warning )

                    except Exception,e :
                        self.logging.notify( 'Problem: %s => %s' % ( chan, e) )
                        if 'except' in self.rules[ chan]:
                            self.data[ chan ][ 'status' ] =  self.rules[ chan ][ 'ifexception' ]
                        else:
                            self.data[ chan ][ 'status' ] =  self.rules[ 'ifexception' ]


                else:
                    self.logging.debug( 'SKIP TEST: status ok' )


                self.logging.debug( 'final status: %s' % self.data[chan]['status'] )

            # Maybe we want to add an HTML element
            if self.output_html == 'True':
                self.data[ chan ][ 'html' ] = \
                        '<td class="%s"><span style="display:none">%s</span>%s</td>' % \
                        ( self.data[ chan ][ 'status' ],
                        self.data[ chan ][ 'original' ],
                        self.data[ chan ][ 'value' ] )


            # Maybe we want to rename this channel
            if 'rename' in self.rules[ chan ]:
                self.data[ self.rules[ chan ][ 'rename' ] ] = self.data[ chan ]
                del self.data[ chan ]

    def _testRange(self, value, okgt, oklt, warninggt, warninglt):
            self.logging.debug('testRange( %s %s %s %s %s)' % (value, okgt, oklt, warninggt, warninglt) )

            try:
                if eval( "%s <= %s and %s <= %s" % (okgt, value, value, oklt)):
                    return self.rules[ 'okstate' ]
            except Exception,e:
                pass

            try:
                if eval( "%s <= %s and %s <= %s" % (warninggt, value, value, warninglt)):
                    return self.rules[ 'warningstate' ]
            except Exception,e:
                pass

            return self.rules[ 'badstate' ]

    def _testLogical(self, value, ok=False, warning=False):
            self.logging.debug('testRange( %s %s %s)' % (value, ok, warning) )

            try:
                value = float(value)
            except:
                pass

            if ok :
                try:
                    if eval( "%s %s" % (value, ok)): return self.rules[ 'okstate' ]
                except:
                    pass

            if warning :
                try:
                    if eval( "%s %s" % (value, warning)): return self.rules[ 'warningstate' ]
                except:
                    pass

            return self.rules[ 'badstate' ]

    def _testValue(self, value, ok=False, warning=False):
            self.logging.debug('testValue( %s %s %s)' % (value, ok, warning) )

            if ok:
                if value == ok: return self.rules[ 'okstate' ]

            if warning :
                if value == warning: return self.rules[ 'warningstate' ]

            return self.rules[ 'badstate' ]

    def _testRegex(self, value, ok=False, warning=False):
            self.logging.debug('testRegex( %s %s %s)' % (value, ok, warning) )

            if ok:
                #self.logging.debug('re.match( %s, %s)' % (ok, value) )
                #regex = re.compile( ok )
                #if regex.match( value ): return self.rules[ 'okstate' ]
                if re.match( ok, value ): return self.rules[ 'okstate' ]

            if warning:
                #self.logging.debug('re.match( %s, %s)' % (warning, value) )
                #regex = re.compile( warning )
                #if regex.match( value ): return self.rules[ 'warningstate' ]
                if re.match( warning, value ): return self.rules[ 'warningstate' ]

            #self.logging.debug('testRegex( NO MATCH)' )
            return self.rules[ 'badstate' ]

    def _toAbs (self, value):
        return abs( float(value) )

    def _toInt (self, value):
        return int( float(value) )

    def _toFloat (self, value):
        return float( value )

    def _toFloat1 (self, value):
        return format(float(value), '0.1f')

    def _toFloat2 (self, value):
        return format(float(value), '0.2f')

    def _toPercent (self, value):
        return "%s %%" % format(float(value), '0.1f')

    def _toTime (self, value):
        return stock.strtime(value)

    #def _toLapse (self, value):
    #    #return stock.strtdelta(value).strip()
    #    return stock.strtdelta(float(value)).strip()

    def _toTemp (self, value):
        return "%s C" % format(float(value), '0.1f')

    def _toTempInt (self, value):
        return "%s C" % int(float(value))

    def _toMassVoltage (self, value):
        return "%s V" % format( (float(value)/10), '0.2f')

    def _toVoltage (self, value):
        return "%s V" % format( float(value) , '0.1f')

    def _toCurrent (self, value):
        return "%s mA" % (float(value)*100.0)

    def _toBytes (self, size):
        suffixes=['B','KB','MB','GB','TB']
        suffixIndex = 0
        size = float(size)
        while size > 1024 and suffixIndex < 4:
            suffixIndex += 1
            size /= 1024.0 #apply the division
        return "%0.1f %s"%(size,suffixes[suffixIndex])

    def _toKBytesSec (self, value):
        return "%s/s" % self._toBytes( value )
