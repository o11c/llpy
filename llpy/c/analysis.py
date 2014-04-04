#   -*- encoding: utf-8 -*-
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

''' low-level wrapper of llvm-c/Analysis.h
'''

import ctypes

from . import _c

from .core import _library
from .core import Bool
from .core import Module
from .core import Value


verifier_failure_actions = [
    'AbortProcess',
    'PrintMessage',
    'ReturnStatus',
]
VerifierFailureAction = _c.enum('VerifierFailureAction', **{v: k for k, v in enumerate(verifier_failure_actions)})
del verifier_failure_actions


VerifyModule = _library.function(Bool, 'LLVMVerifyModule', [Module, VerifierFailureAction, ctypes.POINTER(_c.string_buffer)])

VerifyFunction = _library.function(Bool, 'LLVMVerifyFunction', [Value, VerifierFailureAction])

ViewFunctionCFG = _library.function(None, 'LLVMViewFunctionCFG', [Value])
ViewFunctionCFGOnly = _library.function(None, 'LLVMViewFunctionCFGOnly', [Value])
