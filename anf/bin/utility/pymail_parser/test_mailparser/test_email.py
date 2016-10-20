#!/usr/bin/env python
"""Describe file"""
import email

import pytest

from mailparser._email import get_first_part


EMAILFILES = ['test_mailparser_anfconstruction/data/test_emails/1']


@pytest.fixture(params=EMAILFILES)
def message(request):
    with open(request.param, 'rb') as fp:
        yield email.message_from_file(fp)


def test_get_first_part(message):
    assert get_first_part(message)


