#!/usr/bin/env python

#!/opt/csw/bin/python

##!/usr/bin/env python

"""
Test ORB to AMQP message handler.

Grab ORB packets from antelope and push them to a destination AMQP 

2009-09-15 Juan Reyes <reyes@ucsd.edu>

"""

import sys
import os
import re
#import time
import getopt
import binascii
from struct import *
from amqplib import client_0_8 as amqp

sys.path.append( os.environ['ANTELOPE'] + '/local/data/python' )
try:
    from antelope.orb import *
except:
    print "orb2amqp requires the python 'antelope.orb' (module not found). "
    raise SystemExit

try:
    from antelope.Pkt import *
except:
    print "orb2amqp requires the python 'antelope.Pkt' (module not found). "
    raise SystemExit

try:
    from antelope.stock import *
except:
    print "orb2amqp requires the python 'antelope.stock' (module not found). "
    raise SystemExit



usage = "Usage: orb2amqp [-vd] orbname \n"

elog_init( sys.argv )

try:
    opts, pargs = getopt.getopt(sys.argv[1:], "dv")
except getopt.GetoptError, err:

    print str(err)
    raise SystemExit
    elog_die( usage );

if len(pargs) != 1:
    print usage
    raise SystemExit
    elog_die( usage )
else:
    orbname = pargs[0]
    pfname = 'orb2amqp'
    verbose = False
    debug   = False
    for o, a in opts:
        if o == "-v":
            verbose = 'True'
        if o == "-d":
            verbose = 'True'
            debug   = 'True'

def main():

    orbfd = orbopen( orbname, "r")

    version = orbfd.ping()
    print "Connecting to ORB: %s" % orbname
    print "ORB version: %s" % version


    #conn = amqp.Connection(host="amoeba.ucsd.edu", userid="sqlguest", password="sqlguest", virtual_host="/sqlstream", insist=True)
    #conn = amqp.Connection(host="vista.ucsd.edu", userid="guest", password="guest", virtual_host="/", insist=True)
    #conn = amqp.Connection(host="ec2-50-18-18-199.us-west-1.compute.amazonaws.com", userid="guest", password="guest", virtual_host="/", insist=True)
    conn = amqp.Connection(host="ec2-50-18-66-48.us-west-1.compute.amazonaws.com", userid="guest", password="guest", virtual_host="/", insist=True)

    #amqp_chan_1 = conn.channel()
    #amqp_chan_2 = conn.channel()
    amqp_chan_3 = conn.channel()

    print "Start export of pkts... "

    try:
        while(True):
            (pktid, srcname, time, packet, nbytes) = orbreap( orbfd )
            if verbose:
                print "%s %s" % (pktid,srcname)
            if debug:
                print "pktid:%s srcname:%s time:%s packet:<...> nbytes:%s" % (pktid,srcname,time,nbytes)

            (net, sta, chan, loc, suffix, subcode) = split_srcname(srcname)
            if debug:
                print "(%s, %s, %s, %s, %s, %s) = split_srcname(%s)" % (net,sta,chan,loc,suffix,subcode,srcname)

            (type,pkt) = unstuffPkt( srcname, time, packet, nbytes)
            if debug:
                print "(%s,%s) = unstuffPkt(%s, %s, <...>, %s)" % (type,pkt,srcname,time,nbytes)

            for i in range(pkt.nchannels()):
                pktchannel = pkt.channels(i)

                if debug:
                    print "\n"
                    print "i: %s" % i
                    print "time: %s" % pktchannel.time()
                    print "net: %s" % pktchannel.net()
                    print "sta: %s" % pktchannel.sta()
                    print "chan: %s" % pktchannel.chan()
                    print "loc: %s" % pktchannel.loc()
                    print "nsamp: %s" % pktchannel.nsamp()
                    print "samprate: %s" % pktchannel.samprate()
                    print "calib: %s" % pktchannel.calib()
                    print "calper: %s" % pktchannel.calper()
                    print "segtype: %s" % pktchannel.segtype()

                sps = str(pktchannel.samprate())
                s_type = str(pktchannel.segtype())
                s_time = str(time)
                s_data = str(pktchannel.data())

                r_key = pktchannel.net() + '.' + pktchannel.sta() + '.' + pktchannel.chan()
                if pktchannel.loc(): r_key = r_key + '.' + pktchannel.loc()

                text = {'pktid':pktid, 'time':s_time, 'name':r_key, 'samprate':sps, 'segtype':s_type, 'nbytes':nbytes}
                if debug:
                    print "type: %s" % s_type
                    print "sps: %s" % sps
                    print "time: %s" % s_time
                    print "data: %s" % s_data
                    print "Routing Key => [%s]" % r_key
                    print "Header => [%s]" % str(text)


                #
                # Convert the ascii string s_data to binary data
                #
                #new_bin_data = binascii.a2b_qp(s_data)


                #packet_string = orbpkt_string( srcname, time, packet, nbytes )
                #msg1 = amqp.Message(packet_string, application_headers=text, content_encoding="text", content_type='text/plain')
                #msg2 = amqp.Message(packet, application_headers=text, content_encoding="binary", content_type='application/octet-stream')
                #msg2 = amqp.Message(new_bin_data, application_headers=text, content_encoding="binary", content_type='application/octet-stream')
                msg3 = amqp.Message(s_data, application_headers=text, content_encoding="text", content_type='text/plain')
                # Make msgs persist after server restart
                #msg1.properties["delivery_mode"]=2
                #msg2.properties["delivery_mode"]=2
                
                #amqp_chan_1.basic_publish(msg1, exchange='HEX_DATA')
                #amqp_chan_2.basic_publish(msg2, exchange='BIN_DATA')
                #amqp_chan_3.basic_publish(msg3, exchange='ASCII_DATA')
                amqp_chan_3.basic_publish(msg3, routing_key=r_key, mandatory=True, exchange='magnet.topic')
                #amqp_chan.basic_publish(msg1, exchange='HEX_DATA', mandatory=False, immediate=False)
                #amqp_chan.basic_publish(msg2, exchange='BIN_DATA', mandatory=False, immediate=False)

    except KeyboardInterrupt:
        #amqp_chan_1.close()
        #amqp_chan_2.close()
        amqp_chan_3.close()
        conn.close()
        orbclose(orbfd)

if __name__ == '__main__':
    main()
