#!/usr/bin/env python
"""Describe file"""
from contextlib import contextmanager


def blanking(method_name, *args, **kwargs):
    @contextmanager
    def _blanking(o):
        method = getattr(o, method_name)
        try:
            yield o
        finally:
            method(*args, **kwargs)
    return _blanking


logouting = blanking('logout')
closing = blanking('close')
freeing = blanking('free')
seek0ing = blanking('seek', [0])
quitting = blanking('quit')
