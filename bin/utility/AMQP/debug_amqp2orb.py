#!/usr/bin/env python

"""
Read messages from the AMQP server using py-amqplib 

2009-09-15 Juan Reyes <reyes@ucsd.edu>

"""
import sys
import os
import pprint
import binascii

sys.path.append( os.environ['ANTELOPE'] + '/data/python' )

from amqplib import client_0_8 as amqp
from antelope.Pkt import *

import sys 
import time

conn = amqp.Connection(host="vista.ucsd.edu", userid="guest", password="guest", virtual_host="/", insist=True)

chan = conn.channel()

chan.queue_declare(queue='DEBUG', durable=False, exclusive=False, auto_delete=False)

chan.exchange_declare(exchange='BIN_DATA', type='fanout', durable=False, auto_delete=True)

chan.queue_bind(queue='DEBUG', exchange='BIN_DATA')

def recv_callback(msg):
    t = time.time()
    #print '\nReceived '+ str(t) + ': '  + str(msg.application_headers)
    #print '\t' + str(msg.body) + '\n'
    headers = msg.application_headers
    print '#################################\n'
    print 'Received '+ str(t) + ': '  + str(headers['name'])
    print headers['time']
    (type,pkt) = unstuffPkt( headers['name'], float(headers['time']), msg.body, int(headers['nbytes']) )
    print 'srcname: ' + str(pkt.srcname()) + '\n'
    print 'time: ' + str(pkt.time()) + '\n'
    print 'PktType: ' + str(pkt.PacketType()) + '\n'
    print 'type: ' + str(pkt.type()) + '\n'
    print 'nchannels: ' + str(pkt.nchannels()) + '\n'
    print 'pf: ' + str(pkt.pf()) + '\n'
    print 'string: ' + str(pkt.string()) + '\n'
    print 'db: ' + str(pkt.db()) + '\n'
    print 'dfile: ' + str(pkt.dfile()) + '\n'
    print 'version: ' + str(pkt.version()) + '\n'

    pktchannel = pkt.channels(0)

    print 'time: ' + str(pktchannel.time()) + '\n'
    print 'net: ' + str(pktchannel.net()) + '\n'
    print 'sta: ' + str(pktchannel.sta()) + '\n'
    print 'chan: ' + str(pktchannel.chan()) + '\n'
    print 'loc: ' + str(pktchannel.loc()) + '\n'
    print 'nsamp: ' + str(pktchannel.nsamp()) + '\n'
    print 'samprate: ' + str(pktchannel.samprate()) + '\n'
    print 'data: ' + str(pktchannel.data()) + '\n'
    print 'calib: ' + str(pktchannel.calib()) + '\n'
    print 'calper: ' + str(pktchannel.calper()) + '\n'
    print 'segtype: ' + str(pktchannel.segtype()) + '\n'

    print '##'
    print '## Start binascii test'
    print '##'
    rle = binascii.rledecode_hqx(msg.body)
    print rle
    print '##'
    print '##'


chan.basic_consume(queue="DEBUG", no_ack=True, callback=recv_callback, consumer_tag="mysqlstream_consumer")
try:
    while True:
        chan.wait()
except KeyboardInterrupt:
    chan.basic_cancel("mysqlstream_consumer")
    chan.close()
    conn.close()
    sys.exit(0)
