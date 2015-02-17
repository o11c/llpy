#   -*- encoding: utf-8 -*-
#   Copyright © 2013-2015 Ben Longbons
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
import os
import warnings

import llpy

from . import _c, _hardcoded

from .core import _library, _version
from .core import Context
from .core import Type
from .core import Value
from .core import PassManager

from ..utils import cuntested as untested


del llpy.allow_unknown_machines

byte_orderings = [
    'BigEndian',
    'LittleEndian',
]
ByteOrdering = _c.enum('ByteOrdering', **{v: k for k, v in enumerate(byte_orderings)})
del byte_orderings

TargetData = _c.opaque('TargetData')
TargetLibraryInfo = _c.opaque('TargetLibraryInfoData')
if _version <= (3, 3):
    StructLayout = _c.opaque('StructLayout')


# later filled in with successful add_target
ALL_TARGETS = set()
if (3, 1) <= _version:
    ALL_ASM_PRINTERS = set()
    ALL_ASM_PARSERS = set()
    ALL_DISASSEMBLERS = set()

def add_target(target):
    # assumption: a target must exist in order to have asm printers, etc.
    if target in ALL_TARGETS:
        return
    try:
        name = 'Initialize%sTargetInfo' % target
        globals()[name] = _library.function(None, 'LLVM%s' % name, [])
        name = 'Initialize%sTarget' % target
        globals()[name] = _library.function(None, 'LLVM%s' % name, [])
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
            ALL_DISASSEMBLERS.add(target)
        except AttributeError:
            pass

# This is a list of all the targets I've found across all LLVM versions
# that I can test. If I missed one, you can call add_target yourself.
for target in _hardcoded.TARGETS:
    add_target(target)
del target

def InitializeAllTargetInfos():
    ''' The main program should call this function if it wants access to
        all available targets that LLVM is configured to support.
    '''
    for target in ALL_TARGETS:
        globals()['Initialize%sTargetInfo' % target]()

def InitializeAllTargets():
    ''' The main program should call this function if it wants to link in
        all available targets that LLVM is configured to support.
    '''
    for target in ALL_TARGETS:
        globals()['Initialize%sTarget' % target]()

if (3, 1) <= _version:
    def InitializeAllTargetMCs():
        ''' The main program should call this function if it wants access
            to all available target MC that LLVM is configured to support.
        '''
        for target in ALL_TARGETS:
            globals()['Initialize%sTargetMC' % target]()

    def InitializeAllAsmPrinters():
        ''' The main program should call this function if it wants all
            asm printers that LLVM is configured to support, to make them
            available via the TargetRegistry.
        '''
        for target in ALL_ASM_PRINTERS:
            globals()['Initialize%sAsmPrinter' % target]()

    def InitializeAllAsmParsers():
        ''' The main program should call this function if it wants all
            asm parsers that LLVM is configured to support, to make them
            available via the TargetRegistry.
        '''
        for target in ALL_ASM_PARSERS:
            globals()['Initialize%sAsmParser' % target]()

    def InitializeAllDisassemblers():
        ''' The main program should call this function if it wants all
            disassemblers that LLVM is configured to support, to make them
            available via the TargetRegistry.
        '''
        for target in ALL_DISASSEMBLERS:
            globals()['Initialize%sDisassembler' % target]()

_native = _hardcoded.MACHINES.get(os.uname()[4])

# TODO in 3.4 you can maybe use GetDefaultTargetTriple?
if not llpy.__allow_unknown_machines:
    if _native is None or _native not in ALL_TARGETS:
        msg = ('llpy does not know how to map `uname -m` (%s) to one of:\n%s\nPlease send a patch to the `machines` dict in llpy/__init__.py'
                % (os.uname()[4], ', '.join(sorted(ALL_TARGETS))))
        raise ImportError(msg)
if _native is not None:
    if _native not in ALL_TARGETS:
        add_target(_native)
        if _native in ALL_TARGETS:
            warnings.warn('Native target is not recognized but does exist, please send patches!')
        else:
            warnings.warn('Native target is not recognized and does not exist!')
            _native = None
else:
    warnings.warn('Unable to guess native target, please send patches!')

def InitializeNativeTarget():
    if _native is not None:
        if _native in ALL_TARGETS:
            globals()['Initialize%sTargetInfo' % native]()
            globals()['Initialize%sTarget' % native]()
            globals()['Initialize%sMC' % native]()
            return 0
        else:
            warnings.warn('Native target known but not found (???)')
            return 1
    else:
        if llpy.__native_fallback_all:
            warnings.warn('Unknown native target, falling back to all!')
            InitializeAllTargetInfos()
            InitializeAllTargets()
            InitializeAllTargetMCs()
            return 0
        warnings.warn('Unknown native target and fallback disabled!')
        return 1

if (3, 4) <= _version:
    def InitializeNativeAsmParser():
        if _native is not None:
            if _native in ALL_ASM_PARSERS:
                globals()['Initialize%sAsmParser' % _native]()
                return 0
            else:
                if _native in ALL_TARGETS:
                    warnings.warn('Native target does not support asm parsing')
                else:
                    warnings.warn('Native target known but not found (???)')
                return 1
        else:
            if llpy.__native_fallback_all:
                warnings.warn('Unknown native target, falling back to all!')
                InitializeAllAsmParsers()
                return 0
            warnings.warn('Unknown native target and fallback disabled!')
            return 1

    def InitializeNativeAsmPrinter():
        if _native is not None:
            if _native in ALL_ASM_PRINTERS:
                globals()['Initialize%sAsmPrinter' % _native]()
                return 0
            else:
                if _native in ALL_TARGETS:
                    warnings.warn('Native target does not support asm printing')
                else:
                    warnings.warn('Native target known but not found (???)')
                return 1
        else:
            if llpy.__native_fallback_all:
                warnings.warn('Unknown native target, falling back to all!')
                InitializeAllAsmPrinters()
                return 0
            warnings.warn('Unknown native target and fallback disabled!')
            return 1

    def InitializeNativeDisassembler():
        if _native is not None:
            if _native in ALL_DISASSEMBLERS:
                globals()['Initialize%sDisassembler' % _native]()
                return 0
            else:
                if _native in ALL_TARGETS:
                    warnings.warn('Native target does not support disassembling')
                else:
                    warnings.warn('Native target known but not found (???)')
                return 1
        else:
            if llpy.__native_fallback_all:
                warnings.warn('Unknown native target, falling back to all!')
                InitializeAllDisassemblers()
                return 0
            warnings.warn('Unknown native target and fallback disabled!')
            return 1


CreateTargetData = _library.function(TargetData, 'LLVMCreateTargetData', [ctypes.c_char_p])
AddTargetData = _library.function(None, 'LLVMAddTargetData', [TargetData, PassManager])
AddTargetData = untested(AddTargetData)
AddTargetLibraryInfo = _library.function(None, 'LLVMAddTargetLibraryInfo', [TargetLibraryInfo, PassManager])
AddTargetLibraryInfo = untested(AddTargetLibraryInfo)
CopyStringRepOfTargetData = _library.function(_c.string_buffer, 'LLVMCopyStringRepOfTargetData', [TargetData])
ByteOrder = _library.function(ByteOrdering, 'LLVMByteOrder', [TargetData])
PointerSize = _library.function(ctypes.c_uint, 'LLVMPointerSize', [TargetData])
if (3, 2) <= _version:
    PointerSizeForAS = _library.function(ctypes.c_uint, 'LLVMPointerSizeForAS', [TargetData, ctypes.c_uint])
IntPtrType = _library.function(Type, 'LLVMIntPtrType', [TargetData])
IntPtrType = untested(IntPtrType)
if (3, 2) <= _version:
    IntPtrTypeForAS = _library.function(Type, 'LLVMIntPtrTypeForAS', [TargetData, ctypes.c_uint])
    IntPtrTypeForAS = untested(IntPtrTypeForAS)
if (3, 4) <= _version:
    IntPtrTypeInContext = _library.function(Type, 'LLVMIntPtrTypeInContext', [Context, TargetData])
    IntPtrTypeInContext = untested(IntPtrTypeInContext)
    IntPtrTypeForASInContext = _library.function(Type, 'LLVMIntPtrTypeForASInContext', [Context, TargetData, ctypes.c_uint])
    IntPtrTypeForASInContext = untested(IntPtrTypeForASInContext)
SizeOfTypeInBits = _library.function(ctypes.c_ulonglong, 'LLVMSizeOfTypeInBits', [TargetData, Type])
StoreSizeOfType = _library.function(ctypes.c_ulonglong, 'LLVMStoreSizeOfType', [TargetData, Type])
ABISizeOfType = _library.function(ctypes.c_ulonglong, 'LLVMABISizeOfType', [TargetData, Type])
ABIAlignmentOfType = _library.function(ctypes.c_uint, 'LLVMABIAlignmentOfType', [TargetData, Type])
CallFrameAlignmentOfType = _library.function(ctypes.c_uint, 'LLVMCallFrameAlignmentOfType', [TargetData, Type])
PreferredAlignmentOfType = _library.function(ctypes.c_uint, 'LLVMPreferredAlignmentOfType', [TargetData, Type])
PreferredAlignmentOfGlobal = _library.function(ctypes.c_uint, 'LLVMPreferredAlignmentOfGlobal', [TargetData, Value])
ElementAtOffset = _library.function(ctypes.c_uint, 'LLVMElementAtOffset', [TargetData, Type, ctypes.c_ulonglong])
OffsetOfElement = _library.function(ctypes.c_ulonglong, 'LLVMOffsetOfElement', [TargetData, Type, ctypes.c_uint])
DisposeTargetData = _library.function(None, 'LLVMDisposeTargetData', [TargetData])
