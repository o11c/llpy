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

''' low-level wrapper of llvm-c/Initialization.h
'''

from .core import _library, _version
from .core import PassRegistry


InitializeCore = _library.function(None, 'LLVMInitializeCore', [PassRegistry])
InitializeTransformUtils = _library.function(None, 'LLVMInitializeTransformUtils', [PassRegistry])
InitializeScalarOpts = _library.function(None, 'LLVMInitializeScalarOpts', [PassRegistry])
if (3, 3) <= _version:
    InitializeObjCARCOpts = _library.function(None, 'LLVMInitializeObjCARCOpts', [PassRegistry])
if (3, 1) <= _version:
    InitializeVectorization = _library.function(None, 'LLVMInitializeVectorization', [PassRegistry])
InitializeInstCombine = _library.function(None, 'LLVMInitializeInstCombine', [PassRegistry])
InitializeIPO = _library.function(None, 'LLVMInitializeIPO', [PassRegistry])
InitializeInstrumentation = _library.function(None, 'LLVMInitializeInstrumentation', [PassRegistry])
InitializeAnalysis = _library.function(None, 'LLVMInitializeAnalysis', [PassRegistry])
InitializeIPA = _library.function(None, 'LLVMInitializeIPA', [PassRegistry])
InitializeCodeGen = _library.function(None, 'LLVMInitializeCodeGen', [PassRegistry])
InitializeTarget = _library.function(None, 'LLVMInitializeTarget', [PassRegistry])
