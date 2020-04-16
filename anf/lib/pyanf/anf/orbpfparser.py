# -*- coding: utf-8 -*-
"""Decode an Antelope PF packet from an orb.

This module contains functions to parse an Antelope ParameterFile object from
an orb packet.

"""

from antelope.stock import ParameterFile


def orbpfparse(pktbuf):
    """Decode an orb packet as a ParameterFile object.

    Args:
        pktbuf(bytes): Contents of an orb packet as read by orb.get or orb.getstash

    Returns:
        ParameterFile: data decoded from pktbuf

    Raises:
        UnicodeDecodeError: if the packet does not contain ASCII text
        PfCompileError: If parameter file data parsing fails
    """

    pf = ParameterFile()
    data = pktbuf.rstrip(b"\x00").lstrip(b"\xff").decode("ascii", "strict")
    pf.pfcompile(data)

    return pf
