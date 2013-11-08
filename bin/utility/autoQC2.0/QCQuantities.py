# -*- coding: utf-8 -*-
"""
Functions to calculate QC quanities.

Exported functions:
dc_offset - Return DC offset of a trace.
rms - Return RMS of a trace.
linear_trend - Return best-fitting line parameters of a trace.
std - Return standard deviation of a trace.
skew - Return skewness of a trae NOT IMPEMENTED!

Last edited: Thursday Nov 7, 2013
Author: Malcolm White
        Institution of Geophysics and Planetary Physics
        Scripps Institution of Oceanography
        University of California, San Diego
  
"""

def mean(tr,params):
    """
    Return DC offset of input trace.
    
    Arguments:
    tr - Trace4.1 schema trace object <class 'Dbptr'>
    params - Empty <dict>
    
    Return Values:
    <dict> of field:value pairs. Field values correspond to a CSS3.0 
    schema wfmeas table fields.
    
    """
    print 'calculating DC offset'
    from numpy import mean
    m = mean(tr.data())
    return {'meastype': 'mean', 'val1': m, 'units1': 'cts', 'auth': 'autoQC'}
    
def rms(tr,params):
    """
    Return RMS value of input trace.

    Arguments:
    tr - Trace4.1 schema trace object <class 'Dbptr'>
    params - Empty <dict>
    
    Return Values:
    <dict> of field:value pairs. Field values correspond to a CSS3.0 
    schema wfmeas table fields.

    """
    print 'calculating rms'
    from math import fsum, sqrt
    d = tr.data()
    m = fsum(d)/len(d)
    rms = sqrt(fsum([pow(val-m,2) for val in d])/len(d))
    return {'meastype': 'rms', 'val1': rms, 'units1': 'cts', 'auth': 'autoQC'}

def line(tr,params):
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
    print 'calculating linear trend'
    from numpy import arange,polyfit
    d = tr.data()
    time,endtime,nsamp = tr.getv('time','endtime','nsamp')
    m,b = polyfit(arange(time,endtime,(endtime-time)/nsamp),d,1)
    return {'meastype': 'line', 'val1': m,'units1': 'cts/s', 'auth': 'autoQC'}
    
def std(tr,params):
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
    print 'calculating standard deviation'
    from numpy import std,float64
    #Create a copy of self-contained trace object.
    trcp = tr.trcopy()
    trcp.filter(params['filter'])
    #Extract waveform data
    d = trcp.data()
    #Destroy the trace object copy.
    trcp.trdestroy()
    #Calculate the standard deviation (using 64-bit floating
    #point precision)
    sigma = std(d,dtype=float64)
    return {'meastype': 'std', 'val1': sigma, 'units1': 'cts', \
        'filter': params['filter'], 'auth': 'autoQC'}