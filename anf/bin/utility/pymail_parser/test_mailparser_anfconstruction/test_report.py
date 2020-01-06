#!/usr/bin/env python
"""Describe file"""
import sys
import platform

import pytest

from mailparser_anfconstruction.parser import Date, ConversionError, ValidationError, RequiredFieldsNotFound, Coords, \
    Elevation, StationCode
from mailparser_anfconstruction.report import render_template, send_report


@pytest.fixture
def template_args(mocker):
    email = {
        'From': 'foo@bar.com',
        'Date': 'eleventy billion years in the future',
        'Subject': 'haglhaglahglh'
    }
    errors = [
        Exception('foobar'),
        ConversionError(Date, 'no dates here', ValueError('whatever')),
        ValidationError(Date, 'or here'),
        RequiredFieldsNotFound(set([Date, Coords, Elevation, StationCode]))
    ]
    return dict(
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
        disposition='Created or Updated',
        old_row=None,
        db=''
    )


def test_render_template(mocker, template_args):
    print render_template(**template_args)


def test_send_report(mocker, template_args):
    mocker.patch('mailparser_anfconstruction.report.MIMEText')
    mocker.patch('mailparser_anfconstruction.report.SMTP')
    pf = {
        'report_to': '',
        'report_from': '',
        'mail_subject': '',
        'smtp': {}}
    send_report(pf, render_template(**template_args))
