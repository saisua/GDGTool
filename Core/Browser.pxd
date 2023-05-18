# distutils: language=c++

cimport cython

from Core.Browser cimport Browser
from Core.utils.children cimport Children

ctypedef struct PyObject

cdef class Browser(Children):
    cdef object _storage
    cdef object _pipeline
    cdef object _session
    cdef object _resources
    cdef object _rotating_proxies
    cdef object _search

    cdef object __playwright_instance
    cdef object _playwright_manager

    cdef readonly object browser

    cdef cython.bint browser_headless
    cdef str browser_name
    cdef cython.bint browser_persistent
    cdef cython.bint browser_install_addons

    cdef cython.bint _browser_use_proxies
    cdef cython.bint _browser_closed
    cdef cython.bint _browser_disconected

    cdef cython.bint Browser_init
    cdef cython.bint Browser_enter

    cdef str _browser_open_wait_until