#!/usr/bin/env python
"""Describe file"""
from datetime import datetime

from mailparser_anfconstruction.parser import Date, Elevation, Coords


def test_date(mocker):
    m = mocker.Mock()
    m.group.return_value = '1999', '1', '1'
    assert Date.convert(m) == datetime(1999, 1, 1)


def test_elevation(mocker):
    m = mocker.Mock()
    m.group.return_value = '1000'
    assert Elevation.convert(m) == 1000


def test_coords(mocker):
    m = mocker.Mock()
    m.group.return_value = '1.2', '3.4'
    assert Coords.convert(m) == (1.2, 3.4)
