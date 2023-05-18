# distutils: language=c++

cimport cython

from Core.Pipeline cimport Pipeline

ctypedef struct PyObject

cdef class Pipeline:
    cdef tuple pipe_names
    cdef list _start_management
    cdef list _url_management
    cdef list _page_management
    cdef list _data_management
    cdef list _end_management
    cdef list _post_management
    cdef list _event_management
    cdef list _route_management

    cdef cython.bint Pipeline_init
