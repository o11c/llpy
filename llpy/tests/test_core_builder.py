#!/usr/bin/env python3
from __future__ import unicode_literals

import gc
from itertools import product
import unittest

import llpy.core
from llpy.c.core import _version

from .test_core_misc import DumpTestCase


class TestBuilder(DumpTestCase):

    def setUp(self):
        self.ctx = llpy.core.Context()
        self.mod = llpy.core.Module(self.ctx, 'TestBuilder')
        self.builder = llpy.core.IRBuilder(self.ctx)

    def tearDown(self):
        del self.builder
        del self.mod
        del self.ctx
        gc.collect()

    def test_position(self):
        builder = self.builder
        void = llpy.core.VoidType(self.ctx)
        func_type = llpy.core.FunctionType(void, [])
        func = self.mod.AddFunction(func_type, 'func')
        bb = func.AppendBasicBlock()

        assert builder.GetInsertBlock() is None
        builder.PositionBuilderAtEnd(bb)
        assert bb is builder.GetInsertBlock()
        builder.ClearInsertionPosition()
        assert builder.GetInsertBlock() is None

    @unittest.expectedFailure
    # TODO merge with the previous
    # should use GetNextInstruction/GetPreviousInstruction
    def test_position2(self):
        raise NotImplementedError
        # builder.PositionBuilder(block, instr)
        # builder.PositionBuilderBefore(instr)

    @unittest.expectedFailure
    # I haven't managed to make this not crash yet.
    # Is it even possible for the C API to add unowned instructions?
    # I think it happens when you use a builder with a cleared position.
    # Also maybe .SizeOf() ?
    def test_insert(self):
        raise NotImplementedError
        builder = self.builder
        # builder.InsertIntoBuilder(instr)
        # builder.InsertIntoBuilder(instr, name)

    @unittest.expectedFailure
    # I haven't figured out what these do.
    def test_debuglocation(self):
        raise NotImplementedError
        builder = self.builder
        # builder.SetCurrentDebugLocation(l)
        # builder.GetCurrentDebugLocation()
        # builder.SetInstDebugLocation(inst)

    # Terminators
    def test_BuildRetVoid(self):
        builder = self.builder
        void = llpy.core.VoidType(self.ctx)
        func_type = llpy.core.FunctionType(void, [])
        func = self.mod.AddFunction(func_type, 'func')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        instr = builder.BuildRetVoid()
        assert isinstance(instr, llpy.core.ReturnInst)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.Ret
        assert instr.TypeOf() is void

        assert instr.GetNumOperands() == 0

        self.assertDump(func,
'''
define void @func() {
  ret void
}

''')

    def test_BuildRet(self):
        builder = self.builder
        void = llpy.core.VoidType(self.ctx)
        i32 = llpy.core.IntegerType(self.ctx, 32)
        func_type = llpy.core.FunctionType(i32, [])
        func = self.mod.AddFunction(func_type, 'func')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        instr = builder.BuildRet(i32.ConstNull())
        assert isinstance(instr, llpy.core.ReturnInst)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.Ret
        assert instr.TypeOf() is void

        assert instr.GetNumOperands() == 1
        assert instr.GetOperand(0) is i32.ConstNull()

        self.assertDump(func,
'''
define i32 @func() {
  ret i32 0
}

''')
        instr.SetOperand(0, i32.ConstAllOnes())
        assert instr.GetOperand(0) is i32.ConstAllOnes()
        self.assertDump(func,
'''
define i32 @func() {
  ret i32 -1
}

''')

    def test_BuildAggregateRet_arr(self):
        builder = self.builder
        void = llpy.core.VoidType(self.ctx)
        i32 = llpy.core.IntegerType(self.ctx, 32)
        rt = llpy.core.ArrayType(i32, 2)
        func_type = llpy.core.FunctionType(rt, [i32])
        func = self.mod.AddFunction(func_type, 'func')
        arg = func.GetParam(0)
        arg.SetValueName('arg')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        args = [arg, arg]

        instr = builder.BuildAggregateRet(args)
        assert isinstance(instr, llpy.core.ReturnInst)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.Ret
        assert instr.TypeOf() is void

        assert instr.GetNumOperands() == 1
        op0 = instr.GetOperand(0)
        assert op0.TypeOf() is rt

        self.assertDump(func,
'''
define [2 x i32] @func(i32 %arg) {
  %mrv = insertvalue [2 x i32] undef, i32 %arg, 0
  %mrv1 = insertvalue [2 x i32] %mrv, i32 %arg, 1
  ret [2 x i32] %mrv1
}

''')

    def test_BuildAggregateRet_str(self):
        builder = self.builder
        void = llpy.core.VoidType(self.ctx)
        i32 = llpy.core.IntegerType(self.ctx, 32)
        rt = llpy.core.StructType(self.ctx, [i32, i32], None)
        func_type = llpy.core.FunctionType(rt, [i32])
        func = self.mod.AddFunction(func_type, 'func')
        arg = func.GetParam(0)
        arg.SetValueName('arg')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        args = [arg, arg]

        instr = builder.BuildAggregateRet(args)
        assert isinstance(instr, llpy.core.ReturnInst)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.Ret
        assert instr.TypeOf() is void

        assert instr.GetNumOperands() == 1
        op0 = instr.GetOperand(0)
        assert op0.TypeOf() is rt

        self.assertDump(func,
'''
define { i32, i32 } @func(i32 %arg) {
  %mrv = insertvalue { i32, i32 } undef, i32 %arg, 0
  %mrv1 = insertvalue { i32, i32 } %mrv, i32 %arg, 1
  ret { i32, i32 } %mrv1
}

''')

    def test_BuildAggregateRet_arr_c(self):
        builder = self.builder
        void = llpy.core.VoidType(self.ctx)
        i32 = llpy.core.IntegerType(self.ctx, 32)
        rt = llpy.core.ArrayType(i32, 2)
        func_type = llpy.core.FunctionType(rt, [])
        func = self.mod.AddFunction(func_type, 'func')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        args = [i32.ConstAllOnes(), i32.ConstNull()]

        instr = builder.BuildAggregateRet(args)
        assert isinstance(instr, llpy.core.ReturnInst)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.Ret
        assert instr.TypeOf() is void

        assert instr.GetNumOperands() == 1
        op0 = instr.GetOperand(0)
        assert op0.TypeOf() is rt

        self.assertDump(func,
'''
define [2 x i32] @func() {
  ret [2 x i32] [i32 -1, i32 0]
}

''')

    def test_BuildAggregateRet_str_c(self):
        builder = self.builder
        void = llpy.core.VoidType(self.ctx)
        i32 = llpy.core.IntegerType(self.ctx, 32)
        rt = llpy.core.StructType(self.ctx, [i32, i32], None)
        func_type = llpy.core.FunctionType(rt, [])
        func = self.mod.AddFunction(func_type, 'func')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        args = [i32.ConstAllOnes(), i32.ConstNull()]

        instr = builder.BuildAggregateRet(args)
        assert isinstance(instr, llpy.core.ReturnInst)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.Ret
        assert instr.TypeOf() is void

        assert instr.GetNumOperands() == 1
        op0 = instr.GetOperand(0)
        assert op0.TypeOf() is rt

        self.assertDump(func,
'''
define { i32, i32 } @func() {
  ret { i32, i32 } { i32 -1, i32 0 }
}

''')

    def test_BuildBr(self):
        builder = self.builder
        void = llpy.core.VoidType(self.ctx)
        func_type = llpy.core.FunctionType(void, [])
        func = self.mod.AddFunction(func_type, 'func')
        bb = func.AppendBasicBlock('entry')
        bb_exit = func.AppendBasicBlock('exit')
        builder.PositionBuilderAtEnd(bb_exit)
        builder.BuildRetVoid()
        builder.PositionBuilderAtEnd(bb)

        instr = builder.BuildBr(bb_exit)
        assert isinstance(instr, llpy.core.BranchInst)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.Br
        assert instr.TypeOf() is void

        assert instr.GetNumOperands() == 1
        assert instr.GetOperand(0) is bb_exit

        self.assertDump(func,
'''
define void @func() {
entry:
  br label %exit

exit:                                             ; preds = %entry
  ret void
}

''')

    def test_BuildCondBr(self):
        builder = self.builder
        void = llpy.core.VoidType(self.ctx)
        i1 = llpy.core.IntegerType(self.ctx, 1)
        func_type = llpy.core.FunctionType(i1, [i1])
        func = self.mod.AddFunction(func_type, 'func')
        arg = func.GetParam(0)
        arg.SetValueName('arg')
        bb = func.AppendBasicBlock('entry')
        bb_true = func.AppendBasicBlock('true')
        bb_false = func.AppendBasicBlock('false')
        builder.PositionBuilderAtEnd(bb_true)
        builder.BuildRet(i1.ConstAllOnes())
        builder.PositionBuilderAtEnd(bb_false)
        builder.BuildRet(i1.ConstNull())
        builder.PositionBuilderAtEnd(bb)

        instr = builder.BuildCondBr(arg, bb_true, bb_false)
        assert isinstance(instr, llpy.core.BranchInst)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.Br
        assert instr.TypeOf() is void

        assert instr.GetNumOperands() == 3
        assert instr.GetOperand(0) is arg
        assert instr.GetOperand(1) is bb_false
        assert instr.GetOperand(2) is bb_true

        self.assertDump(func,
'''
define i1 @func(i1 %arg) {
entry:
  br i1 %arg, label %true, label %false

true:                                             ; preds = %entry
  ret i1 true

false:                                            ; preds = %entry
  ret i1 false
}

''')

    def test_BuildSwitch(self):
        builder = self.builder
        void = llpy.core.VoidType(self.ctx)
        i1 = llpy.core.IntegerType(self.ctx, 1)
        func_type = llpy.core.FunctionType(i1, [i1])
        func = self.mod.AddFunction(func_type, 'func')
        arg = func.GetParam(0)
        arg.SetValueName('arg')
        bb = func.AppendBasicBlock('entry')
        bb_true = func.AppendBasicBlock('true')
        bb_false = func.AppendBasicBlock('false')
        bb_other = func.AppendBasicBlock('other')
        builder.PositionBuilderAtEnd(bb_true)
        builder.BuildRet(i1.ConstAllOnes())
        builder.PositionBuilderAtEnd(bb_false)
        builder.BuildRet(i1.ConstNull())
        builder.PositionBuilderAtEnd(bb_other)
        builder.BuildUnreachable()
        builder.PositionBuilderAtEnd(bb)

        instr = builder.BuildSwitch(arg, bb_other, 2)
        assert isinstance(instr, llpy.core.SwitchInst)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.Switch
        assert instr.TypeOf() is void

        assert instr.GetNumOperands() == 2
        assert instr.GetOperand(0) is arg
        assert instr.GetOperand(1) is bb_other
        assert instr.GetSwitchDefaultDest() is bb_other

        instr.AddCase(i1.ConstNull(), bb_false)
        instr.AddCase(i1.ConstAllOnes(), bb_true)

        assert instr.GetNumOperands() == 6
        # wtf?
        assert instr.GetOperand(0) is arg
        assert instr.GetOperand(1) is bb_other
        if _version <= (3, 1):
            assert instr.GetOperand(2) is i1.ConstNull()
        if (3, 2) <= _version:
            if _version <= (3, 3):
                v = llpy.core.ConstVector([i1.ConstNull(), i1.ConstNull()])
                arrv = v.TypeOf().ConstArray([v])
                assert instr.GetOperand(2) is arrv
            if (3, 4) <= _version:
                assert instr.GetOperand(2) is i1.ConstNull()
        assert instr.GetOperand(3) is bb_false
        if _version <= (3, 1):
            assert instr.GetOperand(4) is i1.ConstAllOnes()
        if (3, 2) <= _version:
            if _version <= (3, 3):
                v = llpy.core.ConstVector([i1.ConstAllOnes(), i1.ConstAllOnes()])
                arrv = v.TypeOf().ConstArray([v])
                assert instr.GetOperand(4) is arrv
            if (3, 4) <= _version:
                assert instr.GetOperand(4) is i1.ConstAllOnes()
        assert instr.GetOperand(5) is bb_true

        self.assertDump(func,
'''
define i1 @func(i1 %arg) {
entry:
  switch i1 %arg, label %other [
    i1 false, label %false
    i1 true, label %true
  ]

true:                                             ; preds = %entry
  ret i1 true

false:                                            ; preds = %entry
  ret i1 false

other:                                            ; preds = %entry
  unreachable
}

''')

    def test_BuildIndirectBr(self):
        builder = self.builder
        void = llpy.core.VoidType(self.ctx)
        i1 = llpy.core.IntegerType(self.ctx, 1)
        func_type = llpy.core.FunctionType(i1, [i1])
        func = self.mod.AddFunction(func_type, 'func')
        arg = func.GetParam(0)
        arg.SetValueName('arg')
        bb = func.AppendBasicBlock('entry')
        bb_true = func.AppendBasicBlock('true')
        bb_false = func.AppendBasicBlock('false')
        builder.PositionBuilderAtEnd(bb_true)
        builder.BuildRet(i1.ConstAllOnes())
        builder.PositionBuilderAtEnd(bb_false)
        builder.BuildRet(i1.ConstNull())
        builder.PositionBuilderAtEnd(bb)
        addr = builder.BuildSelect(arg, bb_true, bb_false, 'addr')

        instr = builder.BuildIndirectBr(addr, 2)
        assert isinstance(instr, llpy.core.IndirectBrInst)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.IndirectBr
        assert instr.TypeOf() is void

        assert instr.GetNumOperands() == 1
        assert instr.GetOperand(0) is addr

        instr.AddDestination(bb_true)
        instr.AddDestination(bb_false)

        self.assertDump(func,
'''
define i1 @func(i1 %arg) {
entry:
  %addr = select i1 %arg, label %true, label %false
  indirectbr label %addr, [label %true, label %false]

true:                                             ; preds = %entry
  ret i1 true

false:                                            ; preds = %entry
  ret i1 false
}

''')

    @unittest.expectedFailure
    def test_BuildInvoke(self):
        raise NotImplementedError
        builder = self.builder
        instr = builder.BuildInvoke(fn, args, then, catch, name)

    @unittest.expectedFailure
    def test_BuildLandingPad(self):
        raise NotImplementedError
        builder = self.builder
        instr = builder.BuildLandingPad(ty, persfn, n, name)

    @unittest.expectedFailure
    def test_BuildResume(self):
        raise NotImplementedError
        builder = self.builder
        instr = builder.BuildResume(exn)

    def test_BuildUnreachable(self):
        builder = self.builder
        void = llpy.core.VoidType(self.ctx)
        func_type = llpy.core.FunctionType(void, [])
        func = self.mod.AddFunction(func_type, 'func')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        instr = builder.BuildUnreachable()
        assert isinstance(instr, llpy.core.UnreachableInst)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.Unreachable
        assert instr.TypeOf() is void

        assert instr.GetNumOperands() == 0

        self.assertDump(func,
'''
define void @func() {
  unreachable
}

''')

    # Arithmetic
    def test_BuildAdd(self):
        builder = self.builder
        i32 = llpy.core.IntegerType(self.ctx, 32)
        func_type = llpy.core.FunctionType(i32, [i32, i32])
        func = self.mod.AddFunction(func_type, 'func')
        lhs = func.GetParam(0)
        lhs.SetValueName('lhs')
        rhs = func.GetParam(1)
        rhs.SetValueName('rhs')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        cinstr = builder.BuildAdd(i32.ConstAllOnes(), i32.ConstAllOnes())
        assert isinstance(cinstr, llpy.core.ConstantInt)
        assert cinstr.TypeOf() is i32
        assert cinstr.GetNumOperands() == 0
        assert cinstr.GetSExtValue() == -2

        instr = builder.BuildAdd(lhs, rhs, 'rv')
        assert isinstance(instr, llpy.core.BinaryOperator)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.Add
        assert instr.TypeOf() is i32

        assert instr.GetNumOperands() == 2
        assert instr.GetOperand(0) is lhs
        assert instr.GetOperand(1) is rhs

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define i32 @func(i32 %lhs, i32 %rhs) {
  %rv = add i32 %lhs, %rhs
  ret i32 %rv
}

''')

    def test_BuildNSWAdd(self):
        builder = self.builder
        i32 = llpy.core.IntegerType(self.ctx, 32)
        func_type = llpy.core.FunctionType(i32, [i32, i32])
        func = self.mod.AddFunction(func_type, 'func')
        lhs = func.GetParam(0)
        lhs.SetValueName('lhs')
        rhs = func.GetParam(1)
        rhs.SetValueName('rhs')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        cinstr = builder.BuildNSWAdd(i32.ConstAllOnes(), i32.ConstAllOnes())
        assert isinstance(cinstr, llpy.core.ConstantInt)
        assert cinstr.TypeOf() is i32
        assert cinstr.GetNumOperands() == 0
        assert cinstr.GetSExtValue() == -2

        instr = builder.BuildNSWAdd(lhs, rhs, 'rv')
        assert isinstance(instr, llpy.core.BinaryOperator)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.Add
        assert instr.TypeOf() is i32

        assert instr.GetNumOperands() == 2
        assert instr.GetOperand(0) is lhs
        assert instr.GetOperand(1) is rhs

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define i32 @func(i32 %lhs, i32 %rhs) {
  %rv = add nsw i32 %lhs, %rhs
  ret i32 %rv
}

''')

    def test_BuildNUWAdd(self):
        builder = self.builder
        i32 = llpy.core.IntegerType(self.ctx, 32)
        func_type = llpy.core.FunctionType(i32, [i32, i32])
        func = self.mod.AddFunction(func_type, 'func')
        lhs = func.GetParam(0)
        lhs.SetValueName('lhs')
        rhs = func.GetParam(1)
        rhs.SetValueName('rhs')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        cinstr = builder.BuildNUWAdd(i32.ConstAllOnes(), i32.ConstAllOnes())
        assert isinstance(cinstr, llpy.core.ConstantInt)
        assert cinstr.TypeOf() is i32
        assert cinstr.GetNumOperands() == 0
        assert cinstr.GetSExtValue() == -2

        instr = builder.BuildNUWAdd(lhs, rhs, 'rv')
        assert isinstance(instr, llpy.core.BinaryOperator)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.Add
        assert instr.TypeOf() is i32

        assert instr.GetNumOperands() == 2
        assert instr.GetOperand(0) is lhs
        assert instr.GetOperand(1) is rhs

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define i32 @func(i32 %lhs, i32 %rhs) {
  %rv = add nuw i32 %lhs, %rhs
  ret i32 %rv
}

''')

    def test_BuildFAdd(self):
        builder = self.builder
        double = llpy.core.DoubleType(self.ctx)
        func_type = llpy.core.FunctionType(double, [double, double])
        func = self.mod.AddFunction(func_type, 'func')
        lhs = func.GetParam(0)
        lhs.SetValueName('lhs')
        rhs = func.GetParam(1)
        rhs.SetValueName('rhs')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        cinstr = builder.BuildFAdd(double.ConstReal(-1.0), double.ConstReal(-1.0))
        assert isinstance(cinstr, llpy.core.ConstantFP)
        assert cinstr.TypeOf() is double
        assert cinstr.GetNumOperands() == 0
        assert cinstr is double.ConstReal(-2.0)

        instr = builder.BuildFAdd(lhs, rhs, 'rv')
        assert isinstance(instr, llpy.core.BinaryOperator)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.FAdd
        assert instr.TypeOf() is double

        assert instr.GetNumOperands() == 2
        assert instr.GetOperand(0) is lhs
        assert instr.GetOperand(1) is rhs

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define double @func(double %lhs, double %rhs) {
  %rv = fadd double %lhs, %rhs
  ret double %rv
}

''')

    def test_BuildSub(self):
        builder = self.builder
        i32 = llpy.core.IntegerType(self.ctx, 32)
        func_type = llpy.core.FunctionType(i32, [i32, i32])
        func = self.mod.AddFunction(func_type, 'func')
        lhs = func.GetParam(0)
        lhs.SetValueName('lhs')
        rhs = func.GetParam(1)
        rhs.SetValueName('rhs')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        cinstr = builder.BuildSub(i32.ConstAllOnes(), i32.ConstAllOnes())
        assert isinstance(cinstr, llpy.core.ConstantInt)
        assert cinstr.TypeOf() is i32
        assert cinstr.GetNumOperands() == 0
        assert cinstr.GetSExtValue() == 0

        instr = builder.BuildSub(lhs, rhs, 'rv')
        assert isinstance(instr, llpy.core.BinaryOperator)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.Sub
        assert instr.TypeOf() is i32

        assert instr.GetNumOperands() == 2
        assert instr.GetOperand(0) is lhs
        assert instr.GetOperand(1) is rhs

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define i32 @func(i32 %lhs, i32 %rhs) {
  %rv = sub i32 %lhs, %rhs
  ret i32 %rv
}

''')

    def test_BuildNSWSub(self):
        builder = self.builder
        i32 = llpy.core.IntegerType(self.ctx, 32)
        func_type = llpy.core.FunctionType(i32, [i32, i32])
        func = self.mod.AddFunction(func_type, 'func')
        lhs = func.GetParam(0)
        lhs.SetValueName('lhs')
        rhs = func.GetParam(1)
        rhs.SetValueName('rhs')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        cinstr = builder.BuildNSWSub(i32.ConstAllOnes(), i32.ConstAllOnes())
        assert isinstance(cinstr, llpy.core.ConstantInt)
        assert cinstr.TypeOf() is i32
        assert cinstr.GetNumOperands() == 0
        assert cinstr.GetSExtValue() == 0

        instr = builder.BuildNSWSub(lhs, rhs, 'rv')
        assert isinstance(instr, llpy.core.BinaryOperator)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.Sub
        assert instr.TypeOf() is i32

        assert instr.GetNumOperands() == 2
        assert instr.GetOperand(0) is lhs
        assert instr.GetOperand(1) is rhs

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define i32 @func(i32 %lhs, i32 %rhs) {
  %rv = sub nsw i32 %lhs, %rhs
  ret i32 %rv
}

''')

    def test_BuildNUWSub(self):
        builder = self.builder
        i32 = llpy.core.IntegerType(self.ctx, 32)
        func_type = llpy.core.FunctionType(i32, [i32, i32])
        func = self.mod.AddFunction(func_type, 'func')
        lhs = func.GetParam(0)
        lhs.SetValueName('lhs')
        rhs = func.GetParam(1)
        rhs.SetValueName('rhs')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        cinstr = builder.BuildNUWSub(i32.ConstAllOnes(), i32.ConstAllOnes())
        assert isinstance(cinstr, llpy.core.ConstantInt)
        assert cinstr.TypeOf() is i32
        assert cinstr.GetNumOperands() == 0
        assert cinstr.GetSExtValue() == 0

        instr = builder.BuildNUWSub(lhs, rhs, 'rv')
        assert isinstance(instr, llpy.core.BinaryOperator)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.Sub
        assert instr.TypeOf() is i32

        assert instr.GetNumOperands() == 2
        assert instr.GetOperand(0) is lhs
        assert instr.GetOperand(1) is rhs

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define i32 @func(i32 %lhs, i32 %rhs) {
  %rv = sub nuw i32 %lhs, %rhs
  ret i32 %rv
}

''')

    def test_BuildFSub(self):
        builder = self.builder
        double = llpy.core.DoubleType(self.ctx)
        func_type = llpy.core.FunctionType(double, [double, double])
        func = self.mod.AddFunction(func_type, 'func')
        lhs = func.GetParam(0)
        lhs.SetValueName('lhs')
        rhs = func.GetParam(1)
        rhs.SetValueName('rhs')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        cinstr = builder.BuildFSub(double.ConstReal(-1.0), double.ConstReal(-1.0))
        assert isinstance(cinstr, llpy.core.ConstantFP)
        assert cinstr.TypeOf() is double
        assert cinstr.GetNumOperands() == 0
        assert cinstr is double.ConstReal(0.0)

        instr = builder.BuildFSub(lhs, rhs, 'rv')
        assert isinstance(instr, llpy.core.BinaryOperator)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.FSub
        assert instr.TypeOf() is double

        assert instr.GetNumOperands() == 2
        assert instr.GetOperand(0) is lhs
        assert instr.GetOperand(1) is rhs

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define double @func(double %lhs, double %rhs) {
  %rv = fsub double %lhs, %rhs
  ret double %rv
}

''')

    def test_BuildMul(self):
        builder = self.builder
        i32 = llpy.core.IntegerType(self.ctx, 32)
        func_type = llpy.core.FunctionType(i32, [i32, i32])
        func = self.mod.AddFunction(func_type, 'func')
        lhs = func.GetParam(0)
        lhs.SetValueName('lhs')
        rhs = func.GetParam(1)
        rhs.SetValueName('rhs')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        cinstr = builder.BuildMul(i32.ConstAllOnes(), i32.ConstAllOnes())
        assert isinstance(cinstr, llpy.core.ConstantInt)
        assert cinstr.TypeOf() is i32
        assert cinstr.GetNumOperands() == 0
        assert cinstr.GetSExtValue() == 1

        instr = builder.BuildMul(lhs, rhs, 'rv')
        assert isinstance(instr, llpy.core.BinaryOperator)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.Mul
        assert instr.TypeOf() is i32

        assert instr.GetNumOperands() == 2
        assert instr.GetOperand(0) is lhs
        assert instr.GetOperand(1) is rhs

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define i32 @func(i32 %lhs, i32 %rhs) {
  %rv = mul i32 %lhs, %rhs
  ret i32 %rv
}

''')

    def test_BuildNSWMul(self):
        builder = self.builder
        i32 = llpy.core.IntegerType(self.ctx, 32)
        func_type = llpy.core.FunctionType(i32, [i32, i32])
        func = self.mod.AddFunction(func_type, 'func')
        lhs = func.GetParam(0)
        lhs.SetValueName('lhs')
        rhs = func.GetParam(1)
        rhs.SetValueName('rhs')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        cinstr = builder.BuildNSWMul(i32.ConstAllOnes(), i32.ConstAllOnes())
        assert isinstance(cinstr, llpy.core.ConstantInt)
        assert cinstr.TypeOf() is i32
        assert cinstr.GetNumOperands() == 0
        assert cinstr.GetSExtValue() == 1

        instr = builder.BuildNSWMul(lhs, rhs, 'rv')
        assert isinstance(instr, llpy.core.BinaryOperator)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.Mul
        assert instr.TypeOf() is i32

        assert instr.GetNumOperands() == 2
        assert instr.GetOperand(0) is lhs
        assert instr.GetOperand(1) is rhs

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define i32 @func(i32 %lhs, i32 %rhs) {
  %rv = mul nsw i32 %lhs, %rhs
  ret i32 %rv
}

''')

    def test_BuildNUWMul(self):
        builder = self.builder
        i32 = llpy.core.IntegerType(self.ctx, 32)
        func_type = llpy.core.FunctionType(i32, [i32, i32])
        func = self.mod.AddFunction(func_type, 'func')
        lhs = func.GetParam(0)
        lhs.SetValueName('lhs')
        rhs = func.GetParam(1)
        rhs.SetValueName('rhs')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        cinstr = builder.BuildNUWMul(i32.ConstAllOnes(), i32.ConstAllOnes())
        assert isinstance(cinstr, llpy.core.ConstantInt)
        assert cinstr.TypeOf() is i32
        assert cinstr.GetNumOperands() == 0
        assert cinstr.GetSExtValue() == 1

        instr = builder.BuildNUWMul(lhs, rhs, 'rv')
        assert isinstance(instr, llpy.core.BinaryOperator)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.Mul
        assert instr.TypeOf() is i32

        assert instr.GetNumOperands() == 2
        assert instr.GetOperand(0) is lhs
        assert instr.GetOperand(1) is rhs

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define i32 @func(i32 %lhs, i32 %rhs) {
  %rv = mul nuw i32 %lhs, %rhs
  ret i32 %rv
}

''')

    def test_BuildFMul(self):
        builder = self.builder
        double = llpy.core.DoubleType(self.ctx)
        func_type = llpy.core.FunctionType(double, [double, double])
        func = self.mod.AddFunction(func_type, 'func')
        lhs = func.GetParam(0)
        lhs.SetValueName('lhs')
        rhs = func.GetParam(1)
        rhs.SetValueName('rhs')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        cinstr = builder.BuildFMul(double.ConstReal(-1.0), double.ConstReal(-1.0))
        assert isinstance(cinstr, llpy.core.ConstantFP)
        assert cinstr.TypeOf() is double
        assert cinstr.GetNumOperands() == 0
        assert cinstr is double.ConstReal(1.0)

        instr = builder.BuildFMul(lhs, rhs, 'rv')
        assert isinstance(instr, llpy.core.BinaryOperator)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.FMul
        assert instr.TypeOf() is double

        assert instr.GetNumOperands() == 2
        assert instr.GetOperand(0) is lhs
        assert instr.GetOperand(1) is rhs

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define double @func(double %lhs, double %rhs) {
  %rv = fmul double %lhs, %rhs
  ret double %rv
}

''')

    def test_BuildUDiv(self):
        builder = self.builder
        i32 = llpy.core.IntegerType(self.ctx, 32)
        func_type = llpy.core.FunctionType(i32, [i32, i32])
        func = self.mod.AddFunction(func_type, 'func')
        lhs = func.GetParam(0)
        lhs.SetValueName('lhs')
        rhs = func.GetParam(1)
        rhs.SetValueName('rhs')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        cinstr0 = builder.BuildUDiv(i32.ConstInt(-2), i32.ConstInt(-1))
        assert isinstance(cinstr0, llpy.core.ConstantInt)
        assert cinstr0.TypeOf() is i32
        assert cinstr0.GetNumOperands() == 0
        assert cinstr0.GetSExtValue() == 0

        cinstr1 = builder.BuildUDiv(i32.ConstInt(-1), i32.ConstInt(-2))
        assert isinstance(cinstr1, llpy.core.ConstantInt)
        assert cinstr1.TypeOf() is i32
        assert cinstr1.GetNumOperands() == 0
        assert cinstr1.GetSExtValue() == 1

        instr = builder.BuildUDiv(lhs, rhs, 'rv')
        assert isinstance(instr, llpy.core.BinaryOperator)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.UDiv
        assert instr.TypeOf() is i32

        assert instr.GetNumOperands() == 2
        assert instr.GetOperand(0) is lhs
        assert instr.GetOperand(1) is rhs

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define i32 @func(i32 %lhs, i32 %rhs) {
  %rv = udiv i32 %lhs, %rhs
  ret i32 %rv
}

''')

    def test_BuildSDiv(self):
        builder = self.builder
        i32 = llpy.core.IntegerType(self.ctx, 32)
        func_type = llpy.core.FunctionType(i32, [i32, i32])
        func = self.mod.AddFunction(func_type, 'func')
        lhs = func.GetParam(0)
        lhs.SetValueName('lhs')
        rhs = func.GetParam(1)
        rhs.SetValueName('rhs')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        cinstr0 = builder.BuildSDiv(i32.ConstInt(-1), i32.ConstInt(-2))
        assert isinstance(cinstr0, llpy.core.ConstantInt)
        assert cinstr0.TypeOf() is i32
        assert cinstr0.GetNumOperands() == 0
        assert cinstr0.GetSExtValue() == 0

        cinstr2 = builder.BuildSDiv(i32.ConstInt(-2), i32.ConstInt(-1))
        assert isinstance(cinstr2, llpy.core.ConstantInt)
        assert cinstr2.TypeOf() is i32
        assert cinstr2.GetNumOperands() == 0
        assert cinstr2.GetSExtValue() == 2

        instr = builder.BuildSDiv(lhs, rhs, 'rv')
        assert isinstance(instr, llpy.core.BinaryOperator)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.SDiv
        assert instr.TypeOf() is i32

        assert instr.GetNumOperands() == 2
        assert instr.GetOperand(0) is lhs
        assert instr.GetOperand(1) is rhs

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define i32 @func(i32 %lhs, i32 %rhs) {
  %rv = sdiv i32 %lhs, %rhs
  ret i32 %rv
}

''')

    def test_BuildExactSDiv(self):
        builder = self.builder
        i32 = llpy.core.IntegerType(self.ctx, 32)
        func_type = llpy.core.FunctionType(i32, [i32, i32])
        func = self.mod.AddFunction(func_type, 'func')
        lhs = func.GetParam(0)
        lhs.SetValueName('lhs')
        rhs = func.GetParam(1)
        rhs.SetValueName('rhs')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        cinstr0 = builder.BuildExactSDiv(i32.ConstInt(-1), i32.ConstInt(-2))
        assert isinstance(cinstr0, llpy.core.ConstantInt)
        assert cinstr0.TypeOf() is i32
        assert cinstr0.GetNumOperands() == 0
        assert cinstr0.GetSExtValue() == 0

        cinstr2 = builder.BuildExactSDiv(i32.ConstInt(-2), i32.ConstInt(-1))
        assert isinstance(cinstr2, llpy.core.ConstantInt)
        assert cinstr2.TypeOf() is i32
        assert cinstr2.GetNumOperands() == 0
        assert cinstr2.GetSExtValue() == 2

        instr = builder.BuildExactSDiv(lhs, rhs, 'rv')
        assert isinstance(instr, llpy.core.BinaryOperator)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.SDiv
        assert instr.TypeOf() is i32

        assert instr.GetNumOperands() == 2
        assert instr.GetOperand(0) is lhs
        assert instr.GetOperand(1) is rhs

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define i32 @func(i32 %lhs, i32 %rhs) {
  %rv = sdiv exact i32 %lhs, %rhs
  ret i32 %rv
}

''')

    def test_BuildFDiv(self):
        builder = self.builder
        double = llpy.core.DoubleType(self.ctx)
        func_type = llpy.core.FunctionType(double, [double, double])
        func = self.mod.AddFunction(func_type, 'func')
        lhs = func.GetParam(0)
        lhs.SetValueName('lhs')
        rhs = func.GetParam(1)
        rhs.SetValueName('rhs')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        cinstr = builder.BuildFDiv(double.ConstReal(-1.0), double.ConstReal(-2.0))
        assert isinstance(cinstr, llpy.core.ConstantFP)
        assert cinstr.TypeOf() is double
        assert cinstr.GetNumOperands() == 0
        assert cinstr is double.ConstReal(0.5)

        instr = builder.BuildFDiv(lhs, rhs, 'rv')
        assert isinstance(instr, llpy.core.BinaryOperator)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.FDiv
        assert instr.TypeOf() is double

        assert instr.GetNumOperands() == 2
        assert instr.GetOperand(0) is lhs
        assert instr.GetOperand(1) is rhs

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define double @func(double %lhs, double %rhs) {
  %rv = fdiv double %lhs, %rhs
  ret double %rv
}

''')

    def test_BuildURem(self):
        builder = self.builder
        i32 = llpy.core.IntegerType(self.ctx, 32)
        func_type = llpy.core.FunctionType(i32, [i32, i32])
        func = self.mod.AddFunction(func_type, 'func')
        lhs = func.GetParam(0)
        lhs.SetValueName('lhs')
        rhs = func.GetParam(1)
        rhs.SetValueName('rhs')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        cinstr0 = builder.BuildURem(i32.ConstInt(-2), i32.ConstInt(-1))
        assert isinstance(cinstr0, llpy.core.ConstantInt)
        assert cinstr0.TypeOf() is i32
        assert cinstr0.GetNumOperands() == 0
        assert cinstr0.GetSExtValue() == -2

        cinstr1 = builder.BuildURem(i32.ConstInt(-1), i32.ConstInt(-2))
        assert isinstance(cinstr1, llpy.core.ConstantInt)
        assert cinstr1.TypeOf() is i32
        assert cinstr1.GetNumOperands() == 0
        assert cinstr1.GetSExtValue() == 1

        instr = builder.BuildURem(lhs, rhs, 'rv')
        assert isinstance(instr, llpy.core.BinaryOperator)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.URem
        assert instr.TypeOf() is i32

        assert instr.GetNumOperands() == 2
        assert instr.GetOperand(0) is lhs
        assert instr.GetOperand(1) is rhs

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define i32 @func(i32 %lhs, i32 %rhs) {
  %rv = urem i32 %lhs, %rhs
  ret i32 %rv
}

''')

    def test_BuildSRem(self):
        builder = self.builder
        i32 = llpy.core.IntegerType(self.ctx, 32)
        func_type = llpy.core.FunctionType(i32, [i32, i32])
        func = self.mod.AddFunction(func_type, 'func')
        lhs = func.GetParam(0)
        lhs.SetValueName('lhs')
        rhs = func.GetParam(1)
        rhs.SetValueName('rhs')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        cinstr0 = builder.BuildSRem(i32.ConstInt(-1), i32.ConstInt(-2))
        assert isinstance(cinstr0, llpy.core.ConstantInt)
        assert cinstr0.TypeOf() is i32
        assert cinstr0.GetNumOperands() == 0
        assert cinstr0.GetSExtValue() == -1

        cinstr2 = builder.BuildSRem(i32.ConstInt(-2), i32.ConstInt(-1))
        assert isinstance(cinstr2, llpy.core.ConstantInt)
        assert cinstr2.TypeOf() is i32
        assert cinstr2.GetNumOperands() == 0
        assert cinstr2.GetSExtValue() == 0

        instr = builder.BuildSRem(lhs, rhs, 'rv')
        assert isinstance(instr, llpy.core.BinaryOperator)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.SRem
        assert instr.TypeOf() is i32

        assert instr.GetNumOperands() == 2
        assert instr.GetOperand(0) is lhs
        assert instr.GetOperand(1) is rhs

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define i32 @func(i32 %lhs, i32 %rhs) {
  %rv = srem i32 %lhs, %rhs
  ret i32 %rv
}

''')

    def test_BuildFRem(self):
        builder = self.builder
        double = llpy.core.DoubleType(self.ctx)
        func_type = llpy.core.FunctionType(double, [double, double])
        func = self.mod.AddFunction(func_type, 'func')
        lhs = func.GetParam(0)
        lhs.SetValueName('lhs')
        rhs = func.GetParam(1)
        rhs.SetValueName('rhs')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        cinstr = builder.BuildFRem(double.ConstReal(-1.25), double.ConstReal(-0.5))
        assert isinstance(cinstr, llpy.core.ConstantFP)
        assert cinstr.TypeOf() is double
        assert cinstr.GetNumOperands() == 0
        assert cinstr is double.ConstReal(-0.25)

        instr = builder.BuildFRem(lhs, rhs, 'rv')
        assert isinstance(instr, llpy.core.BinaryOperator)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.FRem
        assert instr.TypeOf() is double

        assert instr.GetNumOperands() == 2
        assert instr.GetOperand(0) is lhs
        assert instr.GetOperand(1) is rhs

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define double @func(double %lhs, double %rhs) {
  %rv = frem double %lhs, %rhs
  ret double %rv
}

''')

    def test_BuildShl(self):
        builder = self.builder
        i32 = llpy.core.IntegerType(self.ctx, 32)
        func_type = llpy.core.FunctionType(i32, [i32, i32])
        func = self.mod.AddFunction(func_type, 'func')
        lhs = func.GetParam(0)
        lhs.SetValueName('lhs')
        rhs = func.GetParam(1)
        rhs.SetValueName('rhs')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        cinstr = builder.BuildShl(i32.ConstAllOnes(), i32.ConstInt(1))
        assert isinstance(cinstr, llpy.core.ConstantInt)
        assert cinstr.TypeOf() is i32
        assert cinstr.GetNumOperands() == 0
        assert cinstr.GetSExtValue() == -2

        instr = builder.BuildShl(lhs, rhs, 'rv')
        assert isinstance(instr, llpy.core.BinaryOperator)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.Shl
        assert instr.TypeOf() is i32

        assert instr.GetNumOperands() == 2
        assert instr.GetOperand(0) is lhs
        assert instr.GetOperand(1) is rhs

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define i32 @func(i32 %lhs, i32 %rhs) {
  %rv = shl i32 %lhs, %rhs
  ret i32 %rv
}

''')

    def test_BuildLShr(self):
        builder = self.builder
        i32 = llpy.core.IntegerType(self.ctx, 32)
        func_type = llpy.core.FunctionType(i32, [i32, i32])
        func = self.mod.AddFunction(func_type, 'func')
        lhs = func.GetParam(0)
        lhs.SetValueName('lhs')
        rhs = func.GetParam(1)
        rhs.SetValueName('rhs')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        cinstr = builder.BuildLShr(i32.ConstInt(-2), i32.ConstInt(1))
        assert isinstance(cinstr, llpy.core.ConstantInt)
        assert cinstr.TypeOf() is i32
        assert cinstr.GetNumOperands() == 0
        assert cinstr.GetZExtValue() == 0x7fFFffFF

        instr = builder.BuildLShr(lhs, rhs, 'rv')
        assert isinstance(instr, llpy.core.BinaryOperator)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.LShr
        assert instr.TypeOf() is i32

        assert instr.GetNumOperands() == 2
        assert instr.GetOperand(0) is lhs
        assert instr.GetOperand(1) is rhs

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define i32 @func(i32 %lhs, i32 %rhs) {
  %rv = lshr i32 %lhs, %rhs
  ret i32 %rv
}

''')

    def test_BuildAShr(self):
        builder = self.builder
        i32 = llpy.core.IntegerType(self.ctx, 32)
        func_type = llpy.core.FunctionType(i32, [i32, i32])
        func = self.mod.AddFunction(func_type, 'func')
        lhs = func.GetParam(0)
        lhs.SetValueName('lhs')
        rhs = func.GetParam(1)
        rhs.SetValueName('rhs')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        cinstr = builder.BuildAShr(i32.ConstInt(-2), i32.ConstInt(1))
        assert isinstance(cinstr, llpy.core.ConstantInt)
        assert cinstr.TypeOf() is i32
        assert cinstr.GetNumOperands() == 0
        assert cinstr.GetSExtValue() == -1

        instr = builder.BuildAShr(lhs, rhs, 'rv')
        assert isinstance(instr, llpy.core.BinaryOperator)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.AShr
        assert instr.TypeOf() is i32

        assert instr.GetNumOperands() == 2
        assert instr.GetOperand(0) is lhs
        assert instr.GetOperand(1) is rhs

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define i32 @func(i32 %lhs, i32 %rhs) {
  %rv = ashr i32 %lhs, %rhs
  ret i32 %rv
}

''')

    def test_BuildAnd(self):
        builder = self.builder
        i32 = llpy.core.IntegerType(self.ctx, 32)
        func_type = llpy.core.FunctionType(i32, [i32, i32])
        func = self.mod.AddFunction(func_type, 'func')
        lhs = func.GetParam(0)
        lhs.SetValueName('lhs')
        rhs = func.GetParam(1)
        rhs.SetValueName('rhs')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        cinstr = builder.BuildAnd(i32.ConstInt(3), i32.ConstInt(6))
        assert isinstance(cinstr, llpy.core.ConstantInt)
        assert cinstr.TypeOf() is i32
        assert cinstr.GetNumOperands() == 0
        assert cinstr.GetSExtValue() == 2

        instr = builder.BuildAnd(lhs, rhs, 'rv')
        assert isinstance(instr, llpy.core.BinaryOperator)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.And
        assert instr.TypeOf() is i32

        assert instr.GetNumOperands() == 2
        assert instr.GetOperand(0) is lhs
        assert instr.GetOperand(1) is rhs

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define i32 @func(i32 %lhs, i32 %rhs) {
  %rv = and i32 %lhs, %rhs
  ret i32 %rv
}

''')

    def test_BuildOr(self):
        builder = self.builder
        i32 = llpy.core.IntegerType(self.ctx, 32)
        func_type = llpy.core.FunctionType(i32, [i32, i32])
        func = self.mod.AddFunction(func_type, 'func')
        lhs = func.GetParam(0)
        lhs.SetValueName('lhs')
        rhs = func.GetParam(1)
        rhs.SetValueName('rhs')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        cinstr = builder.BuildOr(i32.ConstInt(3), i32.ConstInt(6))
        assert isinstance(cinstr, llpy.core.ConstantInt)
        assert cinstr.TypeOf() is i32
        assert cinstr.GetNumOperands() == 0
        assert cinstr.GetSExtValue() == 7

        instr = builder.BuildOr(lhs, rhs, 'rv')
        assert isinstance(instr, llpy.core.BinaryOperator)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.Or
        assert instr.TypeOf() is i32

        assert instr.GetNumOperands() == 2
        assert instr.GetOperand(0) is lhs
        assert instr.GetOperand(1) is rhs

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define i32 @func(i32 %lhs, i32 %rhs) {
  %rv = or i32 %lhs, %rhs
  ret i32 %rv
}

''')

    def test_BuildXor(self):
        builder = self.builder
        i32 = llpy.core.IntegerType(self.ctx, 32)
        func_type = llpy.core.FunctionType(i32, [i32, i32])
        func = self.mod.AddFunction(func_type, 'func')
        lhs = func.GetParam(0)
        lhs.SetValueName('lhs')
        rhs = func.GetParam(1)
        rhs.SetValueName('rhs')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        cinstr = builder.BuildXor(i32.ConstInt(3), i32.ConstInt(6))
        assert isinstance(cinstr, llpy.core.ConstantInt)
        assert cinstr.TypeOf() is i32
        assert cinstr.GetNumOperands() == 0
        assert cinstr.GetSExtValue() == 5

        instr = builder.BuildXor(lhs, rhs, 'rv')
        assert isinstance(instr, llpy.core.BinaryOperator)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.Xor
        assert instr.TypeOf() is i32

        assert instr.GetNumOperands() == 2
        assert instr.GetOperand(0) is lhs
        assert instr.GetOperand(1) is rhs

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define i32 @func(i32 %lhs, i32 %rhs) {
  %rv = xor i32 %lhs, %rhs
  ret i32 %rv
}

''')

    @unittest.expectedFailure
    def test_BuildBinOp(self):
        raise NotImplementedError
        builder = self.builder
        instr = builder.BuildBinOp(op, lhs, rhs, name)

    def test_BuildNeg(self):
        builder = self.builder
        i32 = llpy.core.IntegerType(self.ctx, 32)
        func_type = llpy.core.FunctionType(i32, [i32])
        func = self.mod.AddFunction(func_type, 'func')
        rhs = func.GetParam(0)
        rhs.SetValueName('rhs')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        cinstr = builder.BuildNeg(i32.ConstAllOnes())
        assert isinstance(cinstr, llpy.core.ConstantInt)
        assert cinstr.TypeOf() is i32
        assert cinstr.GetNumOperands() == 0
        assert cinstr.GetSExtValue() == 1

        instr = builder.BuildNeg(rhs, 'rv')
        assert isinstance(instr, llpy.core.BinaryOperator)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.Sub
        assert instr.TypeOf() is i32

        assert instr.GetNumOperands() == 2
        assert instr.GetOperand(0) is i32.ConstNull()
        assert instr.GetOperand(1) is rhs

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define i32 @func(i32 %rhs) {
  %rv = sub i32 0, %rhs
  ret i32 %rv
}

''')

    def test_BuildNSWNeg(self):
        builder = self.builder
        i32 = llpy.core.IntegerType(self.ctx, 32)
        func_type = llpy.core.FunctionType(i32, [i32])
        func = self.mod.AddFunction(func_type, 'func')
        rhs = func.GetParam(0)
        rhs.SetValueName('rhs')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        cinstr = builder.BuildNSWNeg(i32.ConstAllOnes())
        assert isinstance(cinstr, llpy.core.ConstantInt)
        assert cinstr.TypeOf() is i32
        assert cinstr.GetNumOperands() == 0
        assert cinstr.GetSExtValue() == 1

        instr = builder.BuildNSWNeg(rhs, 'rv')
        assert isinstance(instr, llpy.core.BinaryOperator)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.Sub
        assert instr.TypeOf() is i32

        assert instr.GetNumOperands() == 2
        assert instr.GetOperand(0) is i32.ConstNull()
        assert instr.GetOperand(1) is rhs

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define i32 @func(i32 %rhs) {
  %rv = sub nsw i32 0, %rhs
  ret i32 %rv
}

''')

    def test_BuildNUWNeg(self):
        builder = self.builder
        i32 = llpy.core.IntegerType(self.ctx, 32)
        func_type = llpy.core.FunctionType(i32, [i32])
        func = self.mod.AddFunction(func_type, 'func')
        rhs = func.GetParam(0)
        rhs.SetValueName('rhs')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        cinstr = builder.BuildNUWNeg(i32.ConstAllOnes())
        assert isinstance(cinstr, llpy.core.ConstantInt)
        assert cinstr.TypeOf() is i32
        assert cinstr.GetNumOperands() == 0
        assert cinstr.GetSExtValue() == 1

        instr = builder.BuildNUWNeg(rhs, 'rv')
        assert isinstance(instr, llpy.core.BinaryOperator)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.Sub
        assert instr.TypeOf() is i32

        assert instr.GetNumOperands() == 2
        assert instr.GetOperand(0) is i32.ConstNull()
        assert instr.GetOperand(1) is rhs

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define i32 @func(i32 %rhs) {
  %rv = sub nuw i32 0, %rhs
  ret i32 %rv
}

''')

    def test_BuildFNeg(self):
        builder = self.builder
        double = llpy.core.DoubleType(self.ctx)
        func_type = llpy.core.FunctionType(double, [double])
        func = self.mod.AddFunction(func_type, 'func')
        rhs = func.GetParam(0)
        rhs.SetValueName('rhs')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        cinstr = builder.BuildFNeg(double.ConstReal(-1.0))
        assert isinstance(cinstr, llpy.core.ConstantFP)
        assert cinstr.TypeOf() is double
        assert cinstr.GetNumOperands() == 0
        assert cinstr is double.ConstReal(1.0)

        instr = builder.BuildFNeg(rhs, 'rv')
        assert isinstance(instr, llpy.core.BinaryOperator)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.FSub
        assert instr.TypeOf() is double

        assert instr.GetNumOperands() == 2
        assert instr.GetOperand(0) is double.ConstReal(-0.0)
        assert instr.GetOperand(1) is rhs

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define double @func(double %rhs) {
  %rv = fsub double -0.000000e+00, %rhs
  ret double %rv
}

''')

    def test_BuildNot(self):
        builder = self.builder
        i32 = llpy.core.IntegerType(self.ctx, 32)
        func_type = llpy.core.FunctionType(i32, [i32])
        func = self.mod.AddFunction(func_type, 'func')
        rhs = func.GetParam(0)
        rhs.SetValueName('rhs')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        cinstr = builder.BuildNot(i32.ConstAllOnes())
        assert isinstance(cinstr, llpy.core.ConstantInt)
        assert cinstr.TypeOf() is i32
        assert cinstr.GetNumOperands() == 0
        assert cinstr.GetSExtValue() == 0

        instr = builder.BuildNot(rhs, 'rv')
        assert isinstance(instr, llpy.core.BinaryOperator)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.Xor
        assert instr.TypeOf() is i32

        assert instr.GetNumOperands() == 2
        assert instr.GetOperand(0) is rhs
        assert instr.GetOperand(1) is i32.ConstAllOnes()

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define i32 @func(i32 %rhs) {
  %rv = xor i32 %rhs, -1
  ret i32 %rv
}

''')


    # Memory
    @unittest.expectedFailure
    def test_BuildMalloc(self):
        raise NotImplementedError
        builder = self.builder
        instr = builder.BuildMalloc(ty, name)

    @unittest.expectedFailure
    def test_BuildArrayMalloc(self):
        raise NotImplementedError
        builder = self.builder
        instr = builder.BuildArrayMalloc(ty, val, name)

    def test_BuildAlloca(self):
        builder = self.builder
        void = llpy.core.VoidType(self.ctx)
        i32 = llpy.core.IntegerType(self.ctx, 32)
        func_type = llpy.core.FunctionType(void, [])
        func = self.mod.AddFunction(func_type, 'func')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        instr = builder.BuildAlloca(i32, 'aa')
        assert isinstance(instr, llpy.core.AllocaInst)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.Alloca
        assert instr.TypeOf() is llpy.core.PointerType(i32)

        assert instr.GetNumOperands() == 1
        assert instr.GetOperand(0) is i32.ConstInt(1)

        builder.BuildRetVoid()
        self.assertDump(func,
'''
define void @func() {
  %aa = alloca i32
  ret void
}

''')

    def test_BuildArrayAlloca(self):
        builder = self.builder
        void = llpy.core.VoidType(self.ctx)
        i32 = llpy.core.IntegerType(self.ctx, 32)
        func_type = llpy.core.FunctionType(void, [i32])
        func = self.mod.AddFunction(func_type, 'func')
        arg = func.GetParam(0)
        arg.SetValueName('arg')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        instr = builder.BuildArrayAlloca(i32, arg, 'aa')
        assert isinstance(instr, llpy.core.AllocaInst)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.Alloca
        assert instr.TypeOf() is llpy.core.PointerType(i32)

        assert instr.GetNumOperands() == 1
        assert instr.GetOperand(0) is arg

        builder.BuildRetVoid()
        self.assertDump(func,
'''
define void @func(i32 %arg) {
  %aa = alloca i32, i32 %arg
  ret void
}

''')

    @unittest.expectedFailure
    def test_BuildFree(self):
        raise NotImplementedError
        builder = self.builder
        instr = builder.BuildFree(ptr)

    def test_BuildLoad(self):
        builder = self.builder
        void = llpy.core.VoidType(self.ctx)
        i32 = llpy.core.IntegerType(self.ctx, 32)
        func_type = llpy.core.FunctionType(void, [])
        func = self.mod.AddFunction(func_type, 'func')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)
        ptr = builder.BuildAlloca(i32, 'aa')

        instr = builder.BuildLoad(ptr)
        assert isinstance(instr, llpy.core.LoadInst)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.Load
        assert instr.TypeOf() is i32

        assert instr.GetNumOperands() == 1
        assert instr.GetOperand(0) is ptr

        builder.BuildRetVoid()
        self.assertDump(func,
'''
define void @func() {
  %aa = alloca i32
  %1 = load i32* %aa
  ret void
}

''')
        if (3, 1) <= _version:
            assert not instr.GetVolatile()
            instr.SetVolatile(True)
            assert instr.GetVolatile()
            self.assertDump(instr, '  %1 = load volatile i32* %aa\n')

    def test_BuildStore(self):
        builder = self.builder
        void = llpy.core.VoidType(self.ctx)
        i32 = llpy.core.IntegerType(self.ctx, 32)
        func_type = llpy.core.FunctionType(void, [i32])
        func = self.mod.AddFunction(func_type, 'func')
        arg = func.GetParam(0)
        arg.SetValueName('arg')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)
        ptr = builder.BuildAlloca(i32, 'aa')

        instr = builder.BuildStore(arg, ptr)
        assert isinstance(instr, llpy.core.StoreInst)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.Store
        assert instr.TypeOf() is void

        assert instr.GetNumOperands() == 2
        assert instr.GetOperand(0) is arg
        assert instr.GetOperand(1) is ptr

        builder.BuildRetVoid()
        self.assertDump(func,
'''
define void @func(i32 %arg) {
  %aa = alloca i32
  store i32 %arg, i32* %aa
  ret void
}

''')
        if (3, 1) <= _version:
            assert not instr.GetVolatile()
            instr.SetVolatile(True)
            assert instr.GetVolatile()
            self.assertDump(instr, '  store volatile i32 %arg, i32* %aa\n')


    def test_BuildGEP(self):
        builder = self.builder
        i32 = llpy.core.IntegerType(self.ctx, 32)
        i64 = llpy.core.IntegerType(self.ctx, 64)
        i32p = llpy.core.PointerType(i32)
        i32a = llpy.core.ArrayType(i32, 2) #truths!
        i32ap = llpy.core.PointerType(i32a)
        i32as = llpy.core.StructType(self.ctx, [i32a], None)
        i32asp = llpy.core.PointerType(i32as)
        func_type = llpy.core.FunctionType(i32p, [i32asp, i32])
        func = self.mod.AddFunction(func_type, 'func')
        ptr = func.GetParam(0)
        ptr.SetValueName('ptr')
        idx = func.GetParam(1)
        idx.SetValueName('idx')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)


        instr0 = builder.BuildGEP(ptr, [], 'gep0')
        assert isinstance(instr0, llpy.core.GetElementPtrInst)
        assert instr0.GetInstructionParent() is bb
        assert instr0.GetInstructionOpcode() == llpy.core.Opcode.GetElementPtr
        assert instr0.TypeOf() is i32asp

        assert instr0.GetNumOperands() == 1
        assert instr0.GetOperand(0) is ptr


        instr1 = builder.BuildGEP(ptr, [i64.ConstNull()], 'gep1')
        assert isinstance(instr1, llpy.core.GetElementPtrInst)
        assert instr1.GetInstructionParent() is bb
        assert instr1.GetInstructionOpcode() == llpy.core.Opcode.GetElementPtr
        assert instr1.TypeOf() is i32asp

        assert instr1.GetNumOperands() == 2
        assert instr1.GetOperand(0) is ptr
        assert instr1.GetOperand(1) is i64.ConstNull()


        instr2 = builder.BuildGEP(ptr, [i64.ConstNull(), i32.ConstNull()], 'gep2')
        assert isinstance(instr2, llpy.core.GetElementPtrInst)
        assert instr2.GetInstructionParent() is bb
        assert instr2.GetInstructionOpcode() == llpy.core.Opcode.GetElementPtr
        assert instr2.TypeOf() is i32ap

        assert instr2.GetNumOperands() == 3
        assert instr2.GetOperand(0) is ptr
        assert instr2.GetOperand(1) is i64.ConstNull()
        assert instr2.GetOperand(2) is i32.ConstNull()


        instr3 = builder.BuildGEP(ptr, [i64.ConstNull(), i32.ConstNull(), idx])
        assert isinstance(instr3, llpy.core.GetElementPtrInst)
        assert instr3.GetInstructionParent() is bb
        assert instr3.GetInstructionOpcode() == llpy.core.Opcode.GetElementPtr
        assert instr3.TypeOf() is i32p

        assert instr3.GetNumOperands() == 4
        assert instr3.GetOperand(0) is ptr
        assert instr3.GetOperand(1) is i64.ConstNull()
        assert instr3.GetOperand(2) is i32.ConstNull()
        assert instr3.GetOperand(3) is idx


        builder.BuildRet(instr3)
        self.assertDump(func,
'''
define i32* @func({ [2 x i32] }* %ptr, i32 %idx) {
  %gep0 = getelementptr { [2 x i32] }* %ptr
  %gep1 = getelementptr { [2 x i32] }* %ptr, i64 0
  %gep2 = getelementptr { [2 x i32] }* %ptr, i64 0, i32 0
  %1 = getelementptr { [2 x i32] }* %ptr, i64 0, i32 0, i32 %idx
  ret i32* %1
}

''')

    def test_BuildInBoundsGEP(self):
        builder = self.builder
        i32 = llpy.core.IntegerType(self.ctx, 32)
        i64 = llpy.core.IntegerType(self.ctx, 64)
        i32p = llpy.core.PointerType(i32)
        i32a = llpy.core.ArrayType(i32, 2) #truths!
        i32ap = llpy.core.PointerType(i32a)
        i32as = llpy.core.StructType(self.ctx, [i32a], None)
        i32asp = llpy.core.PointerType(i32as)
        func_type = llpy.core.FunctionType(i32p, [i32asp, i32])
        func = self.mod.AddFunction(func_type, 'func')
        ptr = func.GetParam(0)
        ptr.SetValueName('ptr')
        idx = func.GetParam(1)
        idx.SetValueName('idx')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)


        instr0 = builder.BuildInBoundsGEP(ptr, [], 'gep0')
        assert isinstance(instr0, llpy.core.GetElementPtrInst)
        assert instr0.GetInstructionParent() is bb
        assert instr0.GetInstructionOpcode() == llpy.core.Opcode.GetElementPtr
        assert instr0.TypeOf() is i32asp

        assert instr0.GetNumOperands() == 1
        assert instr0.GetOperand(0) is ptr


        instr1 = builder.BuildInBoundsGEP(ptr, [i64.ConstNull()], 'gep1')
        assert isinstance(instr1, llpy.core.GetElementPtrInst)
        assert instr1.GetInstructionParent() is bb
        assert instr1.GetInstructionOpcode() == llpy.core.Opcode.GetElementPtr
        assert instr1.TypeOf() is i32asp

        assert instr1.GetNumOperands() == 2
        assert instr1.GetOperand(0) is ptr
        assert instr1.GetOperand(1) is i64.ConstNull()


        instr2 = builder.BuildInBoundsGEP(ptr, [i64.ConstNull(), i32.ConstNull()], 'gep2')
        assert isinstance(instr2, llpy.core.GetElementPtrInst)
        assert instr2.GetInstructionParent() is bb
        assert instr2.GetInstructionOpcode() == llpy.core.Opcode.GetElementPtr
        assert instr2.TypeOf() is i32ap

        assert instr2.GetNumOperands() == 3
        assert instr2.GetOperand(0) is ptr
        assert instr2.GetOperand(1) is i64.ConstNull()
        assert instr2.GetOperand(2) is i32.ConstNull()


        instr3 = builder.BuildInBoundsGEP(ptr, [i64.ConstNull(), i32.ConstNull(), idx])
        assert isinstance(instr3, llpy.core.GetElementPtrInst)
        assert instr3.GetInstructionParent() is bb
        assert instr3.GetInstructionOpcode() == llpy.core.Opcode.GetElementPtr
        assert instr3.TypeOf() is i32p

        assert instr3.GetNumOperands() == 4
        assert instr3.GetOperand(0) is ptr
        assert instr3.GetOperand(1) is i64.ConstNull()
        assert instr3.GetOperand(2) is i32.ConstNull()
        assert instr3.GetOperand(3) is idx


        builder.BuildRet(instr3)
        self.assertDump(func,
'''
define i32* @func({ [2 x i32] }* %ptr, i32 %idx) {
  %gep0 = getelementptr inbounds { [2 x i32] }* %ptr
  %gep1 = getelementptr inbounds { [2 x i32] }* %ptr, i64 0
  %gep2 = getelementptr inbounds { [2 x i32] }* %ptr, i64 0, i32 0
  %1 = getelementptr inbounds { [2 x i32] }* %ptr, i64 0, i32 0, i32 %idx
  ret i32* %1
}

''')

    @unittest.expectedFailure # got segfaults, haven't looked hard
    def test_BuildStructGEP(self):
        raise NotImplementedError
        builder = self.builder
        instr = builder.BuildStructGEP(ptr, index, name)

    def test_BuildGlobalString(self):
        builder = self.builder
        i8 = llpy.core.IntegerType(self.ctx, 8)
        i8a = llpy.core.ArrayType(i8, 14)
        i8ap = llpy.core.PointerType(i8a)
        func_type = llpy.core.FunctionType(i8ap, [])
        func = self.mod.AddFunction(func_type, 'func')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        instr = builder.BuildGlobalString('Hello, World!', 'hi')
        assert isinstance(instr, llpy.core.GlobalVariable)
        assert instr.TypeOf() is i8ap

        builder.BuildRet(instr)
        if _version <= (3, 0):
            self.assertDump(self.mod,
r'''; ModuleID = 'TestBuilder'

@hi = internal unnamed_addr constant [14 x i8] c"Hello, World!\00"

define [14 x i8]* @func() {
  ret [14 x i8]* @hi
}
''')
        if (3, 1) <= _version:
            self.assertDump(self.mod,
r'''; ModuleID = 'TestBuilder'

@hi = private unnamed_addr constant [14 x i8] c"Hello, World!\00"

define [14 x i8]* @func() {
  ret [14 x i8]* @hi
}
''')

    def test_BuildGlobalStringPtr(self):
        builder = self.builder
        i8 = llpy.core.IntegerType(self.ctx, 8)
        i8p = llpy.core.PointerType(i8)
        func_type = llpy.core.FunctionType(i8p, [])
        func = self.mod.AddFunction(func_type, 'func')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        instr = builder.BuildGlobalStringPtr('Hello, World!', 'hi')
        assert isinstance(instr, llpy.core.GetElementPtrConstantExpr)
        assert instr.TypeOf() is i8p

        builder.BuildRet(instr)
        if _version <= (3, 0):
            self.assertDump(self.mod,
r'''; ModuleID = 'TestBuilder'

@hi = internal unnamed_addr constant [14 x i8] c"Hello, World!\00"

define i8* @func() {
  ret i8* getelementptr inbounds ([14 x i8]* @hi, i32 0, i32 0)
}
''')
        if (3, 1) <= _version:
            self.assertDump(self.mod,
r'''; ModuleID = 'TestBuilder'

@hi = private unnamed_addr constant [14 x i8] c"Hello, World!\00"

define i8* @func() {
  ret i8* getelementptr inbounds ([14 x i8]* @hi, i32 0, i32 0)
}
''')

    # Casts
    def test_BuildTrunc(self):
        builder = self.builder
        i32 = llpy.core.IntegerType(self.ctx, 32)
        i64 = llpy.core.IntegerType(self.ctx, 64)
        func_type = llpy.core.FunctionType(i32, [i64])
        func = self.mod.AddFunction(func_type, 'func')
        rhs = func.GetParam(0)
        rhs.SetValueName('rhs')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        cinstr = builder.BuildTrunc(i64.ConstNull(), i32)
        assert isinstance(cinstr, llpy.core.ConstantInt)
        assert cinstr is i32.ConstNull()

        instr = builder.BuildTrunc(rhs, i32, 'rv')
        assert isinstance(instr, llpy.core.TruncInst)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.Trunc
        assert instr.TypeOf() is i32

        assert instr.GetNumOperands() == 1
        assert instr.GetOperand(0) is rhs

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define i32 @func(i64 %rhs) {
  %rv = trunc i64 %rhs to i32
  ret i32 %rv
}

''')

    def test_BuildZExt(self):
        builder = self.builder
        i32 = llpy.core.IntegerType(self.ctx, 32)
        i64 = llpy.core.IntegerType(self.ctx, 64)
        func_type = llpy.core.FunctionType(i64, [i32])
        func = self.mod.AddFunction(func_type, 'func')
        rhs = func.GetParam(0)
        rhs.SetValueName('rhs')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        cinstr = builder.BuildZExt(i32.ConstNull(), i64)
        assert isinstance(cinstr, llpy.core.ConstantInt)
        assert cinstr is i64.ConstNull()

        instr = builder.BuildZExt(rhs, i64, 'rv')
        assert isinstance(instr, llpy.core.ZExtInst)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.ZExt
        assert instr.TypeOf() is i64

        assert instr.GetNumOperands() == 1
        assert instr.GetOperand(0) is rhs

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define i64 @func(i32 %rhs) {
  %rv = zext i32 %rhs to i64
  ret i64 %rv
}

''')

    def test_BuildSExt(self):
        builder = self.builder
        i32 = llpy.core.IntegerType(self.ctx, 32)
        i64 = llpy.core.IntegerType(self.ctx, 64)
        func_type = llpy.core.FunctionType(i64, [i32])
        func = self.mod.AddFunction(func_type, 'func')
        rhs = func.GetParam(0)
        rhs.SetValueName('rhs')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        cinstr = builder.BuildSExt(i32.ConstNull(), i64)
        assert isinstance(cinstr, llpy.core.ConstantInt)
        assert cinstr is i64.ConstNull()

        instr = builder.BuildSExt(rhs, i64, 'rv')
        assert isinstance(instr, llpy.core.SExtInst)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.SExt
        assert instr.TypeOf() is i64

        assert instr.GetNumOperands() == 1
        assert instr.GetOperand(0) is rhs

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define i64 @func(i32 %rhs) {
  %rv = sext i32 %rhs to i64
  ret i64 %rv
}

''')

    def test_BuildFPToUI(self):
        builder = self.builder
        i32 = llpy.core.IntegerType(self.ctx, 32)
        double = llpy.core.DoubleType(self.ctx)
        func_type = llpy.core.FunctionType(i32, [double])
        func = self.mod.AddFunction(func_type, 'func')
        rhs = func.GetParam(0)
        rhs.SetValueName('rhs')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        cinstr = builder.BuildFPToUI(double.ConstNull(), i32)
        assert isinstance(cinstr, llpy.core.ConstantInt)
        assert cinstr is i32.ConstNull()

        instr = builder.BuildFPToUI(rhs, i32, 'rv')
        assert isinstance(instr, llpy.core.FPToUIInst)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.FPToUI
        assert instr.TypeOf() is i32

        assert instr.GetNumOperands() == 1
        assert instr.GetOperand(0) is rhs

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define i32 @func(double %rhs) {
  %rv = fptoui double %rhs to i32
  ret i32 %rv
}

''')

    def test_BuildFPToSI(self):
        builder = self.builder
        i32 = llpy.core.IntegerType(self.ctx, 32)
        double = llpy.core.DoubleType(self.ctx)
        func_type = llpy.core.FunctionType(i32, [double])
        func = self.mod.AddFunction(func_type, 'func')
        rhs = func.GetParam(0)
        rhs.SetValueName('rhs')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        cinstr = builder.BuildFPToSI(double.ConstNull(), i32)
        assert isinstance(cinstr, llpy.core.ConstantInt)
        assert cinstr is i32.ConstNull()

        instr = builder.BuildFPToSI(rhs, i32, 'rv')
        assert isinstance(instr, llpy.core.FPToSIInst)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.FPToSI
        assert instr.TypeOf() is i32

        assert instr.GetNumOperands() == 1
        assert instr.GetOperand(0) is rhs

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define i32 @func(double %rhs) {
  %rv = fptosi double %rhs to i32
  ret i32 %rv
}

''')

    def test_BuildUIToFP(self):
        builder = self.builder
        i32 = llpy.core.IntegerType(self.ctx, 32)
        double = llpy.core.DoubleType(self.ctx)
        func_type = llpy.core.FunctionType(double, [i32])
        func = self.mod.AddFunction(func_type, 'func')
        rhs = func.GetParam(0)
        rhs.SetValueName('rhs')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        cinstr = builder.BuildUIToFP(i32.ConstNull(), double)
        assert isinstance(cinstr, llpy.core.ConstantFP)
        assert cinstr is double.ConstNull()

        instr = builder.BuildUIToFP(rhs, double, 'rv')
        assert isinstance(instr, llpy.core.UIToFPInst)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.UIToFP
        assert instr.TypeOf() is double

        assert instr.GetNumOperands() == 1
        assert instr.GetOperand(0) is rhs

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define double @func(i32 %rhs) {
  %rv = uitofp i32 %rhs to double
  ret double %rv
}

''')

    def test_BuildSIToFP(self):
        builder = self.builder
        i32 = llpy.core.IntegerType(self.ctx, 32)
        double = llpy.core.DoubleType(self.ctx)
        func_type = llpy.core.FunctionType(double, [i32])
        func = self.mod.AddFunction(func_type, 'func')
        rhs = func.GetParam(0)
        rhs.SetValueName('rhs')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        cinstr = builder.BuildSIToFP(i32.ConstNull(), double)
        assert isinstance(cinstr, llpy.core.ConstantFP)
        assert cinstr is double.ConstNull()

        instr = builder.BuildSIToFP(rhs, double, 'rv')
        assert isinstance(instr, llpy.core.SIToFPInst)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.SIToFP
        assert instr.TypeOf() is double

        assert instr.GetNumOperands() == 1
        assert instr.GetOperand(0) is rhs

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define double @func(i32 %rhs) {
  %rv = sitofp i32 %rhs to double
  ret double %rv
}

''')

    def test_BuildFPTrunc(self):
        builder = self.builder
        float = llpy.core.FloatType(self.ctx)
        double = llpy.core.DoubleType(self.ctx)
        func_type = llpy.core.FunctionType(float, [double])
        func = self.mod.AddFunction(func_type, 'func')
        rhs = func.GetParam(0)
        rhs.SetValueName('rhs')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        cinstr = builder.BuildFPTrunc(double.ConstNull(), float)
        assert isinstance(cinstr, llpy.core.ConstantFP)
        assert cinstr is float.ConstNull()

        instr = builder.BuildFPTrunc(rhs, float, 'rv')
        assert isinstance(instr, llpy.core.FPTruncInst)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.FPTrunc
        assert instr.TypeOf() is float

        assert instr.GetNumOperands() == 1
        assert instr.GetOperand(0) is rhs

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define float @func(double %rhs) {
  %rv = fptrunc double %rhs to float
  ret float %rv
}

''')

    def test_BuildFPExt(self):
        builder = self.builder
        float = llpy.core.FloatType(self.ctx)
        double = llpy.core.DoubleType(self.ctx)
        func_type = llpy.core.FunctionType(double, [float])
        func = self.mod.AddFunction(func_type, 'func')
        rhs = func.GetParam(0)
        rhs.SetValueName('rhs')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        cinstr = builder.BuildFPExt(float.ConstNull(), double)
        assert isinstance(cinstr, llpy.core.ConstantFP)
        assert cinstr is double.ConstNull()

        instr = builder.BuildFPExt(rhs, double, 'rv')
        assert isinstance(instr, llpy.core.FPExtInst)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.FPExt
        assert instr.TypeOf() is double

        assert instr.GetNumOperands() == 1
        assert instr.GetOperand(0) is rhs

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define double @func(float %rhs) {
  %rv = fpext float %rhs to double
  ret double %rv
}

''')

    def test_BuildPtrToInt(self):
        builder = self.builder
        i32 = llpy.core.IntegerType(self.ctx, 32)
        i32p = llpy.core.PointerType(i32)
        func_type = llpy.core.FunctionType(i32, [i32p])
        func = self.mod.AddFunction(func_type, 'func')
        rhs = func.GetParam(0)
        rhs.SetValueName('rhs')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        cinstr = builder.BuildPtrToInt(i32p.ConstPointerNull(), i32)
        assert isinstance(cinstr, llpy.core.ConstantInt)
        assert cinstr is i32.ConstNull()

        instr = builder.BuildPtrToInt(rhs, i32, 'rv')
        assert isinstance(instr, llpy.core.PtrToIntInst)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.PtrToInt
        assert instr.TypeOf() is i32

        assert instr.GetNumOperands() == 1
        assert instr.GetOperand(0) is rhs

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define i32 @func(i32* %rhs) {
  %rv = ptrtoint i32* %rhs to i32
  ret i32 %rv
}

''')

    def test_BuildIntToPtr(self):
        builder = self.builder
        i32 = llpy.core.IntegerType(self.ctx, 32)
        i32p = llpy.core.PointerType(i32)
        func_type = llpy.core.FunctionType(i32p, [i32])
        func = self.mod.AddFunction(func_type, 'func')
        rhs = func.GetParam(0)
        rhs.SetValueName('rhs')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        cinstr = builder.BuildIntToPtr(i32.ConstNull(), i32p)
        assert isinstance(cinstr, llpy.core.ConstantPointerNull)
        assert cinstr is i32p.ConstPointerNull()

        instr = builder.BuildIntToPtr(rhs, i32p, 'rv')
        assert isinstance(instr, llpy.core.IntToPtrInst)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.IntToPtr
        assert instr.TypeOf() is i32p

        assert instr.GetNumOperands() == 1
        assert instr.GetOperand(0) is rhs

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define i32* @func(i32 %rhs) {
  %rv = inttoptr i32 %rhs to i32*
  ret i32* %rv
}

''')

    def test_BuildBitCast(self):
        builder = self.builder
        i8p = llpy.core.PointerType(llpy.core.IntegerType(self.ctx, 8))
        i32p = llpy.core.PointerType(llpy.core.IntegerType(self.ctx, 32))
        func_type = llpy.core.FunctionType(i8p, [i32p])
        func = self.mod.AddFunction(func_type, 'func')
        rhs = func.GetParam(0)
        rhs.SetValueName('rhs')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        cinstr = builder.BuildBitCast(i32p.ConstNull(), i8p)
        assert isinstance(cinstr, llpy.core.ConstantPointerNull)
        assert cinstr is i8p.ConstPointerNull()

        assert rhs is builder.BuildBitCast(rhs, i32p)

        instr = builder.BuildBitCast(rhs, i8p, 'rv')
        assert isinstance(instr, llpy.core.BitCastInst)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.BitCast
        assert instr.TypeOf() is i8p

        assert instr.GetNumOperands() == 1
        assert instr.GetOperand(0) is rhs

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define i8* @func(i32* %rhs) {
  %rv = bitcast i32* %rhs to i8*
  ret i8* %rv
}

''')

    if (3, 4) <= _version:
        def test_BuildAddrSpaceCast(self):
            builder = self.builder
            i32p1 = llpy.core.PointerType(llpy.core.IntegerType(self.ctx, 32), 1)
            i32p = llpy.core.PointerType(llpy.core.IntegerType(self.ctx, 32))
            func_type = llpy.core.FunctionType(i32p1, [i32p])
            func = self.mod.AddFunction(func_type, 'func')
            rhs = func.GetParam(0)
            rhs.SetValueName('rhs')
            bb = func.AppendBasicBlock()
            builder.PositionBuilderAtEnd(bb)

            cinstr = builder.BuildAddrSpaceCast(i32p.ConstNull(), i32p1)
            assert isinstance(cinstr, llpy.core.ConstantPointerNull)
            assert cinstr is i32p1.ConstPointerNull()

            assert rhs is builder.BuildAddrSpaceCast(rhs, i32p)

            instr = builder.BuildAddrSpaceCast(rhs, i32p1, 'rv')
            assert isinstance(instr, llpy.core.AddrSpaceCastInst)
            assert instr.GetInstructionParent() is bb
            assert instr.GetInstructionOpcode() == llpy.core.Opcode.AddrSpaceCast
            assert instr.TypeOf() is i32p1

            assert instr.GetNumOperands() == 1
            assert instr.GetOperand(0) is rhs

            builder.BuildRet(instr)
            self.assertDump(func,
'''
define i32 addrspace(1)* @func(i32* %rhs) {
  %rv = addrspacecast i32* %rhs to i32 addrspace(1)*
  ret i32 addrspace(1)* %rv
}

''')

    @unittest.expectedFailure
    def test_BuildZExtOrBitCast(self):
        raise NotImplementedError
        builder = self.builder
        instr = builder.BuildZExtOrBitCast(rhs, ty, name)

    @unittest.expectedFailure
    def test_BuildSExtOrBitCast(self):
        raise NotImplementedError
        builder = self.builder
        instr = builder.BuildSExtOrBitCast(rhs, ty, name)

    @unittest.expectedFailure
    def test_BuildTruncOrBitCast(self):
        raise NotImplementedError
        builder = self.builder
        instr = builder.BuildTruncOrBitCast(rhs, ty, name)

    @unittest.expectedFailure
    def test_BuildCast(self):
        raise NotImplementedError
        builder = self.builder
        instr = builder.BuildCast(op, rhs, ty, name)

    @unittest.expectedFailure
    def test_BuildPointerCast(self):
        raise NotImplementedError
        builder = self.builder
        instr = builder.BuildPointerCast(rhs, ty, name)

    @unittest.expectedFailure
    def test_BuildIntCast(self):
        raise NotImplementedError
        builder = self.builder
        instr = builder.BuildIntCast(rhs, ty, name)

    @unittest.expectedFailure
    def test_BuildFPCast(self):
        raise NotImplementedError
        builder = self.builder
        instr = builder.BuildFPCast(rhs, ty, name)

    # Comparisons
    def test_BuildICmp(self):
        builder = self.builder
        i1 = llpy.core.IntegerType(self.ctx, 1)
        i2 = llpy.core.IntegerType(self.ctx, 2)
        func_type = llpy.core.FunctionType(i1, [i2, i2])

        ins = [(x, i2.ConstInt(x)) for x in range(4)]
        outs = [i1.ConstInt(bool(x)) for x in range(2)]
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

            func = self.mod.AddFunction(func_type, op)
            lhs = func.GetParam(0)
            lhs.SetValueName('lhs')
            rhs = func.GetParam(1)
            rhs.SetValueName('rhs')
            bb = func.AppendBasicBlock()
            builder.PositionBuilderAtEnd(bb)

            for i, (a, arg) in enumerate(ins):
                for j, (b, brg) in enumerate(ins):
                    cinstr = builder.BuildICmp(pred, arg, brg)
                    r = calc(a, b)
                    assert cinstr is outs[r]

            instr = builder.BuildICmp(pred, lhs, rhs, 'rv')
            assert isinstance(instr, llpy.core.ICmpInst)
            assert instr.GetInstructionParent() is bb
            assert instr.GetInstructionOpcode() == llpy.core.Opcode.ICmp
            assert instr.GetICmpPredicate() == pred
            assert instr.TypeOf() is i1

            assert instr.GetNumOperands() == 2
            assert instr.GetOperand(0) is lhs
            assert instr.GetOperand(1) is rhs

            builder.BuildRet(instr)
            self.assertDump(func,
'''
define i1 @{op}(i2 %lhs, i2 %rhs) {{
  %rv = icmp {op} i2 %lhs, %rhs
  ret i1 %rv
}}

'''.format(op=op))

    def test_BuildFCmp(self):
        builder = self.builder
        i1 = llpy.core.IntegerType(self.ctx, 1)
        double = llpy.core.DoubleType(self.ctx)
        func_type = llpy.core.FunctionType(i1, [double, double])

        ins = [(x, double.ConstReal(x)) for x in [float('nan'), float('-inf'), float('inf'), -2.0, -1.0, -0.0, 0.0, 1.0, 2.0]]
        outs = [i1.ConstInt(x) for x in range(2)]
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

            func = self.mod.AddFunction(func_type, op)
            lhs = func.GetParam(0)
            lhs.SetValueName('lhs')
            rhs = func.GetParam(1)
            rhs.SetValueName('rhs')
            bb = func.AppendBasicBlock()
            builder.PositionBuilderAtEnd(bb)

            for i, (a, arg) in enumerate(ins):
                for j, (b, brg) in enumerate(ins):
                    cinstr = builder.BuildFCmp(pred, arg, brg)
                    r = calc(a, b)
                    assert cinstr is outs[r]

            instr = builder.BuildFCmp(pred, lhs, rhs, 'rv')
            assert isinstance(instr, llpy.core.FCmpInst)
            assert instr.GetInstructionParent() is bb
            assert instr.GetInstructionOpcode() == llpy.core.Opcode.FCmp
            if False: # not exposed in tested version
                assert instr.GetFCmpPredicate() == pred
            assert instr.TypeOf() is i1

            if False: # build and const differ here
                if pred == llpy.core.RealPredicate.FALSE:
                    assert instr is self.false
                    continue
                if pred == llpy.core.RealPredicate.TRUE:
                    assert instr is self.true
                    continue

            assert instr.GetNumOperands() == 2
            assert instr.GetOperand(0) is lhs
            assert instr.GetOperand(1) is rhs

            builder.BuildRet(instr)
            self.assertDump(func,
'''
define i1 @{op}(double %lhs, double %rhs) {{
  %rv = fcmp {op} double %lhs, %rhs
  ret i1 %rv
}}

'''.format(op=op))

    # Miscellaneous instructions
    def test_BuildPhi(self):
        builder = self.builder
        i1 = llpy.core.IntegerType(self.ctx, 1)
        i32 = llpy.core.IntegerType(self.ctx, 32)
        func_type = llpy.core.FunctionType(i32, [i32, i32, i1])
        func = self.mod.AddFunction(func_type, 'func')
        va = func.GetParam(0)
        va.SetValueName('va')
        vb = func.GetParam(1)
        vb.SetValueName('vb')
        vc = func.GetParam(2)
        vc.SetValueName('vc')
        bb = func.AppendBasicBlock('entry')
        la = func.AppendBasicBlock('la')
        lb = func.AppendBasicBlock('lb')
        lc = func.AppendBasicBlock('lc')
        builder.PositionBuilderAtEnd(bb)
        builder.BuildCondBr(vc, la, lb)
        builder.PositionBuilderAtEnd(la)
        builder.BuildBr(lc)
        builder.PositionBuilderAtEnd(lb)
        builder.BuildBr(lc)
        builder.PositionBuilderAtEnd(lc)

        instr = builder.BuildPhi(i32, 'vd')
        assert isinstance(instr, llpy.core.PHINode)
        assert instr.GetInstructionParent() is lc
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.PHI
        assert instr.GetNumOperands() == 0
        assert instr.TypeOf() is i32

        assert instr.CountIncoming() == 0

        instr.AddIncoming([va, vb], [la, lb])

        assert instr.CountIncoming() == 2
        assert instr.GetIncomingValue(0) is va
        assert instr.GetIncomingBlock(0) is la
        assert instr.GetIncomingValue(1) is vb
        assert instr.GetIncomingBlock(1) is lb

        assert instr.GetNumOperands() == 2
        assert instr.GetOperand(0) is va
        assert instr.GetOperand(1) is vb

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define i32 @func(i32 %va, i32 %vb, i1 %vc) {
entry:
  br i1 %vc, label %la, label %lb

la:                                               ; preds = %entry
  br label %lc

lb:                                               ; preds = %entry
  br label %lc

lc:                                               ; preds = %lb, %la
  %vd = phi i32 [ %va, %la ], [ %vb, %lb ]
  ret i32 %vd
}

''')

    def test_BuildCall(self):
        builder = self.builder
        i32 = llpy.core.IntegerType(self.ctx, 32)
        void = llpy.core.VoidType(self.ctx)
        func_type = llpy.core.FunctionType(i32, [])
        vfunc_type = llpy.core.FunctionType(void, [i32, i32])
        ifunc = self.mod.AddFunction(func_type, 'ifunc')
        vfunc = self.mod.AddFunction(vfunc_type, 'vfunc')
        func = self.mod.AddFunction(func_type, 'func')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        instr = builder.BuildCall(ifunc, [], 'rv')
        assert isinstance(instr, llpy.core.CallInst)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.Call
        assert instr.TypeOf() is i32

        assert instr.GetNumOperands() == 1
        assert instr.GetOperand(0) is ifunc

        vinstr = builder.BuildCall(vfunc, [instr, instr])
        assert isinstance(vinstr, llpy.core.CallInst)
        assert vinstr.GetInstructionParent() is bb
        assert vinstr.GetInstructionOpcode() == llpy.core.Opcode.Call
        assert vinstr.TypeOf() is void

        assert vinstr.GetNumOperands() == 3
        assert vinstr.GetOperand(0) is instr
        assert vinstr.GetOperand(1) is instr
        assert vinstr.GetOperand(2) is vfunc

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define i32 @func() {
  %rv = call i32 @ifunc()
  call void @vfunc(i32 %rv, i32 %rv)
  ret i32 %rv
}

''')

    # tested in test_BuildIndirectBr
    def test_BuildSelect(self):
        pass

    @unittest.expectedFailure
    def test_BuildVAArg(self):
        raise NotImplementedError
        builder = self.builder
        instr = builder.BuildVAArg(lst, ty, name)

    def test_BuildExtractElement(self):
        builder = self.builder
        i32 = llpy.core.IntegerType(self.ctx, 32)
        i32v = llpy.core.VectorType(i32, 2)
        func_type = llpy.core.FunctionType(i32, [i32v, i32])
        func = self.mod.AddFunction(func_type, 'func')
        arg = func.GetParam(0)
        arg.SetValueName('arg')
        idx = func.GetParam(1)
        idx.SetValueName('idx')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        cinstr = builder.BuildExtractElement(llpy.core.ConstVector([i32.ConstInt(1), i32.ConstInt(2)]), i32.ConstNull())
        assert isinstance(cinstr, llpy.core.ConstantInt)
        assert cinstr is i32.ConstInt(1)
        assert cinstr.TypeOf() is i32

        instr = builder.BuildExtractElement(arg, idx, 'rv')
        assert isinstance(instr, llpy.core.ExtractElementInst)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.ExtractElement
        assert instr.TypeOf() is i32

        assert instr.GetNumOperands() == 2
        assert instr.GetOperand(0) is arg
        assert instr.GetOperand(1) is idx

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define i32 @func(<2 x i32> %arg, i32 %idx) {
  %rv = extractelement <2 x i32> %arg, i32 %idx
  ret i32 %rv
}

''')

    def test_BuildInsertElement(self):
        builder = self.builder
        i32 = llpy.core.IntegerType(self.ctx, 32)
        i32v = llpy.core.VectorType(i32, 2)
        func_type = llpy.core.FunctionType(i32v, [i32v, i32, i32])
        func = self.mod.AddFunction(func_type, 'func')
        arg = func.GetParam(0)
        arg.SetValueName('arg')
        idx = func.GetParam(1)
        idx.SetValueName('idx')
        val = func.GetParam(2)
        val.SetValueName('val')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        cinstr = builder.BuildInsertElement(llpy.core.ConstVector([i32.ConstInt(3), i32.ConstInt(2)]), i32.ConstInt(1), i32.ConstNull())
        if (3, 1) <= _version:
            assert isinstance(cinstr, llpy.core.ConstantDataVector)
        if _version <= (3, 0):
            assert isinstance(cinstr, llpy.core.ConstantVector)
        assert cinstr is llpy.core.ConstVector([i32.ConstInt(1), i32.ConstInt(2)])
        assert cinstr.TypeOf() is i32v

        instr = builder.BuildInsertElement(arg, val, idx, 'rv')
        assert isinstance(instr, llpy.core.InsertElementInst)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.InsertElement
        assert instr.TypeOf() is i32v

        assert instr.GetNumOperands() == 3
        assert instr.GetOperand(0) is arg
        assert instr.GetOperand(1) is val
        assert instr.GetOperand(2) is idx

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define <2 x i32> @func(<2 x i32> %arg, i32 %idx, i32 %val) {
  %rv = insertelement <2 x i32> %arg, i32 %val, i32 %idx
  ret <2 x i32> %rv
}

''')

    def test_BuildShuffleVector(self):
        builder = self.builder
        i32 = llpy.core.IntegerType(self.ctx, 32)
        v2t = llpy.core.VectorType(i32, 2)
        v4t = llpy.core.VectorType(i32, 4)
        func_type = llpy.core.FunctionType(v4t, [v2t, v2t])
        func = self.mod.AddFunction(func_type, 'func')
        v1 = func.GetParam(0)
        v1.SetValueName('v1')
        v2 = func.GetParam(1)
        v2.SetValueName('v2')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        a = i32.ConstInt(~0)
        b = i32.ConstInt(~1)
        c = i32.ConstInt(~2)
        d = i32.ConstInt(~3)

        e = i32.ConstInt(0)
        f = i32.ConstInt(1)
        g = i32.ConstInt(2)
        h = i32.ConstInt(3)

        mask = llpy.core.ConstVector([e, g, h, f])

        cinstr = builder.BuildShuffleVector(
                llpy.core.ConstVector([a, b]),
                llpy.core.ConstVector([c, d]),
                mask)
        if (3, 1) <= _version:
            assert isinstance(cinstr, llpy.core.ConstantDataVector)
        if _version <= (3, 0):
            assert isinstance(cinstr, llpy.core.ConstantVector)
        assert cinstr is llpy.core.ConstVector([a, c, d, b])
        assert cinstr.TypeOf() is v4t

        instr = builder.BuildShuffleVector(v1, v2, mask, 'rv')
        assert isinstance(instr, llpy.core.ShuffleVectorInst)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.ShuffleVector
        assert instr.TypeOf() is v4t

        assert instr.GetNumOperands() == 3
        assert instr.GetOperand(0) is v1
        assert instr.GetOperand(1) is v2
        assert instr.GetOperand(2) is mask

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define <4 x i32> @func(<2 x i32> %v1, <2 x i32> %v2) {
  %rv = shufflevector <2 x i32> %v1, <2 x i32> %v2, <4 x i32> <i32 0, i32 2, i32 3, i32 1>
  ret <4 x i32> %rv
}

''')

    def test_BuildExtractValue(self):
        builder = self.builder
        i32 = llpy.core.IntegerType(self.ctx, 32)
        i32a = llpy.core.ArrayType(i32, 2)
        func_type = llpy.core.FunctionType(i32, [i32a])
        func = self.mod.AddFunction(func_type, 'func')
        arg = func.GetParam(0)
        arg.SetValueName('arg')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        cinstr = builder.BuildExtractValue(i32.ConstArray([i32.ConstInt(1), i32.ConstInt(2)]), 0)
        assert isinstance(cinstr, llpy.core.ConstantInt)
        assert cinstr is i32.ConstInt(1)
        assert cinstr.TypeOf() is i32

        instr = builder.BuildExtractValue(arg, 1, 'rv')
        assert isinstance(instr, llpy.core.ExtractValueInst)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.ExtractValue
        assert instr.TypeOf() is i32

        assert instr.GetNumOperands() == 1
        assert instr.GetOperand(0) is arg

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define i32 @func([2 x i32] %arg) {
  %rv = extractvalue [2 x i32] %arg, 1
  ret i32 %rv
}

''')

    def test_BuildInsertValue(self):
        builder = self.builder
        i32 = llpy.core.IntegerType(self.ctx, 32)
        i32a = llpy.core.ArrayType(i32, 2)
        func_type = llpy.core.FunctionType(i32a, [i32a, i32])
        func = self.mod.AddFunction(func_type, 'func')
        arg = func.GetParam(0)
        arg.SetValueName('arg')
        val = func.GetParam(1)
        val.SetValueName('val')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        cinstr = builder.BuildInsertValue(i32.ConstArray([i32.ConstInt(3), i32.ConstInt(2)]), i32.ConstInt(1), 0)
        if (3, 1) <= _version:
            assert isinstance(cinstr, llpy.core.ConstantDataArray)
        if _version <= (3, 0):
            assert isinstance(cinstr, llpy.core.ConstantArray)
        assert cinstr is i32.ConstArray([i32.ConstInt(1), i32.ConstInt(2)])
        assert cinstr.TypeOf() is i32a

        instr = builder.BuildInsertValue(arg, val, 1, 'rv')
        assert isinstance(instr, llpy.core.InsertValueInst)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.InsertValue
        assert instr.TypeOf() is i32a

        assert instr.GetNumOperands() == 2
        assert instr.GetOperand(0) is arg
        assert instr.GetOperand(1) is val

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define [2 x i32] @func([2 x i32] %arg, i32 %val) {
  %rv = insertvalue [2 x i32] %arg, i32 %val, 1
  ret [2 x i32] %rv
}

''')

    def test_BuildIsNull(self):
        builder = self.builder
        i1 = llpy.core.IntegerType(self.ctx, 1)
        i1p = llpy.core.PointerType(i1)
        null = i1p.ConstPointerNull()
        func_type = llpy.core.FunctionType(i1, [i1p])
        func = self.mod.AddFunction(func_type, 'func')
        arg = func.GetParam(0)
        arg.SetValueName('arg')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        cinstr = builder.BuildIsNull(null)
        assert cinstr is i1.ConstAllOnes()

        instr = builder.BuildIsNull(arg, 'rv')
        assert isinstance(instr, llpy.core.ICmpInst)
        assert instr.GetICmpPredicate() == llpy.core.IntPredicate.EQ
        assert instr.GetNumOperands() == 2
        assert instr.GetOperand(0) is arg
        assert instr.GetOperand(1) is null

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define i1 @func(i1* %arg) {
  %rv = icmp eq i1* %arg, null
  ret i1 %rv
}

''')

    def test_BuildIsNotNull(self):
        builder = self.builder
        i1 = llpy.core.IntegerType(self.ctx, 1)
        i1p = llpy.core.PointerType(i1)
        null = i1p.ConstPointerNull()
        func_type = llpy.core.FunctionType(i1, [i1p])
        func = self.mod.AddFunction(func_type, 'func')
        arg = func.GetParam(0)
        arg.SetValueName('arg')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        cinstr = builder.BuildIsNotNull(null)
        assert cinstr is i1.ConstNull()

        instr = builder.BuildIsNotNull(arg, 'rv')
        assert isinstance(instr, llpy.core.ICmpInst)
        assert instr.GetICmpPredicate() == llpy.core.IntPredicate.NE
        assert instr.GetNumOperands() == 2
        assert instr.GetOperand(0) is arg
        assert instr.GetOperand(1) is null

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define i1 @func(i1* %arg) {
  %rv = icmp ne i1* %arg, null
  ret i1 %rv
}

''')

    def test_BuildPtrDiff(self):
        builder = self.builder
        i64 = llpy.core.IntegerType(self.ctx, 64)
        i64p = llpy.core.PointerType(i64)
        func_type = llpy.core.FunctionType(i64, [i64p, i64p])
        func = self.mod.AddFunction(func_type, 'func')
        lhs = func.GetParam(0)
        lhs.SetValueName('lhs')
        rhs = func.GetParam(1)
        rhs.SetValueName('rhs')
        bb = func.AppendBasicBlock()
        builder.PositionBuilderAtEnd(bb)

        instr = builder.BuildPtrDiff(lhs, rhs, 'rv')
        assert isinstance(instr, llpy.core.BinaryOperator)
        assert instr.GetInstructionParent() is bb
        assert instr.GetInstructionOpcode() == llpy.core.Opcode.SDiv
        assert instr.TypeOf() is i64

        assert instr.GetNumOperands() == 2
        diff = instr.GetOperand(0)
        size = instr.GetOperand(1)
        assert size is i64.SizeOf()

        assert isinstance(diff, llpy.core.BinaryOperator)
        assert diff.GetInstructionOpcode() == llpy.core.Opcode.Sub
        assert diff.GetNumOperands() == 2
        lhs_ = diff.GetOperand(0)
        rhs_ = diff.GetOperand(1)

        assert isinstance(lhs_, llpy.core.PtrToIntInst)
        assert isinstance(rhs_, llpy.core.PtrToIntInst)
        assert lhs_.GetNumOperands() == 1
        assert rhs_.GetNumOperands() == 1
        assert lhs_.GetOperand(0) is lhs
        assert rhs_.GetOperand(0) is rhs

        builder.BuildRet(instr)
        self.assertDump(func,
'''
define i64 @func(i64* %lhs, i64* %rhs) {
  %1 = ptrtoint i64* %lhs to i64
  %2 = ptrtoint i64* %rhs to i64
  %3 = sub i64 %1, %2
  %rv = sdiv exact i64 %3, ptrtoint (i64* getelementptr (i64* null, i32 1) to i64)
  ret i64 %rv
}

''')

    if (3, 3) <= _version:
        def test_BuildAtomicRMW(self):
            AtomicRMWBinOp = llpy.core.AtomicRMWBinOp
            AtomicOrdering = llpy.core.AtomicOrdering
            ops = [
                'Xchg',
                'Add',
                'Sub',
                'And',
                'Nand',
                'Or',
                'Xor',
                'Max',
                'Min',
                'UMax',
                'UMin',
            ]
            orders = [
                ('NotAtomic', ''),
                ('Unordered', 'unordered'),
                ('Monotonic', 'monotonic'),
                ('Acquire', 'acquire'),
                ('Release', 'release'),
                ('AcquireRelease', 'acq_rel'),
                ('SequentiallyConsistent', 'seq_cst'),
            ]
            threads = [True, False]
            for (op_name, order_name, single) in product(ops, orders, threads):
                op = getattr(AtomicRMWBinOp, op_name)
                order = getattr(AtomicOrdering, order_name[0])
                op_name = op_name.lower()
                order_name = order_name[1]
                if order_name:
                    order_name = ' ' + order_name
                    if single:
                        order_name = ' singlethread' + order_name

                builder = self.builder
                i32 = llpy.core.IntegerType(self.ctx, 32)
                i32p = llpy.core.PointerType(i32)
                func_type = llpy.core.FunctionType(i32, [i32p, i32])
                func = self.mod.AddFunction(func_type, 'func')
                ptr = func.GetParam(0)
                ptr.SetValueName('ptr')
                val = func.GetParam(1)
                val.SetValueName('val')
                bb = func.AppendBasicBlock()
                builder.PositionBuilderAtEnd(bb)

                old = builder.BuildAtomicRMW(op, ptr, val, order, single, 'old')
                builder.BuildRet(old)
                self.assertDump(func,
'''
define i32 @func(i32* %ptr, i32 %val) {{
  %old = atomicrmw {op} i32* %ptr, i32 %val{order}
  ret i32 %old
}}

'''.format(op=op_name, order=order_name))
                func.SetValueName('')


    if (3, 5) <= _version:
        def test_BuildFence(self):
            AtomicOrdering = llpy.core.AtomicOrdering
            orders = [
                ('NotAtomic', ''),
                ('Unordered', 'unordered'),
                ('Monotonic', 'monotonic'),
                ('Acquire', 'acquire'),
                ('Release', 'release'),
                ('AcquireRelease', 'acq_rel'),
                ('SequentiallyConsistent', 'seq_cst'),
            ]
            threads = [True, False]
            for (order_name, single) in product(orders, threads):
                order = getattr(AtomicOrdering, order_name[0])
                order_name = order_name[1]
                if order_name:
                    order_name = ' ' + order_name
                    if single:
                        order_name = ' singlethread' + order_name

                builder = self.builder
                void = llpy.core.VoidType(self.ctx)
                func_type = llpy.core.FunctionType(void, [])
                func = self.mod.AddFunction(func_type, 'func')
                bb = func.AppendBasicBlock()
                builder.PositionBuilderAtEnd(bb)

                builder.BuildFence(order, single)
                builder.BuildRetVoid()
                self.assertDump(func,
'''
define void @func() {{
  fence{order}
  ret void
}}

'''.format(order=order_name))
                func.SetValueName('')

if __name__ == '__main__':
    unittest.main()
