# NOTE!
# The trace object passed in to these functions is in raw counts.
# Any alteration made to this trace object will persist, so make a
# copy if you want to make any alterations.
# Eg. filtering, calibration...
"""
Functions to run QC tests.

Exported functions:
dc_offset - Test for large DC offsets.
rms - Test for flatlines.
linear_trend - Test for linear trends..
std - Test for large spread of data values.

Last edited: Wed Jan 8, 2014
Author: Malcolm White
        Institution of Geophysics and Planetary Physics
        Scripps Institution of Oceanography
        University of California, San Diego

"""
import sys

import CythonicStatistics as cs

sys.path.append("/home/mcwhite/src/anfsrc/anf/bin/utility/auto_qc/CythonModule")

sys.path.remove("/home/mcwhite/src/anfsrc/anf/bin/utility/auto_qc/CythonModule")


def mean(tr, params):
    """
    Return DC offset of input trace.

    Arguments:
    tr - Trace4.1 schema trace object <class 'Dbptr'>
    params - Empty <dict>

    Return Values:
    <list> of <dict>s containing field:value pairs. Field values
    correspond to a CSS3.0 schema wfmeas table fields.

    """
    d = tr.data()
    time, endtime, samprate, nsamp = tr.getv("time", "endtime", "samprate", "nsamp")
    dt = 1.0 / samprate
    nsmps = int(params["twin"] * samprate)
    inds = []
    for i in range(int(nsamp / nsmps)):
        istart = i * nsmps
        iend = istart + nsmps
        if iend > len(d):
            break
        m = cs.mean(d[istart:iend])
        if abs(m) > params["thresh"]:
            inds.append((istart, iend))
    if len(inds) == 0:
        return None
    inds = _flatten_index_tuples(inds)
    ret = []
    for i in inds:
        ret.append(
            {
                "meastype": params["meastype"],
                "tmeas": time + dt * i[0],
                "twin": dt * (i[1] - i[0]),
                "auth": "auto_qc",
            }
        )
    return ret


def rms(tr, params):
    d = tr.data()
    time, endtime, samprate, nsamp = tr.getv("time", "endtime", "samprate", "nsamp")
    dt = 1.0 / samprate
    nsmps = int(params["twin"] * samprate)
    inds = []
    for i in range(int(nsamp / nsmps)):
        istart = i * nsmps
        iend = istart + nsmps
        if iend > len(d):
            break
        rms = cs.rms(d[istart:iend])
        if abs(rms) < params["thresh"]:
            inds.append((istart, iend))
    if len(inds) == 0:
        return None
    inds = _flatten_index_tuples(inds)
    ret = []
    for i in inds:
        ret.append(
            {
                "meastype": params["meastype"],
                "tmeas": time + dt * i[0],
                "twin": dt * (i[1] - i[0]),
                "auth": "auto_qc",
            }
        )
    return ret


def line(tr, params):
    """
    Test for linear trends in the data.

    Arguments:
    tr - Trace4.1 schema trace object <class 'Dbptr'>
    params - Empty <dict>

    Return Values:
    <list> of <dict>s containing field:value pairs. Field values
    correspond to a CSS3.0 schema wfmeas table fields.

    """
    from numpy import linspace, polyfit

    d = tr.data()
    time, endtime, samprate, nsamp = tr.getv("time", "endtime", "samprate", "nsamp")
    dt = 1.0 / samprate
    nsmps = int(params["twin"] * samprate)
    inds = []
    for i in range(int(nsamp / nsmps)):
        istart = i * nsmps
        iend = istart + nsmps
        if iend > len(d):
            break
        D = d[istart:iend]
        x = linspace(time + istart * dt, time + iend * dt, len(D))
        m, b = polyfit(x, D, 1)
        if abs(m) > params["thresh"]:
            inds.append((istart, iend))
    if len(inds) == 0:
        return None
    inds = _flatten_index_tuples(inds)
    ret = []
    for i in inds:
        ret.append(
            {
                "meastype": params["meastype"],
                "tmeas": time + dt * i[0],
                "twin": dt * (i[1] - i[0]),
                "auth": "auto_qc",
            }
        )
    return ret


def skew(tr, params):
    """
    Test for skewed data.

    Arguments:
    tr - Trace4.1 schema trace object <class 'Dbptr'>
    params - Empty <dict>

    Return Values:
    <list> of <dict>s containing field:value pairs. Field values
    correspond to a CSS3.0 schema wfmeas table fields.
    """
    d = tr.data()
    time, endtime, samprate, nsamp = tr.getv("time", "endtime", "samprate", "nsamp")
    dt = 1.0 / samprate
    nsmps = int(params["twin"] * samprate)
    inds = []
    for i in range(int(nsamp / nsmps)):
        istart = i * nsmps
        iend = istart + nsmps
        if iend > len(d):
            break
        skew = cs.skew(d[istart:iend])
        if abs(skew) > params["thresh"]:
            inds.append((istart, iend))
    if len(inds) == 0:
        return None
    inds = _flatten_index_tuples(inds)
    ret = []
    for i in inds:
        ret.append(
            {
                "meastype": params["meastype"],
                "tmeas": time + dt * i[0],
                "twin": dt * (i[1] - i[0]),
                "auth": "auto_qc",
            }
        )
    return ret


def std(tr, params):
    """
    Test for large spread in data.

    Arguments:
    tr - Trace4.1 schema trace object <class 'Dbptr'>
    params - User-defined parameters <dict>
    params['filter'] - Antelope filter string <str>

    Return Values:
    <list> of <dict>s containing field:value pairs. Field values
    correspond to a CSS3.0 schema wfmeas table fields.
    """

    from math import sqrt

    d = tr.data()
    time, endtime, samprate, nsamp = tr.getv("time", "endtime", "samprate", "nsamp")
    dt = 1.0 / samprate
    nsmps = int(params["twin"] * samprate)
    inds = []
    for i in range(int(nsamp / nsmps)):
        istart = i * nsmps
        iend = istart + nsmps
        if iend > len(d):
            break
        var = cs.var(d[istart:iend])
        if sqrt(var) > params["thresh"]:
            inds.append((istart, iend))
    if len(inds) == 0:
        return None
    inds = _flatten_index_tuples(inds)
    ret = []
    for i in inds:
        ret.append(
            {
                "meastype": params["meastype"],
                "tmeas": time + dt * i[0],
                "twin": dt * (i[1] - i[0]),
                "auth": "auto_qc",
            }
        )
    return ret


def _flatten_indices(inds):
    """Reduce consecutive indices to end members only."""
    if len(inds) % 2 != 0:
        print("ERROR - _flatten_indices(): odd number of indices")
        return None
    inds = (
        [inds[0]]
        + [
            inds[i]
            for i in range(1, len(inds) - 1)
            if (inds[i] != inds[i - 1] + 1 or inds[i] != inds[i + 1] - 1)
        ]
        + [inds[-1]]
    )
    return [(inds[i], inds[i + 1]) for i in range(0, len(inds), 2)]


def _flatten_index_tuples(inds):
    """Reduce consecutive tuple of indices to end members only."""
    ret = [inds.pop(0)]
    while True:
        try:
            elem = inds.pop(0)
        except IndexError:
            return ret
        if elem[0] == ret[-1][1]:
            ret[-1] = (ret[-1][0], elem[1])
        else:
            ret.append(elem)
