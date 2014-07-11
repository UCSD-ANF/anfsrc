import sys
import os
sys.path.append('%s/data/python' % os.environ['ANTELOPE'])

from antelope import orb
from antelope import Pkt
from antelope.datascope import closing,\
                               dbopen,\
                               trdestroying
from antelope.stock import epoch2str,\
                           str2epoch
import time as mytime
from segd_cython import my_round

MAX_PKT_LENGTH = 600 #600 seconds

def _parse_args():
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('dbin', type=str, help='Input database.')
    parser.add_argument('orb', type=str, help='Output orb.')
    return parser.parse_args()

if __name__ == '__main__':
    args = _parse_args()
    my_orb = orb.Orb(args.orb, permissions='w')
    my_orb.connect()
    with closing(dbopen(args.dbin, 'r')) as db:
        tbl_wfdisc = db.schema_tables['wfdisc']
        tbl_wfdisc = tbl_wfdisc.sort('time')
        tbl_wfdisc.record = 0
        t = epoch2str(tbl_wfdisc.getv('time')[0], '%Y %j %H %M')
        t = [int(d) for d in t.split()]
        tstart = int(str2epoch('%d%d %d:%d:00' % (t[0],
                                            t[1],
                                            t[2],
                                            t[3] - (t[3] % 10))))
        tbl_wfdisc.record = tbl_wfdisc.record_count - 1
        t = epoch2str(tbl_wfdisc.getv('endtime')[0], '%Y %j %H %M %S %s')
        t = [int(d) for d in t.split()]
        tend = int(str2epoch('%d%d %d:%d:00' % (t[0],
                                               t[1],
                                               t[2],
                                               t[3] + (10 - (t[3] % 10)))))
        sta, chan = tbl_wfdisc.getv('sta', 'chan')
        my_pkt = Pkt.Packet()
        my_pkt.type_suffix = 'GENC'
        my_pkt.channels = [Pkt.PktChannel()]
        my_pkt.channels[0].chan = 'EHZ'
        my_pkt.channels[0].net = 'SGBF'
        my_pkt.channels[0].samprate = 500.0
        my_pkt.channels[0].sta = sta
        s = []
        for t0 in range(tstart, tend, MAX_PKT_LENGTH):
            t1 = t0 + MAX_PKT_LENGTH
            t = mytime.time()
            tr = tbl_wfdisc.trloadchan(t0, t1, sta, chan)
            t = mytime.time() - t
            print '\trloadchan() took: %f seconds' % t
            with trdestroying(tr):
                tr.record = 0
                time = tr.getv('time')[0]
                t = mytime.time()
                tr.trapply_calib()
                t = mytime.time() - t
                print '\ttrapply_calib took: %f seconds' % t
                t = mytime.time()
                my_pkt.channels[0].data = [int(round(d)) for d in tr.trdata()]
                #my_pkt.channels[0].data = my_round(tr.trdata())
                t = mytime.time() - t
                print '\tpython rounding took: %f seconds' % t
                my_pkt.channels[0].time = time
                t = mytime.time()
                pkttype, pktbuf, srcname, time = my_pkt.stuff()
                t = mytime.time() - t
                print '\tmy_pkt_stuff() took: %f seconds' %  t
                t = mytime.time()
                my_orb.put(srcname, time, pktbuf)
                t = mytime.time() - t
                print '\tmy_orb.put() took: %f seconds' % t
        #    s += [t]
        #print 'Average time per 10 minute data block - %f seconds' % (s / len(s))

    my_orb.close()
