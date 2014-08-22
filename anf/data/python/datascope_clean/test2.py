import time
import sys
import os
sys.path.append('%s/data/python' % os.environ['ANTELOPE'])
import datascope_clean as dsc

def print_mem_use(match):
    pipe = os.popen('ps -o pmem,comm')
    print pipe.readline().rstrip()
    for line in pipe:
        if line.find(match) != -1:
            print line

db = dsc.dbopen('/anf/ANZA/work/white/fm3d/test_db/working/anza_2013', 'r')
tbl_origin = db.lookup('', 'origin', '', '')
tstart = time.time()
for j in range(10000):
    print j
    view = tbl_origin.copy()
    #view.subset('time >= _2013361 00:00:00_')
    #view.subset('time >= _2013362 00:00:00_')
    view.subset_clean('time >= _2013361 00:00:00_')
    view.subset_clean('time >= _2013362 00:00:00_')
    for i in range(view.query(dsc.dbRECORD_COUNT)):
        view.set_record(i)
        lat, lon = view.getv('lat', 'lon')
    view.free()
print_mem_use('python')
db.close()
print 'Updated version - %f seconds' % (time.time() - tstart)
