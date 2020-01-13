#!/usr/bin/env python
"""Describe file"""


from mailparser.mailparser import main, parse_args


def test_parse_args(mocker):
    parse_args(["asfsd", "--pffile=asfsda", "-v"])


def test_main_verbose(mocker):
    mocker.patch("mailparser.mailparser.parse_mail")
    assert main(["asfsd", "--pffile=asfsda", "-v"]) == 0
