#!/usr/bin/env python
"""Describe file"""
import sys
import platform

from mailparser_anfconstruction.parser import Date, ConversionError, ValidationError, RequiredFieldsNotFound, Coords, \
    Elevation, StationCode
from mailparser_anfconstruction.report import render_template


def test_render_template(mocker):
    email = mocker.Mock()
    email.from_ = 'foo@bar.com'
    email.date = 'eleventy billion years in the future'
    email.subject = 'haglhaglahglh'
    errors = [
        Exception('foobar'),
        ConversionError(Date, 'no dates here', ValueError('whatever')),
        ValidationError(Date, 'or here'),
        RequiredFieldsNotFound(set([Date, Coords, Elevation, StationCode]))
    ]
    print render_template(
        sta='sta',
        date='date',
        lat=0.0,
        lon=0.0,
        elev=0.0,
        email=email,
        errors=errors,
        argvzero=sys.argv[0],
        platform=platform.platform,
        hostname=platform.node(),
        pythonversion=sys.version,
        pythonpath=sys.path,
        executable=sys.executable,
        disposition='Created or Updated'
    )
