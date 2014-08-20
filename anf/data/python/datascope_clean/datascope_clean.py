import sys
import os
antelope_lib = '%s/data/python' % os.environ['ANTELOPE']
remove_flag = False
if antelope_lib not in sys.path:
    remove_flag = True
    sys.path.append(antelope_lib)
import antelope.datascope as ds 
sys.path.remove(antelope_lib)

if __name__ == '__main__':
    print 'This is a library only!'
    sys.exit(-1)

class DbPtrClean(ds.Dbptr):
    """
    A sub-class of antelope.datascope.Dbptr which cleans up after itself.
    """
    def __init__(self, dbptr):
        self.dbptr = dbptr
        self.database = self.dbptr.database
        self.table = self.dbptr.table
        self.field = self.dbptr.field
        self.record = self.dbptr.record

    def subset_clean(self, *args, **kwargs):
        tmp = self.dbptr.subset(*args, **kwargs)
        #self.dbptr.free()
        self.dbptr = tmp
        self.database = self.dbptr.database
        self.table = self.dbptr.table
        self.field = self.dbptr.field
        self.record = self.dbptr.record

    def lookup(self, *args, **kwargs):
        return DbPtrClean(self.dbptr.lookup(*args, **kwargs))












def group_clean(dbptr, *args, **kwargs):
    ret = dbptr.group(*args, **kwargs)
    dbptr.free()
    return ret

def join_clean(dbptr, *args, **kwargs):
    ret = dbptr.join(*args, **kwargs)
    dbptr.free()
    return ret

def list2subset_clean(dbptr, *args, **kwargs):
    ret = dbptr.list2subset(*args, **kwargs)
    dbptr.fre()
    return ret

def nojoin_clean(dbptr, *args, **kwargs):
    ret = dbptr.nojoin(*args, **kwargs)
    dbptr.free()
    return ret

def process_clean(dbptr, *args, **kwargs):
    ret = dbptr.process(*args, **kwargs)
    dbptr.free()
    return ret

def separate_clean(dbptr, *args, **kwargs):
    ret = dbptr.separate(*args, **kwargs)
    dbptr.free()
    return ret

def sever_clean(dbptr, *args, **kwargs):
    ret = dbptr.sever(*args, **kwargs)
    dbptr.free()
    return ret

def sort_clean(dbptr, *args, **kwargs):
    ret = dbptr.sort(*args, **kwargs)
    dbptr.free()
    return ret

def subset_clean(dbptr, *args, **kwargs):
    ret = dbptr.subset(*args, **kwargs)
    #dbptr.free()
    return ret

def theta_clean(dbptr, *args, **kwargs):
    ret = dbptr.theta(*args, **kwargs)
    dbptr.free()
    return ret
