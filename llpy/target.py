#   -*- encoding: utf-8 -*-
#   Copyright © 2013,2015 Ben Longbons
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

from llpy.compat import is_int
from llpy.utils import b2u, u2b, untested
from llpy.c import (
        _c,
        core as _core,
        target as _target,
        target_machine as _machine,
)
from llpy.core import (
        Type,
        StructType,
        GlobalVariable,

        _message_to_string,
        _version,
)

from llpy.io import (
        MemoryBuffer,
)
from llpy.c.target import ByteOrdering


class TargetData(object):
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
        assert isinstance(pm, PassManager)
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
            assert is_int(space)
            if space == 0:
                return _target.PointerSize(self._raw)
            # messing with the global context here
            i8 = _core.Int8Type()
            i8p = _core.PointerType(i8, space)
            sz = _target.SizeOfTypeInBits(self._raw, i8p)
            return sz // 8

    if (3, 2) <= _version:
        def PointerSize(self, space=0):
            assert is_int(space)
            ''' Returns the pointer size in bytes for a target for a
                specified address space.
            '''
            return _target.PointerSizeForAS(self._raw, space)

    # IntPtrType omitted because it uses the global context
    # it can be implemented properly in terms of the pointer size though

    def SizeOfTypeInBits(self, ty):
        ''' Computes the size of a type in bytes for a target.
        '''
        assert isinstance(ty, Type)
        return _target.SizeOfTypeInBits(self._raw, ty._raw)

    def StoreSizeOfType(self, ty):
        ''' Computes the storage size of a type in bytes for a target.
        '''
        assert isinstance(ty, Type)
        return _target.StoreSizeOfType(self._raw, ty._raw)

    def ABISizeOfType(self, ty):
        ''' Computes the ABI size of a type in bytes for a target.
        '''
        assert isinstance(ty, Type)
        return _target.ABISizeOfType(self._raw, ty._raw)

    def ABIAlignmentOfType(self, ty):
        ''' Computes the ABI alignment of a type in bytes for a target.
        '''
        assert isinstance(ty, Type)
        return _target.ABIAlignmentOfType(self._raw, ty._raw)

    def CallFrameAlignmentOfType(self, ty):
        ''' Computes the call frame alignment of a type in bytes for a target.
        '''
        assert isinstance(ty, Type)
        return _target.CallFrameAlignmentOfType(self._raw, ty._raw)

    def PreferredAlignmentOfType(self, ty):
        ''' Computes the preferred alignment of a type in bytes for a target.
        '''
        assert isinstance(ty, Type)
        return _target.PreferredAlignmentOfType(self._raw, ty._raw)

    def PreferredAlignmentOfGlobal(self, val):
        ''' Computes the preferred alignment of a global variable in bytes for a target.
        '''
        assert isinstance(val, GlobalVariable)
        return _target.PreferredAlignmentOfGlobal(self._raw, val._raw)

    def ElementAtOffset(self, ty, off):
        ''' Computes the structure element that contains the byte offset for a target.
        '''
        assert isinstance(ty, StructType)
        assert is_int(off)
        return _target.ElementAtOffset(self._raw, ty._raw, off)

    def OffsetOfElement(self, ty, eli):
        ''' Computes the byte offset of the indexed struct element for a target.
        '''
        assert isinstance(ty, StructType)
        assert is_int(eli)
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

from llpy.c.target import InitializeNativeTarget
InitializeNativeTarget = untested(InitializeNativeTarget)

if (3, 4) <= _version:
    from llpy.c.target import InitializeNativeAsmParser
    InitializeNativeAsmParser = untested(InitializeNativeAsmParser)
    from llpy.c.target import InitializeNativeAsmPrinter
    InitializeNativeAsmPrinter = untested(InitializeNativeAsmPrinter)
    from llpy.c.target import InitializeNativeDisassembler
    InitializeNativeDisassembler = untested(InitializeNativeDisassembler)


if (3, 1) <= _version:

    from llpy.c.target_machine import (
            CodeGenOptLevel,
            RelocMode,
            CodeModel,
            CodeGenFileType,
    )

    class Target(object):
        __slots__ = ('_raw')

        @untested
        def __new__(cls, raw):
            assert cls is Target
            assert isinstance(raw, _machine.Target)
            if raw:
                self = object.__new__(Target)
                self._raw = raw
                return self
            else:
                return None

        @staticmethod
        @untested
        def GetFirst():
            return Target(_machine.GetFirstTarget())

        @untested
        def GetNext(self):
            return Target(_machine.GetNextTarget(self._raw))

        @untested
        def Name(self):
            return b2u(_machine.GetTargetName(self._raw))

        @untested
        def Description(self):
            return b2u(_machine.GetTargetDescription(self._raw))

        @untested
        def HasJIT(self):
            return bool(_machine.TargetHasJIT(self._raw))

        @untested
        def HasTargetMachine(self):
            return bool(_machine.TargetHasTargetMachine(self._raw))

        @untested
        def HasAsmBackend(self):
            return bool(_machine.TargetHasAsmBackend(self._raw))

    class TargetMachine(object):

        @untested
        def __init__(self, target, triple, cpu, features, opt, reloc, codemodel):
            assert isinstance(opt, CodeGenOptLevel)
            assert isinstance(reloc, RelocMode)
            assert isinstance(codemodel, CodeModel)
            self._raw = _machine.CreateTargetMachine(target._raw, u2b(triple), u2b(cpu), u2b(features), opt, reloc, codemodel)

        @untested
        def __del__(self):
            _machine.DisposeTargetMachine(self._raw)

        @untested
        def Target(self):
            return Target(_machine.GetTargetMachineTarget(self._raw))

        @untested
        def Triple(self):
            return _message_to_string(_machine.GetTargetMachineTriple(self._raw))

        @untested
        def CPU(self):
            return _message_to_string(_machine.GetTargetMachineCPU(self._raw))

        @untested
        def FeatureString(self):
            return _message_to_string(_machine.GetTargetMachineFeatureString(self._raw))

        @untested
        def TargetData(self):
            raw_td = _machine.GetTargetMachineData(self._raw)
            # create a new TargetData with the same info to avoid ownership problems
            return TargetData(_message_to_string(_target.CopyStringRepOfTargetData(raw_td)))

        @untested
        def EmitToFile(self, mod, filename, codegen):
            assert isinstance(mod, Module)
            assert isinstance(codegen, CodeGenFileType)
            error = _c.string_buffer()
            rv = bool(_machine.TargetMachineEmitToFile(self._raw, mod._raw, u2b(filename), codegen, ctypes.byref(error)))
            error = _message_to_string(error)
            if rv:
                raise OSError(error)

        if (3, 3) <= _version:
            @untested
            def EmitToMemoryBuffer(self, mod, codegen):
                assert isinstance(mod, Module)
                assert isinstance(codegen, CodeGenFileType)
                error = _c.string_buffer()
                raw_mb = _core.MemoryBuffer()
                rv = bool(_machine.TargetMachineEmitToMemoryBuffer(self._raw, mod._raw, codegen, ctypes.byref(error), ctypes.byref(raw_mb)))
                error = _message_to_string(error)
                if rv:
                    raise OSError(error)
                mb = object.__new__(MemoryBuffer)
                mb._raw = raw_mb
                return mb
