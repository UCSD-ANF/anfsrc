#!/usr/bin/env python
"""Describe file"""
from datetime import datetime

from antelope.datascope import closing, dbopen, freeing


fields = [
    "sta",
    "ondate",
    "lat",
    "lon",
    "elev",
    "lddate",
]

DB_PATH = ''


def store(sta, ondate, lat, lon, elev):
    lddate = datetime.now()
    row = zip(fields, [sta, ondate, lat, lon, elev, lddate])
    db = dbopen(DB_PATH)
    with closing(db):
        site_table = db.lookup(table='site')
        site_view = site_table.subset('sta == {}'.format(sta))
        with freeing(site_view):
            try:
                rowptr = site_view.iter_record().next()
            except StopIteration:
                site_table.addv(*row)
            else:
                old_row = dict(zip(fields, rowptr.getv(*fields)))
                if lddate > old_row['lddate']:
                    rowptr.putv(*row)
                return old_row


# todo Ok so the table looks like just a normal CSS 3.0 schema with no extensions used.
# The existing SB is only populating the site table. Frank would like the snetsta table
# populated as well which will give you net
