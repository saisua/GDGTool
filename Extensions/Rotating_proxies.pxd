from itertools import cycle
cimport cython

from Extensions.Rotating_proxies cimport Rotating_proxies

ctypedef struct PyObject

cdef class Rotating_proxies:
    cdef object rotating_child
    cdef list _rotating_proxies
    cdef object __rotating_proxy

    cdef cython.bint Rotating_proxies_init
