#!/usr/bin/env python
"""Describe file"""
from collections import OrderedDict
from datetime import datetime
import email

from mailparser_anfconstruction.parser import (
    LAT_BOUNDS,
    LON_BOUNDS,
    ConversionError,
    Coords,
    Date,
    Elevation,
    RequiredFieldsNotFound,
    StationCode,
    ValidationError,
    bounds,
    fmtyday,
    process,
)
import pytest


@pytest.mark.parametrize(
    "boundrange, bounds", [(bounds.lat, LAT_BOUNDS), (bounds.lon, LON_BOUNDS),]
)
def test_boundschecker(boundrange, bounds):
    (lower, upper) = bounds
    assert lower in boundrange
    assert lower - 1 not in boundrange
    assert upper not in boundrange
    assert upper - 1 in boundrange


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
    r = process(
        [
            "hello world",
            "gps: 1,-60",
            "date: 01/01/2005",
            "elevation: 10m",
            "station code: foo.bar",
        ]
    )
    assert r == OrderedDict(
        [
            ("errors", []),
            (Coords, (-60, 1)),
            (Date, datetime(2005, 1, 1)),
            (Elevation, 10),
            (StationCode, ("FOO", "BAR")),
        ]
    )


def test_process_conv_err(mocker):
    r = process(["date: 99/99/9999"])
    assert type(r["errors"][0]) == ConversionError


def test_process_val_err(mocker):
    r = process(["date: 01/01/9999"])
    assert type(r["errors"][0]) == ValidationError


def test_process_req_not_found_err(mocker):
    r = process([])
    assert type(r["errors"][0]) == RequiredFieldsNotFound


@pytest.mark.parametrize(
    "case",
    [
        ("date: 01/01/1999", ("1999", "01", "01")),
        ("date: 01-01-1999", ("1999", "01", "01")),
        ("date: 01 01 1999", ("1999", "01", "01")),
        ("Date: 05/26-5/27/16 UTC", ("16", "5", "27")),
        ("Date: 05/28/16-5/29/16 UTC", ("16", "5", "29")),
        ("Date: 05/28/16-05/29/16 UTC", ("16", "05", "29")),
        ("Date: 5/28/16-05/29/16 UTC", ("16", "05", "29")),
    ],
)
def test_date_pattern(case):
    line, expected = case
    m = Date.pattern.match(line)
    assert m.group("year", "month", "day") == expected


@pytest.mark.parametrize(
    "case",
    [
        ("GPS: 58.6097367, 152.3941867", ("152.3941867", "58.6097367")),
        ("GPS: 58.6097367, -152.3941867", ("-152.3941867", "58.6097367")),
        ("GPS: -58.6097367, -152.3941867", ("-152.3941867", "-58.6097367")),
        ("GPS: -58.6097367, 152.3941867", ("152.3941867", "-58.6097367")),
        ("gps: 58, 152", ("152", "58")),
        ("gps: 58, -152", ("-152", "58")),
        ("gps: -58, 152", ("152", "-58")),
        ("gps: -58, -152", ("-152", "-58")),
        ("gps: -58, 152", ("152", "-58")),
    ],
)
def test_coords_pattern(case):
    line, expected = case
    m = Coords.pattern.match(line)
    assert m.group("lon", "lat") == expected


@pytest.mark.parametrize(
    "case",
    [
        ("Station Code: TA.T35M", ("TA", "T35M")),
        ("Station Code: TA. P16K", ("TA", "P16K")),
        ("Station Code: TA.PPD", ("TA", "PPD")),
        ("Station Code: AK.CAST", ("AK", "CAST")),
        ("Station Code: AK.KAI", ("AK", "KAI")),
        ("Station Code: AK_KAI", ("AK", "KAI")),
        # TODO not sure how to handle these
        # ('Station Code: TA.AK.COLD', ('AK', 'COLD')),
        # ('Station Code:=C2=A0 L02F=20', 'L02F'),
        # ('Station Code:&nbsp; L02F <br id=3D"yui_3_16_0_ym19_1_1462280670632_16752">', 'L02F'),
    ],
)
def test_sta_pattern(case):
    line, expected = case
    m = StationCode.pattern.match(line)
    assert m.group("net", "sta") == expected


@pytest.mark.parametrize(
    "case",
    [
        ("Elevation: 139.6 m", ("139.6", "m")),
        ("Elevation:  1868 ft", ("1868", "ft")),
        ("Elevation:  0.5827 km", ("0.5827", "km")),
        ("Elevation : 960Ft", ("960", "Ft")),
        # Elevation :   146.04 m
    ],
)
def test_elevation_pattern(case):
    line, expected = case
    m = Elevation.pattern.match(line)
    assert m.group("elev", "units") == expected
