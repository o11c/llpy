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

''' low-level wrapper of llvm-c/Transforms/IPO.h
'''

import ctypes

from ..core import _library
from ..core import PassManager

from ...utils import cuntested as untested


AddArgumentPromotionPass = _library.function(None, 'LLVMAddArgumentPromotionPass', [PassManager])
AddArgumentPromotionPass = untested(AddArgumentPromotionPass)
AddConstantMergePass = _library.function(None, 'LLVMAddConstantMergePass', [PassManager])
AddConstantMergePass = untested(AddConstantMergePass)
AddDeadArgEliminationPass = _library.function(None, 'LLVMAddDeadArgEliminationPass', [PassManager])
AddDeadArgEliminationPass = untested(AddDeadArgEliminationPass)
AddFunctionAttrsPass = _library.function(None, 'LLVMAddFunctionAttrsPass', [PassManager])
AddFunctionAttrsPass = untested(AddFunctionAttrsPass)
AddFunctionInliningPass = _library.function(None, 'LLVMAddFunctionInliningPass', [PassManager])
AddFunctionInliningPass = untested(AddFunctionInliningPass)
AddAlwaysInlinerPass = _library.function(None, 'LLVMAddAlwaysInlinerPass', [PassManager])
AddAlwaysInlinerPass = untested(AddAlwaysInlinerPass)
AddGlobalDCEPass = _library.function(None, 'LLVMAddGlobalDCEPass', [PassManager])
AddGlobalDCEPass = untested(AddGlobalDCEPass)
AddGlobalOptimizerPass = _library.function(None, 'LLVMAddGlobalOptimizerPass', [PassManager])
AddGlobalOptimizerPass = untested(AddGlobalOptimizerPass)
AddIPConstantPropagationPass = _library.function(None, 'LLVMAddIPConstantPropagationPass', [PassManager])
AddIPConstantPropagationPass = untested(AddIPConstantPropagationPass)
AddPruneEHPass = _library.function(None, 'LLVMAddPruneEHPass', [PassManager])
AddPruneEHPass = untested(AddPruneEHPass)
AddIPSCCPPass = _library.function(None, 'LLVMAddIPSCCPPass', [PassManager])
AddIPSCCPPass = untested(AddIPSCCPPass)
AddInternalizePass = _library.function(None, 'LLVMAddInternalizePass', [PassManager, ctypes.c_uint])
AddInternalizePass = untested(AddInternalizePass)
AddStripDeadPrototypesPass = _library.function(None, 'LLVMAddStripDeadPrototypesPass', [PassManager])
AddStripDeadPrototypesPass = untested(AddStripDeadPrototypesPass)
AddStripSymbolsPass = _library.function(None, 'LLVMAddStripSymbolsPass', [PassManager])
AddStripSymbolsPass = untested(AddStripSymbolsPass)
