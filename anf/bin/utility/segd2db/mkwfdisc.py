import os
from segd2db import SegD
#for path in ('/anf/ANZA/work/sjfz_500Hz/stage1/', '/anf/ANZA/work/sjfz_500Hz/stage2/'):
for path in ('/anf/ANZA/work/sjfz_500Hz/stage1/',):# '/anf/ANZA/work/sjfz_500Hz/stage2/'):
    #for a_file in sorted(os.listdir(path)):
    for a_file in ('R19_20.1.0.rg16', ):
        print '%s%s' % (path, a_file)
        segd = SegD('%s%s' % (path, a_file))
        sta = a_file.split('.')[0]
        sta = '%s%s' % (sta.split('_')[0], sta.split('_')[1])
        #segd.write_2_wfdisc('/Users/mcwhite/staging/SGBF_SEGD/SGBF_%s' % sta, sta, path, a_file)
        segd.write_2_wfdisc('/Users/mcwhite/staging/SGBF_1920_stage1/SGBF_%s' % sta, sta, path, a_file)

