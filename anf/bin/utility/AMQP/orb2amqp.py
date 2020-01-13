#!/usr/bin/env python

"""Test ORB to AMQP message handler.

Grab ORB packets from antelope and push them to a destination AMQP

2009-09-15 Juan Reyes <reyes@ucsd.edu>
"""

# import time
import getopt
import sys

from amqplib import client_0_8 as amqp
from antelope import Pkt, orb, stock

usage = "Usage: orb2amqp [-vd] orbname \n"

stock.elog_init(sys.argv)

try:
    opts, pargs = getopt.getopt(sys.argv[1:], "dv")
except getopt.GetoptError as err:
    print(str(err))
    raise SystemExit
    stock.elog_die(usage)

if len(pargs) != 1:
    print(usage)
    raise SystemExit
    stock.elog_die(usage)
else:
    orbname = pargs[0]
    pfname = "orb2amqp"
    verbose = False
    debug = False
    for o, a in opts:
        if o == "-v":
            verbose = "True"
        if o == "-d":
            verbose = "True"
            debug = "True"


def main():

    orbfd = orb.orbopen(orbname, "r")

    version = orbfd.ping()
    print("Connecting to ORB: %s" % orbname)
    print("ORB version: %s" % version)

    # conn = amqp.Connection(host="amoeba.ucsd.edu", userid="sqlguest", password="sqlguest", virtual_host="/sqlstream", insist=True)
    # conn = amqp.Connection(host="vista.ucsd.edu", userid="guest", password="guest", virtual_host="/", insist=True)
    # conn = amqp.Connection(host="ec2-50-18-18-199.us-west-1.compute.amazonaws.com", userid="guest", password="guest", virtual_host="/", insist=True)
    conn = amqp.Connection(
        host="ec2-50-18-66-48.us-west-1.compute.amazonaws.com",
        userid="guest",
        password="guest",
        virtual_host="/",
        insist=True,
    )

    # amqp_chan_1 = conn.channel()
    # amqp_chan_2 = conn.channel()
    amqp_chan_3 = conn.channel()

    print("Start export of pkts... ")

    try:
        while True:
            (pktid, srcname, time, packet, nbytes) = orb.orbreap(orbfd)
            if verbose:
                print("%s %s" % (pktid, srcname))
            if debug:
                print(
                    "pktid:%s srcname:%s time:%s packet:<...> nbytes:%s"
                    % (pktid, srcname, time, nbytes,)
                )

            (net, sta, chan, loc, suffix, subcode) = orb.split_srcname(srcname)
            if debug:
                print(
                    "(%s, %s, %s, %s, %s, %s) = split_srcname(%s)"
                    % (net, sta, chan, loc, suffix, subcode, srcname,)
                )

            (type, pkt) = Pkt.unstuffPkt(srcname, time, packet, nbytes)
            if debug:
                print(
                    "(%s,%s) = unstuffPkt(%s, %s, <...>, %s)"
                    % (type, pkt, srcname, time, nbytes,)
                )

            for i in range(pkt.nchannels()):
                pktchannel = pkt.channels(i)

                if debug:
                    print("\n")
                    print("i: " + i)
                    print("time: " + pktchannel.time())
                    print("net: " + pktchannel.net())
                    print("sta: " + pktchannel.sta())
                    print("chan: " + pktchannel.chan())
                    print("loc: " + pktchannel.loc())
                    print("nsamp: " + pktchannel.nsamp())
                    print("samprate: " + pktchannel.samprate())
                    print("calib: " + pktchannel.calib())
                    print("calper: " + pktchannel.calper())
                    print("segtype: " + pktchannel.segtype())

                sps = str(pktchannel.samprate())
                s_type = str(pktchannel.segtype())
                s_time = str(time)
                s_data = str(pktchannel.data())

                r_key = (
                    pktchannel.net() + "." + pktchannel.sta() + "." + pktchannel.chan()
                )
                if pktchannel.loc():
                    r_key = r_key + "." + pktchannel.loc()

                text = {
                    "pktid": pktid,
                    "time": s_time,
                    "name": r_key,
                    "samprate": sps,
                    "segtype": s_type,
                    "nbytes": nbytes,
                }
                if debug:
                    print("type: " + s_type)
                    print("sps: " + sps)
                    print("time: " + s_time)
                    print("data: " + s_data)
                    print("Routing Key => [%s]" % r_key)
                    print("Header => [%s]" % str(text))

                #
                # Convert the ascii string s_data to binary data
                #
                # new_bin_data = binascii.a2b_qp(s_data)

                # packet_string = orbpkt_string( srcname, time, packet, nbytes )
                # msg1 = amqp.Message(packet_string, application_headers=text, content_encoding="text", content_type='text/plain')
                # msg2 = amqp.Message(packet, application_headers=text, content_encoding="binary", content_type='application/octet-stream')
                # msg2 = amqp.Message(new_bin_data, application_headers=text, content_encoding="binary", content_type='application/octet-stream')
                msg3 = amqp.Message(
                    s_data,
                    application_headers=text,
                    content_encoding="text",
                    content_type="text/plain",
                )
                # Make msgs persist after server restart
                # msg1.properties["delivery_mode"]=2
                # msg2.properties["delivery_mode"]=2

                # amqp_chan_1.basic_publish(msg1, exchange='HEX_DATA')
                # amqp_chan_2.basic_publish(msg2, exchange='BIN_DATA')
                # amqp_chan_3.basic_publish(msg3, exchange='ASCII_DATA')
                amqp_chan_3.basic_publish(
                    msg3, routing_key=r_key, mandatory=True, exchange="magnet.topic"
                )
                # amqp_chan.basic_publish(msg1, exchange='HEX_DATA', mandatory=False, immediate=False)
                # amqp_chan.basic_publish(msg2, exchange='BIN_DATA', mandatory=False, immediate=False)

    except KeyboardInterrupt:
        # amqp_chan_1.close()
        # amqp_chan_2.close()
        amqp_chan_3.close()
        conn.close()
        orb.orbclose(orbfd)


if __name__ == "__main__":
    main()
