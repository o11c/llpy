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

''' low-level wrapper of llvm-c/Core.h
'''

import ctypes

from . import _c

import llpy
del llpy.set_library_pattern
del llpy.set_llvm_version
_version = llpy.__library_version
if _version is not None:
    _library = _c.Library(llpy.__library_pattern % _version)
else:
    e = None
    for _version in reversed(llpy.__TESTED_LLVM_VERSIONS):
        try:
            _library = _c.Library(llpy.__library_pattern % _version)
        except OSError as e_:
            e = e_
            continue
        else:
            del e
            break
    else:
        raise e
del llpy


Bool = ctypes.c_int

Context = _c.opaque('Context')
Module = _c.opaque('Module')
Type = _c.opaque('Type')
Value = _c.opaque('Value')
BasicBlock = _c.opaque('BasicBlock')
Builder = _c.opaque('Builder')
ModuleProvider = _c.opaque('ModuleProvider')
MemoryBuffer = _c.opaque('MemoryBuffer')
PassManager = _c.opaque('PassManager')
PassRegistry = _c.opaque('PassRegistry')
Use = _c.opaque('Use')

attributes = dict(
    ZExt            = 1 << 0,   # int param, return, call
    SExt            = 1 << 1,   # int param, return, call
    NoReturn        = 1 << 2,   # function, call
    InReg           = 1 << 3,   # param, return, call
    StructRet       = 1 << 4,   # first, pointer param
    NoUnwind        = 1 << 5,   # function, call
    NoAlias         = 1 << 6,   # param, return
    ByVal           = 1 << 7,   # pointer param
    Nest            = 1 << 8,   # one pointer param
    ReadNone        = 1 << 9,   # function, call
    ReadOnly        = 1 << 10,  # function, call
    NoInline        = 1 << 11,  # function
    AlwaysInline    = 1 << 12,  # function
    OptimizeForSize = 1 << 13,  # function
    StackProtect    = 1 << 14,  # function
    StackProtectReq = 1 << 15,  # function
    Alignment       = 31 << 16, # param, maybe return
    NoCapture       = 1 << 21,  # pointer param
    NoRedZone       = 1 << 22,  # function
    NoImplicitFloat = 1 << 23,  # function
    Naked           = 1 << 24,  # function
    InlineHint      = 1 << 25,  # function
    StackAlignment  = 7 << 26,  # function
    ReturnsTwice    = 1 << 29,  # function
    UWTable         = 1 << 30,  # function
)
if _version <= (3, 0):
    attributes.update(
        NonLazyBind     = 1 << 31,  # function
    )
if (3, 1) <= _version:
    attributes.update(
        NonLazyBind_buggy     = 1 << 31,  # function
        #AddressSafety   = 1 << 32,  # function
    )
if (3, 3) <= _version:
    attributes.update(
        #StackProtectStrong  = 1 << 33,  # function
    )
if (3, 4) <= _version:
    attributes.update(
        #Cold  = 1 << 34,           # function
        #OptimizeNone  = 1 << 34,   # function
    )
Attribute = _c.bit_enum('Attribute', **attributes)
del attributes
Attribute.__doc__ = '''Attributes are used in at least 3 places:
    - for function arguments
    - for function return
    - for function itself
    - maybe for instructions too?

    Not all attributes are valid in all places.
'''

opcodes = dict(
    Ret             = 1,
    Br              = 2,
    Switch          = 3,
    IndirectBr      = 4,
    Invoke          = 5,

    Unreachable     = 7,

    Add             = 8,
    FAdd            = 9,
    Sub             = 10,
    FSub            = 11,
    Mul             = 12,
    FMul            = 13,
    UDiv            = 14,
    SDiv            = 15,
    FDiv            = 16,
    URem            = 17,
    SRem            = 18,
    FRem            = 19,

    Shl             = 20,
    LShr            = 21,
    AShr            = 22,
    And             = 23,
    Or              = 24,
    Xor             = 25,

    Alloca          = 26,
    Load            = 27,
    Store           = 28,
    GetElementPtr   = 29,

    Trunc           = 30,
    ZExt            = 31,
    SExt            = 32,
    FPToUI          = 33,
    FPToSI          = 34,
    UIToFP          = 35,
    SIToFP          = 36,
    FPTrunc         = 37,
    FPExt           = 38,
    PtrToInt        = 39,
    IntToPtr        = 40,
    BitCast         = 41,
    #AddrSpaceCast below

    ICmp            = 42,
    FCmp            = 43,
    PHI             = 44,
    Call            = 45,
    Select          = 46,
    UserOp1         = 47,
    UserOp2         = 48,
    VAArg           = 49,
    ExtractElement  = 50,
    InsertElement   = 51,
    ShuffleVector   = 52,
    ExtractValue    = 53,
    InsertValue     = 54,
    Fence           = 55,
    AtomicCmpXchg   = 56,
    AtomicRMW       = 57,

    Resume          = 58,
    LandingPad      = 59,
)
if _version <= (3, 0):
    opcodes.update(
        Unwind = 60,
    )
if (3, 4) <= _version:
    opcodes.update(
        AddrSpaceCast = 60,
    )
Opcode = _c.enum('Opcode', **opcodes)
del opcodes

typekinds = [
    'Void',
]
if (3, 1) <= _version:
    typekinds += [
        'Half',
    ]
typekinds += [
    'Float',
    'Double',
    'X86_FP80',
    'FP128',
    'PPC_FP128',
    'Label',
    'Integer',
    'Function',
    'Struct',
    'Array',
    'Pointer',
]
typekinds += [
    'Vector',
    'Metadata',
    'X86_MMX',
]
TypeKind = _c.enum('TypeKind', **{v: k for k, v in enumerate(typekinds)})
del typekinds

linkages = [
    'External',
    'AvailableExternally',
    'LinkOnceAny',
    'LinkOnceODR',
]
if (3, 2) <= _version:
    linkages += [
        'LinkOnceODRAutoHide',  # Obsolete in 3.4
    ]
linkages += [
    'WeakAny',
    'WeakODR',
    'Appending',
    'Internal',
    'Private',
    'DLLImport',
    'DLLExport',
    'ExternalWeak',
    'Ghost',
    'Common',
    'LinkerPrivate',
    'LinkerPrivateWeak',
]
if _version <= (3, 1):
    linkages += [
        'LinkerPrivateWeakDefAuto',
    ]
Linkage = _c.enum('Linkage', **{v: k for k, v in enumerate(linkages)})
del linkages

visibilities = [
    'Default',
    'Hidden',
    'Protected',
]
Visibility = _c.enum('Visibility', **{v: k for k, v in enumerate(visibilities)})
del visibilities

call_convs = dict(
    C           = 0,
    Fast        = 8,
    Cold        = 9,
)
if (3, 4) <= _version:
    call_convs.update(
        WebKitJS= 12,
        AnyReg  = 13,
    )
call_convs.update(
    X86Stdcall  = 64,
    X86Fastcall = 65,
)
CallConv = _c.enum('CallConv', **call_convs)
del call_convs

int_predicates = [
    'EQ',
    'NE',
    'UGT',
    'UGE',
    'ULT',
    'ULE',
    'SGT',
    'SGE',
    'SLT',
    'SLE',
]
IntPredicate = _c.enum('IntPredicate', **{v: k for k, v in enumerate(int_predicates, 32)})
del int_predicates

real_predicates = [
    'FALSE',
    'OEQ',
    'OGT',
    'OGE',
    'OLT',
    'OLE',
    'ONE',
    'ORD',
    'UNO',
    'UEQ',
    'UGT',
    'UGE',
    'ULT',
    'ULE',
    'UNE',
    'TRUE',
]
RealPredicate = _c.enum('RealPredicate', **{v: k for k, v in enumerate(real_predicates, 0)})
del real_predicates

landingpad_clause_tys = [
    'Catch',
    'Filter',
]
LandingPadClauseTy = _c.enum('LandingPadClauseTy', **{v: k for k, v in enumerate(landingpad_clause_tys)})
del landingpad_clause_tys

if (3, 3) <= _version:
    threadlocal_modes = [
        'NotThreadLocal',
        'GeneralDynamic',
        'LocalDynamic',
        'InitialExec',
        'LocalExec',
    ]
    ThreadLocalMode = _c.enum('ThreadLocalMode', **{v: k for k, v in enumerate(threadlocal_modes)})
    del threadlocal_modes

    atomic_orderings = dict(
        NotAtomic = 0,
        Unordered = 1,
        Monotonic = 2,
        Acquire = 4,
        Release = 5,
        AcquireRelease = 6,
        SequentiallyConsistent = 7,
    )
    AtomicOrdering = _c.enum('AtomicOrdering', **atomic_orderings)
    del atomic_orderings

    atomic_rmw_binops = [
        'Xchg',
        'Add',
        'Sub',
        'And',
        'Nand',
        'Or',
        'Xor',
        'Max',
        'Min',
        'UMax',
        'UMin',
    ]
    AtomicRMWBinOp = _c.enum('AtomicRMWBinOp', **{v: k for k, v in enumerate(atomic_rmw_binops)})
    del atomic_rmw_binops

if (3, 4) <= _version:
    FatalErrorHandler = ctypes.CFUNCTYPE(None, *[ctypes.c_char_p])


InitializeCore = _library.function(None, 'LLVMInitializeCore', [PassRegistry])
if (3, 3) <= _version:
    Shutdown = _library.function(None, 'LLVMShutdown', [])

if (3, 4) <= _version:
    CreateMessage = _library.function(_c.string_buffer, 'LLVMCreateMessage', [ctypes.c_char_p])
DisposeMessage = _library.function(None, 'LLVMDisposeMessage', [_c.string_buffer])
if (3, 4) <= _version:
    InstallFatalErrorHandler = _library.function(None, 'LLVMInstallFatalErrorHandler', [FatalErrorHandler])
    ResetFatalErrorHandler = _library.function(None, 'LLVMResetFatalErrorHandler', [])
    EnablePrettyStackTrace = _library.function(None, 'LLVMEnablePrettyStackTrace', [])



ContextCreate = _library.function(Context, 'LLVMContextCreate', [])
GetGlobalContext = _library.function(Context, 'LLVMGetGlobalContext', [])
ContextDispose = _library.function(None, 'LLVMContextDispose', [Context])
GetMDKindIDInContext = _library.function(ctypes.c_uint, 'LLVMGetMDKindIDInContext', [Context, ctypes.POINTER(ctypes.c_char), ctypes.c_uint])
GetMDKindID = _library.function(ctypes.c_uint, 'LLVMGetMDKindID', [ctypes.POINTER(ctypes.c_char), ctypes.c_uint])


ModuleCreateWithName = _library.function(Module, 'LLVMModuleCreateWithName', [ctypes.c_char_p])
ModuleCreateWithNameInContext = _library.function(Module, 'LLVMModuleCreateWithNameInContext', [ctypes.c_char_p, Context])
DisposeModule = _library.function(None, 'LLVMDisposeModule', [Module])

GetDataLayout = _library.function(ctypes.c_char_p, 'LLVMGetDataLayout', [Module])
SetDataLayout = _library.function(None, 'LLVMSetDataLayout', [Module, ctypes.c_char_p])
GetTarget = _library.function(ctypes.c_char_p, 'LLVMGetTarget', [Module])
SetTarget = _library.function(None, 'LLVMSetTarget', [Module, ctypes.c_char_p])
DumpModule = _library.function(None, 'LLVMDumpModule', [Module])
if (3, 2) <= _version:
    PrintModuleToFile = _library.function(Bool, 'LLVMPrintModuleToFile', [Module, ctypes.c_char_p, ctypes.POINTER(_c.string_buffer)])
if (3, 4) <= _version:
    PrintModuleToString = _library.function(_c.string_buffer, 'LLVMPrintModuleToString', [Module])
SetModuleInlineAsm = _library.function(None, 'LLVMSetModuleInlineAsm', [Module, ctypes.c_char_p])
GetModuleContext = _library.function(Context, 'LLVMGetModuleContext', [Module])
GetTypeByName = _library.function(Type, 'LLVMGetTypeByName', [Module, ctypes.c_char_p])

GetNamedMetadataNumOperands = _library.function(ctypes.c_uint, 'LLVMGetNamedMetadataNumOperands', [Module, ctypes.c_char_p])
GetNamedMetadataOperands = _library.function(None, 'LLVMGetNamedMetadataOperands', [Module, ctypes.c_char_p, ctypes.POINTER(Value)])
if (3, 1) <= _version:
    AddNamedMetadataOperand = _library.function(None, 'LLVMAddNamedMetadataOperand', [Module, ctypes.c_char_p, Value])

AddFunction = _library.function(Value, 'LLVMAddFunction', [Module, ctypes.c_char_p, Type])
GetNamedFunction = _library.function(Value, 'LLVMGetNamedFunction', [Module, ctypes.c_char_p])
GetFirstFunction = _library.function(Value, 'LLVMGetFirstFunction', [Module])
GetLastFunction = _library.function(Value, 'LLVMGetLastFunction', [Module])
GetNextFunction = _library.function(Value, 'LLVMGetNextFunction', [Value])
GetPreviousFunction = _library.function(Value, 'LLVMGetPreviousFunction', [Value])



GetTypeKind = _library.function(TypeKind, 'LLVMGetTypeKind', [Type])
TypeIsSized = _library.function(Bool, 'LLVMTypeIsSized', [Type])
GetTypeContext = _library.function(Context, 'LLVMGetTypeContext', [Type])
if (3, 4) <= _version:
    DumpType = _library.function(None, 'LLVMDumpType', [Type])
    PrintTypeToString = _library.function(_c.string_buffer, 'LLVMPrintTypeToString', [Type])

Int1TypeInContext = _library.function(Type, 'LLVMInt1TypeInContext', [Context])
Int8TypeInContext = _library.function(Type, 'LLVMInt8TypeInContext', [Context])
Int16TypeInContext = _library.function(Type, 'LLVMInt16TypeInContext', [Context])
Int32TypeInContext = _library.function(Type, 'LLVMInt32TypeInContext', [Context])
Int64TypeInContext = _library.function(Type, 'LLVMInt64TypeInContext', [Context])
IntTypeInContext = _library.function(Type, 'LLVMIntTypeInContext', [Context, ctypes.c_uint])

Int1Type = _library.function(Type, 'LLVMInt1Type', [])
Int8Type = _library.function(Type, 'LLVMInt8Type', [])
Int16Type = _library.function(Type, 'LLVMInt16Type', [])
Int32Type = _library.function(Type, 'LLVMInt32Type', [])
Int64Type = _library.function(Type, 'LLVMInt64Type', [])
IntType = _library.function(Type, 'LLVMIntType', [ctypes.c_uint])

GetIntTypeWidth = _library.function(ctypes.c_uint, 'LLVMGetIntTypeWidth', [Type])


if (3, 1) <= _version:
    HalfTypeInContext = _library.function(Type, 'LLVMHalfTypeInContext', [Context])
FloatTypeInContext = _library.function(Type, 'LLVMFloatTypeInContext', [Context])
DoubleTypeInContext = _library.function(Type, 'LLVMDoubleTypeInContext', [Context])
X86FP80TypeInContext = _library.function(Type, 'LLVMX86FP80TypeInContext', [Context])
FP128TypeInContext = _library.function(Type, 'LLVMFP128TypeInContext', [Context])
PPCFP128TypeInContext = _library.function(Type, 'LLVMPPCFP128TypeInContext', [Context])

if (3, 1) <= _version:
    HalfType = _library.function(Type, 'LLVMHalfType', [])
FloatType = _library.function(Type, 'LLVMFloatType', [])
DoubleType = _library.function(Type, 'LLVMDoubleType', [])
X86FP80Type = _library.function(Type, 'LLVMX86FP80Type', [])
FP128Type = _library.function(Type, 'LLVMFP128Type', [])
PPCFP128Type = _library.function(Type, 'LLVMPPCFP128Type', [])


FunctionType = _library.function(Type, 'LLVMFunctionType', [Type, ctypes.POINTER(Type), ctypes.c_uint, Bool])
IsFunctionVarArg = _library.function(Bool, 'LLVMIsFunctionVarArg', [Type])
GetReturnType = _library.function(Type, 'LLVMGetReturnType', [Type])
CountParamTypes = _library.function(ctypes.c_uint, 'LLVMCountParamTypes', [Type])
GetParamTypes = _library.function(None, 'LLVMGetParamTypes', [Type, ctypes.POINTER(Type)])


StructTypeInContext = _library.function(Type, 'LLVMStructTypeInContext', [Context, ctypes.POINTER(Type), ctypes.c_uint, Bool])
StructType = _library.function(Type, 'LLVMStructType', [ctypes.POINTER(Type), ctypes.c_uint, Bool])
StructCreateNamed = _library.function(Type, 'LLVMStructCreateNamed', [Context, ctypes.c_char_p])
GetStructName = _library.function(ctypes.c_char_p, 'LLVMGetStructName', [Type])
StructSetBody = _library.function(None, 'LLVMStructSetBody', [Type, ctypes.POINTER(Type), ctypes.c_uint, Bool])
CountStructElementTypes = _library.function(ctypes.c_uint, 'LLVMCountStructElementTypes', [Type])
GetStructElementTypes = _library.function(None, 'LLVMGetStructElementTypes', [Type, ctypes.POINTER(Type)])
IsPackedStruct = _library.function(Bool, 'LLVMIsPackedStruct', [Type])
IsOpaqueStruct = _library.function(Bool, 'LLVMIsOpaqueStruct', [Type])


GetElementType = _library.function(Type, 'LLVMGetElementType', [Type])
ArrayType = _library.function(Type, 'LLVMArrayType', [Type, ctypes.c_uint])
GetArrayLength = _library.function(ctypes.c_uint, 'LLVMGetArrayLength', [Type])
PointerType = _library.function(Type, 'LLVMPointerType', [Type, ctypes.c_uint])
GetPointerAddressSpace = _library.function(ctypes.c_uint, 'LLVMGetPointerAddressSpace', [Type])
VectorType = _library.function(Type, 'LLVMVectorType', [Type, ctypes.c_uint])
GetVectorSize = _library.function(ctypes.c_uint, 'LLVMGetVectorSize', [Type])


VoidTypeInContext = _library.function(Type, 'LLVMVoidTypeInContext', [Context])
LabelTypeInContext = _library.function(Type, 'LLVMLabelTypeInContext', [Context])
X86MMXTypeInContext = _library.function(Type, 'LLVMX86MMXTypeInContext', [Context])
VoidType = _library.function(Type, 'LLVMVoidType', [])
LabelType = _library.function(Type, 'LLVMLabelType', [])
X86MMXType = _library.function(Type, 'LLVMX86MMXType', [])



TypeOf = _library.function(Type, 'LLVMTypeOf', [Value])
GetValueName = _library.function(ctypes.c_char_p, 'LLVMGetValueName', [Value])
SetValueName = _library.function(None, 'LLVMSetValueName', [Value, ctypes.c_char_p])
DumpValue = _library.function(None, 'LLVMDumpValue', [Value])
if (3, 4) <= _version:
    PrintValueToString = _library.function(None, 'LLVMPrintValueToString', [Value])
ReplaceAllUsesWith = _library.function(None, 'LLVMReplaceAllUsesWith', [Value, Value])
IsConstant = _library.function(Bool, 'LLVMIsConstant', [Value])
IsUndef = _library.function(Bool, 'LLVMIsUndef', [Value])


IsAArgument = _library.function(Value, 'LLVMIsAArgument', [Value])
IsABasicBlock = _library.function(Value, 'LLVMIsABasicBlock', [Value])
IsAInlineAsm = _library.function(Value, 'LLVMIsAInlineAsm', [Value])
IsAMDNode = _library.function(Value, 'LLVMIsAMDNode', [Value])
IsAMDString = _library.function(Value, 'LLVMIsAMDString', [Value])
IsAUser = _library.function(Value, 'LLVMIsAUser', [Value])
IsAConstant = _library.function(Value, 'LLVMIsAConstant', [Value])
IsABlockAddress = _library.function(Value, 'LLVMIsABlockAddress', [Value])
IsAConstantAggregateZero = _library.function(Value, 'LLVMIsAConstantAggregateZero', [Value])
IsAConstantArray = _library.function(Value, 'LLVMIsAConstantArray', [Value])
if (3, 4) <= _version:
    IsAConstantDataSequential = _library.function(Value, 'LLVMIsAConstantDataSequential', [Value])
    IsAConstantDataArray = _library.function(Value, 'LLVMIsAConstantDataArray', [Value])
    IsAConstantDataVector = _library.function(Value, 'LLVMIsAConstantDataVector', [Value])
IsAConstantExpr = _library.function(Value, 'LLVMIsAConstantExpr', [Value])
IsAConstantFP = _library.function(Value, 'LLVMIsAConstantFP', [Value])
IsAConstantInt = _library.function(Value, 'LLVMIsAConstantInt', [Value])
IsAConstantPointerNull = _library.function(Value, 'LLVMIsAConstantPointerNull', [Value])
IsAConstantStruct = _library.function(Value, 'LLVMIsAConstantStruct', [Value])
IsAConstantVector = _library.function(Value, 'LLVMIsAConstantVector', [Value])
IsAGlobalValue = _library.function(Value, 'LLVMIsAGlobalValue', [Value])
IsAFunction = _library.function(Value, 'LLVMIsAFunction', [Value])
IsAGlobalAlias = _library.function(Value, 'LLVMIsAGlobalAlias', [Value])
IsAGlobalVariable = _library.function(Value, 'LLVMIsAGlobalVariable', [Value])
IsAUndefValue = _library.function(Value, 'LLVMIsAUndefValue', [Value])
IsAInstruction = _library.function(Value, 'LLVMIsAInstruction', [Value])
IsABinaryOperator = _library.function(Value, 'LLVMIsABinaryOperator', [Value])
IsACallInst = _library.function(Value, 'LLVMIsACallInst', [Value])
IsAIntrinsicInst = _library.function(Value, 'LLVMIsAIntrinsicInst', [Value])
IsADbgInfoIntrinsic = _library.function(Value, 'LLVMIsADbgInfoIntrinsic', [Value])
IsADbgDeclareInst = _library.function(Value, 'LLVMIsADbgDeclareInst', [Value])
if _version <= (3, 0) and False:
    # These are declared in the header, but linking finds no such symbol.
    IsAEHExceptionIntrinsic = _library.function(Value, 'LLVMIsAEHExceptionIntrinsic', [Value])
if _version <= (3, 0) and False:
    IsAEHSelectorIntrinsic = _library.function(Value, 'LLVMIsAEHSelectorIntrinsic', [Value])
IsAMemIntrinsic = _library.function(Value, 'LLVMIsAMemIntrinsic', [Value])
IsAMemCpyInst = _library.function(Value, 'LLVMIsAMemCpyInst', [Value])
IsAMemMoveInst = _library.function(Value, 'LLVMIsAMemMoveInst', [Value])
IsAMemSetInst = _library.function(Value, 'LLVMIsAMemSetInst', [Value])
IsACmpInst = _library.function(Value, 'LLVMIsACmpInst', [Value])
IsAFCmpInst = _library.function(Value, 'LLVMIsAFCmpInst', [Value])
IsAICmpInst = _library.function(Value, 'LLVMIsAICmpInst', [Value])
IsAExtractElementInst = _library.function(Value, 'LLVMIsAExtractElementInst', [Value])
IsAGetElementPtrInst = _library.function(Value, 'LLVMIsAGetElementPtrInst', [Value])
IsAInsertElementInst = _library.function(Value, 'LLVMIsAInsertElementInst', [Value])
IsAInsertValueInst = _library.function(Value, 'LLVMIsAInsertValueInst', [Value])
IsALandingPadInst = _library.function(Value, 'LLVMIsALandingPadInst', [Value])
IsAPHINode = _library.function(Value, 'LLVMIsAPHINode', [Value])
IsASelectInst = _library.function(Value, 'LLVMIsASelectInst', [Value])
IsAShuffleVectorInst = _library.function(Value, 'LLVMIsAShuffleVectorInst', [Value])
IsAStoreInst = _library.function(Value, 'LLVMIsAStoreInst', [Value])
IsATerminatorInst = _library.function(Value, 'LLVMIsATerminatorInst', [Value])
IsABranchInst = _library.function(Value, 'LLVMIsABranchInst', [Value])
IsAIndirectBrInst = _library.function(Value, 'LLVMIsAIndirectBrInst', [Value])
IsAInvokeInst = _library.function(Value, 'LLVMIsAInvokeInst', [Value])
IsAReturnInst = _library.function(Value, 'LLVMIsAReturnInst', [Value])
IsASwitchInst = _library.function(Value, 'LLVMIsASwitchInst', [Value])
IsAUnreachableInst = _library.function(Value, 'LLVMIsAUnreachableInst', [Value])
IsAResumeInst = _library.function(Value, 'LLVMIsAResumeInst', [Value])
IsAUnaryInstruction = _library.function(Value, 'LLVMIsAUnaryInstruction', [Value])
IsAAllocaInst = _library.function(Value, 'LLVMIsAAllocaInst', [Value])
IsACastInst = _library.function(Value, 'LLVMIsACastInst', [Value])
if (3, 4) <= _version:
    IsAAddrSpaceCastInst = _library.function(Value, 'LLVMIsAAddrSpaceCastInst', [Value])
IsABitCastInst = _library.function(Value, 'LLVMIsABitCastInst', [Value])
IsAFPExtInst = _library.function(Value, 'LLVMIsAFPExtInst', [Value])
IsAFPToSIInst = _library.function(Value, 'LLVMIsAFPToSIInst', [Value])
IsAFPToUIInst = _library.function(Value, 'LLVMIsAFPToUIInst', [Value])
IsAFPTruncInst = _library.function(Value, 'LLVMIsAFPTruncInst', [Value])
IsAIntToPtrInst = _library.function(Value, 'LLVMIsAIntToPtrInst', [Value])
IsAPtrToIntInst = _library.function(Value, 'LLVMIsAPtrToIntInst', [Value])
IsASExtInst = _library.function(Value, 'LLVMIsASExtInst', [Value])
IsASIToFPInst = _library.function(Value, 'LLVMIsASIToFPInst', [Value])
IsATruncInst = _library.function(Value, 'LLVMIsATruncInst', [Value])
IsAUIToFPInst = _library.function(Value, 'LLVMIsAUIToFPInst', [Value])
IsAZExtInst = _library.function(Value, 'LLVMIsAZExtInst', [Value])
IsAExtractValueInst = _library.function(Value, 'LLVMIsAExtractValueInst', [Value])
IsALoadInst = _library.function(Value, 'LLVMIsALoadInst', [Value])
IsAVAArgInst = _library.function(Value, 'LLVMIsAVAArgInst', [Value])


GetFirstUse = _library.function(Use, 'LLVMGetFirstUse', [Value])
GetNextUse = _library.function(Use, 'LLVMGetNextUse', [Use])
GetUser = _library.function(Value, 'LLVMGetUser', [Use])
GetUsedValue = _library.function(Value, 'LLVMGetUsedValue', [Use])


GetOperand = _library.function(Value, 'LLVMGetOperand', [Value, ctypes.c_uint])
SetOperand = _library.function(None, 'LLVMSetOperand', [Value, ctypes.c_uint, Value])
GetNumOperands = _library.function(ctypes.c_int, 'LLVMGetNumOperands', [Value])


ConstNull = _library.function(Value, 'LLVMConstNull', [Type])
ConstAllOnes = _library.function(Value, 'LLVMConstAllOnes', [Type])
GetUndef = _library.function(Value, 'LLVMGetUndef', [Type])
IsNull = _library.function(Bool, 'LLVMIsNull', [Value])
ConstPointerNull = _library.function(Value, 'LLVMConstPointerNull', [Type])

ConstInt = _library.function(Value, 'LLVMConstInt', [Type, ctypes.c_ulonglong, Bool])
ConstIntOfArbitraryPrecision = _library.function(Value, 'LLVMConstIntOfArbitraryPrecision', [Type, ctypes.c_uint, ctypes.POINTER(ctypes.c_uint64)])
ConstIntOfString = _library.function(Value, 'LLVMConstIntOfString', [Type, ctypes.c_char_p, ctypes.c_uint8])
ConstIntOfStringAndSize = _library.function(Value, 'LLVMConstIntOfStringAndSize', [Type, ctypes.c_char_p, ctypes.c_uint, ctypes.c_uint8])
ConstReal = _library.function(Value, 'LLVMConstReal', [Type, ctypes.c_double])
ConstRealOfString = _library.function(Value, 'LLVMConstRealOfString', [Type, ctypes.c_char_p])
ConstRealOfStringAndSize = _library.function(Value, 'LLVMConstRealOfStringAndSize', [Type, ctypes.c_char_p, ctypes.c_uint])
ConstIntGetZExtValue = _library.function(ctypes.c_ulonglong, 'LLVMConstIntGetZExtValue', [Value])
ConstIntGetSExtValue = _library.function(ctypes.c_longlong, 'LLVMConstIntGetSExtValue', [Value])

ConstStringInContext = _library.function(Value, 'LLVMConstStringInContext', [Context, ctypes.c_char_p, ctypes.c_uint, Bool])
ConstString = _library.function(Value, 'LLVMConstString', [ctypes.c_char_p, ctypes.c_uint, Bool])
ConstStructInContext = _library.function(Value, 'LLVMConstStructInContext', [Context, ctypes.POINTER(Value), ctypes.c_uint, Bool])
ConstStruct = _library.function(Value, 'LLVMConstStruct', [ctypes.POINTER(Value), ctypes.c_uint, Bool])
ConstArray = _library.function(Value, 'LLVMConstArray', [Type, ctypes.POINTER(Value), ctypes.c_uint])
ConstNamedStruct = _library.function(Value, 'LLVMConstNamedStruct', [Type, ctypes.POINTER(Value), ctypes.c_uint])
ConstVector = _library.function(Value, 'LLVMConstVector', [ctypes.POINTER(Value), ctypes.c_uint])

GetConstOpcode = _library.function(Opcode, 'LLVMGetConstOpcode', [Value])
AlignOf = _library.function(Value, 'LLVMAlignOf', [Type])
SizeOf = _library.function(Value, 'LLVMSizeOf', [Type])
ConstNeg = _library.function(Value, 'LLVMConstNeg', [Value])
ConstNSWNeg = _library.function(Value, 'LLVMConstNSWNeg', [Value])
ConstNUWNeg = _library.function(Value, 'LLVMConstNUWNeg', [Value])
ConstFNeg = _library.function(Value, 'LLVMConstFNeg', [Value])
ConstNot = _library.function(Value, 'LLVMConstNot', [Value])
ConstAdd = _library.function(Value, 'LLVMConstAdd', [Value, Value])
ConstNSWAdd = _library.function(Value, 'LLVMConstNSWAdd', [Value, Value])
ConstNUWAdd = _library.function(Value, 'LLVMConstNUWAdd', [Value, Value])
ConstFAdd = _library.function(Value, 'LLVMConstFAdd', [Value, Value])
ConstSub = _library.function(Value, 'LLVMConstSub', [Value, Value])
ConstNSWSub = _library.function(Value, 'LLVMConstNSWSub', [Value, Value])
ConstNUWSub = _library.function(Value, 'LLVMConstNUWSub', [Value, Value])
ConstFSub = _library.function(Value, 'LLVMConstFSub', [Value, Value])
ConstMul = _library.function(Value, 'LLVMConstMul', [Value, Value])
ConstNSWMul = _library.function(Value, 'LLVMConstNSWMul', [Value, Value])
ConstNUWMul = _library.function(Value, 'LLVMConstNUWMul', [Value, Value])
ConstFMul = _library.function(Value, 'LLVMConstFMul', [Value, Value])
ConstUDiv = _library.function(Value, 'LLVMConstUDiv', [Value, Value])
ConstSDiv = _library.function(Value, 'LLVMConstSDiv', [Value, Value])
ConstExactSDiv = _library.function(Value, 'LLVMConstExactSDiv', [Value, Value])
ConstFDiv = _library.function(Value, 'LLVMConstFDiv', [Value, Value])
ConstURem = _library.function(Value, 'LLVMConstURem', [Value, Value])
ConstSRem = _library.function(Value, 'LLVMConstSRem', [Value, Value])
ConstFRem = _library.function(Value, 'LLVMConstFRem', [Value, Value])
ConstAnd = _library.function(Value, 'LLVMConstAnd', [Value, Value])
ConstOr = _library.function(Value, 'LLVMConstOr', [Value, Value])
ConstXor = _library.function(Value, 'LLVMConstXor', [Value, Value])
ConstICmp = _library.function(Value, 'LLVMConstICmp', [IntPredicate, Value, Value])
ConstFCmp = _library.function(Value, 'LLVMConstFCmp', [RealPredicate, Value, Value])
ConstShl = _library.function(Value, 'LLVMConstShl', [Value, Value])
ConstLShr = _library.function(Value, 'LLVMConstLShr', [Value, Value])
ConstAShr = _library.function(Value, 'LLVMConstAShr', [Value, Value])
ConstGEP = _library.function(Value, 'LLVMConstGEP', [Value, ctypes.POINTER(Value), ctypes.c_uint])
ConstInBoundsGEP = _library.function(Value, 'LLVMConstInBoundsGEP', [Value, ctypes.POINTER(Value), ctypes.c_uint])
ConstTrunc = _library.function(Value, 'LLVMConstTrunc', [Value, Type])
ConstSExt = _library.function(Value, 'LLVMConstSExt', [Value, Type])
ConstZExt = _library.function(Value, 'LLVMConstZExt', [Value, Type])
ConstFPTrunc = _library.function(Value, 'LLVMConstFPTrunc', [Value, Type])
ConstFPExt = _library.function(Value, 'LLVMConstFPExt', [Value, Type])
ConstUIToFP = _library.function(Value, 'LLVMConstUIToFP', [Value, Type])
ConstSIToFP = _library.function(Value, 'LLVMConstSIToFP', [Value, Type])
ConstFPToUI = _library.function(Value, 'LLVMConstFPToUI', [Value, Type])
ConstFPToSI = _library.function(Value, 'LLVMConstFPToSI', [Value, Type])
ConstPtrToInt = _library.function(Value, 'LLVMConstPtrToInt', [Value, Type])
ConstIntToPtr = _library.function(Value, 'LLVMConstIntToPtr', [Value, Type])
ConstBitCast = _library.function(Value, 'LLVMConstBitCast', [Value, Type])
if (3, 4) <= _version:
    ConstAddrSpaceCast = _library.function(Value, 'LLVMConstAddrSpaceCast', [Value, Type])
ConstZExtOrBitCast = _library.function(Value, 'LLVMConstZExtOrBitCast', [Value, Type])
ConstSExtOrBitCast = _library.function(Value, 'LLVMConstSExtOrBitCast', [Value, Type])
ConstTruncOrBitCast = _library.function(Value, 'LLVMConstTruncOrBitCast', [Value, Type])
ConstPointerCast = _library.function(Value, 'LLVMConstPointerCast', [Value, Type])
ConstIntCast = _library.function(Value, 'LLVMConstIntCast', [Value, Type, Bool])
ConstFPCast = _library.function(Value, 'LLVMConstFPCast', [Value, Type])
ConstSelect = _library.function(Value, 'LLVMConstSelect', [Value, Value, Value])
ConstExtractElement = _library.function(Value, 'LLVMConstExtractElement', [Value, Value])
ConstInsertElement = _library.function(Value, 'LLVMConstInsertElement', [Value, Value, Value])
ConstShuffleVector = _library.function(Value, 'LLVMConstShuffleVector', [Value, Value, Value])
ConstExtractValue = _library.function(Value, 'LLVMConstExtractValue', [Value, ctypes.POINTER(ctypes.c_uint), ctypes.c_uint])
ConstInsertValue = _library.function(Value, 'LLVMConstInsertValue', [Value, Value, ctypes.POINTER(ctypes.c_uint), ctypes.c_uint])
ConstInlineAsm = _library.function(Value, 'LLVMConstInlineAsm', [Type, ctypes.c_char_p, ctypes.c_char_p, Bool, Bool])
BlockAddress = _library.function(Value, 'LLVMBlockAddress', [Value, BasicBlock])

GetGlobalParent = _library.function(Module, 'LLVMGetGlobalParent', [Value])
IsDeclaration = _library.function(Bool, 'LLVMIsDeclaration', [Value])
GetLinkage = _library.function(Linkage, 'LLVMGetLinkage', [Value])
SetLinkage = _library.function(None, 'LLVMSetLinkage', [Value, Linkage])
GetSection = _library.function(ctypes.c_char_p, 'LLVMGetSection', [Value])
SetSection = _library.function(None, 'LLVMSetSection', [Value, ctypes.c_char_p])
GetVisibility = _library.function(Visibility, 'LLVMGetVisibility', [Value])
SetVisibility = _library.function(None, 'LLVMSetVisibility', [Value, Visibility])
GetAlignment = _library.function(ctypes.c_uint, 'LLVMGetAlignment', [Value])
SetAlignment = _library.function(None, 'LLVMSetAlignment', [Value, ctypes.c_uint])

AddGlobal = _library.function(Value, 'LLVMAddGlobal', [Module, Type, ctypes.c_char_p])
AddGlobalInAddressSpace = _library.function(Value, 'LLVMAddGlobalInAddressSpace', [Module, Type,  ctypes.c_char_p, ctypes.c_uint])
GetNamedGlobal = _library.function(Value, 'LLVMGetNamedGlobal', [Module, ctypes.c_char_p])
GetFirstGlobal = _library.function(Value, 'LLVMGetFirstGlobal', [Module])
GetLastGlobal = _library.function(Value, 'LLVMGetLastGlobal', [Module])
GetNextGlobal = _library.function(Value, 'LLVMGetNextGlobal', [Value])
GetPreviousGlobal = _library.function(Value, 'LLVMGetPreviousGlobal', [Value])
DeleteGlobal = _library.function(None, 'LLVMDeleteGlobal', [Value])
GetInitializer = _library.function(Value, 'LLVMGetInitializer', [Value])
SetInitializer = _library.function(None, 'LLVMSetInitializer', [Value, Value])
IsThreadLocal = _library.function(Bool, 'LLVMIsThreadLocal', [Value])
SetThreadLocal = _library.function(None, 'LLVMSetThreadLocal', [Value, Bool])
IsGlobalConstant = _library.function(Bool, 'LLVMIsGlobalConstant', [Value])
SetGlobalConstant = _library.function(None, 'LLVMSetGlobalConstant', [Value, Bool])
if (3, 3) <= _version:
    GetThreadLocalMode = _library.function(ThreadLocalMode, 'LLVMGetThreadLocalMode', [Value])
    SetThreadLocalMode = _library.function(None, 'LLVMSetThreadLocalMode', [Value, ThreadLocalMode])
    IsExternallyInitialized = _library.function(Bool, 'LLVMIsExternallyInitialized', [Value])
    SetExternallyInitialized = _library.function(None, 'LLVMSetExternallyInitialized', [Value, Bool])

AddAlias = _library.function(Value, 'LLVMAddAlias', [Module, Type, Value, ctypes.c_char_p])

DeleteFunction = _library.function(None, 'LLVMDeleteFunction', [Value])
GetIntrinsicID = _library.function(ctypes.c_uint, 'LLVMGetIntrinsicID', [Value])
GetFunctionCallConv = _library.function(CallConv, 'LLVMGetFunctionCallConv', [Value])
SetFunctionCallConv = _library.function(None, 'LLVMSetFunctionCallConv', [Value, CallConv])
GetGC = _library.function(ctypes.c_char_p, 'LLVMGetGC', [Value])
SetGC = _library.function(None, 'LLVMSetGC', [Value, ctypes.c_char_p])
AddFunctionAttr = _library.function(None, 'LLVMAddFunctionAttr', [Value, Attribute])
if (3, 3) <= _version:
    AddTargetDependentFunctionAttr = _library.function(None, 'LLVMAddTargetDependentFunctionAttr', [Value, ctypes.c_char_p, ctypes.c_char_p])
GetFunctionAttr = _library.function(Attribute, 'LLVMGetFunctionAttr', [Value])
RemoveFunctionAttr = _library.function(None, 'LLVMRemoveFunctionAttr', [Value, Attribute])

CountParams = _library.function(ctypes.c_uint, 'LLVMCountParams', [Value])
GetParams = _library.function(None, 'LLVMGetParams', [Value, ctypes.POINTER(Value)])
GetParam = _library.function(Value, 'LLVMGetParam', [Value, ctypes.c_uint])
GetParamParent = _library.function(Value, 'LLVMGetParamParent', [Value])
GetFirstParam = _library.function(Value, 'LLVMGetFirstParam', [Value])
GetLastParam = _library.function(Value, 'LLVMGetLastParam', [Value])
GetNextParam = _library.function(Value, 'LLVMGetNextParam', [Value])
GetPreviousParam = _library.function(Value, 'LLVMGetPreviousParam', [Value])
AddAttribute = _library.function(None, 'LLVMAddAttribute', [Value, Attribute])
RemoveAttribute = _library.function(None, 'LLVMRemoveAttribute', [Value, Attribute])
GetAttribute = _library.function(Attribute, 'LLVMGetAttribute', [Value])
SetParamAlignment = _library.function(None, 'LLVMSetParamAlignment', [Value, ctypes.c_uint])


MDStringInContext = _library.function(Value, 'LLVMMDStringInContext', [Context, _c.string_buffer, ctypes.c_uint])
MDString = _library.function(Value, 'LLVMMDString', [_c.string_buffer, ctypes.c_uint])
MDNodeInContext = _library.function(Value, 'LLVMMDNodeInContext', [Context, ctypes.POINTER(Value), ctypes.c_uint])
MDNode = _library.function(Value, 'LLVMMDNode', [ctypes.POINTER(Value), ctypes.c_uint])
GetMDString = _library.function(_c.string_buffer, 'LLVMGetMDString', [Value, ctypes.POINTER(ctypes.c_uint)])
if _version <= (3, 0) and False:
    # These are declared in the header, but linking finds no such symbol.
    GetMDNodeNumOperands = _library.function(ctypes.c_int, 'LLVMGetMDNodeNumOperands', [Value])
    GetMDNodeOperand = _library.function(Value, 'LLVMGetMDNodeOperand', [Value, ctypes.c_uint]);
if (3, 2) <= _version:
    # Actually present now. Slightly different signature.
    GetMDNodeNumOperands = _library.function(ctypes.c_uint, 'LLVMGetMDNodeNumOperands', [Value])
    GetMDNodeOperands = _library.function(None, 'LLVMGetMDNodeOperands', [Value, ctypes.POINTER(Value)])


BasicBlockAsValue = _library.function(Value, 'LLVMBasicBlockAsValue', [BasicBlock])
ValueIsBasicBlock = _library.function(Bool, 'LLVMValueIsBasicBlock', [Value])
ValueAsBasicBlock = _library.function(BasicBlock, 'LLVMValueAsBasicBlock', [Value])
GetBasicBlockParent = _library.function(Value, 'LLVMGetBasicBlockParent', [BasicBlock])
GetBasicBlockTerminator = _library.function(Value, 'LLVMGetBasicBlockTerminator', [BasicBlock])
CountBasicBlocks = _library.function(ctypes.c_uint, 'LLVMCountBasicBlocks', [Value])
GetBasicBlocks = _library.function(None, 'LLVMGetBasicBlocks', [Value, ctypes.POINTER(BasicBlock)])
GetFirstBasicBlock = _library.function(BasicBlock, 'LLVMGetFirstBasicBlock', [Value])
GetLastBasicBlock = _library.function(BasicBlock, 'LLVMGetLastBasicBlock', [Value])
GetNextBasicBlock = _library.function(BasicBlock, 'LLVMGetNextBasicBlock', [BasicBlock])
GetPreviousBasicBlock = _library.function(BasicBlock, 'LLVMGetPreviousBasicBlock', [BasicBlock])
GetEntryBasicBlock = _library.function(BasicBlock, 'LLVMGetEntryBasicBlock', [Value])
AppendBasicBlockInContext = _library.function(BasicBlock, 'LLVMAppendBasicBlockInContext', [Context, Value, ctypes.c_char_p])
AppendBasicBlock = _library.function(BasicBlock, 'LLVMAppendBasicBlock', [Value, ctypes.c_char_p])
InsertBasicBlockInContext = _library.function(BasicBlock, 'LLVMInsertBasicBlockInContext', [Context, BasicBlock, ctypes.c_char_p])
InsertBasicBlock = _library.function(BasicBlock, 'LLVMInsertBasicBlock', [BasicBlock, ctypes.c_char_p])
DeleteBasicBlock = _library.function(None, 'LLVMDeleteBasicBlock', [BasicBlock])
RemoveBasicBlockFromParent = _library.function(None, 'LLVMRemoveBasicBlockFromParent', [BasicBlock])
MoveBasicBlockBefore = _library.function(None, 'LLVMMoveBasicBlockBefore', [BasicBlock, BasicBlock])
MoveBasicBlockAfter = _library.function(None, 'LLVMMoveBasicBlockAfter', [BasicBlock, BasicBlock])
GetFirstInstruction = _library.function(Value, 'LLVMGetFirstInstruction', [BasicBlock])
GetLastInstruction = _library.function(Value, 'LLVMGetLastInstruction', [BasicBlock])

HasMetadata = _library.function(ctypes.c_int, 'LLVMHasMetadata', [Value])
GetMetadata = _library.function(Value, 'LLVMGetMetadata', [Value, ctypes.c_uint])
SetMetadata = _library.function(None, 'LLVMSetMetadata', [Value, ctypes.c_uint, Value])
GetInstructionParent = _library.function(BasicBlock, 'LLVMGetInstructionParent', [Value])
GetNextInstruction = _library.function(Value, 'LLVMGetNextInstruction', [Value])
GetPreviousInstruction = _library.function(Value, 'LLVMGetPreviousInstruction', [Value])
InstructionEraseFromParent = _library.function(None, 'LLVMInstructionEraseFromParent', [Value])
GetInstructionOpcode = _library.function(Opcode, 'LLVMGetInstructionOpcode', [Value])
GetICmpPredicate = _library.function(IntPredicate, 'LLVMGetICmpPredicate', [Value])

SetInstructionCallConv = _library.function(None, 'LLVMSetInstructionCallConv', [Value, ctypes.c_uint])
GetInstructionCallConv = _library.function(ctypes.c_uint, 'LLVMGetInstructionCallConv', [Value])
AddInstrAttribute = _library.function(None, 'LLVMAddInstrAttribute', [Value, ctypes.c_uint, Attribute])
RemoveInstrAttribute = _library.function(None, 'LLVMRemoveInstrAttribute', [Value, ctypes.c_uint,  Attribute])
SetInstrParamAlignment = _library.function(None, 'LLVMSetInstrParamAlignment', [Value, ctypes.c_uint, ctypes.c_uint])
IsTailCall = _library.function(Bool, 'LLVMIsTailCall', [Value])
SetTailCall = _library.function(None, 'LLVMSetTailCall', [Value, Bool])

GetSwitchDefaultDest = _library.function(BasicBlock, 'LLVMGetSwitchDefaultDest', [Value])

AddIncoming = _library.function(None, 'LLVMAddIncoming', [Value, ctypes.POINTER(Value), ctypes.POINTER(BasicBlock), ctypes.c_uint])
CountIncoming = _library.function(ctypes.c_uint, 'LLVMCountIncoming', [Value])
GetIncomingValue = _library.function(Value, 'LLVMGetIncomingValue', [Value, ctypes.c_uint])
GetIncomingBlock = _library.function(BasicBlock, 'LLVMGetIncomingBlock', [Value, ctypes.c_uint])


CreateBuilderInContext = _library.function(Builder, 'LLVMCreateBuilderInContext', [Context])
CreateBuilder = _library.function(Builder, 'LLVMCreateBuilder', [])
PositionBuilder = _library.function(None, 'LLVMPositionBuilder', [Builder, BasicBlock, Value])
PositionBuilderBefore = _library.function(None, 'LLVMPositionBuilderBefore', [Builder, Value])
PositionBuilderAtEnd = _library.function(None, 'LLVMPositionBuilderAtEnd', [Builder, BasicBlock])
GetInsertBlock = _library.function(BasicBlock, 'LLVMGetInsertBlock', [Builder])
ClearInsertionPosition = _library.function(None, 'LLVMClearInsertionPosition', [Builder])
InsertIntoBuilder = _library.function(None, 'LLVMInsertIntoBuilder', [Builder, Value])
InsertIntoBuilderWithName = _library.function(None, 'LLVMInsertIntoBuilderWithName', [Builder, Value, ctypes.c_char_p])
DisposeBuilder = _library.function(None, 'LLVMDisposeBuilder', [Builder])

SetCurrentDebugLocation = _library.function(None, 'LLVMSetCurrentDebugLocation', [Builder, Value])
GetCurrentDebugLocation = _library.function(Value, 'LLVMGetCurrentDebugLocation', [Builder])
SetInstDebugLocation = _library.function(None, 'LLVMSetInstDebugLocation', [Builder, Value])

BuildRetVoid = _library.function(Value, 'LLVMBuildRetVoid', [Builder])
BuildRet = _library.function(Value, 'LLVMBuildRet', [Builder, Value])
BuildAggregateRet = _library.function(Value, 'LLVMBuildAggregateRet', [Builder, ctypes.POINTER(Value), ctypes.c_uint])
BuildBr = _library.function(Value, 'LLVMBuildBr', [Builder, BasicBlock])
BuildCondBr = _library.function(Value, 'LLVMBuildCondBr', [Builder, Value, BasicBlock, BasicBlock])
BuildSwitch = _library.function(Value, 'LLVMBuildSwitch', [Builder, Value, BasicBlock, ctypes.c_uint])
BuildIndirectBr = _library.function(Value, 'LLVMBuildIndirectBr', [Builder, Value, ctypes.c_uint])
BuildInvoke = _library.function(Value, 'LLVMBuildInvoke', [Builder, Value, ctypes.POINTER(Value), ctypes.c_uint, BasicBlock, BasicBlock, ctypes.c_char_p])
BuildLandingPad = _library.function(Value, 'LLVMBuildLandingPad', [Builder, Type, Value, ctypes.c_uint, ctypes.c_char_p])
BuildResume = _library.function(Value, 'LLVMBuildResume', [Builder, Value])
BuildUnreachable = _library.function(Value, 'LLVMBuildUnreachable', [Builder])
AddCase = _library.function(None, 'LLVMAddCase', [Value, Value, BasicBlock])
AddDestination = _library.function(None, 'LLVMAddDestination', [Value, BasicBlock])
AddClause = _library.function(None, 'LLVMAddClause', [Value, Value])
SetCleanup = _library.function(None, 'LLVMSetCleanup', [Value, Bool])

BuildAdd = _library.function(Value, 'LLVMBuildAdd', [Builder, Value, Value, ctypes.c_char_p])
BuildNSWAdd = _library.function(Value, 'LLVMBuildNSWAdd', [Builder, Value, Value, ctypes.c_char_p])
BuildNUWAdd = _library.function(Value, 'LLVMBuildNUWAdd', [Builder, Value, Value, ctypes.c_char_p])
BuildFAdd = _library.function(Value, 'LLVMBuildFAdd', [Builder, Value, Value, ctypes.c_char_p])
BuildSub = _library.function(Value, 'LLVMBuildSub', [Builder, Value, Value, ctypes.c_char_p])
BuildNSWSub = _library.function(Value, 'LLVMBuildNSWSub', [Builder, Value, Value, ctypes.c_char_p])
BuildNUWSub = _library.function(Value, 'LLVMBuildNUWSub', [Builder, Value, Value, ctypes.c_char_p])
BuildFSub = _library.function(Value, 'LLVMBuildFSub', [Builder, Value, Value, ctypes.c_char_p])
BuildMul = _library.function(Value, 'LLVMBuildMul', [Builder, Value, Value, ctypes.c_char_p])
BuildNSWMul = _library.function(Value, 'LLVMBuildNSWMul', [Builder, Value, Value, ctypes.c_char_p])
BuildNUWMul = _library.function(Value, 'LLVMBuildNUWMul', [Builder, Value, Value, ctypes.c_char_p])
BuildFMul = _library.function(Value, 'LLVMBuildFMul', [Builder, Value, Value, ctypes.c_char_p])
BuildUDiv = _library.function(Value, 'LLVMBuildUDiv', [Builder, Value, Value, ctypes.c_char_p])
BuildSDiv = _library.function(Value, 'LLVMBuildSDiv', [Builder, Value, Value, ctypes.c_char_p])
BuildExactSDiv = _library.function(Value, 'LLVMBuildExactSDiv', [Builder, Value, Value, ctypes.c_char_p])
BuildFDiv = _library.function(Value, 'LLVMBuildFDiv', [Builder, Value, Value, ctypes.c_char_p])
BuildURem = _library.function(Value, 'LLVMBuildURem', [Builder, Value, Value, ctypes.c_char_p])
BuildSRem = _library.function(Value, 'LLVMBuildSRem', [Builder, Value, Value, ctypes.c_char_p])
BuildFRem = _library.function(Value, 'LLVMBuildFRem', [Builder, Value, Value, ctypes.c_char_p])
BuildShl = _library.function(Value, 'LLVMBuildShl', [Builder, Value, Value, ctypes.c_char_p])
BuildLShr = _library.function(Value, 'LLVMBuildLShr', [Builder, Value, Value, ctypes.c_char_p])
BuildAShr = _library.function(Value, 'LLVMBuildAShr', [Builder, Value, Value, ctypes.c_char_p])
BuildAnd = _library.function(Value, 'LLVMBuildAnd', [Builder, Value, Value, ctypes.c_char_p])
BuildOr = _library.function(Value, 'LLVMBuildOr', [Builder, Value, Value, ctypes.c_char_p])
BuildXor = _library.function(Value, 'LLVMBuildXor', [Builder, Value, Value, ctypes.c_char_p])
BuildBinOp = _library.function(Value, 'LLVMBuildBinOp', [Builder, Opcode, Value, Value, ctypes.c_char_p])
BuildNeg = _library.function(Value, 'LLVMBuildNeg', [Builder, Value, ctypes.c_char_p])
BuildNSWNeg = _library.function(Value, 'LLVMBuildNSWNeg', [Builder, Value, ctypes.c_char_p])
BuildNUWNeg = _library.function(Value, 'LLVMBuildNUWNeg', [Builder, Value, ctypes.c_char_p])
BuildFNeg = _library.function(Value, 'LLVMBuildFNeg', [Builder, Value, ctypes.c_char_p])
BuildNot = _library.function(Value, 'LLVMBuildNot', [Builder, Value, ctypes.c_char_p])

BuildMalloc = _library.function(Value, 'LLVMBuildMalloc', [Builder, Type, ctypes.c_char_p])
BuildArrayMalloc = _library.function(Value, 'LLVMBuildArrayMalloc', [Builder, Type, Value, ctypes.c_char_p])
BuildAlloca = _library.function(Value, 'LLVMBuildAlloca', [Builder, Type, ctypes.c_char_p])
BuildArrayAlloca = _library.function(Value, 'LLVMBuildArrayAlloca', [Builder, Type, Value, ctypes.c_char_p])
BuildFree = _library.function(Value, 'LLVMBuildFree', [Builder, Value])
BuildLoad = _library.function(Value, 'LLVMBuildLoad', [Builder, Value, ctypes.c_char_p])
BuildStore = _library.function(Value, 'LLVMBuildStore', [Builder, Value, Value])
BuildGEP = _library.function(Value, 'LLVMBuildGEP', [Builder, Value, ctypes.POINTER(Value), ctypes.c_uint, ctypes.c_char_p])
BuildInBoundsGEP = _library.function(Value, 'LLVMBuildInBoundsGEP', [Builder, Value, ctypes.POINTER(Value), ctypes.c_uint, ctypes.c_char_p])
BuildStructGEP = _library.function(Value, 'LLVMBuildStructGEP', [Builder, Value, ctypes.c_uint, ctypes.c_char_p])
BuildGlobalString = _library.function(Value, 'LLVMBuildGlobalString', [Builder, ctypes.c_char_p, ctypes.c_char_p])
BuildGlobalStringPtr = _library.function(Value, 'LLVMBuildGlobalStringPtr', [Builder, ctypes.c_char_p, ctypes.c_char_p])
if (3, 1) <= _version:
    GetVolatile = _library.function(Bool, 'LLVMGetVolatile', [Value])
    SetVolatile = _library.function(None, 'LLVMSetVolatile', [Value, Bool])

BuildTrunc = _library.function(Value, 'LLVMBuildTrunc', [Builder, Value, Type, ctypes.c_char_p])
BuildZExt = _library.function(Value, 'LLVMBuildZExt', [Builder, Value, Type, ctypes.c_char_p])
BuildSExt = _library.function(Value, 'LLVMBuildSExt', [Builder, Value, Type, ctypes.c_char_p])
BuildFPToUI = _library.function(Value, 'LLVMBuildFPToUI', [Builder, Value, Type, ctypes.c_char_p])
BuildFPToSI = _library.function(Value, 'LLVMBuildFPToSI', [Builder, Value, Type, ctypes.c_char_p])
BuildUIToFP = _library.function(Value, 'LLVMBuildUIToFP', [Builder, Value, Type, ctypes.c_char_p])
BuildSIToFP = _library.function(Value, 'LLVMBuildSIToFP', [Builder, Value, Type, ctypes.c_char_p])
BuildFPTrunc = _library.function(Value, 'LLVMBuildFPTrunc', [Builder, Value, Type, ctypes.c_char_p])
BuildFPExt = _library.function(Value, 'LLVMBuildFPExt', [Builder, Value, Type, ctypes.c_char_p])
BuildPtrToInt = _library.function(Value, 'LLVMBuildPtrToInt', [Builder, Value, Type, ctypes.c_char_p])
BuildIntToPtr = _library.function(Value, 'LLVMBuildIntToPtr', [Builder, Value, Type, ctypes.c_char_p])
BuildBitCast = _library.function(Value, 'LLVMBuildBitCast', [Builder, Value, Type, ctypes.c_char_p])
if (3, 4) <= _version:
    BuildAddrSpaceCast = _library.function(Value, 'LLVMBuildAddrSpaceCast', [Builder, Value, Type, ctypes.c_char_p])
BuildZExtOrBitCast = _library.function(Value, 'LLVMBuildZExtOrBitCast', [Builder, Value, Type, ctypes.c_char_p])
BuildSExtOrBitCast = _library.function(Value, 'LLVMBuildSExtOrBitCast', [Builder, Value, Type, ctypes.c_char_p])
BuildTruncOrBitCast = _library.function(Value, 'LLVMBuildTruncOrBitCast', [Builder, Value, Type, ctypes.c_char_p])
BuildCast = _library.function(Value, 'LLVMBuildCast', [Builder, Opcode, Value, Type, ctypes.c_char_p])
BuildPointerCast = _library.function(Value, 'LLVMBuildPointerCast', [Builder, Value, Type, ctypes.c_char_p])
BuildIntCast = _library.function(Value, 'LLVMBuildIntCast', [Builder, Value, Type, ctypes.c_char_p])
BuildFPCast = _library.function(Value, 'LLVMBuildFPCast', [Builder, Value, Type, ctypes.c_char_p])

BuildICmp = _library.function(Value, 'LLVMBuildICmp', [Builder, IntPredicate, Value, Value, ctypes.c_char_p])
BuildFCmp = _library.function(Value, 'LLVMBuildFCmp', [Builder, RealPredicate, Value, Value, ctypes.c_char_p])

BuildPhi = _library.function(Value, 'LLVMBuildPhi', [Builder, Type, ctypes.c_char_p])
BuildCall = _library.function(Value, 'LLVMBuildCall', [Builder, Value, ctypes.POINTER(Value), ctypes.c_uint, ctypes.c_char_p])
BuildSelect = _library.function(Value, 'LLVMBuildSelect', [Builder, Value, Value, Value, ctypes.c_char_p])
BuildVAArg = _library.function(Value, 'LLVMBuildVAArg', [Builder, Value, Type, ctypes.c_char_p])
BuildExtractElement = _library.function(Value, 'LLVMBuildExtractElement', [Builder, Value, Value, ctypes.c_char_p])
BuildInsertElement = _library.function(Value, 'LLVMBuildInsertElement', [Builder, Value, Value, Value, ctypes.c_char_p])
BuildShuffleVector = _library.function(Value, 'LLVMBuildShuffleVector', [Builder, Value, Value, Value, ctypes.c_char_p])
BuildExtractValue = _library.function(Value, 'LLVMBuildExtractValue', [Builder, Value, ctypes.c_uint, ctypes.c_char_p])
BuildInsertValue = _library.function(Value, 'LLVMBuildInsertValue', [Builder, Value, Value, ctypes.c_uint, ctypes.c_char_p])

BuildIsNull = _library.function(Value, 'LLVMBuildIsNull', [Builder, Value, ctypes.c_char_p])
BuildIsNotNull = _library.function(Value, 'LLVMBuildIsNotNull', [Builder, Value, ctypes.c_char_p])
BuildPtrDiff = _library.function(Value, 'LLVMBuildPtrDiff', [Builder, Value, Value, ctypes.c_char_p])
if (3, 3) <= _version:
    BuildAtomicRMW = _library.function(Value, 'LLVMBuildAtomicRMW', [Builder, AtomicRMWBinOp, Value, Value, AtomicOrdering, Bool])


CreateModuleProviderForExistingModule = _library.function(ModuleProvider, 'LLVMCreateModuleProviderForExistingModule', [Module])
DisposeModuleProvider = _library.function(None, 'LLVMDisposeModuleProvider', [ModuleProvider])


CreateMemoryBufferWithContentsOfFile = _library.function(Bool, 'LLVMCreateMemoryBufferWithContentsOfFile', [ctypes.c_char_p, ctypes.POINTER(MemoryBuffer), ctypes.POINTER(_c.string_buffer)])
CreateMemoryBufferWithSTDIN = _library.function(Bool, 'LLVMCreateMemoryBufferWithSTDIN', [ctypes.POINTER(MemoryBuffer), ctypes.POINTER(_c.string_buffer)])
if (3, 3) <= _version:
    CreateMemoryBufferWithMemoryRange = _library.function(MemoryBuffer, 'LLVMCreateMemoryBufferWithMemoryRange', [_c.string_buffer, ctypes.c_size_t, ctypes.c_char_p, Bool]);
    CreateMemoryBufferWithMemoryRangeCopy = _library.function(MemoryBuffer, 'LLVMCreateMemoryBufferWithMemoryRangeCopy', [_c.string_buffer, ctypes.c_size_t, ctypes.c_char_p]);
    GetBufferStart = _library.function(_c.string_buffer, 'LLVMGetBufferStart', [MemoryBuffer]);
    GetBufferSize = _library.function(ctypes.c_size_t, 'LLVMGetBufferSize', [MemoryBuffer]);
DisposeMemoryBuffer = _library.function(None, 'LLVMDisposeMemoryBuffer', [MemoryBuffer])


if (3, 3) <= _version:
    _library.function(Bool, 'LLVMStartMultithreaded', [])
    _library.function(None, 'LLVMStopMultithreaded', [])
    _library.function(Bool, 'LLVMIsMultithreaded', [])


GetGlobalPassRegistry = _library.function(PassRegistry, 'LLVMGetGlobalPassRegistry', [])

CreatePassManager = _library.function(PassManager, 'LLVMCreatePassManager', [])
CreateFunctionPassManagerForModule = _library.function(PassManager, 'LLVMCreateFunctionPassManagerForModule', [Module])
CreateFunctionPassManager = _library.function(PassManager, 'LLVMCreateFunctionPassManager', [ModuleProvider])
RunPassManager = _library.function(Bool, 'LLVMRunPassManager', [PassManager, Module])
InitializeFunctionPassManager = _library.function(Bool, 'LLVMInitializeFunctionPassManager', [PassManager])
RunFunctionPassManager = _library.function(Bool, 'LLVMRunFunctionPassManager', [PassManager, Value])
FinalizeFunctionPassManager = _library.function(Bool, 'LLVMFinalizeFunctionPassManager', [PassManager])
DisposePassManager = _library.function(None, 'LLVMDisposePassManager', [PassManager])
