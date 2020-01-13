#!/usr/bin/env python
"""Describe file"""

from mailparser.imap import IMAP4, IMAP4_SSL, ImapHelper, ImapMixin, pleaselog
from mailparser.util import blanking


def test_blanking(mocker):
    foo = blanking("foo")
    bar = mocker.Mock()
    with foo(bar) as r:
        assert r is bar
    bar.foo.assert_called_once_with()


def test_pleaselog(mocker):
    log = mocker.patch("mailparser.imap.log")
    supermethod = mocker.patch("mailparser.imap.supermethod")
    super_outer = supermethod()
    self = mocker.Mock()
    outer = mocker.MagicMock()
    outer.__name__ = "outer"
    wrapped = pleaselog(outer)
    result = wrapped(self)
    (fmt, name, r), kwargs = log.debug.call_args
    assert name == "outer"
    assert outer.call_args == ((self, super_outer()), {})
    assert result == outer()
