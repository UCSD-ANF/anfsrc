#!/usr/bin/env python
"""Describe file"""


from email.mime.text import MIMEText
from smtplib import SMTP

from mailparser.util import quitting

template = """
ANF CONSTRUCTION REPORT RECEPTION REPORT

RECEIVED REPORT

From: {email_From}
Date: {email_Date}
Subject: {email_Subject}


STATION

code: {sta}
date: {date}
gps: {lat} N, {lon} E
elev: {elev}m


REPORT DISPOSITION

{disposition}


OLD RECORD

{old_row!s}


ERRORS

{errors}

DEBUGGING

Program: {argvzero}
Hostname: {hostname}
Database: {db}
Platform: {platform}
Python: {executable}
Python Version: {pythonversion}
""".strip()
# Python Path: { pythonpath }


def render_template(**kwargs):
    kwargs["errors"] = "\r\n".join([str(e) for e in kwargs["errors"]])
    kwargs["email_From"] = kwargs["email"]["From"]
    kwargs["email_Subject"] = kwargs["email"]["Subject"]
    kwargs["email_Date"] = kwargs["email"]["Date"]
    return template.format(**kwargs)


def send_report(pf, text_content):
    host = pf["smtp"].get("host", None)
    port = pf["smtp"].get("port", None)
    email = MIMEText(text_content)
    email["To"] = pf["report_to"]
    email["From"] = pf["report_from"]
    email["Subject"] = pf["mail_subject"]

    with quitting(SMTP(host, port)) as s:
        s.sendmail(pf["report_from"], [pf["report_to"]], email.as_string())
