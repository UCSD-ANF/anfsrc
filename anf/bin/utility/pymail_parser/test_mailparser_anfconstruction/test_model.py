#!/usr/bin/env python
"""Describe file"""

from mailparser_anfconstruction.model import store, fields
from datetime import datetime


def test_store(mocker):
    mocker.patch('mailparser_anfconstruction.model.closing')
    db = mocker.patch('mailparser_anfconstruction.model.dbopen')()
    mocker.patch('mailparser_anfconstruction.model.freeing')
    db.lookup().subset().iter_record().next().getv.return_value = ('STA', datetime.now(), 0.0, 0.0, 0.0, datetime.now())
    store('STA', datetime.now(), 0.0, 0.0, 0.0)
    db.lookup().subset().iter_record().next.side_effect = StopIteration
    store('STA', datetime.now(), 0.0, 0.0, 0.0)
