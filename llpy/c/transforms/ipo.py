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

''' low-level wrapper of llvm-c/Transforms/IPO.h
'''

import ctypes

from ..core import _library
from ..core import PassManager


AddArgumentPromotionPass = _library.function(None, 'LLVMAddArgumentPromotionPass', [PassManager])
AddConstantMergePass = _library.function(None, 'LLVMAddConstantMergePass', [PassManager])
AddDeadArgEliminationPass = _library.function(None, 'LLVMAddDeadArgEliminationPass', [PassManager])
AddFunctionAttrsPass = _library.function(None, 'LLVMAddFunctionAttrsPass', [PassManager])
AddFunctionInliningPass = _library.function(None, 'LLVMAddFunctionInliningPass', [PassManager])
AddAlwaysInlinerPass = _library.function(None, 'LLVMAddAlwaysInlinerPass', [PassManager])
AddGlobalDCEPass = _library.function(None, 'LLVMAddGlobalDCEPass', [PassManager])
AddGlobalOptimizerPass = _library.function(None, 'LLVMAddGlobalOptimizerPass', [PassManager])
AddIPConstantPropagationPass = _library.function(None, 'LLVMAddIPConstantPropagationPass', [PassManager])
AddPruneEHPass = _library.function(None, 'LLVMAddPruneEHPass', [PassManager])
AddIPSCCPPass = _library.function(None, 'LLVMAddIPSCCPPass', [PassManager])
AddInternalizePass = _library.function(None, 'LLVMAddInternalizePass', [PassManager, ctypes.c_uint])
AddStripDeadPrototypesPass = _library.function(None, 'LLVMAddStripDeadPrototypesPass', [PassManager])
AddStripSymbolsPass = _library.function(None, 'LLVMAddStripSymbolsPass', [PassManager])
