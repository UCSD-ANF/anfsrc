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

mxdbuf = 1.0 #This is the maximum internal data buffer size in GB

st2cc = {2: 'Z', 3: 'I', 4: 'C'} #This dictionary maps the
#'Sensor type on this trace' field of the 1st 32-byte Extended Trace
#Header Block to a component code (ie. Z, N, E)

rdir = '/Users/mcwhite/sandbox/wfs/segd' #Input directory
wdir = '/Users/mcwhite/sandbox/wfs/miniSEED' #Output Directory

nthreads = 1

def worker(args):
    sta, path, wdir, mxdbuf, st2cc = args
    segd = SegD(path, 'ZB', sta, 1000.0, mxdbuf, st2cc)
    for i in range(segd.n_channels):
        while segd.fill_buffer(0.00003725290298461914):
            segd.write_buffer(wdir)
        segd.dump_buffer(wdir)

if __name__ == '__main__':
    stas, paths = [], []
    for f in sorted(os.listdir(rdir)):
        stas += [f.split('.')[0]]
        paths += ['%s/%s' % (rdir, f)]
    args = [(stas[i], paths[i], wdir, mxdbuf, st2cc) for i in range(len(stas))]
    pool = Pool(processes=nthreads)
    pool.map(worker, args)

