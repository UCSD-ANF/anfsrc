def mean(d):
    """Return the mean value."""
    cdef int i, l
    cdef double s
    s = 0.0
    l = len(d)
    for i in range(l):
        s += d[i]
    return s/l

def rms(d):
    """Return the root-mean-square value."""
    cdef int i, l
    cdef double m, s
    s = 0.0
    l = len(d)
    for i in range(l):
        s += d[i]
    m = s/l
    s = 0.0
    for i in range(l):
        s += pow((d[i]-m), 2)/l
    return pow(s, (1.0/2.0))

def var(d):
    """Return the variance of the values.

    Variance is the second central moment.
    """
    cdef int i, L
    cdef double m, mu2, s, s2
    s, s2, s3 = 0.0, 0.0, 0.0
    L = len(d)
    r = range(L)

    for i in r:
        s += d[i]
    m = s/L

    for i in r:
        s2 += pow((d[i]-m), 2)
    mu2 = s2/L

    return mu2

def skew(d):
    """Return the skewness of the values.

    Skewness is calculated as mu3 / mu2**(3/2) where mu3 is the
    3rd central moment and mu2 is the second central moment.
    """
    cdef int i, L
    cdef double m, mu2, mu3, s, s2, s3
    s, s2, s3 = 0.0, 0.0, 0.0
    L = len(d)
    r = range(L)

    for i in r:
        s += d[i]
    m = s/L

    for i in r:
        s2 += pow((d[i]-m), 2)
        s3 += pow((d[i]-m), 3)
    mu2 = s2/L
    mu3 = s3/L

    return mu3/(mu2**(3.0/2.0))

#def skew(d, twin, samprate):
#    """Return the maximum skewness of the values in a leaping window.
#
#    Skewness is calculated as mu3 / mu2**(3/2) where mu3 is the
#    3rd central moment and mu2 is the second central moment.
#    """
#    import time
#    cdef int i, j, l
#    cdef double m, mu2, mu3, s, s2, s3
#    skewness = []
#    s, s2, s3 = 0.0, 0.0, 0.0
#    wlen = twin*samprate
#    end = int(len(d) - wlen)
#    r1 = range(0, end, int((wlen/2) - (wlen/2)%1))
#
#    for i in r1:
#        d2 = detrend(range(twin),d[i:i+twin])[1]
#        r2 = range(len(d2))
#        s = 0.0
#        for j in r2:
#            s += d2[j]
#        m = s/wlen
#
#        s2 = 0.0
#        s3 = 0.0
#        for j in r2:
#            s2 += pow((d2[j]-m), 2)
#            s3 += pow((d2[j]-m), 3)
#        mu2 = s2/wlen
#        mu3 = s3/wlen
#        skewness.append(mu3/(mu2**(3.0/2.0)))
#    return max(skewness)

def detrend(x, y):
    import numpy as np
    if len(x) > len(y): x = x[:(len(y) - len(x))]
    if len(y) > len(x): y =  y[:(len(x) - len(y))]
    m, b = np.polyfit(x, y, 1)
    y = [y[i] - (m*x[i] + b) for i in range (len(y))]
    return x, y
    
def lh_ave(d, int i, int nsamp):
    """
    Return the average of the nsamp values to the left of i in d.
    
    """
    cdef int le
    cdef float s
    le = len(d)
    if i == 0:
        return d[0]
    if i-nsamp < 0: nsamp = i
    s = cysum(d[i-nsamp:i])
    return s / nsamp

def rh_ave(d, int i, int nsamp):
    """
    Return the average of the nsamp values to the right of i in d.
    
    """
    cdef int le
    cdef float s
    le = len(d)
    if i == le:
        return d[-1]
    if i+nsamp > le: nsamp = le - i
    s = cysum(d[i:i+nsamp])
    return s / nsamp
    
def cysum(d):
    """Return the sum of elements in d."""
    cdef int le, i
    cdef float s
    s = 0.0
    i = 0
    le = len(d)
    for i in range(le):
        s += d[i]
    return s
