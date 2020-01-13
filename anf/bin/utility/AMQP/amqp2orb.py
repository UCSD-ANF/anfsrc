#!/usr/bin/env python

"""
Read messages from the AMQP server using py-amqplib

2009-09-15 Juan Reyes <reyes@ucsd.edu>

"""
import sys
import time

from amqplib import client_0_8 as amqp

# conn = amqp.Connection(host="amoeba.ucsd.edu", userid="sqlguest", password="sqlguest", virtual_host="/sqlstream", insist=True)
conn = amqp.Connection(
    host="vista.ucsd.edu",
    userid="guest",
    password="guest",
    virtual_host="/",
    insist=True,
)

chan = conn.channel()

chan.queue_declare(queue="TEST", durable=False, exclusive=False, auto_delete=False)

chan.exchange_declare(
    exchange="HEX_DATA", type="fanout", durable=False, auto_delete=True
)
chan.exchange_declare(
    exchange="BIN_DATA", type="fanout", durable=False, auto_delete=True
)
chan.exchange_declare(
    exchange="ASCII_DATA", type="fanout", durable=False, auto_delete=True
)

chan.queue_bind(queue="TEST", exchange="HEX_DATA")
chan.queue_bind(queue="TEST", exchange="BIN_DATA")
chan.queue_bind(queue="TEST", exchange="ASCII_DATA")


def recv_callback(msg):
    t = time.time()
    print("\nReceived " + str(t) + ": " + str(msg.application_headers))
    # print '\t' + str(msg.body) + '\n'


chan.basic_consume(
    queue="TEST",
    no_ack=True,
    callback=recv_callback,
    consumer_tag="mysqlstream_consumer",
)
try:
    while True:
        chan.wait()
except KeyboardInterrupt:
    chan.basic_cancel("mysqlstream_consumer")
    chan.close()
    conn.close()
    sys.exit(0)
