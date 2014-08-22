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

class DblookupError(ds.DatascopeError):
    def __init__(self, *args):
        if args:
            self.message = args[0]

    def __str__(self):
        return "%s\nUSAGE\n-----\nDbPtrCln.lookup('database', 'table', "\
                "'field', 'record')\nOR\nDbPtrCln.lookup(table)\nOR\n"\
                "DbPtrCln.lookup(table='table')" % self.message

class DbPtrClean():
    """
    A sub-class of antelope.datascope.Dbptr which cleans up after itself.
    """
    def __init__(self, dbptr):
        self.field_tables = {}
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

    def add(self, *args, **kwargs):
        #return self.dbptr.add(*args, **kwargs)
        return _ds._dbadd(self.dbptr, *args, **kwargs)


    def addnull(self, *args, **kwargs):
        #return self.dbptr.addnull(*args, **kwargs)
        return _ds._dbaddnull(self.dbptr, *args, **kwargs)

    def addv(self, *args, **kwargs):
        #return self.dbptr.addv(*args, **kwargs)
        return _ds._dbaddv(self.dbptr, *args, **kwargs)

    def copy(self):
        return deepcopy(self)

    def close(self, *args, **kwargs):
        #return self.dbptr.close(*args, **kwargs)
        return _ds._dbclose(self.dbptr, *args, **kwargs)

    def crunch(self, *args, **kwargs):
        #return self.dbptr.crunch(*args, **kwargs)
        return _ds._dbcrunch(self.dbptr, *args, **kwargs)

    def delete(self, *args, **kwargs):
        #return self.dbptr.delete(*args, **kwargs)
        return _ds._dbdelete(self.dbptr, *args, **kwargs)

    def destroy(self, *args, **kwargs):
        #return self.dbptr.destroy(*args, **kwargs)
        return _ds._dbdestroy(self.dbptr, *args, **kwargs)

    def ex_eval(self, *args, **kwargs):
        #return self.dbptr.ex_eval(*args, **kwargs)
        return _ds._dbex_eval(self.dbptr, *args, **kwargs)

    def extfile(self, *args, **kwargs):
        #return self.dbptr.extfile(*args, **kwargs)
        return _ds._dbextfile(self.dbptr, *args, **kwargs)

    def filename(self, *args, **kwargs):
        #return self.dbptr.filename(*args, **kwargs)
        return _ds._dbfilename(self.dbptr, *args, **kwargs)

    def find(self, *args, **kwargs):
        #return self.dbptr.find(*args, **kwargs)
        return _ds._dbfind(self.dbptr, *args, **kwargs)

    def find_join_keys(self, *args, **kwargs):
        #return self.dbptr.find_join_keys(*args, **kwargs)
        return _ds._dbfind_join_keys(self.dbptr, *args, **kwargs)

    def find_join_tables(self, *args, **kwargs):
        #return self.dbptr.find_join_tables(*args, **kwargs)
        return _ds._dbfind_join_tables(self.dbptr, *args, **kwargs)

    def free(self, *args, **kwargs):
        #return self.dbptr.free(*args, **kwargs)
        return _ds._dbfree(self.dbptr, *args, **kwargs)

    def get(self, *args, **kwargs):
        #return self.dbptr.get(*args, **kwargs)
        return _ds._dbget(*args, **kwargs)

    def get_range(self, *args, **kwargs):
        #return self.dbptr.get_range(*args, **kwargs)
        return _ds._dbget_range(self.dbptr, *args, **kwargs)

    def getv(self, *args, **kwargs):
        results = []
        for table in self.field_tables:
            results += _ds._dbgetv(self.dbptr,
                                   table,
                                   *[arg for arg in args if arg in\
                                           self.field_tables[table]])[1]
        return results

    def group(self, *args, **kwargs):
        return self._update(_ds._dbgroup(self.dbptr, *args, **kwargs))

    def group_clean(self, *args, **kwargs):
        return self._update_cleanly(_ds._dbgroup(self.dbptr, *args, **kwargs))

    def join(self, table, pattern1=None, pattern2=None, outer=False, name=None):
        tmp_dbptrcln = self.copy()
        tmp_dbptrcln.lookup('', table, '', '')
        return self._update(_ds._dbjoin(self.dbptr,
                                        tmp_dbptrcln.dbptr,
                                        pattern1,
                                        pattern2,
                                        outer,
                                        name))

    def join_clean(self, table, pattern1=None, pattern2=None, outer=False, name=None):
        #return self._update_cleanly(self.dbptr.join(*args, **kwargs))
        tmp_dbptrcln = self.copy()
        tmp_dbptrcln.lookup('', table, '', '')
        return self._update_cleanly(_ds._dbjoin(self.dbptr,
                                                tmp_dbptrcln.dbptr,
                                                pattern1,
                                                pattern2,
                                                outer,
                                                name))

    def list2subset(self, *args, **kwargs):
        return self._update(_ds._dblist2subset(self.dbptr, *args, **kwargs))

    def list2subset_clean(self, *args, **kwargs):
        return self._update_cleanly(_ds._dblist2subset(self.dbptr,
                                                       *args,
                                                       **kwargs))

    def _parse_lookup_args(self, *args, **kwargs):
        if len(args) == 4:
            for arg in args:
                if not isinstance(arg, str):
                    raise DblookupError("Positional arguments must be string "\
                                        "values.")
        elif len(args) == 1:
            if not isinstance(args[0], str):
                    raise DblookupError("Positional argument must be a string "\
                                        "value.")
            args = ('', args[0], '', '')
        elif len(args) == 0 and len(kwarg.keys()) != 0:
            if not 'database' in kwargs and\
                not 'table' in kwargs and\
                not 'field' in kwargs and\
                not 'record' in kwargs:
                    raise DblookupError("Must supply at least one of the "\
                            "following keyword arguments (database, table, "\
                            "field, record)."
            for kw in ('database', 'table', 'field', 'record'):
                if kw not in kwargs:
                    kwargs[kw] = ''
            args = (kwargs['database'],
                    kwargs['table'],
                    kwargs['field'],
                    kwargs['record'])
        else:
            raise DblookupError
        return args

    def lookup(self, *args, **kwargs):
        return self._update(_ds._dblookup(self.dbptr,
                            *_parse_lookup_args(*args, **kwargs)))

    def lookup_clean(self, *args, **kwargs):
        #return self._update_cleanly(self.dbptr.lookup(*args, **kwargs))
        return self._update_cleanly(_ds._dblookup(self.dbptr,
                                    *_parse_lookup_args(*args, **kwargs)))

    def map_seed_chanloc(self, *args, **kwargs):
        return _ds._dbmap_seed_chanloc(self.dbptr, *args, **kwargs)

    def map_seed_netsta(self, *args, **kwargs):
        return _ds._dbmap_seed_netsta(self.dbptr, *args, **kwargs)

    def mark(self, *args, **kwargs):
        return _ds._dbmark(self.dbptr, *args, **kwargs)

    def matches(self, *args, **kwargs):
        return _ds._dbmatches(self.dbptr, *args, **kwargs)

    def nextid(self, *args, **kwargs):
        return _ds._dbnextid(self.dbptr, *args, **kwargs)

    def nojoin(self, *args, **kwargs):
        return self._update(_ds._dbnojoin(self.dbptr, *args, **kwargs))

    def nojoin_clean(self, *args, **kwargs):
        return self._update_cleanly(_ds._dbnojoin(self.dbptr, *args, **kwargs))

    def process(self, *args, **kwargs):
        return self._update(_ds._dbprocess(self.dbptr, *args, **kwargs))

    def process_clean(self, *args, **kwargs):
        return self._update_cleanly(_ds._dbprocess(self.dbptr, *args, **kwargs))

    def put(self, *args, **kwargs):
        return _ds._dbput(self.dbptr, *args, **kwargs)

    def putv(self, *args, **kwargs):
        return _ds._dbputv(self.dbptr, *args, **kwargs)

    def query(self, *args, **kwargs):
        return _ds._dbquery(self.dbptr, *args, **kwargs)

    def save_view(self, *args, **kwargs):
        return _ds._dbsave_view(self.dbptr, *args, **kwargs)

    def seed_loc(self, *args, **kwargs):
        return _ds._dbseed_loc(self.dbptr, *args, **kwargs)

    def seed_net(self, *args, **kwargs):
        return _ds._dbseed_net(self.dbptr, *args, **kwargs)

    def select(self, *args, **kwargs):
        return _ds._dbselect(self.dbptr, *args, **kwargs)

    def separate(self, *args, **kwargs):
        return self._update(_ds._dbseparate(self.dbptr, *args, **kwargs))

    def separate_clean(self, *args, **kwargs):
        return self._update_cleanly(_ds._dbseparate(self.dbptr, *args, **kwargs))

    def sever(self, *args, **kwargs):
        return self._update(_ds._dbsever(self.dbptr, *args, **kwargs))

    def sever_clean(self, *args, **kwargs):
        return self._update_cleanly(_ds._dbsever(self.dbptr, *args, **kwargs))

    def sort(self, *args, **kwargs):
        return self._update(_ds._dbsort(self.dbptr, *args, **kwargs))

    def sort_clean(self, *args, **kwargs):
        return self._update_cleanly(_ds._dbsort(self.dbptr, *args, **kwargs))

    def subset(self, *args, **kwargs):
        #return self._update(_ds._dbsubset(*args, **kwargs))
        return self._update(_ds._dbsubset(self.dbptr, *args, **kwargs))

    def subset_clean(self, expr):
        #return self._update_cleanly(self.dbptr.subset(*args, **kwargs))
        #return self._update_cleanly(_ds._dbsubset(self.dbptr, *args, **kwargs))
        return self._update_cleanly(_ds._dbsubset(self.dbptr, expr, 'None'))

    def theta(self, *args, **kwargs):
        return self._update(_ds._dbtheta(self.dbptr, *args, **kwargs))

    def theta_clean(self, *args, **kwargs):
        return self._update_cleanly(_ds._dbtheta(self.dbptr, *args, **kwargs))

    def to_pipe(self, *args, **kwargs):
        return _ds._db2pipe(self.dbptr, *args, **kwargs)

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
        if self.table != _ds.dbALL:
            if not _ds._dbquery(self.dbptr, _ds.dbTABLE_IS_VIEW):
                table = _ds._dbquery(self.dbptr, _ds.dbTABLE_NAME)
                self.field_tables[table] = _ds._dbquery(self.dbptr,
                                                        _ds.dbTABLE_FIELDS)
            else:
                view_tables = _ds._dbquery(self.dbptr, _ds.dbVIEW_TABLES)
                used_fields = []
                for table in view_tables:
                    tmp_dbptr = _ds._dblookup(self.dbptr, '', table, '', '')
                    fields = _ds._dbquery(tmp_dbptr, _ds.dbTABLE_FIELDS)
                    self.field_tables[table] = [field if field not in\
                            used_fields else '%s.%s' % (table, field)\
                            for field in fields]
                    used_fields += list(fields)
        return self

def dbopen(*args, **kwargs):
    return DbPtrClean(_ds._dbopen(*args, **kwargs)[1])
