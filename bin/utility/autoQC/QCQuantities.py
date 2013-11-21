# -*- coding: utf-8 -*-
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
skew - Return skewness of a trace.

Last edited: Thursday Nov 7, 2013
Author: Malcolm White
        Institution of Geophysics and Planetary Physics
        Scripps Institution of Oceanography
        University of California, San Diego
  
"""

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
    import sys
    sys.path.append('/Users/mcwhite/src/anfsrc/bin/utility/autoQC/CythonModule')
    import CythonicStatistics as cs
    sys.path.remove('/Users/mcwhite/src/anfsrc/bin/utility/autoQC/CythonModule')
    return {'meastype': 'mean', 'val1': cs.mean(tr.data()), 'units1': 'cts', \
        'auth': 'AutoQC'}
    
def rms(tr, params):
    """
    Return RMS value of input trace.

    Arguments:
    tr - Trace4.1 schema trace object <class 'Dbptr'>
    params - Empty <dict>
    
    Return Values:
    <dict> of field:value pairs. Field values correspond to a CSS3.0 
    schema wfmeas table fields.

    """
    print '\tcalculating rms'
    import sys
    sys.path.append('/Users/mcwhite/src/anfsrc/bin/utility/autoQC/CythonModule')
    import CythonicStatistics as cs
    sys.path.remove('/Users/mcwhite/src/anfsrc/bin/utility/autoQC/CythonModule')
    return {'meastype': 'rms', 'val1': cs.rms(tr.data()), 'units1': 'cts', \
        'auth': 'AutoQC'}

def line(tr, params):
    """
    Return best-fitting line parameter for input trace.
    
    Behaviour:
    Calculate the best-fitting line (in th least-squares sense) and
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
    #The y-intercept
    
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
    #Create a copy of self-contained trace object.
    trcp = tr.trcopy()
    trcp.filter(params['filter'])
    #Extract waveform data
    d = trcp.data()
    #Destroy the trace object copy.
    trcp.trdestroy()
    return {'meastype': 'std', 'val1': std(d,dtype=float64), 'units1': 'cts', \
        'filter': params['filter'], 'auth': 'autoQC'}
        
def skew(tr, params):
    print '\tcalculating skewness'
    import sys
    sys.path.append('/Users/mcwhite/src/anfsrc/bin/utility/autoQC/CythonModule')
    import CythonicStatistics as cs
    sys.path.remove('/Users/mcwhite/src/anfsrc/bin/utility/autoQC/CythonModule')
    from numpy import arange
    twin = params['twin']
    trcp = tr.trcopy()
    trcp.filter(params['filter'])
    ts, te, nsamp, samprate = trcp.getv('time', 'endtime', 'nsamp', 'samprate')
    d = trcp.data()
    trcp.trdestroy()
    d = detrend(arange(ts, te, (te - ts)/nsamp), d)[1]
    return{'meastype': 'skew', 'val1': cs.skew(d, twin, samprate), \
        'units1': 'unitless', 'filter': params['filter'], 'auth': 'AutoQC'}
        
def step(tr, params):
    def f(x, d, i, w):
        if i-w < 0: ls = 0
        else: ls = i-w
        if i+w > len(d): re = len(d)
        else: re = i+w
        print i, w, ls, re, len(x), len(d)
        return abs(mean(detrend(x[ls:i], d[ls:i])[1]) - 
            mean(detrend(x[i:re], d[i:re])[1]))
            
    import time
    t = time.clock()
    print '\tlooking for steps'
    import sys
    sys.path.append('/Users/mcwhite/src/anfsrc/bin/utility/autoQC/CythonModule')
    from CythonicStatistics import mean
    sys.path.remove('/Users/mcwhite/src/anfsrc/bin/utility/autoQC/CythonModule')
    import numpy as np
    trcp = tr.trcopy()
    trcp.filter('DIF')
    ts, te, nsamp = trcp.getv('time', 'endtime', 'nsamp')
    d = trcp.data()
    trcp.trdestroy()
    x = np.arange(ts, te, (te - ts)/nsamp)
    le = len(d)
#    lh = [cs.lh_ave(d, i, params['ave_win']) for i in range(le)]
#    rh = [cs.rh_ave(d, i, params['ave_win']) for i in range(le)]
    inds = [i for i in range(le) if d[i] > params['dif_thresh']]
    print len(inds)
    r = []
    w = params['ave_win']
    delta = params['delta_ave_max']
    inds = filter(lambda i: f(x, d, i, w) > delta, inds)
    print len(inds)
    for i in inds:        
        r.append({'meastype': 'step', 'val1': -1, 'units1': 'cts', \
            'auth': 'AutoQC'})  
    print "\t%f" % (time.clock() - t)
    return r
    
def detrend(x, y):
    import numpy as np
    if len(x) > len(y): x = x[:(len(y) - len(x))]
    if len(y) > len(x): y =  y[:(len(x) - len(y))]
    m, b = np.polyfit(x, y, 1)
    y = [y[i] - (m*x[i] + b) for i in range (len(y))]
    return x, y