#!/usr/bin/env python
"""Describe file"""
from datetime import datetime

import pytest

from mailparser_anfconstruction.parser import Date, Elevation, Coords, StationCode


def test_date(mocker):
    m = mocker.Mock()
    m.group.return_value = '1999', '1', '1'
    assert Date.convert(m) == datetime(1999, 1, 1)


@pytest.mark.parametrize('case', [
    (('0.5827', 'km'), 582.7),
    (('960',    'Ft'), 292.608),
    (('960',    'm'), 960)
])
def test_elevation(case, mocker):
    tokens, expected = case
    m = mocker.Mock()
    m.group.side_effect = tokens
    assert Elevation.convert(m) == expected


def test_coords(mocker):
    m = mocker.Mock()
    m.group.return_value = '1.2', '3.4'
    assert Coords.convert(m) == (1.2, 3.4)


def test_station(mocker):
    m = mocker.Mock()
    m.group.return_value = 'foo', 'bar'
    assert StationCode.convert(m) == ('FOO', 'BAR')

