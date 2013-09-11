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

''' Wrap the C interface to the llvm-c/Target.h
'''

import ctypes

from llpy.utils import u2b, untested
from llpy.c import (
        core as _core,
        target as _target,
)
from llpy.core import (
        _message_to_string,
        _version,
)
from llpy.c.target import ByteOrdering


class TargetData:
    __slots__ = ('_raw')

    def __init__(self, name):
        ''' Creates target data from a target layout string.
        '''
        self._raw = _target.CreateTargetData(u2b(name))

    def __del__(self):
        ''' Deallocates a TargetData.
        '''
        _target.DisposeTargetData(self._raw)

    @untested
    def Add(self, pm):
        ''' Adds target data information to a pass manager. This does not
            take ownership of the target data.
        '''
        _target.AddTargetData(self._raw, pm._raw)

    def StringRep(self):
        ''' Converts target data to a target layout string.
        '''
        return _message_to_string(_target.CopyStringRepOfTargetData(self._raw))

    def ByteOrder(self):
        ''' Returns the byte order of a target, either
            ByteOrdering.BigEndian or ByteOrdering.LittleEndian.
        '''
        return _target.ByteOrder(self._raw)

    if _version <= (3, 1):
        def PointerSize(self, space=0):
            ''' Returns the pointer size in bytes for a target for a
                specified address space.
            '''
            if space == 0:
                return _target.PointerSize(self._raw)
            # messing with the global context here
            i8 = _core.Int8Type()
            i8p = _core.PointerType(i8, space)
            sz = _target.SizeOfTypeInBits(self._raw, i8p)
            return sz // 8

    if (3, 2) <= _version:
        def PointerSize(self, space=0):
            ''' Returns the pointer size in bytes for a target for a
                specified address space.
            '''
            return _target.PointerSizeForAS(self._raw, space)

    # IntPtrType omitted because it uses the global context
    # it can be implemented properly in terms of the pointer size though

    def SizeOfTypeInBits(self, ty):
        ''' Computes the size of a type in bytes for a target.
        '''
        return _target.SizeOfTypeInBits(self._raw, ty._raw)

    def StoreSizeOfType(self, ty):
        ''' Computes the storage size of a type in bytes for a target.
        '''
        return _target.StoreSizeOfType(self._raw, ty._raw)

    def ABISizeOfType(self, ty):
        ''' Computes the ABI size of a type in bytes for a target.
        '''
        return _target.ABISizeOfType(self._raw, ty._raw)

    def ABIAlignmentOfType(self, ty):
        ''' Computes the ABI alignment of a type in bytes for a target.
        '''
        return _target.ABIAlignmentOfType(self._raw, ty._raw)

    def CallFrameAlignmentOfType(self, ty):
        ''' Computes the call frame alignment of a type in bytes for a target.
        '''
        return _target.CallFrameAlignmentOfType(self._raw, ty._raw)

    def PreferredAlignmentOfType(self, ty):
        ''' Computes the preferred alignment of a type in bytes for a target.
        '''
        return _target.PreferredAlignmentOfType(self._raw, ty._raw)

    def PreferredAlignmentOfGlobal(self, val):
        ''' Computes the preferred alignment of a global variable in bytes for a target.
        '''
        return _target.PreferredAlignmentOfGlobal(self._raw, val._raw)

    def ElementAtOffset(self, ty, off):
        ''' Computes the structure element that contains the byte offset for a target.
        '''
        return _target.ElementAtOffset(self._raw, ty._raw, off)

    def OffsetOfElement(self, ty, eli):
        ''' Computes the byte offset of the indexed struct element for a target.
        '''
        return _target.OffsetOfElement(self._raw, ty._raw, eli)

# omit class TargetLibraryInfo, it appears to be unusable
# omit class StructLayout, it is unused


@untested
def initialize_target_info(target):
    assert target in _target.ALL_TARGETS
    getattr(_target, 'Initialize%sTargetInfo' % target)()

@untested
def initialize_target(target):
    assert target in _target.ALL_TARGETS
    getattr(_target, 'Initialize%sTarget' % target)()

if (3, 0) <= _version:
    @untested
    def initialize_target_mc(target):
        assert target in _target.ALL_TARGETS
        getattr(_target, 'Initialize%sTargetMC' % target)()

if (3, 1) <= _version:
    @untested
    def initialize_asm_printer(target):
        assert target in _target.ALL_ASM_PRINTERS
        getattr(_target, 'Initialize%sAsmPrinter' % target)()

    @untested
    def initialize_asm_parser(target):
        assert target in _target.ALL_ASM_PARSERS
        getattr(_target, 'Initialize%sAsmParser' % target)()

    @untested
    def initialize_asm_disassembler(target):
        assert target in _target.ALL_DISASSEMBLERS
        getattr(_target, 'Initialize%sDisassembler' % target)()

from llpy.c.target import InitializeAllTargetInfos
InitializeAllTargetInfos = untested(InitializeAllTargetInfos)
from llpy.c.target import InitializeAllTargets
InitializeAllTargets = untested(InitializeAllTargets)

if (3, 1) <= _version:
    from llpy.c.target import InitializeAllTargetMCs
    InitializeAllTargetMCs = untested(InitializeAllTargetMCs)
    from llpy.c.target import InitializeAllAsmPrinters
    InitializeAllAsmPrinters = untested(InitializeAllAsmPrinters)
    from llpy.c.target import InitializeAllAsmParsers
    InitializeAllAsmParsers = untested(InitializeAllAsmParsers)
    from llpy.c.target import InitializeAllDisassemblers
    InitializeAllDisassemblers = untested(InitializeAllDisassemblers)
