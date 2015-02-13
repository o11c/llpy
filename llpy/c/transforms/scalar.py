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

from ...utils import cuntested as untested


AddAggressiveDCEPass = _library.function(None, 'LLVMAddAggressiveDCEPass', [PassManager])
AddAggressiveDCEPass = untested(AddAggressiveDCEPass)
AddCFGSimplificationPass = _library.function(None, 'LLVMAddCFGSimplificationPass', [PassManager])
AddCFGSimplificationPass = untested(AddCFGSimplificationPass)
AddDeadStoreEliminationPass = _library.function(None, 'LLVMAddDeadStoreEliminationPass', [PassManager])
AddDeadStoreEliminationPass = untested(AddDeadStoreEliminationPass)
if (3, 5) <= _version:
    AddScalarizerPass = _library.function(None, 'LLVMAddScalarizerPass', [PassManager])
    AddScalarizerPass = untested(AddScalarizerPass)
    AddMergedLoadStoreMotionPass = _library.function(None, 'LLVMAddMergedLoadStoreMotionPass', [PassManager])
    AddMergedLoadStoreMotionPass = untested(AddMergedLoadStoreMotionPass)
AddGVNPass = _library.function(None, 'LLVMAddGVNPass', [PassManager])
AddGVNPass = untested(AddGVNPass)
AddIndVarSimplifyPass = _library.function(None, 'LLVMAddIndVarSimplifyPass', [PassManager])
AddIndVarSimplifyPass = untested(AddIndVarSimplifyPass)
AddInstructionCombiningPass = _library.function(None, 'LLVMAddInstructionCombiningPass', [PassManager])
AddInstructionCombiningPass = untested(AddInstructionCombiningPass)
AddJumpThreadingPass = _library.function(None, 'LLVMAddJumpThreadingPass', [PassManager])
AddJumpThreadingPass = untested(AddJumpThreadingPass)
AddLICMPass = _library.function(None, 'LLVMAddLICMPass', [PassManager])
AddLICMPass = untested(AddLICMPass)
AddLoopDeletionPass = _library.function(None, 'LLVMAddLoopDeletionPass', [PassManager])
AddLoopDeletionPass = untested(AddLoopDeletionPass)
if (3, 1) <= _version:
    AddLoopIdiomPass = _library.function(None, 'LLVMAddLoopIdiomPass', [PassManager])
    AddLoopIdiomPass = untested(AddLoopIdiomPass)
AddLoopRotatePass = _library.function(None, 'LLVMAddLoopRotatePass', [PassManager])
AddLoopRotatePass = untested(AddLoopRotatePass)
if (3, 4) <= _version:
    AddLoopRerollPass = _library.function(None, 'LLVMAddLoopRerollPass', [PassManager])
    AddLoopRerollPass = untested(AddLoopRerollPass)
AddLoopUnrollPass = _library.function(None, 'LLVMAddLoopUnrollPass', [PassManager])
AddLoopUnrollPass = untested(AddLoopUnrollPass)
AddLoopUnswitchPass = _library.function(None, 'LLVMAddLoopUnswitchPass', [PassManager])
AddLoopUnswitchPass = untested(AddLoopUnswitchPass)
AddMemCpyOptPass = _library.function(None, 'LLVMAddMemCpyOptPass', [PassManager])
AddMemCpyOptPass = untested(AddMemCpyOptPass)
if (3, 4) <= _version:
    AddPartiallyInlineLibCallsPass = _library.function(None, 'LLVMAddPartiallyInlineLibCallsPass', [PassManager])
    AddPartiallyInlineLibCallsPass = untested(AddPartiallyInlineLibCallsPass)
AddPromoteMemoryToRegisterPass = _library.function(None, 'LLVMAddPromoteMemoryToRegisterPass', [PassManager])
AddPromoteMemoryToRegisterPass = untested(AddPromoteMemoryToRegisterPass)
AddReassociatePass = _library.function(None, 'LLVMAddReassociatePass', [PassManager])
AddReassociatePass = untested(AddReassociatePass)
AddSCCPPass = _library.function(None, 'LLVMAddSCCPPass', [PassManager])
AddSCCPPass = untested(AddSCCPPass)
AddScalarReplAggregatesPass = _library.function(None, 'LLVMAddScalarReplAggregatesPass', [PassManager])
AddScalarReplAggregatesPass = untested(AddScalarReplAggregatesPass)
if (3, 1) <= _version:
    AddScalarReplAggregatesPassSSA = _library.function(None, 'LLVMAddScalarReplAggregatesPassSSA', [PassManager])
    AddScalarReplAggregatesPassSSA = untested(AddScalarReplAggregatesPassSSA)
AddScalarReplAggregatesPassWithThreshold = _library.function(None, 'LLVMAddScalarReplAggregatesPassWithThreshold', [PassManager, ctypes.c_int])
AddScalarReplAggregatesPassWithThreshold = untested(AddScalarReplAggregatesPassWithThreshold)
AddSimplifyLibCallsPass = _library.function(None, 'LLVMAddSimplifyLibCallsPass', [PassManager])
AddSimplifyLibCallsPass = untested(AddSimplifyLibCallsPass)
AddTailCallEliminationPass = _library.function(None, 'LLVMAddTailCallEliminationPass', [PassManager])
AddTailCallEliminationPass = untested(AddTailCallEliminationPass)
AddConstantPropagationPass = _library.function(None, 'LLVMAddConstantPropagationPass', [PassManager])
AddConstantPropagationPass = untested(AddConstantPropagationPass)
AddDemoteMemoryToRegisterPass = _library.function(None, 'LLVMAddDemoteMemoryToRegisterPass', [PassManager])
AddDemoteMemoryToRegisterPass = untested(AddDemoteMemoryToRegisterPass)
AddVerifierPass = _library.function(None, 'LLVMAddVerifierPass', [PassManager])
AddVerifierPass = untested(AddVerifierPass)
if (3, 1) <= _version:
    AddCorrelatedValuePropagationPass = _library.function(None, 'LLVMAddCorrelatedValuePropagationPass', [PassManager])
    AddCorrelatedValuePropagationPass = untested(AddCorrelatedValuePropagationPass)
    AddEarlyCSEPass = _library.function(None, 'LLVMAddEarlyCSEPass', [PassManager])
    AddEarlyCSEPass = untested(AddEarlyCSEPass)
    AddLowerExpectIntrinsicPass = _library.function(None, 'LLVMAddLowerExpectIntrinsicPass', [PassManager])
    AddLowerExpectIntrinsicPass = untested(AddLowerExpectIntrinsicPass)
    AddTypeBasedAliasAnalysisPass = _library.function(None, 'LLVMAddTypeBasedAliasAnalysisPass', [PassManager])
    AddTypeBasedAliasAnalysisPass = untested(AddTypeBasedAliasAnalysisPass)
    AddBasicAliasAnalysisPass = _library.function(None, 'LLVMAddBasicAliasAnalysisPass', [PassManager])
    AddBasicAliasAnalysisPass = untested(AddBasicAliasAnalysisPass)
