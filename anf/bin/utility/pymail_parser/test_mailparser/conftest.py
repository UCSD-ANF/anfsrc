#!/usr/bin/env python
"""Describe file"""

from datetime import datetime

from mailparser.imap import ImapHelper
from mailparser.util import logouting
import pytest

email1 = """From MAILER-DAEMON Fri Jul  8 12:08:34 2011
From: Author <author@example.com>
To: Recipient <recipient@example.com>
Subject: Sample message 1

This is the body.
>From (should be escaped).
There are 3 lines."""


email2 = """From MAILER-DAEMON Fri Jul  8 12:08:34 2011
From: Author <author@example.com>
To: Recipient <recipient@example.com>
Subject: 2

This is the second body."""

emails = [email1, email2]


@pytest.yield_fixture()
def newmails(imapkwargs):
    h = ImapHelper(**imapkwargs)
    with logouting(h.login()):
        h.delete("test")
        h.create("test")
        h.select("test")
        for email in emails:
            h.append("test", None, datetime.now().timetuple(), email)
        new = list(h.getnew())
    yield new
    with logouting(h.login()):
        h.delete("test")
