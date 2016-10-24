#!/usr/bin/env python
"""Describe file"""

import email
from datetime import datetime
import pytest

from mailparser.imap import ImapHelper
from mailparser.util import logouting

with open('test_mailparser_anfconstruction/data/test_emails/1', 'rb') as fp:
    raw_email = fp.read()

@pytest.yield_fixture()
def construction_report_emails(imapkwargs):
    h = ImapHelper(**imapkwargs)
    with logouting(h.login()):
        h.delete('test')
        h.create('test')
        h.append('test', None, datetime.now().timetuple(), raw_email)
    yield
    with logouting(h.login()):
        h.delete('test')
