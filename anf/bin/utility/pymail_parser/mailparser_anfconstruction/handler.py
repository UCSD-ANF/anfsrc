#!/usr/bin/env python
"""Describe file"""
import platform
import sys

from mailparser._email import get_first_part
from mailparser_anfconstruction import model
from mailparser_anfconstruction.parser import (
    Coords,
    Date,
    Elevation,
    StationCode,
    process,
)
from mailparser_anfconstruction.report import render_template, send_report


def handle(msg, pf):
    model.dbpath = pf["database"]
    report = dict(
        argvzero=sys.argv[0],
        platform=platform.platform,
        hostname=platform.node(),
        pythonversion=sys.version,
        pythonpath=sys.path,
        executable=sys.executable,
        disposition="Created",
        old_row=None,
        db=pf["database"],
    )
    report["email"] = msg
    part = get_first_part(msg)
    lines = part.splitlines()
    extracted = process(lines)
    report["errors"] = extracted["errors"]
    net, sta = extracted[StationCode]
    if not extracted["errors"]:
        report["lon"], report["lat"] = extracted[Coords]
        report["date"] = extracted[Date]
        report["sta"] = "-".join((net, sta))
        report["elev"] = extracted[Elevation]
        old_row = model.store(
            net, sta, report["date"], report["lon"], report["lat"], report["elev"]
        )
        if old_row:
            report["old_row"] = old_row
            report["disposition"] = "Updated"
    report_body = render_template(**report)
    send_report(pf, report_body)
