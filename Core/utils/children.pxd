# distutils: language=c++

cimport cython

from Core.utils.children cimport Children

ctypedef struct PyObject

cdef class Children:
    pass