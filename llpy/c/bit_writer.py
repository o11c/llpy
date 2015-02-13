#   -*- encoding: utf-8 -*-
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

''' low-level wrapper of llvm-c/BitWriter.h
'''

import ctypes

from .core import _library
from .core import Module

from ..utils import cuntested as untested


WriteBitcodeToFile = _library.function(ctypes.c_int, 'LLVMWriteBitcodeToFile', [Module, ctypes.c_char_p])
WriteBitcodeToFD = _library.function(ctypes.c_int, 'LLVMWriteBitcodeToFD', [Module, ctypes.c_int, ctypes.c_int, ctypes.c_int])

# deprecated
WriteBitcodeToFileHandle = _library.function(ctypes.c_int, 'LLVMWriteBitcodeToFileHandle', [Module, ctypes.c_int])
WriteBitcodeToFileHandle = untested(WriteBitcodeToFileHandle)
