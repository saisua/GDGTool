cimport cython

from Core.utils cimport children

cdef class Children:
    cdef tuple children

    cpdef __init__(self, tuple children)
    cpdef object __getattr__(self, str attr)
