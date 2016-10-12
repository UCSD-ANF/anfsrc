#!/usr/bin/env python
"""Describe file"""


import pytest
import email

from mailparser.parser import get_first_part, bounds, LON_BOUNDS, LAT_BOUNDS


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
