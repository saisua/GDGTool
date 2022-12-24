# distutils: language=c++

cimport cython

from Core.Storage cimport Storage

ctypedef struct PyObject

cdef class Storage:
    cdef object storage_browser_parent
    cdef str storage_base_path
    cdef str storage_path

    cdef object storage_library
    cdef cython.uint max_memory_domains

    cdef dict storage_data_repr
    cdef dict file_cache
    cdef dict storage_data

    cdef object to_filename_re

    cdef object storage_dict_cls

    cdef cython.bint Storage_init
