# distutils: language=c++

import asyncio
import cython

from Core.Resources cimport Resources

ctypedef struct PyObject

cdef class Resources:
    cdef object _manager
    cdef object resources_pool

    cdef cython.bint Resources_init
