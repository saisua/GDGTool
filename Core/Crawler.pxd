# distutils: language=c++

cimport cython
import re

from Core.Crawler cimport Crawler

ctypedef struct PyObject

cdef class Crawler:
    cdef dict crawler_sites
    cdef dict next_level_sites

    cdef list _crawler_avaliable_tabs
    cdef cython.uint _crawler_open_tabs

    cdef set crawler_visited_urls
    cdef set crawler_blocked_domains
    cdef dict crawler_valid_robots_domains

    cdef dict crawler_website_data

    cdef cython.uint crawler_depth
    
    cdef cython.bint _crawler_rotate_request
    cdef cython.bint _crawler_rotate_in_progress

    cdef re.Pattern crawler_domain_regex
    cdef re.Pattern crawler_robots_regex

    cdef cython.bint Crawler_init
    cdef cython.bint Crawler_enter