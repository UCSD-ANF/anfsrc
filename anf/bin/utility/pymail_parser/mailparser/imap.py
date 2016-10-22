#!/usr/bin/env python
"""Describe file

inspired primarily by http://stackoverflow.com/questions/13210737/get-only-new-emails-imaplib-and-python
"""


from contextlib import closing, contextmanager
import email
import imaplib
from functools import partial, wraps
import logging


log = logging.getLogger(__name__)
# log.setLevel(logging.DEBUG)
# logging.basicConfig(level=logging.DEBUG)


def blanking(method, *args, **kwargs):
    @contextmanager
    def _blanking(o):
        try:
            yield o
        finally:
            getattr(o, method)(*args, **kwargs)
    return _blanking


logouting = blanking('logout')
closing = blanking('close')
freeing = blanking('free')
seek0ing = blanking('seek', [0])


def supermethod(klass, self, name):
    return getattr(super(klass, self), name)


def pleaselog(f):
    @wraps(f)
    def _pleaselog(self, *args, **kwargs):
        super_f = supermethod(ImapMixin, self, f.__name__)
        r = super_f(*args, **kwargs)
        log.debug("%s: %s", f.__name__, repr(r)[:150])
        return f(self, r)
    return _pleaselog


class ImapMixin(object):
    """Augment the IMAP class to make it slightly less crappy."""

    @pleaselog
    def login(self, r):
        pass

    @pleaselog
    def logout(self, r):
        pass

    @pleaselog
    def close(self, r):
        pass

    @pleaselog
    def store(self, r):
        pass

    @pleaselog
    def select(self, r):
        code, (datum,) = r
        return int(datum)

    @pleaselog
    def search(self, r):
        code, (data,) = r
        return [int(n) for n in data.split()]

    @pleaselog
    def fetch(self, r):
        flags, msg = r[1]
        return flags, msg


class IMAP4(ImapMixin, imaplib.IMAP4):
    def __init__(self, *args, **kwargs):
        imaplib.IMAP4.__init__(self, *args, **kwargs)


class IMAP4_SSL(ImapMixin, imaplib.IMAP4_SSL):
    def __init__(self, *args, **kwargs):
        imaplib.IMAP4_SSL.__init__(self, *args, **kwargs)


class NotConnected(Exception):
    pass


def require_conn(f):
    @wraps(f)
    def inner(self, *args, **kwargs):
        if not self._conn:
            self.login()
        return f(self, *args, **kwargs)
    return inner


class ImapHelper(object):
    """High level IMAP API

    Mailbox defaults to 'inbox'

    For SSL supply keyfile and optionally certfile
    """
    _IMAP = None

    def __init__(self, username, password, host, port=None, mailbox='INBOX', keyfile=None, certfile=None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.mailbox = mailbox
        self.keyfile = keyfile
        self.certfile = certfile
        self._conn = None

        self._IMAP = partial(IMAP4, host, port)
        if keyfile:
            self._IMAP = partial(IMAP4_SSL, host, port, keyfile=keyfile, certfile=certfile)

    def login(self):
        if self._conn:
            return
        self._conn = self._IMAP()
        self._conn.login(self.username, self.password)
        self._conn.select(self.mailbox)
        return self

    @require_conn
    def logout(self):
        self._conn.close()
        self._conn.logout()
        self._conn = None

    @require_conn
    def setseen(self, n, seen=True):
        if seen:
            self._conn.store(n, '+FLAGS', r'\Seen')
        else:
            self._conn.store(n, '-FLAGS', r'\Seen')

    @require_conn
    def fetch(self, n):
        (flags, msg), junk = self._conn.fetch(n, '(RFC822)')
        return flags, email.message_from_string(msg)

    @require_conn
    def getnew(self):
        for n in self.search('unseen'):
            flags, msg = self.fetch(n)
            yield n, flags, msg
            self.setseen(n)

    @require_conn
    def search(self, term):
        """Yields emails matching term"""
        msg_nums = self._conn.search(None, '(%s)' % term.upper())
        for n in msg_nums:
            yield n

    def __del__(self):
        try:
            self.close()
        except Exception, e:
            pass

    def __getattr__(self, item):
        if not self._conn:
            raise AttributeError(item)
        return getattr(self._conn, item)
