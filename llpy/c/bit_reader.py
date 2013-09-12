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

''' low-level wrapper of llvm-c/BitReader.h
'''

import ctypes

from . import _c

from .core import _library
from .core import Bool
from .core import Context
from .core import Module
from .core import ModuleProvider
from .core import MemoryBuffer


ParseBitcode = _library.function(Bool, 'LLVMParseBitcode', [MemoryBuffer, ctypes.POINTER(Module), ctypes.POINTER(_c.string_buffer)])
ParseBitcodeInContext = _library.function(Bool, 'LLVMParseBitcodeInContext', [Context, MemoryBuffer, ctypes.POINTER(Module), ctypes.POINTER(_c.string_buffer)])
GetBitcodeModuleInContext = _library.function(Bool, 'LLVMGetBitcodeModuleInContext', [Context, MemoryBuffer, ctypes.POINTER(Module), ctypes.POINTER(_c.string_buffer)]);
GetBitcodeModule = _library.function(Bool, 'LLVMGetBitcodeModule', [MemoryBuffer, ctypes.POINTER(Module), ctypes.POINTER(_c.string_buffer)]);

# deprecated
GetBitcodeModuleProviderInContext = _library.function(Bool, 'LLVMGetBitcodeModuleProviderInContext', [Context, MemoryBuffer, ctypes.POINTER(ModuleProvider), ctypes.POINTER(_c.string_buffer)]);
GetBitcodeModuleProvider = _library.function(Bool, 'LLVMGetBitcodeModuleProvider', [MemoryBuffer, ctypes.POINTER(ModuleProvider), ctypes.POINTER(_c.string_buffer)]);
