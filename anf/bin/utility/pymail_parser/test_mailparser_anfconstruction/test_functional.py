#!/usr/bin/env python
"""Describe file"""


from mailparser.imap import ImapHelper
from mailparser.mailparser import parse_mail
from mailparser.util import logouting


class FakePF(dict):
    auto_convert = False


def test_one(mocker, construction_report_emails, imapkwargs):
    pf = FakePF(
        Handlers=[
            dict(
                handler="anfconstruction",
                sender=".*",
                subject=".*",
                smtp=dict(host="192.168.56.101", port="smtp"),
                database="testdb",
                report_to="imaptest@localhost",
                report_from="test@test.com",
                mail_subject="test@test.com",
            )
        ],
        logging=dict(version=1),
        imap=dict(
            host="192.168.56.101",
            username="imaptest",
            password="imaptest",
            port="imap",
            mailbox="test",
        ),
    )
    mocker.patch("mailparser.mailparser.pfread").return_value = pf
    mocker.patch("mailparser_anfconstruction.handler.store").return_value = pf
    parse_mail(mocker.Mock())
    del pf["imap"]["mailbox"]
    h = ImapHelper(**pf["imap"]).login()
    with logouting(h):
        new = list(h.getnew())
        assert len(new) == 1
        print(new)
        n, flags, msg = new[0]
        # h.store(n, '+FLAGS', '\\Deleted')
