#!/usr/bin/env python

import pytest

from mailparser.imap import ImapHelper, logouting


@pytest.fixture()
def imapkwargs():
    return dict(
        username='imaptest',
        password='imaptest',
        host='192.168.56.101',
        port='imap'
    )


@pytest.yield_fixture()
def newmails(imapkwargs):
    h = ImapHelper(**imapkwargs).login()
    with logouting(h):
        for n in h.search('all'):
            h.setseen(n, False)
        yield list(h.getnew())

