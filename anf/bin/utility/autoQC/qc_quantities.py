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
    print '\tdetecting DC offsets'
    d = tr.data()
    time, endtime, samprate, nsamp = tr.getv('time', 'endtime', 'samprate', \
            'nsamp')
    dt = 1.0/samprate
    nsmps = int(params['twin']*samprate)
    inds = []
    for i in range(int(nsamp/nsmps)):
        istart = i*nsmps
        iend = istart + nsmps
        if iend > len(d):  break
        m = cs.mean(d[istart:iend])
        if abs(m) > params['thresh']:
            inds.append((istart, iend))
    if len(inds) == 0: return None
    inds = _flatten_index_tuples(inds)
    ret = []
    for i in inds:
        ret.append({'meastype': params['meastype'], \
                'tmeas': time + dt*i[0], \
                'twin': dt*(i[1]-i[0]), \
                'auth': 'auto_qc'})
    return ret

def rms(tr, params):
    print "\tdetecting flatlines"
    d = tr.data()
    time, endtime, samprate, nsamp = tr.getv('time', 'endtime', 'samprate', \
            'nsamp')
    dt = 1.0/samprate
    nsmps = int(params['twin']*samprate)
    inds = []
    for i in range(int(nsamp/nsmps)):
        istart = i*nsmps
        iend = istart + nsmps
        if iend > len(d):  break
        rms = cs.rms(d[istart:iend])
        if abs(rms) < params['thresh']:
            inds.append((istart, iend))
    if len(inds) == 0: return None
    inds = _flatten_index_tuples(inds)
    ret = []
    for i in inds:
        ret.append({'meastype': params['meastype'], \
                'tmeas': time + dt*i[0], \
                'twin': dt*(i[1]-i[0]), \
                'auth': 'auto_qc'})
    return ret

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
    print '\tdetecting linear trends'
    from numpy import linspace,polyfit
    d = tr.data()
    time, endtime, samprate, nsamp = tr.getv('time', 'endtime', 'samprate', \
            'nsamp')
    dt = 1.0/samprate
    nsmps = int(params['twin']*samprate)
    inds = []
    for i in range(int(nsamp/nsmps)):
        istart = i*nsmps
        iend = istart + nsmps
        if iend > len(d):  break
        D = d[istart:iend]
        x = linspace(time + istart*dt, time + iend*dt, len(D))
        m, b = polyfit(x, D, 1)
        if abs(m) > params['thresh']:
            inds.append((istart, iend))
    if len(inds) == 0: return None
    inds = _flatten_index_tuples(inds)
    ret = []
    for i in inds:
        ret.append({'meastype': params['meastype'], \
                'tmeas': time + dt*i[0], \
                'twin': dt*(i[1]-i[0]), \
                'auth': 'auto_qc'})
    return ret

def skew(tr, params):
    print '\tdetecting skewed data'
    d = tr.data()
    time, endtime, samprate, nsamp = tr.getv('time', 'endtime', 'samprate', \
            'nsamp')
    dt = 1.0/samprate
    nsmps = int(params['twin']*samprate)
    inds = []
    for i in range(int(nsamp/nsmps)):
        istart = i*nsmps
        iend = istart + nsmps
        if iend > len(d):  break
        skew = cs.skew(d[istart:iend])
        if abs(skew) > params['thresh']:
            inds.append((istart, iend))
        if len(inds) == 0: return None
        inds = _flatten_index_tuples(inds)
        ret = []
        for i in inds:
            ret.append({'meastype': params['meastype'], \
                    'tmeas': time + dt*i[0], \
                    'twin': dt*(i[1]-i[0]), \
                    'auth': 'auto_qc'})
        return ret

def var(tr, params):
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
    print '\tdetecting highly variable data'
    from numpy import std,float64
    d = tr.data()
    time, endtime, samprate, nsamp = tr.getv('time', 'endtime', 'samprate', \
            'nsamp')
    dt = 1.0/samprate
    nsmps = int(params['twin']*samprate)
    inds = []
    for i in range(int(nsamp/nsmps)):
        istart = i*nsmps
        iend = istart + nsmps
        if iend > len(d):  break
        var = cs.var(d[istart:iend])
        if abs(var) > params['thresh']:
            inds.append((istart, iend))
    if len(inds) == 0: return None
    inds = _flatten_index_tuples(inds)
    ret = []
    for i in inds:
        ret.append({'meastype': params['meastype'], \
                'tmeas': time + dt*i[0], \
                'twin': dt*(i[1]-i[0]), \
                'auth': 'auto_qc'})
    return ret

def _test_thresholds(d, threshon, threshoff):
    i = 0
    inds = []
    while i < len(d):
        if d[i] > threshon:
            ind_on = i
            i += 1
            while d[i] > threshoff:
                i += 1
            ind_off = i
            inds.append((ind_on, ind_off))
    return inds

def _flatten_indices(inds):
    if len(inds) % 2 != 0:
        print "ERROR - _flatten_indices(): odd number of indices"
    return None
    inds = [inds[0]] + [inds[i] for i in range(1, len(a)-1) if \
            (inds[i] != inds[i-1] + 1 or inds[i] != inds[i+1] - 1)] \
            + [inds[-1]]
    return [(inds[i], inds[i+1]) for i in range(0, len(inds), 2)]

def _flatten_index_tuples(inds):
    ret = [inds.pop(0)]
    while True:
        try: elem = inds.pop(0)
        except IndexError: return ret
        if elem[0] == ret[-1][1]: ret[-1] = (ret[-1][0], elem[1])
        else: ret.append(elem)
