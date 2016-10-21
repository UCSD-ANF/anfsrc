#!/usr/bin/env python
"""Describe file"""
import pytest

from mailparser.imap import ImapHelper, logouting
from mailparser.mailparser import parse_mail

class FakePF(dict):
    auto_convert = False

@pytest.mark.xfail
def test_one(mocker, newmails, imapkwargs):
    pf = FakePF(
        imap_host='192.168.56.101',
        Handlers=[dict(
            handler='anfconstruction',
            sender='sender',
            subject='subject')],
        imap_username='imaptest',
        imap_password='imaptest',
        imap_port='imap',
    )
    mocker.patch('mailparser.mailparser.pfread').return_value = pf
    parse_mail(mocker.Mock())
    h = ImapHelper(pf['imap_username'], pf['imap_password'], pf['imap_host']).login()
    with logouting(h):
        assert len(h.getnew()) == 1
        print list(h.getnew())
