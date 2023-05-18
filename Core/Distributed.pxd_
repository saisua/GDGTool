# distutils: language=c++

cimport cython

from Core.Server cimport Server, Client

ctypedef struct PyObject

cdef class Server:
    cdef object _server_loop
    cdef set _server_exposed

    cdef cython.bint Server_init

cdef class Client:
    cdef object crawler
    cdef set _exposed
    cdef dict sited
