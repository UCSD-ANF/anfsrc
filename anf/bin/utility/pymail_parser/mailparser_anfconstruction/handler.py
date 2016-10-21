#!/usr/bin/env python
"""Describe file"""
import platform
import sys

from mailparser._email import get_first_part
from mailparser_anfconstruction.parser import process
from mailparser_anfconstruction.model import store
from mailparser_anfconstruction.report import render_template, send_report


def handle(msg, pf):
    report = dict(
        argvzero=sys.argv[0],
        platform=platform.platform,
        hostname=platform.node(),
        pythonversion=sys.version,
        pythonpath=sys.path,
        executable=sys.executable,
        disposition='Created',
        old_row=None,
    )
    report['email'] = msg
    part = get_first_part(msg)
    extracted = process(part)
    report.update(extracted)
    if not report['errors']:
        old_row = store(report['sta'], report['date'], report['lon'], report['lat'], report['elev'])
        if old_row:
            report['old_row'] = old_row
            report['disposition'] = 'Updated'
    report_body = render_template(**report)
    send_report(report_body)

