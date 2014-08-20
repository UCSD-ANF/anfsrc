import sys
import os
from copy import deepcopy
antelope_lib = '%s/data/python' % os.environ['ANTELOPE']
remove_flag = False
if antelope_lib not in sys.path:
    remove_flag = True
    sys.path.append(antelope_lib)
import antelope.datascope as ds 
for thing in dir(ds):
    locals()[thing] = getattr(ds, thing)

sys.path.remove(antelope_lib)

if __name__ == '__main__':
    print 'This is a library only!'
    sys.exit(-1)

class DbPtrClean():
    """
    A sub-class of antelope.datascope.Dbptr which cleans up after itself.
    """
    def __init__(self, dbptr):
        self.dbptr = dbptr
        self.database = self.dbptr.database
        self.table = self.dbptr.table
        self.field = self.dbptr.field
        self.record = self.dbptr.record

    def set_database(self, value):
        if not isinstance(value, int):
            raise TypeError('set_database() - value must be an integer')
        self.dbptr.database = value
        self.database = value

    def set_table(self, value):
        if not isinstance(value, int):
            raise TypeError('set_table() - value must be an integer')
        self.dbptr.table = value
        self.table = value

    def set_field(self, value):
        if not isinstance(value, int):
            raise TypeError('set_field() - value must be an integer')
        self.dbptr.field = value
        self.field = value

    def set_record(self, value):
        if not isinstance(value, int):
            raise TypeError('set_record() - value must be an integer')
        self.dbptr.record = value
        self.record = value

    def add(self, *args, **kwargs):
        return self.dbptr.add(*args, **kwargs)

    def addnull(self, *args, **kwargs):
        return self.dbptr.addnull(*args, **kwargs)

    def addv(self, *args, **kwargs):
        return self.dbptr.addv(*args, **kwargs)

    def copy(self):
        return deepcopy(self)

    def close(self, *args, **kwargs):
        return self.dbptr.close(*args, **kwargs)

    def crunch(self, *args, **kwargs):
        return self.dbptr.crunch(*args, **kwargs)

    def delete(self, *args, **kwargs):
        return self.dbptr.delete(*args, **kwargs)

    def destroy(self, *args, **kwargs):
        return self.dbptr.destroy(*args, **kwargs)

    def ex_eval(self, *args, **kwargs):
        return self.dbptr.ex_eval(*args, **kwargs)

    def extfile(self, *args, **kwargs):
        return self.dbptr.extfile(*args, **kwargs)

    def filename(self, *args, **kwargs):
        return self.dbptr.filename(*args, **kwargs)

    def find(self, *args, **kwargs):
        return self.dbptr.find(*args, **kwargs)

    def find_join_keys(self, *args, **kwargs):
        return self.dbptr.find_join_keys(*args, **kwargs)

    def find_join_tables(self, *args, **kwargs):
        return self.dbptr.find_join_tables(*args, **kwargs)

    def free(self, *args, **kwargs):
        return self.dbptr.free(*args, **kwargs)

    def get(self, *args, **kwargs):
        return self.dbptr.get(*args, **kwargs)

    def get_range(self, *args, **kwargs):
        return self.dbptr.get_range(*args, **kwargs)

    def getv(self, *args, **kwargs):
        return self.dbptr.getv(*args, **kwargs)

    def group(self, *args, **kwargs):
        return self._update(self.dbptr.group(self, *args, **kwargs))

    def group_clean(self, *args, **kwargs):
        return self._update_cleanly(self.dbptr.group(self, *args, **kwargs))

    def iter_record(self, *args, **kwargs):
        return self.dbptr.iter_record(*args, **kwargs)

    def join(self, *args, **kwargs):
        return self._update(self.dbptr.join(*args, **kwargs))

    def join_clean(self, *args, **kwargs):
        return self._update_cleanly(self.dbptr.join(*args, **kwargs))

    def list2subset(self, *args, **kwargs):
        return self._update(self.dbptr.list2subset(*args, **kwargs))

    def list2subset_clean(self, *args, **kwargs):
        return self._update_cleanly(self.dbptr.list2subset(*args, **kwargs))

    def lookup(self, *args, **kwargs):
        return self._update(self.dbptr.lookup(*args, **kwargs))

    def lookup_clean(self, *args, **kwargs):
        return self._update_cleanly(self.dbptr.lookup(*args, **kwargs))

    def map_seed_chanloc(self, *args, **kwargs):
        return self.dbptr.map_seed_chanloc(*args, **kwargs)

    def map_seed_netsta(self, *args, **kwargs):
        return self.dbptr.map_seed_netsta(*args, **kwargs)

    def mark(self, *args, **kwargs):
        return self.dbptr.mark(*args, **kwargs)

    def matches(self, *args, **kwargs):
        return self.dbptr.matches(*args, **kwargs)

    def nextid(self, *args, **kwargs):
        return self.dbptr.nextid(*args, **kwargs)

    def nojoin(self, *args, **kwargs):
        return self._update(self.dbptr.nojoin(*args, **kwargs))

    def nojoin_clean(self, *args, **kwargs):
        return self._update_cleanly(self.dbptr.nojoin(*args, **kwargs))

    def process(self, *args, **kwargs):
        return self._update(self.dbptr.process(*args, **kwargs))

    def process_clean(self, *args, **kwargs):
        return self._update_cleanly(self.dbptr.process(*args, **kwargs))

    def put(self, *args, **kwargs):
        return self.dbptr.put(*args, **kwargs)

    def putv(self, *args, **kwargs):
        return self.dbptr.putv(*args, **kwargs)

    def query(self, *args, **kwargs):
        return self.dbptr.query(*args, **kwargs)

    def save_view(self, *args, **kwargs):
        return self.dbptr.save_view(*args, **kwargs)

    def seed_loc(self, *args, **kwargs):
        return self.dbptr.seed_loc(*args, **kwargs)

    def seed_net(self, *args, **kwargs):
        return self.dbptr.seed_net(*args, **kwargs)

    def select(self, *args, **kwargs):
        return self.dbptr.select(*args, **kwargs)

    def separate(self, *args, **kwargs):
        return self._update(self.dbptr.separate(*args, **kwargs))

    def separate_clean(self, *args, **kwargs):
        return self._update_cleanly(self.dbptr.separate(*args, **kwargs))

    def sever(self, *args, **kwargs):
        return self._update(self.dbptr.sever(*args, **kwargs))

    def sever_clean(self, *args, **kwargs):
        return self._update_cleanly(self.dbptr.sever(*args, **kwargs))

    def sort(self, *args, **kwargs):
        return self._update(self.dbptr.sort(*args, **kwargs))

    def sort_clean(self, *args, **kwargs):
        return self._update_cleanly(self.dbptr.sort(*args, **kwargs))

    def subset(self, *args, **kwargs):
        return self._update(self.dbptr.subset(*args, **kwargs))

    def subset_clean(self, *args, **kwargs):
        return self._update_cleanly(self.dbptr.subset(*args, **kwargs))

    def theta(self, *args, **kwargs):
        return self._update(self.dbptr.theta(*args, **kwargs))

    def theta_clean(self, *args, **kwargs):
        return self._update_cleanly(self.dbptr.theta(*args, **kwargs))

    def to_pipe(self, *args, **kwargs):
        return self.dbptr.to_pipe(*args, **kwargs)

    def _update_cleanly(self, new_dbptr):
        if self.dbptr.query(ds.dbTABLE_IS_VIEW):
            self.dbptr.free()
        return self._update(new_dbptr)

    def _update(self, new_dbptr):
        self.dbptr = new_dbptr
        self.database = self.dbptr.database
        self.table = self.dbptr.table
        self.field = self.dbptr.field
        self.record = self.dbptr.record
        return 0

def dbopen(*args, **kwargs):
    return DbPtrClean(ds.dbopen(*args, **kwargs))
