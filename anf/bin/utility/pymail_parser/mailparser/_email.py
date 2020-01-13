#!/usr/bin/env python

MIMETYPES = ["text/plain", "text/html"]


def get_first_part(msg):
    """Get the first leaf node part"""
    try:
        part = (
            part for part in msg.walk() if part.get_content_type() in MIMETYPES
        ).next()
    except StopIteration:
        return None
    return part.get_payload(decode=True)
