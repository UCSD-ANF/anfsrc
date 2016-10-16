#!/usr/bin/env python
"""Describe file"""
import re
from collections import OrderedDict


# The first part that matches one of these types is parsed for construction data
from functools import partial
from datetime import datetime


MIMETYPES = [
    'text/plain',
    'text/html'
]


def fmtyday(dt):
    return dt.strftime("%Y%j")


# bounds = min, max
LON_BOUNDS = -180.0, -50.0
LAT_BOUNDS = -20.0, 80.0


class BoundsChecker(object):
    def __init__(self, bounds):
        self.min, self.max = bounds

    def __contains__(self, value):
        return self.min <= value < self.max


class bounds:
    lon = BoundsChecker(LON_BOUNDS)
    lat = BoundsChecker(LAT_BOUNDS)


class ParserError(Exception): pass
class ConversionError(ParserError): pass
class ValidationError(ParserError): pass


def get_first_part(msg):
    """Get the first leaf node part"""
    try:
        part = (part for part in msg.walk() if part.get_content_type() in MIMETYPES).next()
    except StopIteration:
        return None
    return part.get_payload(decode=True)


class ConstructionReport(object):
    def __init__(self, sta=None, year=None, month=None, day=None, lddate=None, elev=None,
                 unit=None, lat=None, lon=None, epoch=None, yday=None):
        self._rec = OrderedDict([
            ('sta', sta),
            ('year', year),
            ('month', month),
            ('day', day),
            ('lddate', lddate),
            ('elev', elev),
            ('unit', unit),
            ('lat', lat),
            ('lon', lon),
            ('epoch', epoch),
            ('yday', yday),
        ])


_fields = []


def field(klass):
    klass.pattern = re.compile(klass.pattern, re.I)
    _fields.append(klass)
    return klass


class Field(object):
    pattern = None
    convert = None
    validate = None

    def __init__(self):
        raise Exception("singleton; do not instantiate")


@field
class Date(Field):
    pattern = 'date\s*(?:=|:)\s*(?P<month>\d{1,2}).(?P<day>\d{1,2}).(?P<year>\d{2,4})'

    @staticmethod
    def convert(m):
        year = int(m.group('year'))
        year = year if year >= 100 else year + 2000
        month = int(m.group('month'))
        day = int(m.group('day'))
        return datetime(year, month, day)

    @staticmethod
    def validate(value):
        pass


@field
class Coords(Field):
    pattern = '(?:gps|coordinates)\s*(?:=|:)\s*(\S+)'
    convert = staticmethod(
        lambda m: tuple(reversed([long(degrees) for degrees in m.group(1).split(',')])))

    @staticmethod
    def validate(value):
        lon, lat = value
        if lon not in bounds.lon or lat not in bounds.lat:
            raise ValidationError(Coords, value)


def process(lines):
    output = OrderedDict()
    for line in lines:
        for field in _fields:
            m = field.pattern.match(line)
            if m:
                v = field.convert(m)
                field.validate(v)
                output[field] = v
    return output

