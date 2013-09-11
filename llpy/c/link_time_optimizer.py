#   Copyright © 2013 Ben Longbons
#
#   This file is part of Python3 bindings for LLVM.
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Lesser General Public License as published
#   by the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Lesser General Public License for more details.
#
#   You should have received a copy of the GNU Lesser General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

''' This header is unusable; the symbols are not found anywhere.

    low-level wrapper of llvm-c/LinkTimeOptimizer.h
'''

import ctypes

from . import _c


_library = _c.Library('???')


lto = _c.opaque('lto')
lto_stati = [
    'UNKNOWN',
    'OPT_SUCCESS',
    'READ_SUCCESS',
    'READ_FAILURE',
    'WRITE_FAILURE',
    'NO_TARGET',
    'NO_WORK',
    'MODULE_MERGE_FAILURE',
    'ASM_FAILURE',

    # Added C-specific error codes
    'NULL_OBJECT',
]
lto_status = _c.enum('lto_status', **{v: k for k, v in enumerate(lto_stati)})
del lto_stati


create_optimizer = _library.function(lto, 'llvm_create_optimizer', [])
destroy_optimizer = _library.function(None, 'llvm_destroy_optimizer', [lto])

llvm_read_object_file = _library.function(lto_status, 'llvm_read_object_file', [lto, ctypes.c_char_p])
llvm_optimize_modules = _library.function(lto_status, 'llvm_optimize_modules', [lto, ctypes.c_char_p])
