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

''' low-level wrapper of llvm-c/Object.h
'''

import ctypes

from . import _c

from .core import _library, _version
from .core import Bool
from .core import Value
from .core import MemoryBuffer

from ..utils import cuntested as untested


ObjectFile = _c.opaque('ObjectFile')
SectionIterator = _c.opaque('SectionIterator')
if (3, 1) <= _version:
    SymbolIterator = _c.opaque('SymbolIterator')
    RelocationIterator = _c.opaque('RelocationIterator')


CreateObjectFile = _library.function(ObjectFile, 'LLVMCreateObjectFile', [MemoryBuffer])
CreateObjectFile = untested(CreateObjectFile)
DisposeObjectFile = _library.function(None, 'LLVMDisposeObjectFile', [ObjectFile])
DisposeObjectFile = untested(DisposeObjectFile)

GetSections = _library.function(SectionIterator, 'LLVMGetSections', [ObjectFile])
GetSections = untested(GetSections)
DisposeSectionIterator = _library.function(None, 'LLVMDisposeSectionIterator', [SectionIterator])
DisposeSectionIterator = untested(DisposeSectionIterator)
IsSectionIteratorAtEnd = _library.function(Bool, 'LLVMIsSectionIteratorAtEnd', [ObjectFile, SectionIterator])
IsSectionIteratorAtEnd = untested(IsSectionIteratorAtEnd)
MoveToNextSection = _library.function(None, 'LLVMMoveToNextSection', [SectionIterator])
MoveToNextSection = untested(MoveToNextSection)
if (3, 1) <= _version:
    MoveToContainingSection = _library.function(None, 'LLVMMoveToContainingSection', [SectionIterator, SymbolIterator])
    MoveToContainingSection = untested(MoveToContainingSection)

    GetSymbols = _library.function(SymbolIterator, 'LLVMGetSymbols', [ObjectFile])
    GetSymbols = untested(GetSymbols)
    DisposeSymbolIterator = _library.function(None, 'LLVMDisposeSymbolIterator', [SymbolIterator])
    DisposeSymbolIterator = untested(DisposeSymbolIterator)
    IsSymbolIteratorAtEnd = _library.function(Bool, 'LLVMIsSymbolIteratorAtEnd', [ObjectFile, SymbolIterator])
    IsSymbolIteratorAtEnd = untested(IsSymbolIteratorAtEnd)
    MoveToNextSymbol = _library.function(None, 'LLVMMoveToNextSymbol', [SymbolIterator])
    MoveToNextSymbol = untested(MoveToNextSymbol)

GetSectionName = _library.function(ctypes.c_char_p, 'LLVMGetSectionName', [SectionIterator])
GetSectionName = untested(GetSectionName)
GetSectionSize = _library.function(ctypes.c_uint64, 'LLVMGetSectionSize', [SectionIterator])
GetSectionSize = untested(GetSectionSize)
GetSectionContents = _library.function(ctypes.c_char_p, 'LLVMGetSectionContents', [SectionIterator])
GetSectionContents = untested(GetSectionContents)

if (3, 1) <= _version:
    GetSectionAddress = _library.function(ctypes.c_uint64, 'LLVMGetSectionAddress', [SectionIterator])
    GetSectionAddress = untested(GetSectionAddress)
    GetSectionContainsSymbol = _library.function(Bool, 'LLVMGetSectionContainsSymbol', [SectionIterator, SymbolIterator])
    GetSectionContainsSymbol = untested(GetSectionContainsSymbol)

    GetRelocations = _library.function(RelocationIterator, 'LLVMGetRelocations', [SectionIterator])
    GetRelocations = untested(GetRelocations)
    DisposeRelocationIterator = _library.function(None, 'LLVMDisposeRelocationIterator', [RelocationIterator])
    DisposeRelocationIterator = untested(DisposeRelocationIterator)
    IsRelocationIteratorAtEnd = _library.function(Bool, 'LLVMIsRelocationIteratorAtEnd', [SectionIterator, RelocationIterator])
    IsRelocationIteratorAtEnd = untested(IsRelocationIteratorAtEnd)
    MoveToNextRelocation = _library.function(None, 'LLVMMoveToNextRelocation', [RelocationIterator])
    MoveToNextRelocation = untested(MoveToNextRelocation)

    GetSymbolName = _library.function(ctypes.c_char_p, 'LLVMGetSymbolName', [SymbolIterator])
    GetSymbolName = untested(GetSymbolName)
    GetSymbolAddress = _library.function(ctypes.c_uint64, 'LLVMGetSymbolAddress', [SymbolIterator])
    GetSymbolAddress = untested(GetSymbolAddress)
if (3, 1) <= _version <= (3, 4):
    GetSymbolFileOffset = _library.function(ctypes.c_uint64, 'LLVMGetSymbolFileOffset', [SymbolIterator])
    GetSymbolFileOffset = untested(GetSymbolFileOffset)
if (3, 1) <= _version:
    GetSymbolSize = _library.function(ctypes.c_uint64, 'LLVMGetSymbolSize', [SymbolIterator])
    GetSymbolSize = untested(GetSymbolSize)

    GetRelocationAddress = _library.function(ctypes.c_uint64, 'LLVMGetRelocationAddress', [RelocationIterator])
    GetRelocationAddress = untested(GetRelocationAddress)
    GetRelocationOffset = _library.function(ctypes.c_uint64, 'LLVMGetRelocationOffset', [RelocationIterator])
    GetRelocationOffset = untested(GetRelocationOffset)
    GetRelocationSymbol = _library.function(SymbolIterator, 'LLVMGetRelocationSymbol', [RelocationIterator])
    GetRelocationSymbol = untested(GetRelocationSymbol)
    GetRelocationType = _library.function(ctypes.c_uint64, 'LLVMGetRelocationType', [RelocationIterator])
    GetRelocationType = untested(GetRelocationType)
    GetRelocationTypeName = _library.function(ctypes.c_char_p, 'LLVMGetRelocationTypeName', [RelocationIterator])
    GetRelocationTypeName = untested(GetRelocationTypeName)
    GetRelocationValueString = _library.function(ctypes.c_char_p, 'LLVMGetRelocationValueString', [RelocationIterator])
    GetRelocationValueString = untested(GetRelocationValueString)
