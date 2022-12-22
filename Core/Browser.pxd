# distutils: language=c++

cimport cython
import re

from Core.Browser cimport Browser

ctypedef struct PyObject

cdef class Browser:
    cdef object _storage
    cdef object _pipeline
    cdef object _session
    cdef object _resources
    cdef object _rotating_proxies
    cdef object _search

    cdef object __playwright_instance
    cdef object _playwright_manager

    cdef object browser

    cdef cython.bint browser_headless
    cdef str browser_name
    cdef cython.bint browser_persistent
    browser_install_addons: cython.bint

    _browser_use_proxies: cython.bint
    _browser_closed: cython.bint = True
    _browser_disconected: cython.bint

    Browser_init: cython.bint
    Browser_enter: cython.bint

    _browser_open_wait_until: str