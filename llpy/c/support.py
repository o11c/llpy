#   -*- encoding: utf-8 -*-
#   Copyright © 2015 Ben Longbons
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

''' low-level wrapper of llvm-c/Support.h
'''

import ctypes

from . import _c

from ._c2 import _library, _version

if _version <= (3, 4):
    from .core import Bool

if (3, 5) <= _version:
    Bool = ctypes.c_int
    MemoryBuffer = _c.opaque('MemoryBuffer')

if (3, 4) <= _version:
    LoadLibraryPermanently = _library.function(Bool, 'LLVMLoadLibraryPermanently', [ctypes.c_char_p])
