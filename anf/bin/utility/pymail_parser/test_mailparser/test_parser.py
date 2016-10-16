#!/usr/bin/env python
"""Describe file"""
from collections import OrderedDict

import pytest
import email

from mailparser.parser import get_first_part, bounds, LON_BOUNDS, LAT_BOUNDS, Coords, Date
from mailparser.parser import fmtyday
from mailparser.parser import process


EMAILFILES = ['test_mailparser/data/test_emails/1']


@pytest.fixture(params=EMAILFILES)
def message(request):
    with open(request.param, 'rb') as fp:
        yield email.message_from_file(fp)


def test_get_first_part(message):
    assert get_first_part(message)


@pytest.mark.parametrize('boundrange, bounds', [
    (bounds.lat, LAT_BOUNDS),
    (bounds.lon, LON_BOUNDS),
])
def test_boundschecker(boundrange, bounds):
    (lower, upper) = bounds
    assert lower in boundrange
    assert lower - 1 not in boundrange
    assert upper not in boundrange
    assert upper - 1 in boundrange


from datetime import datetime


def test_date_format():
    d = datetime(1999, 1, 1)
    s = fmtyday(d)
    assert s == "1999001"


# split email into lines
# for each line:
#   run patterns to extract fields
#       return dict of strings

# convert types of strings

# assign to object (validate in properties)



def test_process(mocker):
    r = process(['hello world', 'gps: 1,-60', 'date: 01/01/1999'])
    assert r == OrderedDict([(Coords, (-60, 1)), (Date, datetime(1999, 1, 1))])
