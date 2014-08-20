import sys
import os
sys.path.append('%s/data/python' % os.environ['ANTELOPE'])
import antelope.datascope as ds
import datascope_clean as dsc
db = ds.dbopen('/anf/ANZA/work/white/fm3d/test_db/working/anza_2013', 'r')
db = dsc.DbPtrClean(db)
while True:
    tbl_origin = db.lookup(table='origin')
    print tbl_origin.record_count
    tbl_origin.subset_clean('time >= _2013361 00:00:00_')
    print tbl_origin.record_count
    tbl_origin.record = 0
    print tbl_origin.getv('lat')[0], '\n\n'
