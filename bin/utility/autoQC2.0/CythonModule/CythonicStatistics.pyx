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
        
def skew(d):
    """Return the skewness of the values.
    
    Skewness is calculated as mu3 / mu2**(3/2) where mu3 is the
    3rd central moment and mu2 is the second central moment.
    """
    cdef int i, l
    cdef double m, mu2, mu3, s, s2, s3
    x2, x3 = [], []
    s, s2, s3 = 0.0, 0.0, 0.0
    l = len(d)
    r = range(l)

    for i in r:
        s += d[i]
    m = s/l

    for i in r:
        s2 += pow((d[i]-m), 2)
        s3 += pow((d[i]-m), 3)
    mu2 = s2/l
    mu3 = s3/l

    return mu3/(mu2**(3.0/2.0))

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
    cdef int le, i
    cdef float s
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
    for i in range(le):
        s += d[i]
    return s