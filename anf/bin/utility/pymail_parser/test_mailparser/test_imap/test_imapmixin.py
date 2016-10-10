#!/usr/bin/env python
"""Describe file"""


import pytest

from mailparser.imap import ImapMixin


@pytest.fixture()
def supermethod(mocker):
    return mocker.patch('mailparser.imap.supermethod')()


def test_login(supermethod):
    ImapMixin().login()


def test_select(supermethod):
    supermethod.return_value = None, ('0',)
    ImapMixin().select()


def test_search(supermethod):
    supermethod.return_value = None, ('0 1',)
    assert ImapMixin().search() == [0, 1]


def test_fetch(supermethod):
    supermethod.return_value = ['OK', ('flags', 'msg')]
    assert ImapMixin().fetch() == ('flags', 'msg')

