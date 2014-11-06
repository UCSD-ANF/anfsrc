import numpy as np
#from core import read_tt_vector

class LinearIndex():
    '''
    A class to convert between 1D and 3D indices. The z-index varies
    fastest, y-index second fastest and x-index slowest.
    '''
    def __init__(self, int nx, int ny, int nz):
        import numpy as np
        cdef int i, x, y, z
        self.index_1D = np.zeros(nx * ny * nz, dtype=np.ndarray)
        self.index_3D = np.zeros([nx, ny, nz], dtype=np.int)
        self.nx = nx
        self.ny = ny
        self.nz = nz
        i, x = 0, 0
        while x < nx:
            y = 0
            while y < ny:
                z = 0
                while z < nz:
                    self.index_1D[i] = [x, y, z]
                    self.index_3D[x, y, z] = i
                    i += 1
                    z += 1
                y += 1
            x += 1

    def convert_to_1D(self, int x, int y, int z):
        '''
        Given a 3D index, return the corresponding 1D index.
        '''
        return self.index_3D[x, y, z]

    def convert_to_3D(self, i):
        '''
        Given a 1D index, return the corresponding 3D index.
        '''
        return self.index_1D[i]

def grid_search_abs(qx, qy, qz, arrivals, pred_tts, linear_index):
    '''
    Find the minimum of the absolute value of the calculated origin
    time following Ben-Zion et al., 1992 (JGR)
    '''
    cdef float best_misfit = 1000000.0
    cdef int i, j, k, nx, ny, nz
    nx = len(qx)
    ny = len(qy)
    nz = len(qz)
    stas = [arrival.sta for arrival in arrivals]
    i = 0
    while i < nx:
        j = 0
        while j < ny:
            k = 0
            while k < nz:
                index = linear_index.convert_to_1D(i, j, k)
                if min([pred_tts[sta][index] for sta in pred_tts]) < 0:
                    k += 1
                    continue
                estimated_origin_times = [arrival.time -\
                        pred_tts[arrival.sta][index] for arrival in arrivals]
                origin_time = sum(estimated_origin_times) /\
                        len(estimated_origin_times)
                residuals = [estimated_origin_time - origin_time for\
                        estimated_origin_time in estimated_origin_times]
                misfit = sum([abs(residual) for residual in residuals])
                if misfit < best_misfit:
                    best_misfit = misfit
                    x, y, z = qx[i], qy[j], qz[k]
                    best_origin_time = origin_time
                k += 1
            j += 1
        i += 1
    return x, y, z, best_origin_time, best_misfit

#def grid_search_abs_dep_2014310(stas, qx, qy, qz, arrival_times, linear_index, tt_map_dir):
#    '''
#    Find the minimum of the absolute value of the calculated origin
#    time following Ben-Zion et al., 1992 (JGR)
#    '''
#    cdef float best_misfit = 1000000.0
#    cdef int i, j, k, nx, ny, nz
#    nx = len(qx)
#    ny = len(qy)
#    nz = len(qz)
#    i = 0
#    while i < nx:
#        j = 0
#        while j < ny:
#            k = 0
#            while k < nz:
#                index = linear_index.convert_to_1D(qx[i], qy[j], qz[k])
##Read the travel times for this node from the travel time file
#                calc_tts = read_tt_vector(stas,
#                                          index,
#                                          tt_map_dir)
#                if min(calc_tts) < 0:
#                    k += 1
#                    continue
#                estimated_origin_times = arrival_times - calc_tts
#                origin_time = estimated_origin_times.mean()
#                residuals = estimated_origin_times - origin_time
#                misfit = abs(residuals).sum()
#                if misfit < best_misfit:
#                    best_misfit = misfit
#                    x, y, z = qx[i], qy[j], qz[k]
#                    best_origin_time = origin_time
#                k += 1
#            j += 1
#        i += 1
#    return x, y, z, best_origin_time, best_misfit
