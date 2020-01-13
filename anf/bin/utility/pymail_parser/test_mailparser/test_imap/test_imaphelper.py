#!/usr/bin/env python
"""Describe file"""


def test_getnew(newmails):
    assert len(newmails) == 2
    n, flags, msg = newmails[0]
    assert msg["Subject"]
