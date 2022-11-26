from typing import Union, Iterable

from Extensions cimport Search


cimport cython

ctypedef struct PyObject

cdef class Search:
    cdef object search_child
    cdef set valid_search_contexts
