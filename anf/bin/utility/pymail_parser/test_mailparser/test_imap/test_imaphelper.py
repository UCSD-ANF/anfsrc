#!/usr/bin/env python
"""Describe file"""


import pytest

from mailparser.imap import ImapHelper, logouting


kwargs=dict(
    username='imaptest',
    password='imaptest',
    host='192.168.56.101',
    port='imap'
)


@pytest.yield_fixture()
def newmails():
    h = ImapHelper(**kwargs).login()
    with logouting(h):
        for n in h.search('all'):
            h.setseen(n, False)
        yield list(h.getnew())


def test_getnew(newmails):
    assert len(newmails) == 4
    n, flags, msg = newmails[0]
    msg['Subject']
