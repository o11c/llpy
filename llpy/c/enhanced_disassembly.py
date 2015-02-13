#   -*- encoding: utf-8 -*-
#   Copyright © 2013-2014 Ben Longbons
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

''' low-level wrapper of llvm-c/EnhancedDisassembly.h
'''

import ctypes

from . import _c
from .core import _version

from ..utils import cuntested as untested


# 2.9 ships a shared library
# 3.0 only seems to ship a static library (unusable)
# 3.1 and 3.2 ship the symbols as part of the main library
# 3.3 no longer ships the header
if (3, 1) <= _version <= (3, 2):
    # _library = _c.Library('libEnhancedDisassembly.so')
    from .core import _library


    ByteReaderCallback = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.POINTER(ctypes.c_uint8), ctypes.c_uint64, ctypes.c_void_p)
    RegisterReaderCallback = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.POINTER(ctypes.c_uint64), ctypes.c_uint, ctypes.c_void_p)

    assembly_syns = dict(
        X86Intel  = 0,
        X86ATT    = 1,
        ARMUAL    = 2,
    )
    AssemblySyntax = _c.enum('AssemblySyntax', **assembly_syns)
    del assembly_syns

    Disassembler = _c.opaque('Disassembler')
    Inst = _c.opaque('Inst')
    Token = _c.opaque('Token')
    Operand = _c.opaque('Operand')


    GetDisassembler = _library.function(ctypes.c_int, 'EDGetDisassembler', [ctypes.POINTER(Disassembler), ctypes.c_char_p, AssemblySyntax])
    GetDisassembler = untested(GetDisassembler)
    GetRegisterName = _library.function(ctypes.c_int, 'EDGetRegisterName', [ctypes.POINTER(ctypes.c_char_p), Disassembler, ctypes.c_uint])
    GetRegisterName = untested(GetRegisterName)

    RegisterIsStackPointer = _library.function(ctypes.c_int, 'EDRegisterIsStackPointer', [Disassembler, ctypes.c_uint])
    RegisterIsStackPointer = untested(RegisterIsStackPointer)
    RegisterIsProgramCounter = _library.function(ctypes.c_int, 'EDRegisterIsProgramCounter', [Disassembler, ctypes.c_uint])
    RegisterIsProgramCounter = untested(RegisterIsProgramCounter)
    CreateInsts = _library.function(ctypes.c_uint, 'EDCreateInsts', [ctypes.POINTER(Inst), ctypes.c_uint, Disassembler, ByteReaderCallback, ctypes.c_uint64, ctypes.c_void_p])
    CreateInsts = untested(CreateInsts)
    ReleaseInst = _library.function(None, 'EDReleaseInst', [Inst])
    ReleaseInst = untested(ReleaseInst)
    InstByteSize = _library.function(ctypes.c_int, 'EDInstByteSize', [Inst])
    InstByteSize = untested(InstByteSize)
    GetInstString = _library.function(ctypes.c_int, 'EDGetInstString', [ctypes.POINTER(ctypes.c_char_p), Inst])
    GetInstString = untested(GetInstString)
    InstID = _library.function(ctypes.c_int, 'EDInstID', [ctypes.POINTER(ctypes.c_uint), Inst])
    InstID = untested(InstID)
    InstIsBranch = _library.function(ctypes.c_int, 'EDInstIsBranch', [Inst])
    InstIsBranch = untested(InstIsBranch)
    InstIsMove = _library.function(ctypes.c_int, 'EDInstIsMove', [Inst])
    InstIsMove = untested(InstIsMove)
    BranchTargetID = _library.function(ctypes.c_int, 'EDBranchTargetID', [Inst])
    BranchTargetID = untested(BranchTargetID)
    MoveSourceID = _library.function(ctypes.c_int, 'EDMoveSourceID', [Inst])
    MoveSourceID = untested(MoveSourceID)
    MoveTargetID = _library.function(ctypes.c_int, 'EDMoveTargetID', [Inst])
    MoveTargetID = untested(MoveTargetID)

    NumTokens = _library.function(ctypes.c_int, 'EDNumTokens', [Inst])
    NumTokens = untested(NumTokens)
    GetToken = _library.function(ctypes.c_int, 'EDGetToken', [ctypes.POINTER(Token), Inst, ctypes.c_int])
    GetToken = untested(GetToken)
    GetTokenString = _library.function(ctypes.c_int, 'EDGetTokenString', [ctypes.POINTER(ctypes.c_char_p), Token])
    GetTokenString = untested(GetTokenString)
    OperandIndexForToken = _library.function(ctypes.c_int, 'EDOperandIndexForToken', [Token])
    OperandIndexForToken = untested(OperandIndexForToken)
    TokenIsWhitespace = _library.function(ctypes.c_int, 'EDTokenIsWhitespace', [Token])
    TokenIsWhitespace = untested(TokenIsWhitespace)
    TokenIsPunctuation = _library.function(ctypes.c_int, 'EDTokenIsPunctuation', [Token])
    TokenIsPunctuation = untested(TokenIsPunctuation)
    TokenIsOpcode = _library.function(ctypes.c_int, 'EDTokenIsOpcode', [Token])
    TokenIsOpcode = untested(TokenIsOpcode)
    TokenIsLiteral = _library.function(ctypes.c_int, 'EDTokenIsLiteral', [Token])
    TokenIsLiteral = untested(TokenIsLiteral)
    TokenIsRegister = _library.function(ctypes.c_int, 'EDTokenIsRegister', [Token])
    TokenIsRegister = untested(TokenIsRegister)
    TokenIsNegativeLiteral = _library.function(ctypes.c_int, 'EDTokenIsNegativeLiteral', [Token])
    TokenIsNegativeLiteral = untested(TokenIsNegativeLiteral)
    LiteralTokenAbsoluteValue = _library.function(ctypes.c_int, 'EDLiteralTokenAbsoluteValue', [ctypes.POINTER(ctypes.c_uint64), Token])
    LiteralTokenAbsoluteValue = untested(LiteralTokenAbsoluteValue)
    RegisterTokenValue = _library.function(ctypes.c_int, 'EDRegisterTokenValue', [ctypes.POINTER(ctypes.c_uint), Token])
    RegisterTokenValue = untested(RegisterTokenValue)
    NumOperands = _library.function(ctypes.c_int, 'EDNumOperands', [Inst])
    NumOperands = untested(NumOperands)
    GetOperand = _library.function(ctypes.c_int, 'EDGetOperand', [ctypes.POINTER(Operand), Inst, ctypes.c_int])
    OperandIsRegister = _library.function(ctypes.c_int, 'EDOperandIsRegister', [Operand])
    OperandIsRegister = untested(OperandIsRegister)
    OperandIsImmediate = _library.function(ctypes.c_int, 'EDOperandIsImmediate', [Operand])
    OperandIsImmediate = untested(OperandIsImmediate)
    OperandIsMemory = _library.function(ctypes.c_int, 'EDOperandIsMemory', [Operand])
    OperandIsMemory = untested(OperandIsMemory)
    RegisterOperandValue = _library.function(ctypes.c_int, 'EDRegisterOperandValue', [ctypes.POINTER(ctypes.c_uint), Operand])
    RegisterOperandValue = untested(RegisterOperandValue)
    ImmediateOperandValue = _library.function(ctypes.c_int, 'EDImmediateOperandValue', [ctypes.POINTER(ctypes.c_uint64), Operand])
    ImmediateOperandValue = untested(ImmediateOperandValue)
    EvaluateOperand = _library.function(ctypes.c_int, 'EDEvaluateOperand', [ctypes.POINTER(ctypes.c_uint64), Operand, RegisterReaderCallback, ctypes.c_void_p])
    EvaluateOperand = untested(EvaluateOperand)

    # snip some stuff with __BLOCKS__. Objective-C?
    # strings here so the C symbol table matches the py files
    'EDBlockCreateInsts'
    'EDBlockEvaluateOperand'
    'EDBlockVisitTokens'
