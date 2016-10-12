#!/usr/bin/env python
"""Describe file"""


from collections import OrderedDict


# The first part that matches one of these types is parsed for construction data
MIMETYPES = [
    'text/plain',
    'text/html'
]


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


class ParserValueError(ValueError):
    pass


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

    @property
    def sta(self):
        return self._rec['sta']

    @sta.setter
    def sta(self, v):
        if v is None or 0 < len(v) <= 9:
            self._rec['sta'] = v

    @property
    def yday(self):
        return self._rec['yday']

    @yday.setter
    def yday(self, v):
        assert len(v) == 7
        self._rec['yday'] = int(v)

    @property
    def elev(self):
        return self._rec['elev']

    @elev.setter
    def elev(self, v):
        assert len(v) == 7
        self._rec['elev'] = int(v)

    @property
    def lat(self):
        return self._rec['lat']

    @lat.setter
    def lat(self, v):
        lat = float(v)
        if lat not in bounds.lat:
            raise ParserValueError(lat)
        self._rec['lat'] = lat

    @property
    def lon(self):
        return self._rec['lon']

    @lon.setter
    def lon(self, v):
        lon = float(v)
        if lon not in bounds.lon:
            raise ParserValueError(lon)
        self._rec['lon'] = lon

    def __getattr__(self, key):
        if key not in self._rec.keys():
            raise AttributeError(key)
        return self._rec[key]

    def __setattr__(self, key, value):
        if key not in self._rec.keys():
            raise AttributeError(key)
        setattr(super(ConstructionReport, self), key, value)

