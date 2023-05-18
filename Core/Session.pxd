# distutils: language=c++

cimport cython

from Core.Session cimport Session

ctypedef struct PyObject

cdef class Session:
    cdef object session_parent
    cdef str session_name

    cdef cython.bint autosave_session
    cdef cython.bint autoload_session

    cdef str session_storage_path

    cdef list session_contexts
    cdef cython.bint Session_init

    cdef set _fall_missing_session
