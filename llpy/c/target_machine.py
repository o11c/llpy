#   -*- encoding: utf-8 -*-
#   Copyright © 2013-2014 Ben Longbons
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

''' low-level wrapper of llvm-c/TargetMachine.h
'''

import ctypes

from . import _c

from .core import _library, _version
from .core import Bool
from .core import Module
from .core import MemoryBuffer
from .core import PassManager

from .target import TargetData

from ..utils import cuntested as untested


if (3, 1) <= _version:

    TargetMachine = _c.opaque('TargetMachine')
    Target = _c.opaque('Target')

    codegen_opt_levels = [
        'None',
        'Less',
        'Default',
        'Aggressive',
    ]
    CodeGenOptLevel = _c.enum('CodeGenOptLevel', **{v: k for k, v in enumerate(codegen_opt_levels)})
    del codegen_opt_levels

    reloc_modes = [
        'Default',
        'Static',
        'PIC',
        'DynamicNoPic',
    ]
    RelocMode = _c.enum('RelocMode', **{v: k for k, v in enumerate(reloc_modes)})
    del reloc_modes

    code_models = [
        'Default',
        'JITDefault',
        'Small',
        'Kernel',
        'Medium',
        'Large',
    ]
    CodeModel = _c.enum('CodeModel', **{v: k for k, v in enumerate(code_models)})
    del code_models

    codegen_filetypes = [
        'Assembly',
        'Object',
    ]
    CodeGenFileType = _c.enum('CodeGenFileType', **{v: k for k, v in enumerate(codegen_filetypes)})
    del codegen_filetypes


    GetFirstTarget = _library.function(Target, 'LLVMGetFirstTarget', [])
    GetFirstTarget = untested(GetFirstTarget)
    GetNextTarget = _library.function(Target, 'LLVMGetNextTarget', [Target])
    GetNextTarget = untested(GetNextTarget)
if (3, 4) <= _version:
    GetTargetFromName = _library.function(Target, 'LLVMGetTargetFromName', [ctypes.c_char_p])
    GetTargetFromName = untested(GetTargetFromName)
    GetTargetFromTriple = _library.function(Bool, 'LLVMGetTargetFromTriple', [ctypes.c_char_p, ctypes.POINTER(Target), ctypes.POINTER(_c.string_buffer)])
    GetTargetFromTriple = untested(GetTargetFromTriple)

if (3, 1) <= _version:
    GetTargetName = _library.function(ctypes.c_char_p, 'LLVMGetTargetName', [Target])
    GetTargetName = untested(GetTargetName)
    GetTargetDescription = _library.function(ctypes.c_char_p, 'LLVMGetTargetDescription', [Target])
    GetTargetDescription = untested(GetTargetDescription)
    TargetHasJIT = _library.function(Bool, 'LLVMTargetHasJIT', [Target])
    TargetHasJIT = untested(TargetHasJIT)
    TargetHasTargetMachine = _library.function(Bool, 'LLVMTargetHasTargetMachine', [Target])
    TargetHasTargetMachine = untested(TargetHasTargetMachine)
    TargetHasAsmBackend = _library.function(Bool, 'LLVMTargetHasAsmBackend', [Target])
    TargetHasAsmBackend = untested(TargetHasAsmBackend)

    CreateTargetMachine = _library.function(TargetMachine, 'LLVMCreateTargetMachine', [Target, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, CodeGenOptLevel, RelocMode, CodeModel])
    CreateTargetMachine = untested(CreateTargetMachine)
    DisposeTargetMachine = _library.function(None, 'LLVMDisposeTargetMachine', [TargetMachine])
    DisposeTargetMachine = untested(DisposeTargetMachine)
    GetTargetMachineTarget = _library.function(Target, 'LLVMGetTargetMachineTarget', [TargetMachine])
    GetTargetMachineTarget = untested(GetTargetMachineTarget)
    GetTargetMachineTriple = _library.function(_c.string_buffer, 'LLVMGetTargetMachineTriple', [TargetMachine])
    GetTargetMachineTriple = untested(GetTargetMachineTriple)
    GetTargetMachineCPU = _library.function(_c.string_buffer, 'LLVMGetTargetMachineCPU', [TargetMachine])
    GetTargetMachineCPU = untested(GetTargetMachineCPU)
    GetTargetMachineFeatureString = _library.function(_c.string_buffer, 'LLVMGetTargetMachineFeatureString', [TargetMachine])
    GetTargetMachineFeatureString = untested(GetTargetMachineFeatureString)
    GetTargetMachineData = _library.function(TargetData, 'LLVMGetTargetMachineData', [TargetMachine])
    GetTargetMachineData = untested(GetTargetMachineData)
if (3, 4) <= _version:
    SetTargetMachineAsmVerbosity = _library.function(None, 'LLVMSetTargetMachineAsmVerbosity', [TargetMachine, Bool])
    SetTargetMachineAsmVerbosity = untested(SetTargetMachineAsmVerbosity)
if (3, 1) <= _version:
    TargetMachineEmitToFile = _library.function(Bool, 'LLVMTargetMachineEmitToFile', [TargetMachine, Module, ctypes.c_char_p, CodeGenFileType, ctypes.POINTER(_c.string_buffer)])
    TargetMachineEmitToFile = untested(TargetMachineEmitToFile)
if (3, 3) <= _version:
    TargetMachineEmitToMemoryBuffer = _library.function(Bool, 'LLVMTargetMachineEmitToMemoryBuffer', [TargetMachine, Module, CodeGenFileType, ctypes.POINTER(_c.string_buffer), ctypes.POINTER(MemoryBuffer)])
    TargetMachineEmitToMemoryBuffer = untested(TargetMachineEmitToMemoryBuffer)

if (3, 4) <= _version:
    GetDefaultTargetTriple = _library.function(_c.string_buffer, 'LLVMGetDefaultTargetTriple', [])
    GetDefaultTargetTriple = untested(GetDefaultTargetTriple)
if (3, 5) <= _version:
    AddAnalysisPasses = _library.function(None, 'LLVMAddAnalysisPasses', [TargetMachine, PassManager])
    AddAnalysisPasses = untested(AddAnalysisPasses)
