from antelope.datascope import closing, dbopen
from antelope.stock import now

def _parse_args():
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('db', type=str, help='database')
    return parser.parse_args()

def _get_prefor_duplicate(event):
    view = event.join('origin')
    tmp = view.subset('orid == prefor')
    if tmp.record_count == 0:
        print "\n**COMPLAIN**: please set preferred origin for evid - %d" % evid
        view.free()
        return None, None
    tmp.record = 0
    plat, plon, pdepth, ptime, prefor, pauth = tmp.getv('lat',
                                                        'lon',
                                                        'depth',
                                                        'time',
                                                        'orid',
                                                        'origin.auth')
    tmp.free()
    tmp = view.subset('orid != prefor')
    view.free()
    view = tmp
    for origin in view.iter_record():
        lat, lon, depth, time, orid, auth = origin.getv('lat',
                                                        'lon',
                                                        'depth',
                                                        'time',
                                                        'orid',
                                                        'origin.auth')
        if lat == plat and\
           lon == plon and\
           depth == pdepth and\
           time == ptime and\
           auth == pauth:
               view.free()
               return prefor, orid
    view.free()
    return None, None

def _reassoc_prefor(db, prefor, orid):
    view = db.lookup(table='assoc')
    tmp = view.subset('orid == %d' % prefor)
    nass_old = tmp.record_count
    tmp.free()
    view = view.subset('orid == %d' % orid)
    nass = nass_old
    for assoc in view.iter_record():
        assoc.putv(('orid', prefor))
        nass += 1
    view.free()
    view = db.lookup(table='origin')
    view.record = view.find('orid == %d' % orid)
    view.delete()
    view = db.lookup(table='origin')
    view.record = view.find('orid == %d' % prefor)
    view.putv(('nass', nass))
    evid = view.getv('evid')[0]
    print "\tprefor solution for evid: %d had %d associated phases and "\
            "now has %d associated phases." % (evid, nass_old, nass)
    return 0

if __name__ == '__main__':
    args = _parse_args()
    with closing(dbopen(args.db, 'r+')) as db:
        tbl_event = db.lookup(table='event')
        for event in tbl_event.iter_record():
            evid = event.getv('evid')[0]
            event = tbl_event.subset('evid == %d' % evid)
            prefor, prefor_duplicate = _get_prefor_duplicate(event)
            if prefor_duplicate:
                print "\nprefor solution for evid: %d is duplicated by orid: "\
                        "%d. Consolidating associated arrivals..."\
                        % (evid, prefor_duplicate)
                _reassoc_prefor(db, prefor, prefor_duplicate)
