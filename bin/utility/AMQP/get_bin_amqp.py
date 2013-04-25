#!/usr/bin/env python

"""
Read binary messages from the AMQP server using py-amqplib 

2010-01-11 Juan Reyes <reyes@ucsd.edu>

"""
from amqplib import client_0_8 as amqp

import sys 
import time
import binascii

conn = amqp.Connection(host="vista.ucsd.edu", userid="guest", password="guest", virtual_host="/", insist=True)

chan = conn.channel()

chan.queue_declare(queue='BIN', durable=False, exclusive=False, auto_delete=False)

chan.exchange_declare(exchange='BIN_DATA', type='fanout', durable=False, auto_delete=True)

chan.queue_bind(queue='BIN', exchange='BIN_DATA')

def recv_callback(msg):
    t = time.time()
    print '\nReceived '+ str(t) + ': '  + str(msg.application_headers)
    data = binascii.b2a_qp(msg.body)
    print '\t' + data + '\n'

chan.basic_consume(queue="BIN", no_ack=True, callback=recv_callback, consumer_tag="sqlstream_consumer")
try:
    while True:
        chan.wait()
except KeyboardInterrupt:
    chan.basic_cancel("mysqlstream_consumer")
    chan.close()
    conn.close()
    sys.exit(0)

