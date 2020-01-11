#!/usr/bin/env python
"""Describe file"""
from datetime import datetime
import logging

from antelope.datascope import closing, dbopen, freeing


log = logging.getLogger(__name__)


fields = [
    "sta",
    "ondate",
    "lat",
    "lon",
    "elev",
    "lddate",
]


snetsta_fields = [
    'snet',
    'fsta',
    'sta',
    'lddate',
]

dbpath=None

def convtime(dt):
    return dt.strftime('%s')


def store(net, sta, ondate, lon, lat, elev):
    lddate = datetime.now()
    row = zip(fields, [sta, ondate.strftime('%Y%j'), lat, lon, elev / 1000.0,
                        convtime(lddate)])
    db = dbopen(dbpath, 'r+')
    with closing(db):
        snetsta_table = db.lookup(table='snetsta')
        snetsta_view = snetsta_table.subset("sta == '{}'".format(sta))
        log.debug("snetsta_view %s", snetsta_view)
        with freeing(snetsta_view):
            try:
                rowptr = snetsta_view.iter_record().next()
            except StopIteration:
                snetsta_table.addv(*zip(snetsta_fields, [net, sta, sta, convtime(lddate)]))
                log.info("added snetsta record")

        site_table = db.lookup(table='site')
        site_view = site_table.subset("sta == '{}'".format(sta))
        log.debug("site_view %s", site_view)
        with freeing(site_view):
            try:
                rowptr = site_view.iter_record().next()
            except StopIteration:
                site_table.addv(*row)
                log.info("added record %s", row)
            else:
                log.debug("rowptr %s", rowptr)
                old_row = dict(zip(fields, rowptr.getv(*fields)))
                if float(convtime(lddate)) > float(old_row['lddate']):
                    rowptr.putv(*row)
                log.info("updated record %s %s", old_row, row)
                return old_row


# todo Ok so the table looks like just a normal CSS 3.0 schema with no extensions used.
# The existing SB is only populating the site table. Frank would like the snetsta table
# populated as well which will give you net
