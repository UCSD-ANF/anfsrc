#!/usr/bin/env python
"""Describe file"""


from mailparser._email import get_first_part


def handle(msg, pf):
    part = get_first_part(msg)
