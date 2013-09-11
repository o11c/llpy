#!/usr/bin/env python3

import gc
import unittest

import llpy.core
import llpy.target

class TestTargetData(unittest.TestCase):

    # the string for x86
    tds = 'e-p:32:32:32-i1:8:8-i8:8:8-i16:16:16-i32:32:32-i64:32:64-f32:32:32-f64:32:64-v64:64:64-v128:128:128-a0:0:64-f80:32:32-n8:16:32-S128'

    def setUp(self):
        self.td = llpy.target.TargetData(self.tds)

    def tearDown(self):
        del self.td
        gc.collect()

    @unittest.skip('NYI')
    def testAdd(self):
        pass # needs pass manager

    def test_StringRep(self):
        assert set(self.td.StringRep()) == set(self.tds)

    def test_ByteOrder(self):
        assert self.td.ByteOrder() == llpy.target.ByteOrdering.LittleEndian

    def test_PointerSize(self):
        assert self.td.PointerSize() == 4
        assert self.td.PointerSize(1) == 4

    def test_type_sizes(self):
        ctx = llpy.core.Context()
        mod = llpy.core.Module(ctx, 'TestTargetData.test_type_sizes')

        i8 = llpy.core.IntegerType(ctx, 8)
        i56 = llpy.core.IntegerType(ctx, 56)
        i64 = llpy.core.IntegerType(ctx, 64)
        f80 = llpy.core.X86FP80Type(ctx)
        st = llpy.core.StructType(ctx, [i8, i64], None)

        assert self.td.SizeOfTypeInBits(i8) == 8
        assert self.td.SizeOfTypeInBits(i56) == 56
        assert self.td.SizeOfTypeInBits(i64) == 64
        assert self.td.SizeOfTypeInBits(f80) == 80
        assert self.td.SizeOfTypeInBits(st) == 96

        assert self.td.StoreSizeOfType(i8) == 1
        assert self.td.StoreSizeOfType(i56) == 7
        assert self.td.StoreSizeOfType(i64) == 8
        assert self.td.StoreSizeOfType(f80) == 10
        assert self.td.StoreSizeOfType(st) == 12

        assert self.td.ABISizeOfType(i8) == 1
        assert self.td.ABISizeOfType(i56) == 8
        assert self.td.ABISizeOfType(i64) == 8
        assert self.td.ABISizeOfType(f80) == 12
        assert self.td.ABISizeOfType(st) == 12

        assert self.td.ABIAlignmentOfType(i8) == 1
        assert self.td.ABIAlignmentOfType(i56) == 4
        assert self.td.ABIAlignmentOfType(i64) == 4
        assert self.td.ABIAlignmentOfType(f80) == 4
        assert self.td.ABIAlignmentOfType(st) == 4

        assert self.td.CallFrameAlignmentOfType(i8) == 1
        assert self.td.CallFrameAlignmentOfType(i56) == 4
        assert self.td.CallFrameAlignmentOfType(i64) == 4
        assert self.td.CallFrameAlignmentOfType(f80) == 4
        assert self.td.CallFrameAlignmentOfType(st) == 4

        assert self.td.PreferredAlignmentOfType(i8) == 1
        assert self.td.PreferredAlignmentOfType(i56) == 8
        assert self.td.PreferredAlignmentOfType(i64) == 8
        assert self.td.PreferredAlignmentOfType(f80) == 4
        assert self.td.PreferredAlignmentOfType(st) == 8

        assert self.td.PreferredAlignmentOfGlobal(mod.AddGlobal(i8)) == 1
        assert self.td.PreferredAlignmentOfGlobal(mod.AddGlobal(i56)) == 8
        assert self.td.PreferredAlignmentOfGlobal(mod.AddGlobal(i64)) == 8
        assert self.td.PreferredAlignmentOfGlobal(mod.AddGlobal(f80)) == 4
        assert self.td.PreferredAlignmentOfGlobal(mod.AddGlobal(st)) == 8

    def test_offset(self):
        ctx = llpy.core.Context()
        i8 = llpy.core.IntegerType(ctx, 8)
        i64 = llpy.core.IntegerType(ctx, 64)
        st = llpy.core.StructType(ctx, [i8, i64], None)
        assert self.td.OffsetOfElement(st, 1) == 4
        assert self.td.ElementAtOffset(st, 4) == 1

@unittest.skip('NYI')
class TestTargetInit(unittest.TestCase):

    def test_add(self):
        pass

    def test_init(self):
        pass
