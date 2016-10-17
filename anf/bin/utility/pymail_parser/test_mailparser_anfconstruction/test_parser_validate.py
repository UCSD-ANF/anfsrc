#!/usr/bin/env python
"""Describe file"""

from datetime import datetime

import pytest

from mailparser_anfconstruction.parser import StationCode, Date, Elevation, Coords


@pytest.mark.parametrize('case', [
    (datetime(2016, 1, 1), True),
    (datetime(3000, 1, 1), False),
    (datetime(1950, 1, 1), False),
])
def test_date(case, mocker):
    date, expected = case
    assert Date.validate(date) == expected



