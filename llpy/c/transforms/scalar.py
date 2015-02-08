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

''' low-level wrapper of llvm-c/Transforms/Scalar.h
'''

import ctypes

from .. import _c

from ..core import _library, _version
from ..core import PassManager


AddAggressiveDCEPass = _library.function(None, 'LLVMAddAggressiveDCEPass', [PassManager])
AddCFGSimplificationPass = _library.function(None, 'LLVMAddCFGSimplificationPass', [PassManager])
AddDeadStoreEliminationPass = _library.function(None, 'LLVMAddDeadStoreEliminationPass', [PassManager])
if (3, 5) <= _version:
    AddScalarizerPass = _library.function(None, 'LLVMAddScalarizerPass', [PassManager])
    AddMergedLoadStoreMotionPass = _library.function(None, 'LLVMAddMergedLoadStoreMotionPass', [PassManager])
AddGVNPass = _library.function(None, 'LLVMAddGVNPass', [PassManager])
AddIndVarSimplifyPass = _library.function(None, 'LLVMAddIndVarSimplifyPass', [PassManager])
AddInstructionCombiningPass = _library.function(None, 'LLVMAddInstructionCombiningPass', [PassManager])
AddJumpThreadingPass = _library.function(None, 'LLVMAddJumpThreadingPass', [PassManager])
AddLICMPass = _library.function(None, 'LLVMAddLICMPass', [PassManager])
AddLoopDeletionPass = _library.function(None, 'LLVMAddLoopDeletionPass', [PassManager])
AddLoopRotatePass = _library.function(None, 'LLVMAddLoopRotatePass', [PassManager])
if (3, 4) <= _version:
    AddLoopRerollPass = _library.function(None, 'LLVMAddLoopRerollPass', [PassManager])
AddLoopUnrollPass = _library.function(None, 'LLVMAddLoopUnrollPass', [PassManager])
AddLoopUnswitchPass = _library.function(None, 'LLVMAddLoopUnswitchPass', [PassManager])
AddMemCpyOptPass = _library.function(None, 'LLVMAddMemCpyOptPass', [PassManager])
if (3, 4) <= _version:
    AddPartiallyInlineLibCallsPass = _library.function(None, 'LLVMAddPartiallyInlineLibCallsPass', [PassManager])
AddPromoteMemoryToRegisterPass = _library.function(None, 'LLVMAddPromoteMemoryToRegisterPass', [PassManager])
AddReassociatePass = _library.function(None, 'LLVMAddReassociatePass', [PassManager])
AddSCCPPass = _library.function(None, 'LLVMAddSCCPPass', [PassManager])
AddScalarReplAggregatesPass = _library.function(None, 'LLVMAddScalarReplAggregatesPass', [PassManager])
AddScalarReplAggregatesPassWithThreshold = _library.function(None, 'LLVMAddScalarReplAggregatesPassWithThreshold', [PassManager, ctypes.c_int])
AddSimplifyLibCallsPass = _library.function(None, 'LLVMAddSimplifyLibCallsPass', [PassManager])
AddTailCallEliminationPass = _library.function(None, 'LLVMAddTailCallEliminationPass', [PassManager])
AddConstantPropagationPass = _library.function(None, 'LLVMAddConstantPropagationPass', [PassManager])
AddDemoteMemoryToRegisterPass = _library.function(None, 'LLVMAddDemoteMemoryToRegisterPass', [PassManager])
AddVerifierPass = _library.function(None, 'LLVMAddVerifierPass', [PassManager])
