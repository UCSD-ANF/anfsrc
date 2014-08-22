import sys
import os
from copy import deepcopy
antelope_lib = '%s/data/python' % os.environ['ANTELOPE']
remove_flag = False
if antelope_lib not in sys.path:
    remove_flag = True
    sys.path.append(antelope_lib)
import antelope.datascope as ds 
import antelope._datascope as _ds 
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
        self.view_tables = None
        self._update(dbptr)

    def __str__(self):
        return "<DbPtrClean database=%d,  table=%d,  field=%d, record=%d>"\
                % (self.database, self.table, self.field, self.record)


    def set_database(self, value):
        if not isinstance(value, int):
            raise TypeError('set_database() - value must be an integer')
        self.dbptr[0] = value
        self.database = value

    def set_table(self, value):
        if not isinstance(value, int):
            raise TypeError('set_table() - value must be an integer')
        self.dbptr[1] = value
        self.table = value

    def set_field(self, value):
        if not isinstance(value, int):
            raise TypeError('set_field() - value must be an integer')
        self.dbptr[2] = value
        self.field = value

    def set_record(self, value):
        if not isinstance(value, int):
            raise TypeError('set_record() - value must be an integer')
        self.dbptr[3] = value
        self.record = value

    def set_record_dep(self, value):
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
        #return self.dbptr.free(*args, **kwargs)
        return _ds._dbfree(self.dbptr, *args, **kwargs)

    def get(self, *args, **kwargs):
        return self.dbptr.get(*args, **kwargs)

    def get_range(self, *args, **kwargs):
        return self.dbptr.get_range(*args, **kwargs)

    def getv_dep(self, *args, **kwargs):
        return self.dbptr.getv(*args, **kwargs)

    def getv(self, *args, **kwargs):
        #return self.dbptr.getv(*args, **kwargs)
        #view_tables = _ds._dbquery(self.dbptr, _ds.dbVIEW_TABLES)
        #if len(view_tables) == 1:
        #    return _ds._dbgetv(self.dbptr, view_tables[0], *args)[1]
        #else:
        #    return_values = []
        #    field_tables = {}
        #    for arg in args:
        #        split_arg = arg.split('.')
        #        if len(split_arg) == 1:
        #            tmp_dbptrcln = self.copy()
        #            for my_table in view_tables:
        #                tmp_dbptrcln.lookup('', my_table, '', '')
        #                if arg in tmp_dbptrcln.query(_ds.dbTABLE_FIELDS):
        #                    table = my_table
        #                    break
        #        else:
        #            table = split_arg[0]
        #            arg = split_arg[1]
        #        if table not in field_tables:
        #            field_tables[table] = [arg]
        #        else:
        #            field_tables[table].append(arg)
        #    for table in field_tables:
        #        args = tuple(field_tables[table])
        #        return_values += _ds._dbgetv(self.dbptr,
        #                                     table)
        #        #return_values += _ds._dbgetv(self.dbptr,
        #        #                             table,
        #        #                             *args)[1]
        #    return return_values
            return _ds._dbgetv(self.dbptr, 'origin', *args)[1]

    def group(self, *args, **kwargs):
        return self._update(self.dbptr.group(self, *args, **kwargs))

    def group_clean(self, *args, **kwargs):
        return self._update_cleanly(self.dbptr.group(self, *args, **kwargs))

    def iter_record(self, *args, **kwargs):
        return self.dbptr.iter_record(*args, **kwargs)

    def join(self, *args, **kwargs):
        return self._update(self.dbptr.join(*args, **kwargs))

    def join_clean(self, table, pattern1=None, pattern2=None, outer=False, name=None):
        #return self._update_cleanly(self.dbptr.join(*args, **kwargs))
        tmp_dbptrcln = self.copy()
        tmp_dbptrcln.lookup('', table, '', '')
        return_value =  self._update_cleanly(_ds._dbjoin(self.dbptr,
                                                         tmp_dbptrcln.dbptr,
                                                         pattern1,
                                                         pattern2,
                                                         outer,
                                                         name))
        return return_value

    def join_clean_dep(self, *args, **kwargs):
        return self._update_cleanly(self.dbptr.join(*args, **kwargs))

    def list2subset(self, *args, **kwargs):
        return self._update(self.dbptr.list2subset(*args, **kwargs))

    def list2subset_clean(self, *args, **kwargs):
        return self._update_cleanly(self.dbptr.list2subset(*args, **kwargs))

    def lookup(self, *args):
        return self._update(_ds._dblookup(self.dbptr, *args))
        #return self._update(self.dbptr.lookup(*args, **kwargs))

    def lookup_dep(self, *args, **kwargs):
        return self._update(self.dbptr.lookup(*args, **kwargs))

    def lookup_clean(self, *args):
        #return self._update_cleanly(self.dbptr.lookup(*args, **kwargs))
        return self._update_cleanly(_ds._dblookup(self.dbptr, *args))

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

    def query_dep(self, *args, **kwargs):
        return self.dbptr.query(*args, **kwargs)

    def query(self, *args, **kwargs):
        #return self.dbptr.query(*args, **kwargs)
        return _ds._dbquery(self.dbptr, *args, **kwargs)

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
        #return self._update(self.dbptr.subset(*args, **kwargs))
        return self._update(_ds._dbsubset(self.dbptr, *args, **kwargs))

    def subset_clean_dep(self, *args, **kwargs):
        return self._update_cleanly(self.dbptr.subset(*args, **kwargs))

    def subset_clean(self, expr):
        #return self._update_cleanly(self.dbptr.subset(*args, **kwargs))
        #return self._update_cleanly(_ds._dbsubset(self.dbptr, *args, **kwargs))
        return self._update_cleanly(_ds._dbsubset(self.dbptr, expr, 'None'))

    def theta(self, *args, **kwargs):
        return self._update(self.dbptr.theta(*args, **kwargs))

    def theta_clean(self, *args, **kwargs):
        return self._update_cleanly(self.dbptr.theta(*args, **kwargs))

    def to_pipe(self, *args, **kwargs):
        return self.dbptr.to_pipe(*args, **kwargs)

    def _update_cleanly(self, new_dbptr):
        #if self.dbptr.query(ds.dbTABLE_IS_VIEW):
        #    self.dbptr.free()
        if _ds._dbquery(self.dbptr, _ds.dbTABLE_IS_VIEW):
            _ds._dbfree(self.dbptr)
        return self._update(new_dbptr)

    def _update(self, new_dbptr):
        self.dbptr = new_dbptr
        self.database = self.dbptr[0]
        self.table = self.dbptr[1]
        self.field = self.dbptr[2]
        self.record = self.dbptr[3]
        return self

class DbPtrClean_dep(DbPtrClean):
    def __init__(self, dbptr):
        self.dbptr = dbptr
        self.database = self.dbptr.database
        self.table = self.dbptr.table
        self.field = self.dbptr.field
        self.record = self.dbptr.record

    def free(self, *args, **kwargs):
        return self.dbptr.free(*args, **kwargs)

    def _update_cleanly(self, new_dbptr):
        #if self.dbptr.query(ds.dbTABLE_IS_VIEW):
        #    self.dbptr.free()
        if self.dbptr.query(ds.dbTABLE_IS_VIEW):
            self.dbptr.free()
        return self._update(new_dbptr)

    def _update(self, new_dbptr):
        self.dbptr = new_dbptr
        self.database = self.dbptr.database
        self.table = self.dbptr.table
        self.field = self.dbptr.field
        self.record = self.dbptr.record
        return self

def dbopen(*args, **kwargs):
    return DbPtrClean(_ds._dbopen(*args, **kwargs)[1])

def dbopen_dep(*args, **kwargs):
    return DbPtrClean_dep(ds.dbopen(*args, **kwargs))
