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

''' low-level wrapper of llvm-c/EnhancedDisassembly.h
'''

import ctypes

from . import _c
from .core import _version

if _version <= (3, 2):
    # that's when the header disappeared, at least
    # I can only find the library for 2.9
    _library = _c.Library('libEnhancedDisassembly.so')


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
    GetRegisterName = _library.function(ctypes.c_int, 'EDGetRegisterName', [ctypes.POINTER(ctypes.c_char_p), Disassembler, ctypes.c_uint])

    RegisterIsStackPointer = _library.function(ctypes.c_int, 'EDRegisterIsStackPointer', [Disassembler, ctypes.c_uint])
    RegisterIsProgramCounter = _library.function(ctypes.c_int, 'EDRegisterIsProgramCounter', [Disassembler, ctypes.c_uint])
    CreateInsts = _library.function(ctypes.c_uint, 'EDCreateInsts', [ctypes.POINTER(Inst), ctypes.c_uint, Disassembler, ByteReaderCallback, ctypes.c_uint64, ctypes.c_void_p])
    ReleaseInst = _library.function(None, 'EDReleaseInst', [Inst])
    InstByteSize = _library.function(ctypes.c_int, 'EDInstByteSize', [Inst])
    GetInstString = _library.function(ctypes.c_int, 'EDGetInstString', [ctypes.POINTER(ctypes.c_char_p), Inst])
    InstID = _library.function(ctypes.c_int, 'EDInstID', [ctypes.POINTER(ctypes.c_uint), Inst])
    InstIsBranch = _library.function(ctypes.c_int, 'EDInstIsBranch', [Inst])
    InstIsMove = _library.function(ctypes.c_int, 'EDInstIsMove', [Inst])
    BranchTargetID = _library.function(ctypes.c_int, 'EDBranchTargetID', [Inst])
    MoveSourceID = _library.function(ctypes.c_int, 'EDMoveSourceID', [Inst])
    MoveTargetID = _library.function(ctypes.c_int, 'EDMoveTargetID', [Inst])

    NumTokens = _library.function(ctypes.c_int, 'EDNumTokens', [Inst])
    GetToken = _library.function(ctypes.c_int, 'EDGetToken', [ctypes.POINTER(Token), Inst, ctypes.c_int])
    GetTokenString = _library.function(ctypes.c_int, 'EDGetTokenString', [ctypes.POINTER(ctypes.c_char_p), Token])
    OperandIndexForToken = _library.function(ctypes.c_int, 'EDOperandIndexForToken', [Token])
    TokenIsWhitespace = _library.function(ctypes.c_int, 'EDTokenIsWhitespace', [Token])
    TokenIsPunctuation = _library.function(ctypes.c_int, 'EDTokenIsPunctuation', [Token])
    TokenIsOpcode = _library.function(ctypes.c_int, 'EDTokenIsOpcode', [Token])
    TokenIsLiteral = _library.function(ctypes.c_int, 'EDTokenIsLiteral', [Token])
    TokenIsRegister = _library.function(ctypes.c_int, 'EDTokenIsRegister', [Token])
    TokenIsNegativeLiteral = _library.function(ctypes.c_int, 'EDTokenIsNegativeLiteral', [Token])
    LiteralTokenAbsoluteValue = _library.function(ctypes.c_int, 'EDLiteralTokenAbsoluteValue', [ctypes.POINTER(ctypes.c_uint64), Token])
    RegisterTokenValue = _library.function(ctypes.c_int, 'EDRegisterTokenValue', [ctypes.POINTER(ctypes.c_uint), Token])
    NumOperands = _library.function(ctypes.c_int, 'EDNumOperands', [Inst])
    GetOperand = _library.function(ctypes.c_int, 'EDGetOperand', [ctypes.POINTER(Operand), Inst, ctypes.c_int])
    OperandIsRegister = _library.function(ctypes.c_int, 'EDOperandIsRegister', [Operand])
    OperandIsImmediate = _library.function(ctypes.c_int, 'EDOperandIsImmediate', [Operand])
    OperandIsMemory = _library.function(ctypes.c_int, 'EDOperandIsMemory', [Operand])
    RegisterOperandValue = _library.function(ctypes.c_int, 'EDRegisterOperandValue', [ctypes.POINTER(ctypes.c_uint), Operand])
    ImmediateOperandValue = _library.function(ctypes.c_int, 'EDImmediateOperandValue', [ctypes.POINTER(ctypes.c_uint64), Operand])
    EvaluateOperand = _library.function(ctypes.c_int, 'EDEvaluateOperand', [ctypes.POINTER(ctypes.c_uint64), Operand, RegisterReaderCallback, ctypes.c_void_p])

    # snip some stuff with __BLOCKS__. Objective-C?
