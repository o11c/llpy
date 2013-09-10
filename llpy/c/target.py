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

''' low-level wrapper of llvm-c/Target.h
'''

import ctypes

from . import _c

from .core import _library, _version
from .core import Bool
from .core import Context
from .core import Module
from .core import Type
if _version <= (2, 9):
    from .core import TypeHandle
from .core import Value
from .core import BasicBlock
from .core import Builder
from .core import ModuleProvider
from .core import MemoryBuffer
from .core import PassManager
from .core import PassRegistry
from .core import Use

from .core import Attribute
from .core import Opcode
from .core import TypeKind
from .core import Linkage
from .core import Visibility
from .core import CallConv
from .core import IntPredicate
from .core import RealPredicate
if (3, 0) <= _version:
    from .core import LandingPadClauseTy

if (3, 3) <= _version:
    from .core import ThreadLocalMode
    from .core import AtomicOrdering
    from .core import AtomicRMWBinOp


byte_orderings = [
    'BigEndian',
    'LittleEndian',
]
ByteOrdering = _c.enum('ByteOrdering', **{v: k for k, v in enumerate(byte_orderings)})
del byte_orderings

TargetData = _c.opaque('TargetData')
if (3, 0) <= _version:
    TargetLibraryInfo = _c.opaque('TargetLibraryInfoData')
StructLayout = _c.opaque('StructLayout')


# later filled in with successful add_target
ALL_TARGETS = set()
if (3, 1) <= _version:
    ALL_ASM_PRINTERS = set()
    ALL_ASM_PARSERS = set()
    ALL_ASM_DISASSEMBLERS = set()

def add_target(target):
    # assumption: a target must exist in order to have asm printers, etc.
    if target in ALL_TARGETS:
        return
    try:
        name = 'Initialize%sTargetInfo' % target
        globals()[name] = _library.function(None, 'LLVM%s' % name, [])
        name = 'Initialize%sTarget' % target
        globals()[name] = _library.function(None, 'LLVM%s' % name, [])
        if (3, 0) <= _version:
            name = 'Initialize%sTargetMC' % target
            globals()[name] = _library.function(None, 'LLVM%s' % name, [])
        ALL_TARGETS.add(target)
    except AttributeError:
        return

    if (3, 1) <= _version:
        try:
            name = 'Initialize%sAsmPrinter' % target
            globals()[name] = _library.function(None, 'LLVM%s' % name, [])
            ALL_ASM_PRINTERS.add(target)
        except AttributeError:
            pass

        try:
            name = 'Initialize%sAsmParser' % target
            globals()[name] = _library.function(None, 'LLVM%s' % name, [])
            ALL_ASM_PARSERS.add(target)
        except AttributeError:
            pass

        try:
            name = 'Initialize%sDisassembler' % target
            globals()[name] = _library.function(None, 'LLVM%s' % name, [])
            ALL_ASM_DISASSEMBLERS.add(target)
        except AttributeError:
            pass

# This is a list of all the targets I've found across all LLVM versions
# that I can test. If I missed one, you can call add_target yourself.
for target in [
    'AArch64',
    'Alpha',
    'ARM',
    'Blackfin',
    'CBackend',
    'CellSPU',
    'CppBackend',
    'Hexagon',
    'MBlaze',
    'Mips',
    'MSP430',
    'NVPTX',
    'PowerPC',
    'PTX',
    'R600',
    'Sparc',
    'SystemZ',
    'XCore',
    'X86',
]:
    add_target(target)

def InitializeAllTargetInfos():
    'synthesized'
    for target in ALL_TARGETS:
        globals()['Initialize%sTargetInfo' % target]()

def InitializeAllTarget():
    'synthesized'
    for target in ALL_TARGETS:
        globals()['Initialize%sTarget' % target]()

if (3, 1) <= _version:
    def InitializeAllTargetMC():
        'synthesized'
        for target in ALL_TARGETS:
            globals()['Initialize%sTargetMC' % target]()

    def InitializeAllAsmPrinters():
        'synthesized'
        for target in ALL_ASM_PRINTERS:
            globals()['Initialize%sAsmPrinter' % target]()

    def InitializeAllAsmParsers():
        'synthesized'
        for target in ALL_ASM_PARSERS:
            globals()['Initialize%sAsmParser' % target]()

    def InitializeAllDisassemblers():
        'synthesized'
        for target in ALL_DISASSEMBLERS:
            globals()['Initialize%sDisassembler' % target]()


def InitializeNativeTarget_nyi():
    if False: # have native target
        'init native target info'
        'init native target'
        if (3, 0) <= _version:
            'init native mc'
        return 0
    return 1


CreateTargetData = _library.function(TargetData, 'LLVMCreateTargetData', [ctypes.c_char_p])
AddTargetData = _library.function(None, 'LLVMAddTargetData', [TargetData, PassManager])
if (3, 0) <= _version:
    AddTargetLibraryInfo = _library.function(None, 'LLVMAddTargetLibraryInfo', [TargetLibraryInfo, PassManager])
CopyStringRepOfTargetData = _library.function(_c.string_buffer, 'LLVMCopyStringRepOfTargetData', [TargetData])
ByteOrder = _library.function(ByteOrdering, 'LLVMByteOrder', [TargetData])
PointerSize = _library.function(ctypes.c_uint, 'LLVMPointerSize', [TargetData])
if (3, 2) <= _version:
    PointerSizeForAS = _library.function(ctypes.c_uint, 'LLVMPointerSizeForAS', [TargetData, ctypes.c_uint])
IntPtrType = _library.function(Type, 'LLVMIntPtrType', [TargetData])
if (3, 2) <= _version:
    IntPtrTypeForAS = _library.function(Type, 'LLVMIntPtrTypeForAS', [TargetData, ctypes.c_uint])
SizeOfTypeInBits = _library.function(ctypes.c_ulonglong, 'LLVMSizeOfTypeInBits', [TargetData, Type])
StoreSizeOfType = _library.function(ctypes.c_ulonglong, 'LLVMStoreSizeOfType', [TargetData, Type])
ABISizeOfType = _library.function(ctypes.c_ulonglong, 'LLVMABISizeOfType', [TargetData, Type])
ABIAlignmentOfType = _library.function(ctypes.c_uint, 'LLVMABIAlignmentOfType', [TargetData, Type])
CallFrameAlignmentOfType = _library.function(ctypes.c_uint, 'LLVMCallFrameAlignmentOfType', [TargetData, Type])
PreferredAlignmentOfType = _library.function(ctypes.c_uint, 'LLVMPreferredAlignmentOfType', [TargetData, Type])
PreferredAlignmentOfGlobal = _library.function(ctypes.c_uint, 'LLVMPreferredAlignmentOfGlobal', [TargetData, Value])
ElementAtOffset = _library.function(ctypes.c_uint, 'LLVMElementAtOffset', [TargetData, Type, ctypes.c_ulonglong])
OffsetOfElement = _library.function(ctypes.c_ulonglong, 'LLVMOffsetOfElement', [TargetData, Type, ctypes.c_uint])
if _version <= (2, 9):
    InvalidateStructLayout = _library.function(None, 'LLVMInvalidateStructLayout', [TargetData, Type])
DisposeTargetData = _library.function(None, 'LLVMDisposeTargetData', [TargetData])
