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

''' low-level wrapper of llvm-c/Disassembler.h
'''

import ctypes

from . import _c

from .core import _library, _version

from ..utils import cuntested as untested


DisasmContext = _c.opaque('DisasmContext')

OpInfoCallback = ctypes.CFUNCTYPE(ctypes.c_int, *[ctypes.c_void_p, ctypes.c_uint64, ctypes.c_uint64, ctypes.c_uint64, ctypes.c_int, ctypes.c_void_p])

class OpInfoSymbol1(ctypes.Structure):
    _fields_ = [
        ('Present', ctypes.c_uint64),
        ('Name', ctypes.c_char_p),
        ('Value', ctypes.c_uint64),
    ]

class OpInfo1(ctypes.Structure):
    _fields_ = [
        ('AddSymbol', OpInfoSymbol1),
        ('SubtractSymbol', OpInfoSymbol1),
        ('Value', ctypes.c_uint64),
        ('VariantKind', ctypes.c_uint64),
    ]

# TODO see about making these enums
VariantKind_None = 0

VariantKind_ARM_HI16 = 1
VariantKind_ARM_LO16 = 2

if (3, 5) <= _version:
    VariantKind_ARM64_PAGE       = 1
    VariantKind_ARM64_PAGEOFF    = 2
    VariantKind_ARM64_GOTPAGE    = 3
    VariantKind_ARM64_GOTPAGEOFF = 4
    VariantKind_ARM64_TLVP       = 5
    VariantKind_ARM64_TLVOFF     = 6

SymbolLookupCallback = ctypes.CFUNCTYPE(ctypes.c_char_p, *[ctypes.c_void_p, ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64), ctypes.c_uint64, ctypes.POINTER(ctypes.c_char_p)])

ReferenceType_InOut_None = 0

ReferenceType_In_Branch = 1
ReferenceType_In_PCrel_Load = 2
if (3, 5) <= _version:
    ReferenceType_In_ARM64_ADRP   = 0x100000001
    ReferenceType_In_ARM64_ADDXri = 0x100000002
    ReferenceType_In_ARM64_LDRXui = 0x100000003
    ReferenceType_In_ARM64_LDRXl  = 0x100000004
    ReferenceType_In_ARM64_ADR    = 0x100000005

ReferenceType_Out_SymbolStub = 1
ReferenceType_Out_LitPool_SymAddr = 2
ReferenceType_Out_LitPool_CstrAddr = 3
if (3, 4) <= _version:
    ReferenceType_Out_Objc_CFString_Ref = 4
    ReferenceType_Out_Objc_Message = 5
    ReferenceType_Out_Objc_Message_Ref = 6
    ReferenceType_Out_Objc_Selector_Ref = 7
    ReferenceType_Out_Objc_Class_Ref = 8
if (3, 5) <= _version:
    ReferenceType_DeMangled_Name = 9


Option_UseMarkup = 1
if (3, 3) <= _version:
    Option_PrintImmHex = 2
    Option_AsmPrinterVariant = 4
if (3, 4) <= _version:
    Option_SetInstrComments =  8
    Option_PrintLatency = 16

CreateDisasm = _library.function(DisasmContext, 'LLVMCreateDisasm', [ctypes.c_char_p, ctypes.c_void_p, ctypes.c_int, OpInfoCallback, SymbolLookupCallback])
CreateDisasm = untested(CreateDisasm)
if (3, 3) <= _version:
    CreateDisasmCPU = _library.function(DisasmContext, 'LLVMCreateDisasmCPU', [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_void_p, ctypes.c_int, OpInfoCallback, SymbolLookupCallback])
    CreateDisasmCPU = untested(CreateDisasmCPU)
if (3, 2) <= _version:
    SetDisasmOptions = _library.function(ctypes.c_int, 'LLVMSetDisasmOptions', [DisasmContext, ctypes.c_uint64])
    SetDisasmOptions = untested(SetDisasmOptions)
DisasmDispose = _library.function(None, 'LLVMDisasmDispose', [DisasmContext])
DisasmDispose = untested(DisasmDispose)
DisasmInstruction = _library.function(ctypes.c_size_t, 'LLVMDisasmInstruction', [DisasmContext, ctypes.POINTER(ctypes.c_uint8), ctypes.c_uint64, ctypes.c_uint64, ctypes.POINTER(ctypes.c_char), ctypes.c_size_t])
DisasmInstruction = untested(DisasmInstruction)
