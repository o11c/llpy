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

''' low-level wrapper of llvm-c/IRReader.h
'''

import ctypes

from . import _c

from .core import _library, _version
from .core import Bool
from .core import Context
from .core import Module
from .core import MemoryBuffer

from ..utils import cuntested as untested


if (3, 4) <= _version:
    ParseIRInContext = _library.function(Bool, 'LLVMParseIRInContext', [Context, MemoryBuffer, ctypes.POINTER(Module), ctypes.POINTER(_c.string_buffer)])
