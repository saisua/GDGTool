# distutils: language=c++

import asyncio
from distutils.command.install_egg_info import to_filename
import os
import pickle, json
cimport cython
import re

from typing import Iterable
from datetime import datetime

from Core.Storage cimport Storage

ctypedef struct PyObject

cdef class Storage:
    cdef str storage_base_path
    cdef str storage_path

    cdef object storage_library
    cdef cython.uint max_memory_domains

    cdef dict storage_data_repr
    cdef dict file_cache
    cdef dict storage_data

    cdef object to_filename_re

    cdef cython.bint Storage_init
