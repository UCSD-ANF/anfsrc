"""
This is a short script to convert 3-component SEG-D Nodal data,
collected during the Blackburn deployment (December 2015), to miniSEED
format. The SegD class of the seispy.segd module was written to provide
I/O functionality and can be re-used for future experiments.
"""
import sys
import os
sys.path.append('%s/data/python' % os.environ['ANF'])
from seispy.segd import SegD
from multiprocessing import Pool
from time import time
from os.path import isfile

mxdbuf = 0.35 #This is the maximum internal data buffer size in GB

st2cc = {2: 'Z', 3: 'N', 4: 'E'} #This dictionary maps the
#'Sensor type on this trace' field of the 1st 32-byte Extended Trace
#Header Block to a component code (ie. Z, N, E)

rdir = '/anf/ANZA/SJFZ/nodal_blackburn/wfs_from_Amir' #Input directory
wdir = '/anf/ANZA/SJFZ/nodal_blackburn/miniseed' #Output Directory

samprate = 1000.0

chanprfx = 'GP'

nthreads = 10

def worker(args):
    try:
        sta, path, wdir, samprate, chanprfx, mxdbuf, st2cc = args
        segd = SegD(path, 'ZB', sta, samprate, chanprfx, mxdbuf, st2cc)
        for i in range(segd.n_channels):
            while segd.fill_buffer(0.00003725290298461914):
                segd.write_buffer(wdir)
            segd.dump_buffer(wdir)
        done_file = open('%s/done/%s' % (wdir, sta), 'w')
        done_file.write('%f' % time())
        done_file.close()
    except ValueError as err:
        fname = '%s/err/%s' % (wdir, sta)
        if isfile(fname):
            err_file = open('%s/err/%s' % (wdir, sta), 'r+')
        else:
            err_file = open('%s/err/%s' % (wdir, sta), 'w')
        err_file.write('%f\n' % time())
        err_file.close()
        worker(args)

if __name__ == '__main__':
    stas, paths = [], []
    for f in sorted(os.listdir(rdir)):
        sta = f.split('.')[0]
        if isfile('%s/done/%s' % (wdir, sta)):
            continue
        stas += [sta]
        paths += ['%s/%s' % (rdir, f)]
    args = [(stas[i], paths[i], wdir, samprate, chanprfx, mxdbuf, st2cc) for i in range(len(stas))]
    pool = Pool(processes=nthreads)
    pool.map(worker, args)

