#   -*- encoding: utf-8 -*-
#   Copyright © 2014 Ben Longbons
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

''' low-level wrapper of llvm-c/Transforms/PassManagerBuilder.h
'''

import ctypes

from .. import _c

from ..core import _library, _version
from ..core import Bool
from ..core import PassManager


PassManagerBuilder = _c.opaque('PassManagerBuilder')
if _version <= (3, 2):
    bool = ctypes.c_bool
if (3, 3) <= _version:
    bool = Bool

PassManagerBuilderCreate = _library.function(PassManagerBuilder, 'LLVMPassManagerBuilderCreate', [])
PassManagerBuilderDispose = _library.function(None, 'LLVMPassManagerBuilderDispose', [PassManagerBuilder])
PassManagerBuilderSetOptLevel = _library.function(None, 'LLVMPassManagerBuilderSetOptLevel', [PassManagerBuilder, ctypes.c_uint])
PassManagerBuilderSetSizeLevel = _library.function(None, 'LLVMPassManagerBuilderSetSizeLevel', [PassManagerBuilder, ctypes.c_uint])
PassManagerBuilderSetDisableUnitAtATime = _library.function(None, 'LLVMPassManagerBuilderSetDisableUnitAtATime', [PassManagerBuilder, Bool])
PassManagerBuilderSetDisableUnrollLoops = _library.function(None, 'LLVMPassManagerBuilderSetDisableUnrollLoops', [PassManagerBuilder, Bool])
PassManagerBuilderSetDisableSimplifyLibCalls = _library.function(None, 'LLVMPassManagerBuilderSetDisableSimplifyLibCalls', [PassManagerBuilder, Bool])
PassManagerBuilderUseInlinerWithThreshold = _library.function(None, 'LLVMPassManagerBuilderUseInlinerWithThreshold', [PassManagerBuilder, ctypes.c_uint])
PassManagerBuilderPopulateFunctionPassManager = _library.function(None, 'LLVMPassManagerBuilderPopulateFunctionPassManager', [PassManagerBuilder, PassManager])
PassManagerBuilderPopulateModulePassManager = _library.function(None, 'LLVMPassManagerBuilderPopulateModulePassManager', [PassManagerBuilder, PassManager])
PassManagerBuilderPopulateLTOPassManager = _library.function(None, 'LLVMPassManagerBuilderPopulateLTOPassManager', [PassManagerBuilder, PassManager, bool, bool])
