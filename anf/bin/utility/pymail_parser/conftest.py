#!/usr/bin/env python

import pytest


@pytest.fixture
def smtpkwargs():
    return dict(host="192.168.56.101", port="smtp")


@pytest.fixture()
def imapkwargs():
    return dict(
        username="imaptest", password="imaptest", host="192.168.56.101", port="imap"
    )
