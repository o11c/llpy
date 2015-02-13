#!/usr/bin/env python3
from __future__ import unicode_literals

from functools import reduce
import gc
import operator
import unittest

import llpy.core
from llpy.c.core import _version

from .test_core_misc import DumpTestCase


class TestArgument(DumpTestCase):

    def setUp(self):
        self.ctx = llpy.core.Context()
        self.mod = llpy.core.Module(self.ctx, 'TestArgument')
        void = llpy.core.VoidType(self.ctx)
        i32 = llpy.core.IntegerType(self.ctx, 32)
        func_type = llpy.core.FunctionType(void, [i32, i32])
        self.func = self.mod.AddFunction(func_type, 'func')
        arg = self.func.GetParam(0)
        arg.SetValueName('arg')
        brg = self.func.GetParam(1)
        brg.SetValueName('brg')

        bb = self.func.AppendBasicBlock()
        builder = llpy.core.IRBuilder(self.ctx)
        builder.PositionBuilderAtEnd(bb)
        builder.BuildRetVoid()

    def tearDown(self):
        del self.func
        del self.mod
        del self.ctx
        gc.collect()

    def test_order(self):
        arg = self.func.GetParam(0)
        brg = self.func.GetParam(1)
        assert arg.GetParamParent() is self.func
        assert brg.GetParamParent() is self.func
        assert arg is self.func.GetFirstParam()
        assert brg is self.func.GetLastParam()
        assert arg.GetNextParam() is brg
        assert brg.GetNextParam() is None
        assert arg.GetPreviousParam() is None
        assert brg.GetPreviousParam() is arg
        assert self.func.GetParams() == [arg, brg]

    Attribute = llpy.core.Attribute
    attrs = [
            ('zeroext', Attribute.ZExt),
            ('signext', Attribute.SExt),
            ('inreg', Attribute.InReg),
            ('noalias', Attribute.NoAlias),
            ('nocapture', Attribute.NoCapture),
            ('sret', Attribute.StructRet),
            ('byval', Attribute.ByVal),
            ('nest', Attribute.Nest),
    ]
    del Attribute
    if (3, 3) <= _version:
        attrs.sort()

    def test_attr(self):
        arg = self.func.GetParam(0)
        for ir, at in self.attrs:
            arg.AddAttribute(at)
            assert arg.GetAttribute() == at
            self.assertDump(self.func,
'''
define void @func(i32 %s %%arg, i32 %%brg) {
  ret void
}

''' % ir)
            arg.RemoveAttribute(at)

    def test_allattr(self):
        Attribute = llpy.core.Attribute
        attrs = reduce(operator.or_, (at for ir, at in self.attrs))
        attrs |= Attribute.Alignment
        ir = ' '.join(ir for ir, at in self.attrs)
        arg = self.func.GetParam(0)
        arg.AddAttribute(attrs)
        self.assertDump(self.func,
'''
define void @func(i32 %s align 1073741824 %%arg, i32 %%brg) {
  ret void
}

''' % ir)

    def test_align(self):
        arg = self.func.GetParam(0)
        assert llpy.core.Attribute.Alignment.value == 0x1F0000
        for e in range(0, 31):
            i = 2 ** e
            x = (e + 1) << 16
            a = llpy.core.Attribute(x)
            assert repr(a) == 'Attribute(0x%X)' % x
            arg.SetParamAlignment(i)
            assert arg.GetAttribute() == a
            self.assertDump(self.func,
'''
define void @func(i32 align %d %%arg, i32 %%brg) {
  ret void
}

''' % i)
            arg.RemoveAttribute(a)
        arg.SetParamAlignment(1)
        arg.AddAttribute(llpy.core.Attribute.ZExt)
        self.assertDump(self.func,
'''
define void @func(i32 zeroext align 1 %arg, i32 %brg) {
  ret void
}

''')

class TestBasicBlock(DumpTestCase):

    def setUp(self):
        self.ctx = llpy.core.Context()
        self.mod = llpy.core.Module(self.ctx, 'TestBasicBlock')
        void = llpy.core.VoidType(self.ctx)
        func_type = llpy.core.FunctionType(void, [])
        self.func = self.mod.AddFunction(func_type, 'func')

    def tearDown(self):
        del self.mod
        del self.ctx
        gc.collect()

    def check_order(self, blocks):
        assert self.func.GetBasicBlocks() == blocks
        if not blocks:
            return
        assert self.func.GetEntryBasicBlock() is blocks[0]
        assert self.func.GetFirstBasicBlock() is blocks[0]
        assert self.func.GetLastBasicBlock() is blocks[-1]
        prev = None
        for b in blocks:
            assert b.GetBasicBlockParent() is self.func
            assert b.GetPreviousBasicBlock() is prev
            if prev is not None:
                assert prev.GetNextBasicBlock() is b
            prev = b
        assert prev.GetNextBasicBlock() is None

    def test_block(self):
        bb1 = self.func.AppendBasicBlock()
        self.check_order([bb1])
        bb2 = self.func.AppendBasicBlock()
        self.check_order([bb1, bb2])
        bb0 = bb1.InsertBasicBlock()
        self.check_order([bb0, bb1, bb2])
        bb1.MoveBasicBlockBefore(bb0)
        self.check_order([bb1, bb0, bb2])
        bb2.MoveBasicBlockAfter(bb1)
        self.check_order([bb1, bb2, bb0])

    def test_instruction(self):
        bb = self.func.AppendBasicBlock()
        assert bb.GetBasicBlockTerminator() is None
        assert bb.GetFirstInstruction() is None
        assert bb.GetLastInstruction() is None

        builder = llpy.core.IRBuilder(self.ctx)
        builder.PositionBuilderAtEnd(bb)

        call = builder.BuildCall(self.func, [])
        assert bb.GetBasicBlockTerminator() is None
        assert bb.GetFirstInstruction() is call
        assert bb.GetLastInstruction() is call

        ret = builder.BuildRetVoid()
        assert bb.GetBasicBlockTerminator() is ret
        assert bb.GetFirstInstruction() is call
        assert bb.GetLastInstruction() is ret

        assert call.GetInstructionParent() is bb
        assert ret.GetInstructionParent() is bb
        assert call.GetNextInstruction() is ret
        assert ret.GetNextInstruction() is None
        assert call.GetPreviousInstruction() is None
        assert ret.GetPreviousInstruction() is call


class TestInlineAsm(DumpTestCase):
    __slots__ = ()

    def setUp(self):
        ctx = llpy.core.Context()
        void = llpy.core.VoidType(ctx)
        self.fty = llpy.core.FunctionType(void, [])

    def tearDown(self):
        del self.fty
        gc.collect()

    def test_ff(self):
        asm = llpy.core.InlineAsm(self.fty, "asm_string", "constraints", False, False)
        self.assertDump(asm,
'''void ()* asm "asm_string", "constraints"
''')

    def test_ft(self):
        asm = llpy.core.InlineAsm(self.fty, "asm_string", "constraints", False, True)
        self.assertDump(asm,
'''void ()* asm alignstack "asm_string", "constraints"
''')

    def test_tf(self):
        asm = llpy.core.InlineAsm(self.fty, "asm_string", "constraints", True, False)
        self.assertDump(asm,
'''void ()* asm sideeffect "asm_string", "constraints"
''')

    def test_tt(self):
        asm = llpy.core.InlineAsm(self.fty, "asm_string", "constraints", True, True)
        self.assertDump(asm,
'''void ()* asm sideeffect alignstack "asm_string", "constraints"
''')

class TestConstant(DumpTestCase):
    __slots__ = ()
    xi1_dump = 'i64 ptrtoint (i1* getelementptr (i1* null, i32 1) to i64)'
    xi8_dump = 'i64 ptrtoint (i64* getelementptr (i64* null, i32 1) to i64)'
    xf1_dump = 'float uitofp (%s to float)' % (xi1_dump)
    xf8_dump = 'float uitofp (%s to float)' % (xi8_dump)

    xp1_dump = 'i64* inttoptr (i64 1 to i64*)'
    xp8_dump = 'i64* inttoptr (i64 8 to i64*)'

    def setUp(self):
        self.ctx = llpy.core.Context()

        self.i1 = llpy.core.IntegerType(self.ctx, 1)
        self.i64 = llpy.core.IntegerType(self.ctx, 64)
        i64p = llpy.core.PointerType(self.i64)
        self.float = llpy.core.FloatType(self.ctx)

        self.false = self.i1.ConstInt(0)
        self.true = self.i1.ConstInt(1)
        self.int1 = self.i64.ConstInt(1)
        self.int2 = self.i64.ConstInt(2)
        self.float1 = self.float.ConstReal(1.0)
        self.float2 = self.float.ConstReal(2.0)

        self.xi1 = self.i1.SizeOf()
        self.xi8 = self.i64.SizeOf()
        # note how we're just sort of assuming this works
        # it's not like any of the testcases run in order anyway
        self.xf1 = self.xi1.ConstUIToFP(self.float)
        self.xf8 = self.xi8.ConstUIToFP(self.float)
        # doing it based on xi1/xi8 makes stuff break
        self.xp1 = self.i64.ConstInt(1).ConstIntToPtr(i64p)
        self.xp8 = self.i64.ConstInt(8).ConstIntToPtr(i64p)

    def tearDown(self):
        del self.ctx

        del self.i1
        del self.i64
        del self.float

        del self.false
        del self.true
        del self.int1
        del self.int2
        del self.float1
        del self.float2

        del self.xi1
        del self.xi8
        del self.xf1
        del self.xf8
        del self.xp1
        del self.xp8

        gc.collect()

    def test_ConstNeg(self):
        cnv = self.int1.ConstNeg()
        assert cnv is self.i64.ConstInt(-1)
        cne = self.xi8.ConstNeg()
        assert isinstance(cne, llpy.core.BinarySubConstantExpr)
        assert cne.GetNumOperands() == 2
        assert cne.GetOperand(0) is self.i64.ConstNull()
        assert cne.GetOperand(1) is self.xi8
        self.assertDump(cne, 'i64 sub (i64 0, %s)\n' % (self.xi8_dump))

    def test_ConstNSWNeg(self):
        cnv = self.int1.ConstNSWNeg()
        assert cnv is self.i64.ConstInt(-1)
        cne = self.xi8.ConstNSWNeg()
        assert isinstance(cne, llpy.core.BinarySubConstantExpr)
        assert cne.GetNumOperands() == 2
        assert cne.GetOperand(0) is self.i64.ConstNull()
        assert cne.GetOperand(1) is self.xi8
        self.assertDump(cne, 'i64 sub nsw (i64 0, %s)\n' % (self.xi8_dump))

    def test_ConstNUWNeg(self):
        cnv = self.int1.ConstNUWNeg()
        assert cnv is self.i64.ConstInt(-1)
        cne = self.xi8.ConstNUWNeg()
        assert isinstance(cne, llpy.core.BinarySubConstantExpr)
        assert cne.GetNumOperands() == 2
        assert cne.GetOperand(0) is self.i64.ConstNull()
        assert cne.GetOperand(1) is self.xi8
        self.assertDump(cne, 'i64 sub nuw (i64 0, %s)\n' % (self.xi8_dump))

    def test_ConstFNeg(self):
        cnv = self.float1.ConstFNeg()
        assert cnv is self.float.ConstReal(-1.0)
        cne = self.xf8.ConstFNeg()
        assert isinstance(cne, llpy.core.BinaryFSubConstantExpr)
        assert cne.GetNumOperands() == 2
        assert cne.GetOperand(0) is self.float.ConstReal(-0.0)
        assert cne.GetOperand(1) is self.xf8
        self.assertDump(cne, 'float fsub (float -0.000000e+00, %s)\n' % (self.xf8_dump))

    def test_ConstNot(self):
        cnv = self.int1.ConstNot()
        assert cnv is self.i64.ConstInt(~1)
        cne = self.xi8.ConstNot()
        assert isinstance(cne, llpy.core.BinaryXorConstantExpr)
        assert cne.GetNumOperands() == 2
        assert cne.GetOperand(0) is self.xi8
        assert cne.GetOperand(1) is self.i64.ConstAllOnes()
        self.assertDump(cne, 'i64 xor (%s, i64 -1)\n' % (self.xi8_dump))

    def test_ConstAdd(self):
        cnv = self.int1.ConstAdd(self.int2)
        assert cnv is self.i64.ConstInt(3)
        cne = self.xi8.ConstAdd(self.xi1)
        assert isinstance(cne, llpy.core.BinaryAddConstantExpr)
        assert cne.GetNumOperands() == 2
        assert cne.GetOperand(0) is self.xi8
        assert cne.GetOperand(1) is self.xi1
        self.assertDump(cne, 'i64 add (%s, %s)\n' % (self.xi8_dump, self.xi1_dump))

    def test_ConstNSWAdd(self):
        cnv = self.int1.ConstNSWAdd(self.int2)
        assert cnv is self.i64.ConstInt(3)
        cne = self.xi8.ConstNSWAdd(self.xi1)
        assert isinstance(cne, llpy.core.BinaryAddConstantExpr)
        assert cne.GetNumOperands() == 2
        assert cne.GetOperand(0) is self.xi8
        assert cne.GetOperand(1) is self.xi1
        self.assertDump(cne, 'i64 add nsw (%s, %s)\n' % (self.xi8_dump, self.xi1_dump))

    def test_ConstNUWAdd(self):
        cnv = self.int1.ConstNUWAdd(self.int2)
        assert cnv is self.i64.ConstInt(3)
        cne = self.xi8.ConstNUWAdd(self.xi1)
        assert isinstance(cne, llpy.core.BinaryAddConstantExpr)
        assert cne.GetNumOperands() == 2
        assert cne.GetOperand(0) is self.xi8
        assert cne.GetOperand(1) is self.xi1
        self.assertDump(cne, 'i64 add nuw (%s, %s)\n' % (self.xi8_dump, self.xi1_dump))

    def test_ConstFAdd(self):
        cnv = self.float1.ConstFAdd(self.float2)
        assert cnv is self.float.ConstReal(3.0)
        cne = self.xf8.ConstFAdd(self.xf1)
        assert isinstance(cne, llpy.core.BinaryFAddConstantExpr)
        assert cne.GetNumOperands() == 2
        assert cne.GetOperand(0) is self.xf8
        assert cne.GetOperand(1) is self.xf1
        self.assertDump(cne, 'float fadd (%s, %s)\n' % (self.xf8_dump, self.xf1_dump))

    def test_ConstSub(self):
        cnv = self.int1.ConstSub(self.int2)
        assert cnv is self.i64.ConstInt(-1)
        cne = self.xi8.ConstSub(self.xi1)
        assert isinstance(cne, llpy.core.BinarySubConstantExpr)
        assert cne.GetNumOperands() == 2
        assert cne.GetOperand(0) is self.xi8
        assert cne.GetOperand(1) is self.xi1
        self.assertDump(cne, 'i64 sub (%s, %s)\n' % (self.xi8_dump, self.xi1_dump))

    def test_ConstNSWSub(self):
        cnv = self.int1.ConstNSWSub(self.int2)
        assert cnv is self.i64.ConstInt(-1)
        cne = self.xi8.ConstNSWSub(self.xi1)
        assert isinstance(cne, llpy.core.BinarySubConstantExpr)
        assert cne.GetNumOperands() == 2
        assert cne.GetOperand(0) is self.xi8
        assert cne.GetOperand(1) is self.xi1
        self.assertDump(cne, 'i64 sub nsw (%s, %s)\n' % (self.xi8_dump, self.xi1_dump))

    def test_ConstNUWSub(self):
        cnv = self.int1.ConstNUWSub(self.int2)
        assert cnv is self.i64.ConstInt(-1)
        cne = self.xi8.ConstNUWSub(self.xi1)
        assert isinstance(cne, llpy.core.BinarySubConstantExpr)
        assert cne.GetNumOperands() == 2
        assert cne.GetOperand(0) is self.xi8
        assert cne.GetOperand(1) is self.xi1
        self.assertDump(cne, 'i64 sub nuw (%s, %s)\n' % (self.xi8_dump, self.xi1_dump))

    def test_ConstFSub(self):
        cnv = self.float1.ConstFSub(self.float2)
        assert cnv is self.float.ConstReal(-1.0)
        cne = self.xf8.ConstFSub(self.xf1)
        assert isinstance(cne, llpy.core.BinaryFSubConstantExpr)
        assert cne.GetNumOperands() == 2
        assert cne.GetOperand(0) is self.xf8
        assert cne.GetOperand(1) is self.xf1
        self.assertDump(cne, 'float fsub (%s, %s)\n' % (self.xf8_dump, self.xf1_dump))

    def test_ConstMul(self):
        cnv = self.int1.ConstMul(self.int2)
        assert cnv is self.i64.ConstInt(2)
        cne = self.xi8.ConstMul(self.xi1)
        assert isinstance(cne, llpy.core.BinaryMulConstantExpr)
        assert cne.GetNumOperands() == 2
        assert cne.GetOperand(0) is self.xi8
        assert cne.GetOperand(1) is self.xi1
        self.assertDump(cne, 'i64 mul (%s, %s)\n' % (self.xi8_dump, self.xi1_dump))

    def test_ConstNSWMul(self):
        cnv = self.int1.ConstNSWMul(self.int2)
        assert cnv is self.i64.ConstInt(2)
        cne = self.xi8.ConstNSWMul(self.xi1)
        assert isinstance(cne, llpy.core.BinaryMulConstantExpr)
        assert cne.GetNumOperands() == 2
        assert cne.GetOperand(0) is self.xi8
        assert cne.GetOperand(1) is self.xi1
        self.assertDump(cne, 'i64 mul nsw (%s, %s)\n' % (self.xi8_dump, self.xi1_dump))

    def test_ConstNUWMul(self):
        cnv = self.int1.ConstNUWMul(self.int2)
        assert cnv is self.i64.ConstInt(2)
        cne = self.xi8.ConstNUWMul(self.xi1)
        assert isinstance(cne, llpy.core.BinaryMulConstantExpr)
        assert cne.GetNumOperands() == 2
        assert cne.GetOperand(0) is self.xi8
        assert cne.GetOperand(1) is self.xi1
        self.assertDump(cne, 'i64 mul nuw (%s, %s)\n' % (self.xi8_dump, self.xi1_dump))

    def test_ConstFMul(self):
        cnv = self.float1.ConstFMul(self.float2)
        assert cnv is self.float.ConstReal(2.0)
        cne = self.xf8.ConstFMul(self.xf1)
        assert isinstance(cne, llpy.core.BinaryFMulConstantExpr)
        assert cne.GetNumOperands() == 2
        assert cne.GetOperand(0) is self.xf8
        assert cne.GetOperand(1) is self.xf1
        self.assertDump(cne, 'float fmul (%s, %s)\n' % (self.xf8_dump, self.xf1_dump))

    def test_ConstUDiv(self):
        cnv = self.int1.ConstUDiv(self.int2)
        assert cnv is self.i64.ConstInt(0)
        cne = self.xi8.ConstUDiv(self.xi1)
        assert isinstance(cne, llpy.core.BinaryUDivConstantExpr)
        assert cne.GetNumOperands() == 2
        assert cne.GetOperand(0) is self.xi8
        assert cne.GetOperand(1) is self.xi1
        self.assertDump(cne, 'i64 udiv (%s, %s)\n' % (self.xi8_dump, self.xi1_dump))

    def test_ConstSDiv(self):
        cnv = self.int1.ConstSDiv(self.int2)
        assert cnv is self.i64.ConstInt(0)
        cne = self.xi8.ConstSDiv(self.xi1)
        assert isinstance(cne, llpy.core.BinarySDivConstantExpr)
        assert cne.GetNumOperands() == 2
        assert cne.GetOperand(0) is self.xi8
        assert cne.GetOperand(1) is self.xi1
        self.assertDump(cne, 'i64 sdiv (%s, %s)\n' % (self.xi8_dump, self.xi1_dump))

    def test_ConstExactSDiv(self):
        cnv = self.int1.ConstExactSDiv(self.int2)
        assert cnv is self.i64.ConstInt(0)
        cne = self.xi8.ConstExactSDiv(self.xi1)
        assert isinstance(cne, llpy.core.BinarySDivConstantExpr)
        assert cne.GetNumOperands() == 2
        assert cne.GetOperand(0) is self.xi8
        assert cne.GetOperand(1) is self.xi1
        self.assertDump(cne, 'i64 sdiv exact (%s, %s)\n' % (self.xi8_dump, self.xi1_dump))

    def test_ConstFDiv(self):
        cnv = self.float1.ConstFDiv(self.float2)
        assert cnv is self.float.ConstReal(0.5)
        cne = self.xf8.ConstFDiv(self.xf1)
        assert isinstance(cne, llpy.core.BinaryFDivConstantExpr)
        assert cne.GetNumOperands() == 2
        assert cne.GetOperand(0) is self.xf8
        assert cne.GetOperand(1) is self.xf1
        self.assertDump(cne, 'float fdiv (%s, %s)\n' % (self.xf8_dump, self.xf1_dump))

    def test_ConstURem(self):
        cnv = self.int1.ConstURem(self.int2)
        assert cnv is self.i64.ConstInt(1)
        cne = self.xi8.ConstURem(self.xi1)
        assert isinstance(cne, llpy.core.BinaryURemConstantExpr)
        assert cne.GetNumOperands() == 2
        assert cne.GetOperand(0) is self.xi8
        assert cne.GetOperand(1) is self.xi1
        self.assertDump(cne, 'i64 urem (%s, %s)\n' % (self.xi8_dump, self.xi1_dump))

    def test_ConstSRem(self):
        cnv = self.int1.ConstSRem(self.int2)
        assert cnv is self.i64.ConstInt(1)
        cne = self.xi8.ConstSRem(self.xi1)
        assert isinstance(cne, llpy.core.BinarySRemConstantExpr)
        assert cne.GetNumOperands() == 2
        assert cne.GetOperand(0) is self.xi8
        assert cne.GetOperand(1) is self.xi1
        self.assertDump(cne, 'i64 srem (%s, %s)\n' % (self.xi8_dump, self.xi1_dump))

    def test_ConstFRem(self):
        cnv = self.float1.ConstFRem(self.float2)
        assert cnv is self.float.ConstReal(1.0)
        cne = self.xf8.ConstFRem(self.xf1)
        assert isinstance(cne, llpy.core.BinaryFRemConstantExpr)
        assert cne.GetNumOperands() == 2
        assert cne.GetOperand(0) is self.xf8
        assert cne.GetOperand(1) is self.xf1
        self.assertDump(cne, 'float frem (%s, %s)\n' % (self.xf8_dump, self.xf1_dump))

    def test_ConstAnd(self):
        cnv = self.i64.ConstInt(3).ConstAnd(self.i64.ConstInt(5))
        assert cnv is self.i64.ConstInt(1)
        cne = self.xi8.ConstAnd(self.xi1)
        assert isinstance(cne, llpy.core.BinaryAndConstantExpr)
        assert cne.GetNumOperands() == 2
        assert cne.GetOperand(0) is self.xi8
        assert cne.GetOperand(1) is self.xi1
        self.assertDump(cne, 'i64 and (%s, %s)\n' % (self.xi8_dump, self.xi1_dump))

    def test_ConstOr(self):
        cnv = self.i64.ConstInt(3).ConstOr(self.i64.ConstInt(5))
        assert cnv is self.i64.ConstInt(7)
        cne = self.xi8.ConstOr(self.xi1)
        assert isinstance(cne, llpy.core.BinaryOrConstantExpr)
        assert cne.GetNumOperands() == 2
        assert cne.GetOperand(0) is self.xi8
        assert cne.GetOperand(1) is self.xi1
        self.assertDump(cne, 'i64 or (%s, %s)\n' % (self.xi8_dump, self.xi1_dump))

    def test_ConstXor(self):
        cnv = self.i64.ConstInt(3).ConstXor(self.i64.ConstInt(5))
        assert cnv is self.i64.ConstInt(6)
        cne = self.xi8.ConstXor(self.xi1)
        assert isinstance(cne, llpy.core.BinaryXorConstantExpr)
        assert cne.GetNumOperands() == 2
        assert cne.GetOperand(0) is self.xi8
        assert cne.GetOperand(1) is self.xi1
        self.assertDump(cne, 'i64 xor (%s, %s)\n' % (self.xi8_dump, self.xi1_dump))

    def test_ConstICmp(self):
        i1 = llpy.core.IntegerType(self.ctx, 1)
        i2 = llpy.core.IntegerType(self.ctx, 2)

        ins = [(x, i2.ConstInt(x)) for x in range(4)]
        outs = [i1.ConstInt(x) for x in range(2)]
        for op, calc in [
            ['eq',  lambda x, y: x == y],
            ['ne',  lambda x, y: x != y],
            ['sge', lambda x, y: ((x + 2) % 4) >= ((y + 2) % 4)],
            ['sgt', lambda x, y: ((x + 2) % 4) > ((y + 2) % 4)],
            ['sle', lambda x, y: ((x + 2) % 4) <= ((y + 2) % 4)],
            ['slt', lambda x, y: ((x + 2) % 4) < ((y + 2) % 4)],
            ['uge', lambda x, y: x >= y],
            ['ugt', lambda x, y: x > y],
            ['ule', lambda x, y: x <= y],
            ['ult', lambda x, y: x < y],
        ]:
            pred = getattr(llpy.core.IntPredicate, op.upper())

            for i, (a, arg) in enumerate(ins):
                for j, (b, brg) in enumerate(ins):
                    cnv = arg.ConstICmp(pred, brg)
                    r = calc(a, b)
                    assert cnv is outs[r]

            cne = self.xi8.ConstICmp(pred, self.xi1)
            assert isinstance(cne, llpy.core.ICmpConstantExpr)
            assert cne.GetNumOperands() == 2
            assert cne.GetOperand(0) is self.xi8
            assert cne.GetOperand(1) is self.xi1
            self.assertDump(cne, 'i1 icmp %s (%s, %s)\n' % (op, self.xi8_dump, self.xi1_dump))

    def test_ConstFCmp(self):
        ins = [(x, self.float.ConstReal(x)) for x in [float('nan'), float('-inf'),  float('inf'), -2.0, -1.0, -0.0, 0.0, 1.0, 2.0]]
        outs = [self.i1.ConstInt(x) for x in range(2)]
        for op, calc in [
            ['false', lambda x, y: False],
            ['oeq', lambda x, y: x == x and y == y and x == y],
            ['ogt', lambda x, y: x == x and y == y and x > y],
            ['oge', lambda x, y: x == x and y == y and x >= y],
            ['olt', lambda x, y: x == x and y == y and x < y],
            ['ole', lambda x, y: x == x and y == y and x <= y],
            ['one', lambda x, y: x == x and y == y and x != y],
            ['ord', lambda x, y: x == x and y == y],
            ['ueq', lambda x, y: x != x or y != y or x == y],
            ['ugt', lambda x, y: x != x or y != y or x > y],
            ['uge', lambda x, y: x != x or y != y or x >= y],
            ['ult', lambda x, y: x != x or y != y or x < y],
            ['ule', lambda x, y: x != x or y != y or x <= y],
            ['une', lambda x, y: x != x or y != y or x != y],
            ['uno', lambda x, y: x != x or y != y],
            ['true', lambda x, y: True],
        ]:
            pred = getattr(llpy.core.RealPredicate, op.upper())

            for i, (a, arg) in enumerate(ins):
                for j, (b, brg) in enumerate(ins):
                    cnv = arg.ConstFCmp(pred, brg)
                    r = calc(a, b)
                    assert cnv is outs[r]

            cne = self.xf8.ConstFCmp(pred, self.xf1)
            if True: # build and const differ here
                if pred == llpy.core.RealPredicate.FALSE:
                    assert cne is self.false
                    continue
                if pred == llpy.core.RealPredicate.TRUE:
                    assert cne is self.true
                    continue
            assert isinstance(cne, llpy.core.FCmpConstantExpr)
            assert cne.GetNumOperands() == 2
            assert cne.GetOperand(0) is self.xf8
            assert cne.GetOperand(1) is self.xf1
            self.assertDump(cne, 'i1 fcmp %s (%s, %s)\n' % (op, self.xf8_dump, self.xf1_dump))

    def test_ConstShl(self):
        cnv = self.i64.ConstAllOnes().ConstShl(self.int1)
        assert cnv is self.i64.ConstInt(-2)
        cne = self.xi8.ConstShl(self.xi1)
        assert isinstance(cne, llpy.core.BinaryShlConstantExpr)
        assert cne.GetNumOperands() == 2
        assert cne.GetOperand(0) is self.xi8
        assert cne.GetOperand(1) is self.xi1
        self.assertDump(cne, 'i64 shl (%s, %s)\n' % (self.xi8_dump, self.xi1_dump))

    def test_ConstLShr(self):
        cnv = self.i64.ConstInt(-2).ConstLShr(self.int1)
        assert cnv is self.i64.ConstInt(0x7fFFffFFffFFffFF)
        cne = self.xi8.ConstLShr(self.xi1)
        assert isinstance(cne, llpy.core.BinaryLShrConstantExpr)
        assert cne.GetNumOperands() == 2
        assert cne.GetOperand(0) is self.xi8
        assert cne.GetOperand(1) is self.xi1
        self.assertDump(cne, 'i64 lshr (%s, %s)\n' % (self.xi8_dump, self.xi1_dump))

    def test_ConstAShr(self):
        cnv = self.i64.ConstInt(-2).ConstAShr(self.int1)
        assert cnv is self.i64.ConstAllOnes()
        cne = self.xi8.ConstAShr(self.xi1)
        assert isinstance(cne, llpy.core.BinaryAShrConstantExpr)
        assert cne.GetNumOperands() == 2
        assert cne.GetOperand(0) is self.xi8
        assert cne.GetOperand(1) is self.xi1
        self.assertDump(cne, 'i64 ashr (%s, %s)\n' % (self.xi8_dump, self.xi1_dump))

    def test_ConstGEP(self):
        i64p = llpy.core.PointerType(self.i64)
        i64null = i64p.ConstPointerNull()
        cnv = i64null.ConstGEP([self.i64.ConstNull()])
        assert cnv is i64null
        cne = self.xp8.ConstGEP([self.xi8])
        assert isinstance(cne, llpy.core.GetElementPtrConstantExpr)
        assert cne.GetNumOperands() == 2
        assert cne.GetOperand(0) is self.xp8
        assert cne.GetOperand(1) is self.xi8
        self.assertDump(cne, 'i64* getelementptr (%s, %s)\n' % (self.xp8_dump, self.xi8_dump))

        s_i64 = llpy.core.StructType(self.ctx, [self.i64], None)
        s_i64p = llpy.core.PointerType(s_i64)
        s_i64null = s_i64p.ConstPointerNull()
        i32 = llpy.core.IntegerType(self.ctx, 32) # required for struct
        cnv = s_i64null.ConstGEP([self.i64.ConstNull(), i32.ConstNull()])
        assert cnv is i64null
        xps = self.i64.ConstInt(8).ConstIntToPtr(s_i64p)
        xps_dump = '{ i64 }* inttoptr (i64 8 to { i64 }*)'
        cne = xps.ConstGEP([self.xi8, i32.ConstNull()])
        assert isinstance(cne, llpy.core.GetElementPtrConstantExpr)
        assert cne.GetNumOperands() == 3
        assert cne.GetOperand(0) is xps
        assert cne.GetOperand(1) is self.xi8
        assert cne.GetOperand(2) is i32.ConstNull()
        self.assertDump(cne, 'i64* getelementptr (%s, %s, i32 0)\n' % (xps_dump, self.xi8_dump))

        a_i64 = llpy.core.ArrayType(self.i64, 2)
        a_i64p = llpy.core.PointerType(a_i64)
        a_i64null = a_i64p.ConstPointerNull()
        cnv = a_i64null.ConstGEP([self.i64.ConstNull(), self.i64.ConstNull()])
        assert cnv is i64null
        xpa = self.i64.ConstInt(8).ConstIntToPtr(a_i64p)
        xpa_dump = '[2 x i64]* inttoptr (i64 8 to [2 x i64]*)'
        cne = xpa.ConstGEP([self.xi8, self.xi1])
        assert isinstance(cne, llpy.core.GetElementPtrConstantExpr)
        assert cne.GetNumOperands() == 3
        assert cne.GetOperand(0) is xpa
        assert cne.GetOperand(1) is self.xi8
        assert cne.GetOperand(2) is self.xi1
        self.assertDump(cne, 'i64* getelementptr (%s, %s, %s)\n' % (xpa_dump, self.xi8_dump, self.xi1_dump))

    def test_ConstInBoundsGEP(self):
        i64p = llpy.core.PointerType(self.i64)
        i64null = i64p.ConstPointerNull()
        cnv = i64null.ConstInBoundsGEP([self.i64.ConstNull()])
        assert cnv is i64null
        cne = self.xp8.ConstInBoundsGEP([self.xi8])
        assert isinstance(cne, llpy.core.GetElementPtrConstantExpr)
        assert cne.GetNumOperands() == 2
        assert cne.GetOperand(0) is self.xp8
        assert cne.GetOperand(1) is self.xi8
        self.assertDump(cne, 'i64* getelementptr inbounds (%s, %s)\n' % (self.xp8_dump, self.xi8_dump))

        s_i64 = llpy.core.StructType(self.ctx, [self.i64], None)
        s_i64p = llpy.core.PointerType(s_i64)
        s_i64null = s_i64p.ConstPointerNull()
        i32 = llpy.core.IntegerType(self.ctx, 32) # required for struct
        cnv = s_i64null.ConstInBoundsGEP([self.i64.ConstNull(), i32.ConstNull()])
        assert cnv is i64null
        xps = self.i64.ConstInt(8).ConstIntToPtr(s_i64p)
        xps_dump = '{ i64 }* inttoptr (i64 8 to { i64 }*)'
        cne = xps.ConstInBoundsGEP([self.xi8, i32.ConstNull()])
        assert isinstance(cne, llpy.core.GetElementPtrConstantExpr)
        assert cne.GetNumOperands() == 3
        assert cne.GetOperand(0) is xps
        assert cne.GetOperand(1) is self.xi8
        assert cne.GetOperand(2) is i32.ConstNull()
        self.assertDump(cne, 'i64* getelementptr inbounds (%s, %s, i32 0)\n' % (xps_dump, self.xi8_dump))

        a_i64 = llpy.core.ArrayType(self.i64, 2)
        a_i64p = llpy.core.PointerType(a_i64)
        a_i64null = a_i64p.ConstPointerNull()
        cnv = a_i64null.ConstInBoundsGEP([self.i64.ConstNull(), self.i64.ConstNull()])
        assert cnv is i64null
        xpa = self.i64.ConstInt(8).ConstIntToPtr(a_i64p)
        xpa_dump = '[2 x i64]* inttoptr (i64 8 to [2 x i64]*)'

        cne = xpa.ConstInBoundsGEP([self.xi8, self.xi1])
        assert isinstance(cne, llpy.core.GetElementPtrConstantExpr)
        assert cne.GetNumOperands() == 3
        assert cne.GetOperand(0) is xpa
        assert cne.GetOperand(1) is self.xi8
        assert cne.GetOperand(2) is self.xi1
        self.assertDump(cne, 'i64* getelementptr inbounds (%s, %s, %s)\n' % (xpa_dump, self.xi8_dump, self.xi1_dump))

    def test_ConstTrunc(self):
        i32 = llpy.core.IntegerType(self.ctx, 32)
        xi = self.xi1.ConstAdd(self.xi8) # otherwise it simplifies too much
        xi_dump = 'i64 add (%s, %s)' % (self.xi1_dump, self.xi8_dump)
        cnv = self.int1.ConstTrunc(i32)
        assert cnv is i32.ConstInt(1)
        cne = xi.ConstTrunc(i32)
        assert isinstance(cne, llpy.core.UnaryTruncConstantExpr)
        assert cne.GetNumOperands() == 1
        assert cne.GetOperand(0) is xi
        self.assertDump(cne, 'i32 trunc (%s to i32)\n' % (xi_dump))

    def test_ConstSExt(self):
        i32 = llpy.core.IntegerType(self.ctx, 32)
        xi32 = self.xi1.ConstTrunc(i32).ConstAdd(i32.ConstInt(1))
        xi32_dump = 'i32 add (%s, i32 1)' % (self.xi1_dump.replace('i64', 'i32'))
        cnv = i32.ConstInt(-1).ConstSExt(self.i64)
        assert cnv is self.i64.ConstInt(-1)
        cne = xi32.ConstSExt(self.i64)
        assert isinstance(cne, llpy.core.UnarySExtConstantExpr)
        assert cne.GetNumOperands() == 1
        assert cne.GetOperand(0) is xi32
        self.assertDump(cne, 'i64 sext (%s to i64)\n' % (xi32_dump))

    def test_ConstZExt(self):
        i32 = llpy.core.IntegerType(self.ctx, 32)
        xi32 = self.xi1.ConstTrunc(i32).ConstAdd(i32.ConstInt(1))
        xi32_dump = 'i32 add (%s, i32 1)' % (self.xi1_dump.replace('i64', 'i32'))
        cnv = i32.ConstInt(-1).ConstZExt(self.i64)
        assert cnv is self.i64.ConstInt(0xFFffFFff)
        cne = xi32.ConstZExt(self.i64)
        assert isinstance(cne, llpy.core.UnaryZExtConstantExpr)
        assert cne.GetNumOperands() == 1
        assert cne.GetOperand(0) is xi32
        self.assertDump(cne, 'i64 zext (%s to i64)\n' % (xi32_dump))

    def test_ConstFPTrunc(self):
        float = self.float
        double = llpy.core.DoubleType(self.ctx)
        double1 = double.ConstReal(1.0)
        xd1 = self.xi1.ConstUIToFP(double)
        xd1_dump = 'double uitofp (%s to double)' % (self.xi1_dump)
        cnv = double1.ConstFPTrunc(float)
        assert cnv is float.ConstReal(1.0)
        cne = xd1.ConstFPTrunc(float)
        assert isinstance(cne, llpy.core.UnaryFPTruncConstantExpr)
        assert cne.GetNumOperands() == 1
        assert cne.GetOperand(0) is xd1
        self.assertDump(cne, 'float fptrunc (%s to float)\n' % (xd1_dump))

    def test_ConstFPExt(self):
        double = llpy.core.DoubleType(self.ctx)
        cnv = self.float1.ConstFPExt(double)
        assert cnv is double.ConstReal(1.0)
        cne = self.xf1.ConstFPExt(double)
        assert isinstance(cne, llpy.core.UnaryFPExtConstantExpr)
        assert cne.GetNumOperands() == 1
        assert cne.GetOperand(0) is self.xf1
        self.assertDump(cne, 'double fpext (%s to double)\n' % (self.xf1_dump))

    def test_ConstUIToFP(self):
        cnv = self.int1.ConstUIToFP(self.float)
        assert cnv is self.float1
        cne = self.xi1.ConstUIToFP(self.float)
        assert isinstance(cne, llpy.core.UnaryUIToFPConstantExpr)
        assert cne.GetNumOperands() == 1
        assert cne.GetOperand(0) is self.xi1
        self.assertDump(cne, 'float uitofp (%s to float)\n' % (self.xi1_dump))

    def test_ConstSIToFP(self):
        cnv = self.int1.ConstSIToFP(self.float)
        assert cnv is self.float1
        cne = self.xi1.ConstSIToFP(self.float)
        assert isinstance(cne, llpy.core.UnarySIToFPConstantExpr)
        assert cne.GetNumOperands() == 1
        assert cne.GetOperand(0) is self.xi1
        self.assertDump(cne, 'float sitofp (%s to float)\n' % (self.xi1_dump))

    def test_ConstFPToUI(self):
        xf2 = self.xf1.ConstFAdd(self.float1)
        xf2_dump = 'float fadd (%s, float 1.000000e+00)' % (self.xf1_dump)
        cnv = self.float1.ConstFPToUI(self.i64)
        assert cnv is self.int1
        cne = xf2.ConstFPToUI(self.i64)
        assert isinstance(cne, llpy.core.UnaryFPToUIConstantExpr)
        assert cne.GetNumOperands() == 1
        assert cne.GetOperand(0) is xf2
        self.assertDump(cne, 'i64 fptoui (%s to i64)\n' % (xf2_dump))

    def test_ConstFPToSI(self):
        xf2 = self.xf1.ConstFAdd(self.float1)
        xf2_dump = 'float fadd (%s, float 1.000000e+00)' % (self.xf1_dump)
        cnv = self.float1.ConstFPToSI(self.i64)
        assert cnv is self.int1
        cne = xf2.ConstFPToSI(self.i64)
        assert isinstance(cne, llpy.core.UnaryFPToSIConstantExpr)
        assert cne.GetNumOperands() == 1
        assert cne.GetOperand(0) is xf2
        self.assertDump(cne, 'i64 fptosi (%s to i64)\n' % (xf2_dump))

    def test_ConstPtrToInt(self):
        i64p = llpy.core.PointerType(self.i64)
        null = i64p.ConstPointerNull()
        xp = null.ConstGEP([self.int1])
        xp_dump = 'i64* getelementptr (i64* null, i64 1)'
        cnv = i64p.ConstPointerNull().ConstPtrToInt(self.i64)
        assert cnv is self.i64.ConstNull()
        cne = xp.ConstPtrToInt(self.i64)
        assert isinstance(cne, llpy.core.UnaryPtrToIntConstantExpr)
        assert cne.GetNumOperands() == 1
        assert cne.GetOperand(0) is xp
        self.assertDump(cne, 'i64 ptrtoint (%s to i64)\n' % (xp_dump))

    def test_ConstIntToPtr(self):
        i64p = llpy.core.PointerType(self.i64)
        null = i64p.ConstPointerNull()
        cnv = self.i64.ConstNull().ConstIntToPtr(i64p)
        assert cnv is null
        cne = self.int1.ConstIntToPtr(i64p)
        assert isinstance(cne, llpy.core.UnaryIntToPtrConstantExpr)
        assert cne.GetNumOperands() == 1
        assert cne.GetOperand(0) is self.int1
        self.assertDump(cne, 'i64* inttoptr (i64 1 to i64*)\n')

    def test_ConstBitCast(self):
        i1p = llpy.core.PointerType(self.i1)
        i64p = llpy.core.PointerType(self.i64)
        null1 = i1p.ConstPointerNull()
        null64 = i64p.ConstPointerNull()
        xp = null64.ConstGEP([self.int1])
        xp_dump = 'i64* getelementptr (i64* null, i64 1)'
        cnv = null1.ConstBitCast(i64p)
        assert cnv is null64
        cne = xp.ConstBitCast(i1p)
        assert isinstance(cne, llpy.core.UnaryBitCastConstantExpr)
        assert cne.GetNumOperands() == 1
        assert cne.GetOperand(0) is xp
        self.assertDump(cne, 'i1* bitcast (%s to i1*)\n' % (xp_dump))

    if (3, 4) <= _version:
        def test_ConstAddrSpaceCast(self):
            i64p1 = llpy.core.PointerType(self.i64, 1)
            i64p = llpy.core.PointerType(self.i64)
            null64_1 = i64p1.ConstPointerNull()
            null64 = i64p.ConstPointerNull()
            xp = null64.ConstGEP([self.int1])
            xp_dump = 'i64* getelementptr (i64* null, i64 1)'
            cnv = null64_1.ConstAddrSpaceCast(i64p)
            assert cnv is null64
            cne = xp.ConstAddrSpaceCast(i64p1)
            assert isinstance(cne, llpy.core.UnaryAddrSpaceCastConstantExpr)
            assert cne.GetNumOperands() == 1
            assert cne.GetOperand(0) is xp
            self.assertDump(cne, 'i64 addrspace(1)* addrspacecast (%s to i64 addrspace(1)*)\n' % (xp_dump))

    @unittest.expectedFailure
    def test_ConstZExtOrBitCast(self):
        assert False

    @unittest.expectedFailure
    def test_ConstSExtOrBitCast(self):
        assert False

    @unittest.expectedFailure
    def test_ConstTruncOrBitCast(self):
        assert False

    @unittest.expectedFailure
    def test_ConstPointerCast(self):
        assert False

    @unittest.expectedFailure
    def test_ConstIntCast(self):
        assert False

    @unittest.expectedFailure
    def test_ConstFPCast(self):
        assert False

    def test_ConstSelect(self):
        xb = self.xi1.ConstTrunc(self.i1)
        xb_dump = self.xi1_dump.replace('i64', 'i1')
        cnv = self.false.ConstSelect(self.int1, self.int2)
        assert cnv is self.int2
        cnv = self.true.ConstSelect(self.int1, self.int2)
        assert cnv is self.int1
        cne = xb.ConstSelect(self.xi1, self.xi8)
        assert isinstance(cne, llpy.core.SelectConstantExpr)
        assert cne.GetNumOperands() == 3
        assert cne.GetOperand(0) is xb
        assert cne.GetOperand(1) is self.xi1
        assert cne.GetOperand(2) is self.xi8
        self.assertDump(cne, 'i64 select (%s, %s, %s)\n' % (xb_dump, self.xi1_dump, self.xi8_dump))

    def test_ConstExtractElement(self):
        vec12 = llpy.core.ConstVector([self.int1, self.int2])
        xvec = llpy.core.ConstVector([self.xi1, self.xi8])
        cnv = vec12.ConstExtractElement(self.i64.ConstNull())
        assert cnv is self.int1
        cnv = vec12.ConstExtractElement(self.int1)
        assert cnv is self.int2
        cne = xvec.ConstExtractElement(self.xi1)
        assert isinstance(cne, llpy.core.ExtractElementConstantExpr)
        assert cne.GetNumOperands() == 2
        assert cne.GetOperand(0) is xvec
        assert cne.GetOperand(1) is self.xi1
        self.assertDump(cne, 'i64 extractelement (<2 x i64> <%s, %s>, %s)\n' % (self.xi1_dump, self.xi8_dump, self.xi1_dump))

    def test_ConstInsertElement(self):
        vec12 = llpy.core.ConstVector([self.int1, self.int2])
        xvec = llpy.core.ConstVector([self.xi1, self.xi8])
        cnv = vec12.ConstInsertElement(self.i64.ConstNull(), self.int1)
        assert cnv is llpy.core.ConstVector([self.int1, self.i64.ConstNull()])
        cne = xvec.ConstInsertElement(self.xi8, self.xi1)
        assert isinstance(cne, llpy.core.InsertElementConstantExpr)
        assert cne.GetNumOperands() == 3
        assert cne.GetOperand(0) is xvec
        assert cne.GetOperand(1) is self.xi8
        assert cne.GetOperand(2) is self.xi1
        self.assertDump(cne, '<2 x i64> insertelement (<2 x i64> <%s, %s>, %s, %s)\n' % (self.xi1_dump, self.xi8_dump, self.xi8_dump, self.xi1_dump))

    def test_ConstShuffleVector(self):
        i2 = llpy.core.IntegerType(self.ctx, 2)
        i3 = llpy.core.IntegerType(self.ctx, 3)
        i4 = llpy.core.IntegerType(self.ctx, 4)
        i32 = llpy.core.IntegerType(self.ctx, 32)
        i64 = self.i64
        xi1 = self.xi1
        xi2 = i2.SizeOf()
        xi3 = i3.SizeOf()
        xi4 = i4.SizeOf()
        #xi1_dump = self.xi1_dump
        #xi2_dump = 'i64 ptrtoint (i2* getelementptr (i2* null, i32 1) to i64)'
        #xi3_dump = 'i64 ptrtoint (i3* getelementptr (i3* null, i32 1) to i64)'
        #xi4_dump = 'i64 ptrtoint (i4* getelementptr (i4* null, i32 1) to i64)'
        a = i64.ConstInt(~0)
        b = i64.ConstInt(~1)
        c = i64.ConstInt(~2)
        d = i64.ConstInt(~3)
        e = i32.ConstInt(0)
        f = i32.ConstInt(1)
        g = i32.ConstInt(2)
        h = i32.ConstInt(3)
        v1 = llpy.core.ConstVector([a, b])
        v2 = llpy.core.ConstVector([c, d])
        vr = llpy.core.ConstVector([a, c, d, b])
        mask = llpy.core.ConstVector([e, g, h, f])
        #mask_dump = '<4 x i32> <i32 0, i32 2, i32 3, i32 1>'
        xv1 = llpy.core.ConstVector([xi1, xi2])
        xv2 = llpy.core.ConstVector([xi3, xi4])
        xvr = llpy.core.ConstVector([xi1, xi3, xi4, xi2])
        #xv1_dump = '<2 x i64> <%s, %s>' % (xi1_dump, xi2_dump)
        #xv2_dump = '<2 x i64> <%s, %s>' % (xi3_dump, xi4_dump)
        cnv = v1.ConstShuffleVector(v2, mask)
        assert cnv is vr
        cne = xv1.ConstShuffleVector(xv2, mask)
        #assert isinstance(cne, llpy.core.ShuffleVectorConstantExpr)
        #assert cne.GetNumOperands() == 3
        #assert cne.GetOperand(0) is xv1
        #assert cne.GetOperand(1) is xv2
        #assert cne.GetOperand(2) is mask
        #self.assertDump(cne, '<4 x i64> shufflevector (%s, %s, %s)\n' % (xv1_dump, xv2_dump, mask_dump))
        assert isinstance(cne, llpy.core.ConstantVector)
        assert cne is xvr

    def test_ConstExtractValue(self):
        av = self.i64.ConstArray([self.int1, self.int2])
        sv = self.ctx.ConstStruct([av])
        xav = self.i64.ConstArray([self.xi1, self.xi8])
        xsv = self.ctx.ConstStruct([xav])
        #xsv_dump = '{ [2 x i64] } { [ %s, %s ] }' % (self.xi1_dump, self.xi8_dump)
        cnv = sv.ConstExtractValue([0, 1])
        assert cnv is self.int2
        cne = xsv.ConstExtractValue([0, 1])
        #assert isinstance(cne, llpy.core.ExtractValueConstantExpr)
        #assert cne.GetNumOperands() == 3
        #assert cne.GetOperand(0) is xsv
        #assert cne.GetOperand(1) is i32.ConstNull()
        #assert cne.GetOperand(2) is i32.ConstInt(1)
        #self.assertDump(cne, 'i64 extractelement (%s, %s, %s)\n' % (xsv_dump, 'i32 0', 'i32 1'))
        assert cne is self.xi8

    def test_ConstInsertValue(self):
        av = self.i64.ConstArray([self.int1, self.int2])
        sv = self.ctx.ConstStruct([av])
        xav = self.i64.ConstArray([self.xi1, self.xi8])
        xsv = self.ctx.ConstStruct([xav])
        #xsv_dump = '{ [2 x i64] } { [ %s, %s ] }' % (self.xi1_dump, self.xi8_dump)
        value = self.int2
        #value_dump = 'i64 2'
        cnv = sv.ConstInsertValue(self.i64.ConstInt(3), [0, 1])
        assert cnv is self.ctx.ConstStruct([self.i64.ConstArray([self.int1, self.i64.ConstInt(3)])])
        cne = xsv.ConstInsertValue(value, [0, 1])
        #assert isinstance(cne, llpy.core.InsertValueConstantExpr)
        #assert cne.GetNumOperands() == 4
        #assert cne.GetOperand(0) is xsv
        #assert cne.GetOperand(1) is value
        #assert cne.GetOperand(2) is i32.ConstNull()
        #assert cne.GetOperand(3) is i32.ConstInt(1)
        #self.assertDump(cne, 'i64 insertelement (%s, %s, %s, %s)\n' % (xsv_dump, value_dump, 'i32 0', 'i32 1'))
        assert cne is self.ctx.ConstStruct([self.i64.ConstArray([self.xi1, value])])

class TestBlockAddress(DumpTestCase):

    def setUp(self):
        pass

    def tearDown(self):
        gc.collect()

    def test_it(self):
        ctx = llpy.core.Context()
        mod = llpy.core.Module(ctx, 'TestBlockAddress')
        void = llpy.core.VoidType(ctx)
        i8 = llpy.core.IntegerType(ctx, 8)
        i8p = llpy.core.PointerType(i8)
        func_type = llpy.core.FunctionType(void, [])
        func = mod.AddFunction(func_type, 'func')
        bb = func.AppendBasicBlock()

        ba = llpy.core.BlockAddress(bb)
        assert ba.GetNumOperands() == 2
        assert ba.GetOperand(0) is func
        assert ba.GetOperand(1) is bb
        assert ba.TypeOf() is i8p

class TestFunction(DumpTestCase):

    def setUp(self):
        self.ctx = llpy.core.Context()
        self.mod = llpy.core.Module(self.ctx, 'TestFunction')
        self.i32 = llpy.core.IntegerType(self.ctx, 32)
        func_type = llpy.core.FunctionType(self.i32, [])
        self.func_decl = self.mod.AddFunction(func_type, 'func_decl')
        void = llpy.core.VoidType(self.ctx)
        func_type = llpy.core.FunctionType(void, [])
        self.func_def = self.mod.AddFunction(func_type, 'func_def')
        bb = self.func_def.AppendBasicBlock()
        builder = llpy.core.IRBuilder(self.ctx)
        builder.PositionBuilderAtEnd(bb)
        builder.BuildRetVoid()

    def tearDown(self):
        del self.func_decl
        del self.func_def
        del self.i32
        del self.mod
        del self.ctx
        gc.collect()

    def test_decl(self):
        assert self.func_decl.IsDeclaration()
        self.assertDump(self.func_decl,
'''
declare i32 @func_decl()

''')
        assert not self.func_def.IsDeclaration()
        self.assertDump(self.func_def,
'''
define void @func_def() {
  ret void
}

''')
        self.assertDump(self.mod,
'''; ModuleID = 'TestFunction'

declare i32 @func_decl()

define void @func_def() {
  ret void
}
''')

    def test_linkage(self):
        Linkage = llpy.core.Linkage
        assert self.func_decl.GetLinkage() == Linkage.External
        self.func_decl.SetLinkage(Linkage.Private)
        assert self.func_decl.GetLinkage() == Linkage.Private
        self.assertDump(self.func_decl,
'''
declare private i32 @func_decl()

''')
        assert self.func_def.GetLinkage() == Linkage.External
        self.func_def.SetLinkage(Linkage.Private)
        assert self.func_def.GetLinkage() == Linkage.Private
        self.assertDump(self.func_def,
'''
define private void @func_def() {
  ret void
}

''')
        self.assertDump(self.mod,
'''; ModuleID = 'TestFunction'

declare private i32 @func_decl()

define private void @func_def() {
  ret void
}
''')

    def test_section(self):
        assert self.func_decl.GetSection() == ''
        self.func_decl.SetSection('foo')
        assert self.func_decl.GetSection() == 'foo'
        self.assertDump(self.func_decl,
'''
declare i32 @func_decl() section "foo"

''')
        assert self.func_def.GetSection() == ''
        self.func_def.SetSection('foo')
        assert self.func_def.GetSection() == 'foo'
        self.assertDump(self.func_def,
'''
define void @func_def() section "foo" {
  ret void
}

''')
        self.assertDump(self.mod,
'''; ModuleID = 'TestFunction'

declare i32 @func_decl() section "foo"

define void @func_def() section "foo" {
  ret void
}
''')

    def test_visibility(self):
        Visibility = llpy.core.Visibility
        assert self.func_decl.GetVisibility() == Visibility.Default
        self.func_decl.SetVisibility(Visibility.Hidden)
        assert self.func_decl.GetVisibility() == Visibility.Hidden
        self.assertDump(self.func_decl,
'''
declare hidden i32 @func_decl()

''')
        assert self.func_def.GetVisibility() == Visibility.Default
        self.func_def.SetVisibility(Visibility.Hidden)
        assert self.func_def.GetVisibility() == Visibility.Hidden
        self.assertDump(self.func_def,
'''
define hidden void @func_def() {
  ret void
}

''')
        self.assertDump(self.mod,
'''; ModuleID = 'TestFunction'

declare hidden i32 @func_decl()

define hidden void @func_def() {
  ret void
}
''')

    def test_alignment(self):
        assert self.func_decl.GetAlignment() == 0
        self.func_decl.SetAlignment(1)
        assert self.func_decl.GetAlignment() == 1
        self.assertDump(self.func_decl,
'''
declare i32 @func_decl() align 1

''')
        assert self.func_def.GetAlignment() == 0
        self.func_def.SetAlignment(1)
        assert self.func_def.GetAlignment() == 1
        self.assertDump(self.func_def,
'''
define void @func_def() align 1 {
  ret void
}

''')
        self.assertDump(self.mod,
'''; ModuleID = 'TestFunction'

declare i32 @func_decl() align 1

define void @func_def() align 1 {
  ret void
}
''')

    if (3, 5) <= _version:
        def test_dll_storage_class(self):
            DLLStorageClass = llpy.core.DLLStorageClass
            assert self.func_decl.GetDLLStorageClass() == DLLStorageClass.Default
            self.func_decl.SetDLLStorageClass(DLLStorageClass.DLLImport)
            assert self.func_decl.GetDLLStorageClass() == DLLStorageClass.DLLImport
            self.assertDump(self.func_decl,
'''
declare dllimport i32 @func_decl()

''')
            assert self.func_def.GetDLLStorageClass() == DLLStorageClass.Default
            self.func_def.SetDLLStorageClass(DLLStorageClass.DLLExport)
            assert self.func_def.GetDLLStorageClass() == DLLStorageClass.DLLExport
            self.assertDump(self.func_def,
'''
define dllexport void @func_def() {
  ret void
}

''')
            self.assertDump(self.mod,
'''; ModuleID = 'TestFunction'

declare dllimport i32 @func_decl()

define dllexport void @func_def() {
  ret void
}
''')

        def test_unnamed_addr(self):
            assert self.func_decl.HasUnnamedAddr() == False
            self.func_decl.SetUnnamedAddr(True)
            assert self.func_decl.HasUnnamedAddr() == True
            self.assertDump(self.func_decl,
'''
declare i32 @func_decl() unnamed_addr

''')
            assert self.func_def.HasUnnamedAddr() == False
            self.func_def.SetUnnamedAddr(True)
            assert self.func_def.HasUnnamedAddr() == True
            self.assertDump(self.func_def,
'''
define void @func_def() unnamed_addr {
  ret void
}

''')
            self.assertDump(self.mod,
'''; ModuleID = 'TestFunction'

declare i32 @func_decl() unnamed_addr

define void @func_def() unnamed_addr {
  ret void
}
''')

    def test_cc(self):
        CallConv = llpy.core.CallConv
        assert self.func_decl.GetCallConv() == CallConv.C
        self.func_decl.SetCallConv(CallConv.Fast)
        assert self.func_decl.GetCallConv() == CallConv.Fast
        self.assertDump(self.func_decl,
'''
declare fastcc i32 @func_decl()

''')
        assert self.func_def.GetCallConv() == CallConv.C
        self.func_def.SetCallConv(CallConv.Fast)
        assert self.func_def.GetCallConv() == CallConv.Fast
        self.assertDump(self.func_def,
'''
define fastcc void @func_def() {
  ret void
}

''')
        self.assertDump(self.mod,
'''; ModuleID = 'TestFunction'

declare fastcc i32 @func_decl()

define fastcc void @func_def() {
  ret void
}
''')

    def test_gc(self):
        assert self.func_decl.GetGC() is None
        self.func_decl.SetGC('foo')
        assert self.func_decl.GetGC() == 'foo'
        self.assertDump(self.func_decl,
'''
declare i32 @func_decl() gc "foo"

''')
        assert self.func_def.GetGC() is None
        self.func_def.SetGC('foo')
        assert self.func_def.GetGC() == 'foo'
        self.assertDump(self.func_def,
'''
define void @func_def() gc "foo" {
  ret void
}

''')
        self.assertDump(self.mod,
'''; ModuleID = 'TestFunction'

declare i32 @func_decl() gc "foo"

define void @func_def() gc "foo" {
  ret void
}
''')
        self.func_decl.SetGC(None)
        self.assertDump(self.func_decl,
'''
declare i32 @func_decl()

''')
        self.func_def.SetGC(None)
        self.assertDump(self.func_def,
'''
define void @func_def() {
  ret void
}

''')
        self.assertDump(self.mod,
'''; ModuleID = 'TestFunction'

declare i32 @func_decl()

define void @func_def() {
  ret void
}
''')

    Attribute = llpy.core.Attribute
    attrs = [
        ('noreturn', Attribute.NoReturn),
        ('nounwind', Attribute.NoUnwind),
        ('uwtable', Attribute.UWTable),
        ('returns_twice', Attribute.ReturnsTwice),
        ('readnone', Attribute.ReadNone),
        ('readonly', Attribute.ReadOnly),
        ('optsize', Attribute.OptimizeForSize),
        ('noinline', Attribute.NoInline),
        ('inlinehint', Attribute.InlineHint),
        ('alwaysinline', Attribute.AlwaysInline),
        ('ssp', Attribute.StackProtect),
        ('sspreq', Attribute.StackProtectReq),
        ('noredzone', Attribute.NoRedZone),
        ('noimplicitfloat', Attribute.NoImplicitFloat),
        ('naked', Attribute.Naked),
    ]
    if _version <= (3, 0): # buggy afterwards, see below
        attrs += [
            ('nonlazybind', Attribute.NonLazyBind),
        ]
    if (3, 3) <= _version:
        attrs.sort()
    del Attribute

    def test_attr(self):
        Attribute = llpy.core.Attribute
        f = self.func_decl
        assert f.GetAttr() == Attribute()
        for ir, at in self.attrs:
            f.AddAttr(at)
            assert f.GetAttr() == at
            if _version <= (3, 2):
                self.assertDump(f,
'''
declare i32 @func_decl() %s

''' % ir)
            if (3, 3) <= _version:
                self.assertDump(f,
'''
; Function Attrs: %s
declare i32 @func_decl() #0

''' % ir)
            f.RemoveAttr(at)

    if (3, 1) <= _version:
        @unittest.expectedFailure
        def test_attr_bug(self):
            Attribute = llpy.core.Attribute
            ir = 'nonlazybind'
            at = Attribute.NonLazyBind_buggy
            f = self.func_decl
            assert f.GetAttr() == Attribute()
            f.AddAttr(at)
            assert f.GetAttr() == at
            self.assertDump(f,
'''
declare i32 @func_decl() %s

''' % ir)
            f.RemoveAttr(at)
            assert f.GetAttr() == Attribute()

        def test_attr_buggy(self):
            # This one *should* fail
            Attribute = llpy.core.Attribute
            if _version <= (3, 1):
                ir = 'nonlazybind address_safety'
            if (3, 2) <= _version <= (3, 2):
                ir = 'nonlazybind address_safety minsize'
            if (3, 3) <= _version <= (3, 3):
                ir = 'minsize nobuiltin noduplicate nonlazybind returned sspstrong sanitize_address sanitize_thread sanitize_memory'
            if (3, 4) <= _version <= (3, 4):
                ir = 'builtin cold minsize nobuiltin noduplicate nonlazybind optnone returned sspstrong sanitize_address sanitize_thread sanitize_memory'
            if (3, 5) <= _version:
                ir = 'builtin inalloca cold jumptable minsize nobuiltin noduplicate nonlazybind nonnull optnone returned sspstrong sanitize_address sanitize_thread sanitize_memory'
            at = Attribute.NonLazyBind_buggy
            f = self.func_decl
            assert f.GetAttr() == Attribute()
            f.AddAttr(at)
            assert f.GetAttr() == at
            if _version <= (3, 2):
                self.assertDump(f,
'''
declare i32 @func_decl() %s

''' % ir)
            if (3, 3) <= _version:
                self.assertDump(f,
'''
; Function Attrs: %s
declare i32 @func_decl() #0

''' % ir)
            f.RemoveAttr(at)
            assert f.GetAttr() == Attribute()

    def test_allattr(self):
        Attribute = llpy.core.Attribute
        attrs = reduce(operator.or_, (at for ir, at in self.attrs))
        irs = ' '.join(ir for ir, at in self.attrs)
        if (3, 1) <= _version:
            attrs |= Attribute.NonLazyBind_buggy
            irs += ' nonlazybind'
        if (3, 1) <= _version <= (3, 2):
            irs += ' address_safety'
        if (3, 2) <= _version:
            irs += ' minsize'
        if (3, 4) <= _version:
            irs += ' builtin cold optnone'
        if (3, 3) <= _version:
            irs += ' nobuiltin noduplicate returned sspstrong'
            irs = ' '.join(sorted(irs.split(' ')))
            irs = irs.replace('uwtable', 'sanitize_address sanitize_thread sanitize_memory uwtable')
        if (3, 4) <= _version:
            irs = irs.replace('optnone optsize', 'optsize optnone')
        if (3, 5) <= _version:
            irs = irs.replace('builtin cold', 'builtin inalloca cold')
            irs = irs.replace('inlinehint minsize', 'inlinehint jumptable minsize')
            irs = irs.replace('nonlazybind noredzone', 'nonlazybind nonnull noredzone')
        attrs |= Attribute.StackAlignment
        irs += ' alignstack(64)'
        f = self.func_decl
        f.AddAttr(attrs)
        if _version <= (3, 2):
            self.assertDump(f,
'''
declare i32 @func_decl() %s

''' % irs)
        if (3, 3) <= _version:
            self.assertDump(f,
'''
; Function Attrs: %s
declare i32 @func_decl() #0

''' % irs)

    def test_attr_stackalign(self):
        Attribute = llpy.core.Attribute
        f = self.func_decl
        for i in range(1, 8):
            n = 1 << (i - 1)
            x = i << 26
            at = Attribute(x)
            f.AddAttr(at)
            assert f.GetAttr() == at
            if _version <= (3, 2):
                self.assertDump(f,
'''
declare i32 @func_decl() alignstack(%d)

''' % n)
            if (3, 3) <= _version:
                self.assertDump(f,
'''
; Function Attrs: alignstack(%d)
declare i32 @func_decl() #0

''' % n)
            f.RemoveAttr(at)

    def test_order(self):
        f = self.func_decl
        f.AddAttr(llpy.core.Attribute.NoReturn)
        f.SetAlignment(1)
        f.SetCallConv(llpy.core.CallConv.Fast)
        f.SetGC('gc')
        f.SetLinkage(llpy.core.Linkage.Private)
        f.SetSection('section')
        f.SetVisibility(llpy.core.Visibility.Hidden)
        if (3, 5) <= _version:
            f.SetDLLStorageClass(llpy.core.DLLStorageClass.DLLImport)
            f.SetUnnamedAddr(True)
        if _version <= (3, 2):
            self.assertDump(self.func_decl,
'''
declare private hidden fastcc i32 @func_decl() noreturn section "section" align 1 gc "gc"

''')
        if (3, 3) <= _version <= (3, 4):
            self.assertDump(self.func_decl,
'''
; Function Attrs: noreturn
declare private hidden fastcc i32 @func_decl() #0 section "section" align 1 gc "gc"

''')
        if (3, 5) <= _version:
            self.assertDump(self.func_decl,
'''
; Function Attrs: noreturn
declare private hidden dllimport fastcc i32 @func_decl() unnamed_addr #0 section "section" align 1 gc "gc"

''')

    def test_verify(self):
        i32 = self.i32
        i8 = llpy.core.IntegerType(self.ctx, 8)
        i8p = llpy.core.PointerType(i8)
        printf_type = llpy.core.FunctionType(i32, [i8p], True)
        printf = self.mod.AddFunction(printf_type, 'printf')
        bb = printf.AppendBasicBlock()
        irb = llpy.core.IRBuilder(self.ctx)
        irb.PositionBuilderAtEnd(bb)
        irb.BuildRet(i32.ConstNull())
        printf.Verify(llpy.core.VerifierFailureAction.ReturnStatus)
        printf.SetCallConv(llpy.core.CallConv.Fast)
        with self.assertRaises(OSError):
            printf.Verify(llpy.core.VerifierFailureAction.ReturnStatus)

    @unittest.expectedFailure
    def test_GetIntrinsicID(self):
        raise NotImplementedError


class TestGlobalAlias(DumpTestCase):

    def setUp(self):
        self.ctx = llpy.core.Context()
        self.mod = llpy.core.Module(self.ctx, 'TestGlobalAlias')
        self.i32 = llpy.core.IntegerType(self.ctx, 32)
        func_type = llpy.core.FunctionType(self.i32, [])
        self.func = self.mod.AddFunction(func_type, 'func')
        self.var = self.mod.AddGlobal(self.i32, 'var')

    def tearDown(self):
        del self.var
        del self.func
        del self.i32
        del self.mod
        del self.ctx
        gc.collect()

    def test_decl(self):
        a = self.mod.AddAlias(self.func, 'func_alias')
        assert not a.IsDeclaration()
        self.assertDump(a, '@func_alias = alias i32 ()* @func\n\n')
        a = self.mod.AddAlias(self.var, 'var_alias')
        assert not a.IsDeclaration()
        self.assertDump(a, '@var_alias = alias i32* @var\n\n')
        i8p = llpy.core.PointerType(llpy.core.IntegerType(self.ctx, 8))
        a = self.mod.AddAlias(self.var.ConstBitCast(i8p), 'bitcast_alias')
        assert not a.IsDeclaration()
        self.assertDump(a, '@bitcast_alias = alias bitcast (i32* @var to i8*)\n\n')
        self.assertDump(self.mod,
'''; ModuleID = 'TestGlobalAlias'

@var = external global i32

@func_alias = alias i32 ()* @func
@var_alias = alias i32* @var
@bitcast_alias = alias bitcast (i32* @var to i8*)

declare i32 @func()
''')

    def test_linkage(self):
        Linkage = llpy.core.Linkage
        a = self.mod.AddAlias(self.func, 'func_alias')
        assert a.GetLinkage() == Linkage.External
        a.SetLinkage(Linkage.Private)
        assert a.GetLinkage() == Linkage.Private
        self.assertDump(a, '@func_alias = alias private i32 ()* @func\n\n')
        a = self.mod.AddAlias(self.var, 'var_alias')
        assert a.GetLinkage() == Linkage.External
        a.SetLinkage(Linkage.Private)
        assert a.GetLinkage() == Linkage.Private
        self.assertDump(a, '@var_alias = alias private i32* @var\n\n')
        self.assertDump(self.mod,
'''; ModuleID = 'TestGlobalAlias'

@var = external global i32

@func_alias = alias private i32 ()* @func
@var_alias = alias private i32* @var

declare i32 @func()
''')

    def test_section(self):
        # aliases have, but ignore, a section
        a = self.mod.AddAlias(self.func, 'func_alias')
        assert a.GetSection() == ''
        self.func.SetSection('foo')
        assert a.GetSection() == 'foo'
        self.assertDump(a, '@func_alias = alias i32 ()* @func\n\n')
        a = self.mod.AddAlias(self.var, 'var_alias')
        assert a.GetSection() == ''
        self.var.SetSection('foo')
        assert a.GetSection() == 'foo'
        self.assertDump(a, '@var_alias = alias i32* @var\n\n')
        self.assertDump(self.mod,
'''; ModuleID = 'TestGlobalAlias'

@var = external global i32, section "foo"

@func_alias = alias i32 ()* @func
@var_alias = alias i32* @var

declare i32 @func() section "foo"
''')

    def test_visibility(self):
        Visibility = llpy.core.Visibility
        a = self.mod.AddAlias(self.func, 'func_alias')
        assert a.GetVisibility() == Visibility.Default
        a.SetVisibility(Visibility.Hidden)
        assert a.GetVisibility() == Visibility.Hidden
        self.assertDump(a, '@func_alias = hidden alias i32 ()* @func\n\n')
        a = self.mod.AddAlias(self.var, 'var_alias')
        assert a.GetVisibility() == Visibility.Default
        a.SetVisibility(Visibility.Hidden)
        assert a.GetVisibility() == Visibility.Hidden
        self.assertDump(a, '@var_alias = hidden alias i32* @var\n\n')
        self.assertDump(self.mod,
'''; ModuleID = 'TestGlobalAlias'

@var = external global i32

@func_alias = hidden alias i32 ()* @func
@var_alias = hidden alias i32* @var

declare i32 @func()
''')

    def test_alignment(self):
        # aliases have, but ignore, an alignment
        a = self.mod.AddAlias(self.func, 'func_alias')
        assert a.GetAlignment() == 0
        self.func.SetAlignment(1)
        assert a.GetAlignment() == 1
        self.assertDump(a, '@func_alias = alias i32 ()* @func\n\n')
        a = self.mod.AddAlias(self.var, 'var_alias')
        assert a.GetAlignment() == 0
        self.var.SetAlignment(1)
        assert a.GetAlignment() == 1
        self.assertDump(a, '@var_alias = alias i32* @var\n\n')
        self.assertDump(self.mod,
'''; ModuleID = 'TestGlobalAlias'

@var = external global i32, align 1

@func_alias = alias i32 ()* @func
@var_alias = alias i32* @var

declare i32 @func() align 1
''')


class TestGlobalVariable(DumpTestCase):

    def setUp(self):
        self.ctx = llpy.core.Context()
        self.mod = llpy.core.Module(self.ctx, 'TestGlobalVariable')
        self.i32 = llpy.core.IntegerType(self.ctx, 32)
        self.ext = self.mod.AddGlobal(self.i32, 'ext')
        self.ini = self.mod.AddGlobal(self.i32, 'ini')
        self.ini.SetInitializer(self.i32.ConstInt(42))

    def tearDown(self):
        del self.ext
        del self.ini
        del self.i32
        del self.mod
        del self.ctx
        gc.collect()

    def test_order(self):
        if (3, 3) <= _version:
            self.ext.SetExternallyInitialized(True)
            self.ini.SetExternallyInitialized(True)
        self.ext.SetThreadLocal(True)
        self.ini.SetThreadLocal(True)
        self.ext.SetConstant(True)
        self.ini.SetConstant(True)
        self.ext.SetLinkage(llpy.core.Linkage.Private)
        self.ini.SetLinkage(llpy.core.Linkage.Private)
        self.ext.SetSection('foo')
        self.ini.SetSection('foo')
        self.ext.SetVisibility(llpy.core.Visibility.Hidden)
        self.ini.SetVisibility(llpy.core.Visibility.Hidden)
        self.ext.SetAlignment(1)
        self.ini.SetAlignment(1)
        if (3, 5) <= _version:
            self.ext.SetDLLStorageClass(llpy.core.DLLStorageClass.DLLImport)
            self.ini.SetDLLStorageClass(llpy.core.DLLStorageClass.DLLExport)
            self.ext.SetUnnamedAddr(True)
            self.ini.SetUnnamedAddr(True)
        if _version <= (3, 2):
            self.assertDump(self.ext, '@ext = private hidden thread_local constant i32, section "foo", align 1\n')
            self.assertDump(self.ini, '@ini = private hidden thread_local constant i32 42, section "foo", align 1\n')
            self.ext.SetLinkage(llpy.core.Linkage.External)
            self.ini.SetLinkage(llpy.core.Linkage.External)
            self.assertDump(self.ext, '@ext = external hidden thread_local constant i32, section "foo", align 1\n')
            self.assertDump(self.ini, '@ini = hidden thread_local constant i32 42, section "foo", align 1\n')
        if (3, 3) <= _version <= (3, 4):
            self.assertDump(self.ext, '@ext = private hidden thread_local externally_initialized constant i32, section "foo", align 1\n')
            self.assertDump(self.ini, '@ini = private hidden thread_local externally_initialized constant i32 42, section "foo", align 1\n')
            self.ext.SetLinkage(llpy.core.Linkage.External)
            self.ini.SetLinkage(llpy.core.Linkage.External)
            self.assertDump(self.ext, '@ext = external hidden thread_local externally_initialized constant i32, section "foo", align 1\n')
            self.assertDump(self.ini, '@ini = hidden thread_local externally_initialized constant i32 42, section "foo", align 1\n')
        if (3, 5) <= _version:
            self.assertDump(self.ext, '@ext = private hidden dllimport thread_local unnamed_addr externally_initialized constant i32, section "foo", align 1\n')
            self.assertDump(self.ini, '@ini = private hidden dllexport thread_local unnamed_addr externally_initialized constant i32 42, section "foo", align 1\n')
            self.ext.SetLinkage(llpy.core.Linkage.External)
            self.ini.SetLinkage(llpy.core.Linkage.External)
            self.assertDump(self.ext, '@ext = external hidden dllimport thread_local unnamed_addr externally_initialized constant i32, section "foo", align 1\n')
            self.assertDump(self.ini, '@ini = hidden dllexport thread_local unnamed_addr externally_initialized constant i32 42, section "foo", align 1\n')

    def test_decl(self):
        assert self.ext.IsDeclaration()
        assert self.ext.GetInitializer() is None
        self.assertDump(self.ext, '@ext = external global i32\n')
        assert not self.ini.IsDeclaration()
        assert self.ini.GetInitializer() is self.i32.ConstInt(42)
        self.assertDump(self.ini, '@ini = global i32 42\n')
        self.assertDump(self.mod,
'''; ModuleID = 'TestGlobalVariable'

@ext = external global i32
@ini = global i32 42
''')
        if (3, 3) <= _version:
            assert not self.ext.IsExternallyInitialized()
            assert not self.ini.IsExternallyInitialized()
            self.ext.SetExternallyInitialized(True)
            self.ini.SetExternallyInitialized(True)
            self.assertDump(self.ext, '@ext = external externally_initialized global i32\n')
            self.assertDump(self.ini, '@ini = externally_initialized global i32 42\n')
            self.assertDump(self.mod,
'''; ModuleID = 'TestGlobalVariable'

@ext = external externally_initialized global i32
@ini = externally_initialized global i32 42
''')
            self.ext.SetExternallyInitialized(False)
            self.ini.SetExternallyInitialized(False)
        self.ini.SetInitializer(None)
        self.assertDump(self.ini, '@ini = external global i32\n')

    def test_threadlocal(self):
        if (3, 3) <= _version:
            ThreadLocalMode = llpy.core.ThreadLocalMode
        assert not self.ext.IsThreadLocal()
        if (3, 3) <= _version:
            assert self.ext.GetThreadLocalMode() == ThreadLocalMode.NotThreadLocal
            # bool checks
            assert not self.ext.GetThreadLocalMode()
        self.ext.SetThreadLocal(True)
        self.assertDump(self.ext, '@ext = external thread_local global i32\n')
        assert not self.ini.IsThreadLocal()
        if (3, 3) <= _version:
            assert self.ini.GetThreadLocalMode() == ThreadLocalMode.NotThreadLocal
            # bool checks
            assert not self.ini.GetThreadLocalMode()
        self.ini.SetThreadLocal(True)
        self.assertDump(self.ini, '@ini = thread_local global i32 42\n')
        self.assertDump(self.mod,
'''; ModuleID = 'TestGlobalVariable'

@ext = external thread_local global i32
@ini = thread_local global i32 42
''')
        if (3, 3) <= _version:
            assert self.ext.GetThreadLocalMode() == ThreadLocalMode.GeneralDynamic
            assert self.ini.GetThreadLocalMode() == ThreadLocalMode.GeneralDynamic
            # bool checks
            assert self.ext.GetThreadLocalMode()
            assert self.ini.GetThreadLocalMode()

            self.ext.SetThreadLocalMode(ThreadLocalMode.NotThreadLocal)
            self.ini.SetThreadLocalMode(ThreadLocalMode.NotThreadLocal)
            assert self.ext.GetThreadLocalMode() == ThreadLocalMode.NotThreadLocal
            assert self.ini.GetThreadLocalMode() == ThreadLocalMode.NotThreadLocal
            assert not self.ext.IsThreadLocal()
            assert not self.ini.IsThreadLocal()
            self.assertDump(self.mod,
'''; ModuleID = 'TestGlobalVariable'

@ext = external global i32
@ini = global i32 42
''')

            self.ext.SetThreadLocalMode(ThreadLocalMode.GeneralDynamic)
            self.ini.SetThreadLocalMode(ThreadLocalMode.GeneralDynamic)
            assert self.ext.GetThreadLocalMode() == ThreadLocalMode.GeneralDynamic
            assert self.ini.GetThreadLocalMode() == ThreadLocalMode.GeneralDynamic
            assert self.ext.IsThreadLocal()
            assert self.ini.IsThreadLocal()
            self.assertDump(self.mod,
'''; ModuleID = 'TestGlobalVariable'

@ext = external thread_local global i32
@ini = thread_local global i32 42
''')

            self.ext.SetThreadLocalMode(ThreadLocalMode.LocalDynamic)
            self.ini.SetThreadLocalMode(ThreadLocalMode.LocalDynamic)
            assert self.ext.GetThreadLocalMode() == ThreadLocalMode.LocalDynamic
            assert self.ini.GetThreadLocalMode() == ThreadLocalMode.LocalDynamic
            assert self.ext.IsThreadLocal()
            assert self.ini.IsThreadLocal()
            self.assertDump(self.mod,
'''; ModuleID = 'TestGlobalVariable'

@ext = external thread_local(localdynamic) global i32
@ini = thread_local(localdynamic) global i32 42
''')

            self.ext.SetThreadLocalMode(ThreadLocalMode.InitialExec)
            self.ini.SetThreadLocalMode(ThreadLocalMode.InitialExec)
            assert self.ext.GetThreadLocalMode() == ThreadLocalMode.InitialExec
            assert self.ini.GetThreadLocalMode() == ThreadLocalMode.InitialExec
            assert self.ext.IsThreadLocal()
            assert self.ini.IsThreadLocal()
            self.assertDump(self.mod,
'''; ModuleID = 'TestGlobalVariable'

@ext = external thread_local(initialexec) global i32
@ini = thread_local(initialexec) global i32 42
''')

            self.ext.SetThreadLocalMode(ThreadLocalMode.LocalExec)
            self.ini.SetThreadLocalMode(ThreadLocalMode.LocalExec)
            assert self.ext.GetThreadLocalMode() == ThreadLocalMode.LocalExec
            assert self.ini.GetThreadLocalMode() == ThreadLocalMode.LocalExec
            assert self.ext.IsThreadLocal()
            assert self.ini.IsThreadLocal()
            self.assertDump(self.mod,
'''; ModuleID = 'TestGlobalVariable'

@ext = external thread_local(localexec) global i32
@ini = thread_local(localexec) global i32 42
''')

    def test_constant(self):
        assert not self.ext.IsConstant()
        self.ext.SetConstant(True)
        self.assertDump(self.ext, '@ext = external constant i32\n')
        assert self.ext.IsConstant()
        assert not self.ini.IsConstant()
        self.ini.SetConstant(True)
        assert self.ini.IsConstant()
        self.assertDump(self.ini, '@ini = constant i32 42\n')
        self.assertDump(self.mod,
'''; ModuleID = 'TestGlobalVariable'

@ext = external constant i32
@ini = constant i32 42
''')

    def test_linkage(self):
        Linkage = llpy.core.Linkage
        assert self.ext.GetLinkage() == Linkage.External
        self.ext.SetLinkage(Linkage.Private)
        assert self.ext.GetLinkage() == Linkage.Private
        self.assertDump(self.ext, '@ext = private global i32\n')
        assert self.ini.GetLinkage() == Linkage.External
        self.ini.SetLinkage(Linkage.Private)
        assert self.ini.GetLinkage() == Linkage.Private
        self.assertDump(self.ini, '@ini = private global i32 42\n')
        self.assertDump(self.mod,
'''; ModuleID = 'TestGlobalVariable'

@ext = private global i32
@ini = private global i32 42
''')

    def test_section(self):
        assert self.ext.GetSection() == ''
        self.ext.SetSection('foo')
        assert self.ext.GetSection() == 'foo'
        self.assertDump(self.ext, '@ext = external global i32, section "foo"\n')
        assert self.ini.GetSection() == ''
        self.ini.SetSection('foo')
        assert self.ini.GetSection() == 'foo'
        self.assertDump(self.ini, '@ini = global i32 42, section "foo"\n')
        self.assertDump(self.mod,
'''; ModuleID = 'TestGlobalVariable'

@ext = external global i32, section "foo"
@ini = global i32 42, section "foo"
''')

    def test_visibility(self):
        Visibility = llpy.core.Visibility
        assert self.ext.GetVisibility() == Visibility.Default
        self.ext.SetVisibility(Visibility.Hidden)
        assert self.ext.GetVisibility() == Visibility.Hidden
        self.assertDump(self.ext, '@ext = external hidden global i32\n')
        assert self.ini.GetVisibility() == Visibility.Default
        self.ini.SetVisibility(Visibility.Hidden)
        assert self.ini.GetVisibility() == Visibility.Hidden
        self.assertDump(self.ini, '@ini = hidden global i32 42\n')
        self.assertDump(self.mod,
'''; ModuleID = 'TestGlobalVariable'

@ext = external hidden global i32
@ini = hidden global i32 42
''')

    def test_alignment(self):
        assert self.ext.GetAlignment() == 0
        self.ext.SetAlignment(1)
        assert self.ext.GetAlignment() == 1
        self.assertDump(self.ext, '@ext = external global i32, align 1\n')
        assert self.ini.GetAlignment() == 0
        self.ini.SetAlignment(1)
        assert self.ini.GetAlignment() == 1
        self.assertDump(self.ini, '@ini = global i32 42, align 1\n')
        self.assertDump(self.mod,
'''; ModuleID = 'TestGlobalVariable'

@ext = external global i32, align 1
@ini = global i32 42, align 1
''')

    if (3, 5) <= _version:
        def test_dll_storage_class(self):
            DLLStorageClass = llpy.core.DLLStorageClass
            assert self.ext.GetDLLStorageClass() == DLLStorageClass.Default
            self.ext.SetDLLStorageClass(DLLStorageClass.DLLImport)
            assert self.ext.GetDLLStorageClass() == DLLStorageClass.DLLImport
            self.assertDump(self.ext, '@ext = external dllimport global i32\n')
            assert self.ini.GetDLLStorageClass() == DLLStorageClass.Default
            self.ini.SetDLLStorageClass(DLLStorageClass.DLLExport)
            assert self.ini.GetDLLStorageClass() == DLLStorageClass.DLLExport
            self.assertDump(self.ini, '@ini = dllexport global i32 42\n')
            self.assertDump(self.mod,
'''; ModuleID = 'TestGlobalVariable'

@ext = external dllimport global i32
@ini = dllexport global i32 42
''')

        def test_unnamed_addr(self):
            assert self.ext.HasUnnamedAddr() == False
            self.ext.SetUnnamedAddr(True)
            assert self.ext.HasUnnamedAddr() == True
            self.assertDump(self.ext, '@ext = external unnamed_addr global i32\n')
            assert self.ini.HasUnnamedAddr() == False
            self.ini.SetUnnamedAddr(True)
            assert self.ini.HasUnnamedAddr() == True
            self.assertDump(self.ini, '@ini = unnamed_addr global i32 42\n')
            self.assertDump(self.mod,
'''; ModuleID = 'TestGlobalVariable'

@ext = external unnamed_addr global i32
@ini = unnamed_addr global i32 42
''')


class TestInstruction(DumpTestCase):

    def setUp(self):
        pass

    def tearDown(self):
        gc.collect()

    @unittest.expectedFailure
    def test_metadata(self):
        raise NotImplementedError


class TestAnyCallOrInvoke(DumpTestCase):

    def setUp(self):
        pass

    def tearDown(self):
        gc.collect()

    @unittest.expectedFailure
    def test_cc(self):
        raise NotImplementedError

    @unittest.expectedFailure
    def test_attr(self):
        raise NotImplementedError

    @unittest.expectedFailure
    def test_align(self):
        raise NotImplementedError


class TestCallInst(DumpTestCase):

    def setUp(self):
        pass

    def tearDown(self):
        gc.collect()

    @unittest.expectedFailure
    def test_tail(self):
        raise NotImplementedError


class TestUse(DumpTestCase):

    def setUp(self):
        pass

    def tearDown(self):
        gc.collect()

    def test_use(self):
        ctx = llpy.core.Context()
        mod = llpy.core.Module(ctx, 'TestUse')
        i32 = llpy.core.IntegerType(ctx, 32)
        func_type = llpy.core.FunctionType(i32, [i32, i32])
        func = mod.AddFunction(func_type, 'func')
        arg = func.GetParam(0)
        arg.SetValueName('arg')
        brg = func.GetParam(1)
        brg.SetValueName('brg')
        bb = func.AppendBasicBlock()
        builder = llpy.core.IRBuilder(ctx)
        builder.PositionBuilderAtEnd(bb)

        a = builder.BuildAdd(arg, arg, 'a')
        b = builder.BuildMul(arg, arg, 'b')
        r = builder.BuildRet(arg)


        u = arg.GetFirstUse()
        assert u.GetUsedValue() is arg
        assert u.GetUser() is r

        u = u.GetNextUse()
        assert u.GetUsedValue() is arg
        assert u.GetUser() is b

        u = u.GetNextUse()
        assert u.GetUsedValue() is arg
        assert u.GetUser() is b

        u = u.GetNextUse()
        assert u.GetUsedValue() is arg
        assert u.GetUser() is a

        u = u.GetNextUse()
        assert u.GetUsedValue() is arg
        assert u.GetUser() is a

        assert brg.GetFirstUse() is None

        self.assertDump(func,
'''
define i32 @func(i32 %arg, i32 %brg) {
  %a = add i32 %arg, %arg
  %b = mul i32 %arg, %arg
  ret i32 %arg
}

''')


        arg.ReplaceAllUsesWith(brg)

        u = brg.GetFirstUse()
        assert u.GetUsedValue() is brg
        assert u.GetUser() is a

        u = u.GetNextUse()
        assert u.GetUsedValue() is brg
        assert u.GetUser() is a

        u = u.GetNextUse()
        assert u.GetUsedValue() is brg
        assert u.GetUser() is b

        u = u.GetNextUse()
        assert u.GetUsedValue() is brg
        assert u.GetUser() is b

        u = u.GetNextUse()
        assert u.GetUsedValue() is brg
        assert u.GetUser() is r

        assert arg.GetFirstUse() is None


        self.assertDump(func,
'''
define i32 @func(i32 %arg, i32 %brg) {
  %a = add i32 %brg, %brg
  %b = mul i32 %brg, %brg
  ret i32 %brg
}

''')

if __name__ == '__main__':
    unittest.main()
