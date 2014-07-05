def divide_through(data, divisor):
    return [int(round(d / divisor)) for d in data]

def divide_through_2(data, divisor):
    cdef int length
    length = len(data)
    ret = []
    for i in range(length):
        ret += [int(round(data[i] / divisor))]
    return ret
