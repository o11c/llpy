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

''' low-level wrapper of llvm-c/ExecutionEngine.h
'''

import ctypes

from . import _c

from .core import _library, _version
from .core import Bool
from .core import Module
from .core import Type
from .core import Value
from .core import ModuleProvider

from .target import TargetData

if (3, 3) <= _version:
    from .target_machine import CodeModel
if (3, 5) <= _version:
    from .target_machine import TargetMachine

GenericValue = _c.opaque('GenericValue')
ExecutionEngine = _c.opaque('ExecutionEngine')
MCJITMemoryManager = _c.opaque('MCJITMemoryManager')
if (3, 3) <= _version:
    class MCJITCompilerOptions(ctypes.Structure):
        _fields_ = [
            ('OptLevel', ctypes.c_uint),
            ('CodeModel', CodeModel),
            ('NoFramePointerElim', Bool),
            ('EnableFastISel', Bool),
        ]
        if (3, 4) <= _version:
            _fields_ += [
                ('MCJMM', MCJITMemoryManager)
            ]

        # Normally I have a rule not to have any calls in llpy.c.* modules,
        # But this is important and doesn't belong elsewhere.
        def __init__(self, *args, **kwargs):
            InitializeMCJITCompilerOptions(ctypes.byref(self), ctypes.sizeof(self))
            ctypes.Structure.__init__(self, *args, **kwargs)

if (3, 4) <= _version:
    MemoryManagerAllocateCodeSectionCallback = ctypes.CFUNCTYPE(ctypes.POINTER(ctypes.c_uint8), *[ctypes.c_void_p, ctypes.c_size_t, ctypes.c_uint, ctypes.c_uint, ctypes.c_char_p]);
    MemoryManagerAllocateDataSectionCallback = ctypes.CFUNCTYPE(ctypes.POINTER(ctypes.c_uint8), *[ctypes.c_void_p, ctypes.c_size_t, ctypes.c_uint, ctypes.c_uint, ctypes.c_char_p, Bool])
    MemoryManagerFinalizeMemoryCallback = ctypes.CFUNCTYPE(Bool, *[ctypes.c_void_p, ctypes.POINTER(_c.string_buffer)])
    MemoryManagerDestroyCallback = ctypes.CFUNCTYPE(None, *[ctypes.c_void_p])


LinkInJIT = _library.function(None, 'LLVMLinkInJIT', [])
# not in the header until 3.3, but in the library in 3.0
LinkInMCJIT = _library.function(None, 'LLVMLinkInMCJIT', [])
LinkInInterpreter = _library.function(None, 'LLVMLinkInInterpreter', [])

CreateGenericValueOfInt = _library.function(GenericValue, 'LLVMCreateGenericValueOfInt', [Type, ctypes.c_ulonglong, Bool])
CreateGenericValueOfPointer = _library.function(GenericValue, 'LLVMCreateGenericValueOfPointer', [ctypes.c_void_p])
CreateGenericValueOfFloat = _library.function(GenericValue, 'LLVMCreateGenericValueOfFloat', [Type, ctypes.c_double])
GenericValueIntWidth = _library.function(ctypes.c_uint, 'LLVMGenericValueIntWidth', [GenericValue])
GenericValueToInt = _library.function(ctypes.c_ulonglong, 'LLVMGenericValueToInt', [GenericValue, Bool])
GenericValueToPointer = _library.function(ctypes.c_void_p, 'LLVMGenericValueToPointer', [GenericValue])
GenericValueToFloat = _library.function(ctypes.c_double, 'LLVMGenericValueToFloat', [Type, GenericValue])
DisposeGenericValue = _library.function(None, 'LLVMDisposeGenericValue', [GenericValue])

CreateExecutionEngineForModule = _library.function(Bool, 'LLVMCreateExecutionEngineForModule', [ctypes.POINTER(ExecutionEngine), Module, ctypes.POINTER(_c.string_buffer)])
CreateInterpreterForModule = _library.function(Bool, 'LLVMCreateInterpreterForModule', [ctypes.POINTER(ExecutionEngine), Module, ctypes.POINTER(_c.string_buffer)])
CreateJITCompilerForModule = _library.function(Bool, 'LLVMCreateJITCompilerForModule', [ctypes.POINTER(ExecutionEngine), Module, ctypes.c_uint, ctypes.POINTER(_c.string_buffer)])

if (3, 3) <= _version:
    InitializeMCJITCompilerOptions = _library.function(None, 'LLVMInitializeMCJITCompilerOptions', [ctypes.POINTER(MCJITCompilerOptions), ctypes.c_size_t])
    CreateMCJITCompilerForModule = _library.function(Bool, 'LLVMCreateMCJITCompilerForModule', [ctypes.POINTER(ExecutionEngine), Module, ctypes.POINTER(MCJITCompilerOptions), ctypes.c_size_t, ctypes.POINTER(_c.string_buffer)])

CreateExecutionEngine = _library.function(Bool, 'LLVMCreateExecutionEngine', [ctypes.POINTER(ExecutionEngine), ModuleProvider, ctypes.POINTER(_c.string_buffer)])
CreateInterpreter = _library.function(Bool, 'LLVMCreateInterpreter', [ctypes.POINTER(ExecutionEngine), ModuleProvider, ctypes.POINTER(_c.string_buffer)])
CreateJITCompiler = _library.function(Bool, 'LLVMCreateJITCompiler', [ctypes.POINTER(ExecutionEngine), ModuleProvider, ctypes.c_uint, ctypes.POINTER(_c.string_buffer)])
DisposeExecutionEngine = _library.function(None, 'LLVMDisposeExecutionEngine', [ExecutionEngine])
RunStaticConstructors = _library.function(None, 'LLVMRunStaticConstructors', [ExecutionEngine])
RunStaticDestructors = _library.function(None, 'LLVMRunStaticDestructors', [ExecutionEngine])
RunFunctionAsMain = _library.function(ctypes.c_int, 'LLVMRunFunctionAsMain', [ExecutionEngine, Value, ctypes.c_uint, ctypes.POINTER(ctypes.c_char_p), ctypes.POINTER(ctypes.c_char_p)])

RunFunction = _library.function(GenericValue, 'LLVMRunFunction', [ExecutionEngine, Value, ctypes.c_uint, ctypes.POINTER(GenericValue)])
FreeMachineCodeForFunction = _library.function(None, 'LLVMFreeMachineCodeForFunction', [ExecutionEngine, Value])
AddModule = _library.function(None, 'LLVMAddModule', [ExecutionEngine, Module])
AddModuleProvider = _library.function(None, 'LLVMAddModuleProvider', [ExecutionEngine, ModuleProvider])
RemoveModule = _library.function(Bool, 'LLVMRemoveModule', [ExecutionEngine, Module, ctypes.POINTER(Module), ctypes.POINTER(_c.string_buffer)])
RemoveModuleProvider = _library.function(Bool, 'LLVMRemoveModuleProvider', [ExecutionEngine, ModuleProvider, ctypes.POINTER(Module), ctypes.POINTER(_c.string_buffer)])
FindFunction = _library.function(Bool, 'LLVMFindFunction', [ExecutionEngine, ctypes.c_char_p, ctypes.POINTER(Value)])
RecompileAndRelinkFunction = _library.function(ctypes.c_void_p, 'LLVMRecompileAndRelinkFunction', [ExecutionEngine, Value])
GetExecutionEngineTargetData = _library.function(TargetData, 'LLVMGetExecutionEngineTargetData', [ExecutionEngine])
if (3, 5) <= _version:
    GetExecutionEngineTargetMachine = _library.function(TargetMachine, 'LLVMGetExecutionEngineTargetMachine', [ExecutionEngine])
AddGlobalMapping = _library.function(None, 'LLVMAddGlobalMapping', [ExecutionEngine, Value, ctypes.c_void_p])
GetPointerToGlobal = _library.function(ctypes.c_void_p, 'LLVMGetPointerToGlobal', [ExecutionEngine, Value])

if (3, 4) <= _version:
    CreateSimpleMCJITMemoryManager = _library.function(MCJITMemoryManager, 'LLVMCreateSimpleMCJITMemoryManager', [ctypes.c_void_p, MemoryManagerAllocateCodeSectionCallback, MemoryManagerAllocateDataSectionCallback, MemoryManagerFinalizeMemoryCallback, MemoryManagerDestroyCallback])
    DisposeMCJITMemoryManager = _library.function(None, 'LLVMDisposeMCJITMemoryManager', [MCJITMemoryManager])
