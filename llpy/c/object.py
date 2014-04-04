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


ObjectFile = _c.opaque('ObjectFile')
SectionIterator = _c.opaque('SectionIterator')
if (3, 1) <= _version:
    SymbolIterator = _c.opaque('SymbolIterator')
    RelocationIterator = _c.opaque('RelocationIterator')


CreateObjectFile = _library.function(ObjectFile, 'LLVMCreateObjectFile', [MemoryBuffer])
DisposeObjectFile = _library.function(None, 'LLVMDisposeObjectFile', [ObjectFile])

GetSections = _library.function(SectionIterator, 'LLVMGetSections', [ObjectFile])
DisposeSectionIterator = _library.function(None, 'LLVMDisposeSectionIterator', [SectionIterator])
IsSectionIteratorAtEnd = _library.function(Bool, 'LLVMIsSectionIteratorAtEnd', [ObjectFile, SectionIterator])
MoveToNextSection = _library.function(None, 'LLVMMoveToNextSection', [SectionIterator])
if (3, 1) <= _version:
    MoveToContainingSection = _library.function(None, 'LLVMMoveToContainingSection', [SectionIterator, SymbolIterator])

    GetSymbols = _library.function(SymbolIterator, 'LLVMGetSymbols', [ObjectFile])
    DisposeSymbolIterator = _library.function(None, 'LLVMDisposeSymbolIterator', [SymbolIterator])
    IsSymbolIteratorAtEnd = _library.function(Bool, 'LLVMIsSymbolIteratorAtEnd', [ObjectFile, SymbolIterator])
    MoveToNextSymbol = _library.function(None, 'LLVMMoveToNextSymbol', [SymbolIterator])

GetSectionName = _library.function(ctypes.c_char_p, 'LLVMGetSectionName', [SectionIterator])
GetSectionSize = _library.function(ctypes.c_uint64, 'LLVMGetSectionSize', [SectionIterator])
GetSectionContents = _library.function(ctypes.c_char_p, 'LLVMGetSectionContents', [SectionIterator])

if (3, 1) <= _version:
    GetSectionAddress = _library.function(ctypes.c_uint64, 'LLVMGetSectionAddress', [SectionIterator])
    GetSectionContainsSymbol = _library.function(Bool, 'LLVMGetSectionContainsSymbol', [SectionIterator, SymbolIterator])

    GetRelocations = _library.function(RelocationIterator, 'LLVMGetRelocations', [SectionIterator])
    DisposeRelocationIterator = _library.function(None, 'LLVMDisposeRelocationIterator', [RelocationIterator])
    IsRelocationIteratorAtEnd = _library.function(Bool, 'LLVMIsRelocationIteratorAtEnd', [SectionIterator, RelocationIterator])
    MoveToNextRelocation = _library.function(None, 'LLVMMoveToNextRelocation', [RelocationIterator])

    GetSymbolName = _library.function(ctypes.c_char_p, 'LLVMGetSymbolName', [SymbolIterator])
    GetSymbolAddress = _library.function(ctypes.c_uint64, 'LLVMGetSymbolAddress', [SymbolIterator])
    GetSymbolFileOffset = _library.function(ctypes.c_uint64, 'LLVMGetSymbolFileOffset', [SymbolIterator])
    GetSymbolSize = _library.function(ctypes.c_uint64, 'LLVMGetSymbolSize', [SymbolIterator])

    GetRelocationAddress = _library.function(ctypes.c_uint64, 'LLVMGetRelocationAddress', [RelocationIterator])
    GetRelocationOffset = _library.function(ctypes.c_uint64, 'LLVMGetRelocationOffset', [RelocationIterator])
    GetRelocationSymbol = _library.function(SymbolIterator, 'LLVMGetRelocationSymbol', [RelocationIterator])
    GetRelocationType = _library.function(ctypes.c_uint64, 'LLVMGetRelocationType', [RelocationIterator])
    GetRelocationTypeName = _library.function(ctypes.c_char_p, 'LLVMGetRelocationTypeName', [RelocationIterator])
    GetRelocationValueString = _library.function(ctypes.c_char_p, 'LLVMGetRelocationValueString', [RelocationIterator])
