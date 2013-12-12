#NOTE!
#The trace object passed in to these functions is in raw counts.
#Any alteration made to this trace object will persist, so make a
#copy if you want to make any alterations.
#Eg. filtering, calibration...
"""
Functions to calculate QC quanities.

Exported functions:
dc_offset - Return DC offset of a trace.
rms - Return RMS of a trace.
linear_trend - Return best-fitting line parameters of a trace.
std - Return standard deviation of a trace.

Last edited: Thursday Nov 7, 2013
Author: Malcolm White
        Institution of Geophysics and Planetary Physics
        Scripps Institution of Oceanography
        University of California, San Diego

"""
import sys
sys.path.append('/Users/mcwhite/src/anfsrc/anf/bin/utility/autoQC/CythonModule')
import CythonicStatistics as cs
sys.path.remove('/Users/mcwhite/src/anfsrc/anf/bin/utility/autoQC/CythonModule')

def mean(tr, params):
    """
    Return DC offset of input trace.

    Arguments:
    tr - Trace4.1 schema trace object <class 'Dbptr'>
    params - Empty <dict>

    Return Values:
    <dict> of field:value pairs. Field values correspond to a CSS3.0
    schema wfmeas table fields.

    """
    print '\tcalculating DC offset'
    return {'meastype': 'mean', 'val1': cs.mean(tr.data()), 'units1': 'cts', \
        'auth': 'AutoQC'}

def rms(tr, params):
    print "\tcalculating rms"
    from math import sqrt
    tr.filter("SQ")
    m = cs.mean(tr.data())
    rms = sqrt(m)
    return {'meastype': 'rms', 'val1': rms, 'units1': 'cts', \
        'auth': 'AutoQC'}

def line(tr, params):
    """
    Return best-fitting line parameter for input trace.

    Behaviour:
    Calculate the best-fitting line (in the least-squares sense) and
    return the parameters of this line.
    Caveat - y-intercept value is routinely overflowing the allowed
    'val2' field of the wfmeas table and so is not being returned.

    Arguments:
    tr - Trace4.1 schema trace object <class 'Dbptr'>
    params - Empty <dict>

    Return Values:
    <dict> of field:value pairs. Field values correspond to a CSS3.0
    schema wfmeas table fields.

    """
    print '\tcalculating linear trend'
    from numpy import arange,polyfit
    d = tr.data()
    time,endtime,nsamp = tr.getv('time', 'endtime', 'nsamp')
    x = arange(time, endtime, (endtime-time)/nsamp)
    if len(x) != len(d):
        if len(x) > len(d): x = x[:-(len(x)-len(d))]
        else: d = d[:-(len(d)-len(x))]
    m, b = polyfit(x, d, 1)
    return {'meastype': 'line', 'val1': m,'units1': 'cts/s', 'auth': 'AutoQC'}

def std(tr, params):
    """
    Return the standard deviation of filtered input trace values.

    Behaviour:
    Filter the input trace data with the input filter and return the
    standard deviation of the values of this trace.

    Arguments:
    tr - Trace4.1 schema trace object <class 'Dbptr'>
    params - User-defined parameters <dict>
    params['filter'] - Antelope filter string <str>

    Return Values:
    <dict> of field:value pairs. Field values correspond to a CSS3.0
    schema wfmeas table fields.

    """
    print '\tcalculating std'
    from numpy import std,float64
    trcp = tr.trcopy()
    trcp.filter(params['filter'])
    d = trcp.data()
    trcp.trdestroy()
    return {'meastype': 'std', 'val1': std(d,dtype=float64), 'units1': 'cts', \
        'filter': params['filter'], 'auth': 'autoQC'}
