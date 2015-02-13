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

from ..utils import cuntested as untested


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
    MemoryManagerAllocateCodeSectionCallback = ctypes.CFUNCTYPE(ctypes.POINTER(ctypes.c_uint8), *[ctypes.c_void_p, ctypes.c_size_t, ctypes.c_uint, ctypes.c_uint, ctypes.c_char_p])
    MemoryManagerAllocateDataSectionCallback = ctypes.CFUNCTYPE(ctypes.POINTER(ctypes.c_uint8), *[ctypes.c_void_p, ctypes.c_size_t, ctypes.c_uint, ctypes.c_uint, ctypes.c_char_p, Bool])
    MemoryManagerFinalizeMemoryCallback = ctypes.CFUNCTYPE(Bool, *[ctypes.c_void_p, ctypes.POINTER(_c.string_buffer)])
    MemoryManagerDestroyCallback = ctypes.CFUNCTYPE(None, *[ctypes.c_void_p])


LinkInJIT = _library.function(None, 'LLVMLinkInJIT', [])
LinkInJIT = untested(LinkInJIT)
# not in the header until 3.3, but in the library in 3.0
LinkInMCJIT = _library.function(None, 'LLVMLinkInMCJIT', [])
LinkInMCJIT = untested(LinkInMCJIT)
LinkInInterpreter = _library.function(None, 'LLVMLinkInInterpreter', [])
LinkInInterpreter = untested(LinkInInterpreter)

CreateGenericValueOfInt = _library.function(GenericValue, 'LLVMCreateGenericValueOfInt', [Type, ctypes.c_ulonglong, Bool])
CreateGenericValueOfInt = untested(CreateGenericValueOfInt)
CreateGenericValueOfPointer = _library.function(GenericValue, 'LLVMCreateGenericValueOfPointer', [ctypes.c_void_p])
CreateGenericValueOfPointer = untested(CreateGenericValueOfPointer)
CreateGenericValueOfFloat = _library.function(GenericValue, 'LLVMCreateGenericValueOfFloat', [Type, ctypes.c_double])
CreateGenericValueOfFloat = untested(CreateGenericValueOfFloat)
GenericValueIntWidth = _library.function(ctypes.c_uint, 'LLVMGenericValueIntWidth', [GenericValue])
GenericValueIntWidth = untested(GenericValueIntWidth)
GenericValueToInt = _library.function(ctypes.c_ulonglong, 'LLVMGenericValueToInt', [GenericValue, Bool])
GenericValueToInt = untested(GenericValueToInt)
GenericValueToPointer = _library.function(ctypes.c_void_p, 'LLVMGenericValueToPointer', [GenericValue])
GenericValueToPointer = untested(GenericValueToPointer)
GenericValueToFloat = _library.function(ctypes.c_double, 'LLVMGenericValueToFloat', [Type, GenericValue])
GenericValueToFloat = untested(GenericValueToFloat)
DisposeGenericValue = _library.function(None, 'LLVMDisposeGenericValue', [GenericValue])
DisposeGenericValue = untested(DisposeGenericValue)

CreateExecutionEngineForModule = _library.function(Bool, 'LLVMCreateExecutionEngineForModule', [ctypes.POINTER(ExecutionEngine), Module, ctypes.POINTER(_c.string_buffer)])
CreateExecutionEngineForModule = untested(CreateExecutionEngineForModule)
CreateInterpreterForModule = _library.function(Bool, 'LLVMCreateInterpreterForModule', [ctypes.POINTER(ExecutionEngine), Module, ctypes.POINTER(_c.string_buffer)])
CreateInterpreterForModule = untested(CreateInterpreterForModule)
CreateJITCompilerForModule = _library.function(Bool, 'LLVMCreateJITCompilerForModule', [ctypes.POINTER(ExecutionEngine), Module, ctypes.c_uint, ctypes.POINTER(_c.string_buffer)])
CreateJITCompilerForModule = untested(CreateJITCompilerForModule)

if (3, 3) <= _version:
    InitializeMCJITCompilerOptions = _library.function(None, 'LLVMInitializeMCJITCompilerOptions', [ctypes.POINTER(MCJITCompilerOptions), ctypes.c_size_t])
    InitializeMCJITCompilerOptions = untested(InitializeMCJITCompilerOptions)
    CreateMCJITCompilerForModule = _library.function(Bool, 'LLVMCreateMCJITCompilerForModule', [ctypes.POINTER(ExecutionEngine), Module, ctypes.POINTER(MCJITCompilerOptions), ctypes.c_size_t, ctypes.POINTER(_c.string_buffer)])
    CreateMCJITCompilerForModule = untested(CreateMCJITCompilerForModule)

CreateExecutionEngine = _library.function(Bool, 'LLVMCreateExecutionEngine', [ctypes.POINTER(ExecutionEngine), ModuleProvider, ctypes.POINTER(_c.string_buffer)])
CreateExecutionEngine = untested(CreateExecutionEngine)
CreateInterpreter = _library.function(Bool, 'LLVMCreateInterpreter', [ctypes.POINTER(ExecutionEngine), ModuleProvider, ctypes.POINTER(_c.string_buffer)])
CreateInterpreter = untested(CreateInterpreter)
CreateJITCompiler = _library.function(Bool, 'LLVMCreateJITCompiler', [ctypes.POINTER(ExecutionEngine), ModuleProvider, ctypes.c_uint, ctypes.POINTER(_c.string_buffer)])
CreateJITCompiler = untested(CreateJITCompiler)
DisposeExecutionEngine = _library.function(None, 'LLVMDisposeExecutionEngine', [ExecutionEngine])
DisposeExecutionEngine = untested(DisposeExecutionEngine)
RunStaticConstructors = _library.function(None, 'LLVMRunStaticConstructors', [ExecutionEngine])
RunStaticConstructors = untested(RunStaticConstructors)
RunStaticDestructors = _library.function(None, 'LLVMRunStaticDestructors', [ExecutionEngine])
RunStaticDestructors = untested(RunStaticDestructors)
RunFunctionAsMain = _library.function(ctypes.c_int, 'LLVMRunFunctionAsMain', [ExecutionEngine, Value, ctypes.c_uint, ctypes.POINTER(ctypes.c_char_p), ctypes.POINTER(ctypes.c_char_p)])
RunFunctionAsMain = untested(RunFunctionAsMain)

RunFunction = _library.function(GenericValue, 'LLVMRunFunction', [ExecutionEngine, Value, ctypes.c_uint, ctypes.POINTER(GenericValue)])
RunFunction = untested(RunFunction)
FreeMachineCodeForFunction = _library.function(None, 'LLVMFreeMachineCodeForFunction', [ExecutionEngine, Value])
FreeMachineCodeForFunction = untested(FreeMachineCodeForFunction)
AddModule = _library.function(None, 'LLVMAddModule', [ExecutionEngine, Module])
AddModule = untested(AddModule)
AddModuleProvider = _library.function(None, 'LLVMAddModuleProvider', [ExecutionEngine, ModuleProvider])
AddModuleProvider = untested(AddModuleProvider)
RemoveModule = _library.function(Bool, 'LLVMRemoveModule', [ExecutionEngine, Module, ctypes.POINTER(Module), ctypes.POINTER(_c.string_buffer)])
RemoveModule = untested(RemoveModule)
RemoveModuleProvider = _library.function(Bool, 'LLVMRemoveModuleProvider', [ExecutionEngine, ModuleProvider, ctypes.POINTER(Module), ctypes.POINTER(_c.string_buffer)])
RemoveModuleProvider = untested(RemoveModuleProvider)
FindFunction = _library.function(Bool, 'LLVMFindFunction', [ExecutionEngine, ctypes.c_char_p, ctypes.POINTER(Value)])
FindFunction = untested(FindFunction)
RecompileAndRelinkFunction = _library.function(ctypes.c_void_p, 'LLVMRecompileAndRelinkFunction', [ExecutionEngine, Value])
RecompileAndRelinkFunction = untested(RecompileAndRelinkFunction)
GetExecutionEngineTargetData = _library.function(TargetData, 'LLVMGetExecutionEngineTargetData', [ExecutionEngine])
GetExecutionEngineTargetData = untested(GetExecutionEngineTargetData)
if (3, 5) <= _version:
    GetExecutionEngineTargetMachine = _library.function(TargetMachine, 'LLVMGetExecutionEngineTargetMachine', [ExecutionEngine])
    GetExecutionEngineTargetMachine = untested(GetExecutionEngineTargetMachine)
AddGlobalMapping = _library.function(None, 'LLVMAddGlobalMapping', [ExecutionEngine, Value, ctypes.c_void_p])
AddGlobalMapping = untested(AddGlobalMapping)
GetPointerToGlobal = _library.function(ctypes.c_void_p, 'LLVMGetPointerToGlobal', [ExecutionEngine, Value])
GetPointerToGlobal = untested(GetPointerToGlobal)

if (3, 4) <= _version:
    CreateSimpleMCJITMemoryManager = _library.function(MCJITMemoryManager, 'LLVMCreateSimpleMCJITMemoryManager', [ctypes.c_void_p, MemoryManagerAllocateCodeSectionCallback, MemoryManagerAllocateDataSectionCallback, MemoryManagerFinalizeMemoryCallback, MemoryManagerDestroyCallback])
    CreateSimpleMCJITMemoryManager = untested(CreateSimpleMCJITMemoryManager)
    DisposeMCJITMemoryManager = _library.function(None, 'LLVMDisposeMCJITMemoryManager', [MCJITMemoryManager])
    DisposeMCJITMemoryManager = untested(DisposeMCJITMemoryManager)
