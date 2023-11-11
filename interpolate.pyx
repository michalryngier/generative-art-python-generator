# interpolate.pyx
# cython: language_level=3
# distutils: language = c++

cimport cython

cdef extern from "cmath":
    double pow(double x, double y)

@cython.boundscheck(False)
@cython.wraparound(False)
def interpolate(double t, int[:, ::1] points):
    if t == 0:
        return [points[0][0], points[0][1]]

    cdef int order = points.shape[0] - 1

    if t == 1:
        return [points[order][0], points[order][1]]

    cdef double mt = 1 - t
    cdef int p[points.shape[0]][2]
    cdef int i = 0
    for i in range(points.shape[0]):
        p[i][:] = points[i]

    # linear curve
    if order == 1:
        return [
            mt *  float(p[0][0]) + t *  float(p[1][0]),
            mt *  float(p[0][1]) + t *  float(p[1][1])
        ]

    # quadratic or cubic curve
    cdef double mt2 = mt * mt
    cdef double t2 = t * t
    cdef double a, b, c, d = 0
    if 2 <= order < 4:
        if order == 2:
            p = [p[0], p[1], p[2], [0, 0]]
            a = mt2
            b = mt * t * 2
            c = t2
        else:
            a = mt2 * mt
            b = mt2 * t * 3
            c = mt * t2 * 3
            d = t * t2

        return [
            a * float(p[0][0]) + b *  float(p[1][0]) + c *  float(p[2][0]) + d *  float(p[3][0]),
            a *  float(p[0][1]) + b *  float(p[1][1]) + c *  float(p[2][1]) + d *  float(p[3][1])
        ]

    # Higher order curves - use de Casteljau's computation.
    cdef int[:, ::1] dCpts = points.copy()

    cdef int i
    cdef double x0, y0, x1, y1

    while dCpts.shape[0] > 1:
        for i in range(dCpts.shape[0] - 1):
            # Explicit type declarations for the elements of dCpts
            x0 = dCpts[i, 0]
            y0 = dCpts[i, 1]
            x1 = dCpts[i + 1, 0]
            y1 = dCpts[i + 1, 1]

            # Update the elements of dCpts with explicit types
            dCpts[i, 0] = <int> (x0 + (x1 - x0) * t)
            dCpts[i, 1] = <int> (y0 + (y1 - y0) * t)

        # Resize the memory view
        dCpts = dCpts[:-1, :]

    # Convert the final result to a Python list
    return dCpts[0, :].tolist()
