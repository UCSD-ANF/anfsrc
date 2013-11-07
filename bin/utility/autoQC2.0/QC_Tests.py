def DC_offset(tr,params):
    """A test for DC offset greater than some threshold."""
    print 'Running DC_offset'
    from math import fsum
    d = tr.data()
    m = fsum(d)/len(d)
    return {'meastype':'mean','val1':m,'units1':'cts','auth':'autoQC'}

########################################################################
    
def RMS(tr,params):
    """A test for RMS greater than some threshold (noisy) or below\
    some threshold (flatline)."""
    print 'Running RMS'
    from math import fsum, sqrt
    d = tr.data()
    #Compute the mean.
    m = fsum(d)/len(d)
    #Compute the demeaned RMS
    rms = sqrt(fsum([pow(val-m,2) for val in d])/len(d))
    return {'meastype':'RMS','val1':rms,'units1':'cts','auth':'autoQC'}
    
########################################################################

def linear_trend(tr,params):
    """A test for a linear trend in data with slope greater than\
    some threshold."""
    print 'Running linear_trend'
    from numpy import arange,polyfit
    #Extract waveform data fom self-contained trace object.
    d = tr.data()
    #Retrieve data time, endtime and nsamp values
    time,endtime,nsamp = tr.getv('time','endtime','nsamp')
    #Find the line which best fits the data in the least squares
    #sense.
    m,b = polyfit(arange(time,endtime,(endtime-time)/nsamp),d,1)
    #If the slope is outside the acceptable threshold, report a
    #QC issue.
    #return {'meastype':'line','val1':m,'units1':'cts/s','val2':b,\
    #    'units2':'cts','auth':'autoQC'}
    #y-intercept (b) is overflowing fied 'val2' in the wfmeas table and
    #so is being omitted until a solution is found.
    return {'meastype':'line','val1':m,'units1':'cts/s','auth':'autoQC'}
########################################################################
    
def STD(tr,params):
    """A test for standard deviation greater than some threshold\
    ."""
    print 'Running STD'
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
    return {'meastype':'STD','val1':sigma,'units1':'cts',\
        'filter':params['filter'],'auth':'autoQC'}

########################################################################
  
def skew(tr,params):
    print 'Running skew'
#    from scipy import skew
#   Use scipy skew() method. Need scipy.
    d = tr.data()
    return {'meastype':'skew','val1':skew(d),'units1':'unitless','auth':'autoQC'}    