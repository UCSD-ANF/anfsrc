#!/usr/bin/env python

import pytest

from django.conf import settings
import django

settings.configure()
django.setup()

settings.EMAIL_HOST = '192.168.56.101'


@pytest.fixture()
def imapkwargs():
    return dict(
        username='imaptest',
        password='imaptest',
        host='192.168.56.101',
        port='imap'
    )


