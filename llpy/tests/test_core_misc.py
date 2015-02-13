#!/usr/bin/env python3
from __future__ import unicode_literals

import gc
import os
import unittest

import llpy.core
from llpy.c.core import _version
from llpy.compat import long, unicode


class ReplaceOutFD(object):
    ''' Capture output send to stderr via C functions
    '''

    def __init__(self, fd):
        self.fd = fd

    def __enter__(self):
        self.saved_fd = os.dup(self.fd)
        r, w = os.pipe()
        os.dup2(w, self.fd)
        os.close(w)
        return os.fdopen(r)

    def __exit__(self, type, value, trace):
        os.dup2(self.saved_fd, self.fd)
        os.close(self.saved_fd)
        del self.saved_fd

class DumpTestCase(unittest.TestCase):

    def assertDump(self, obj, s):
        if _version <= (3, 1):
            if isinstance(obj, llpy.core.GlobalVariable):
                s += '\n'
        with ReplaceOutFD(2) as f:
            obj.Dump()
        with f:
            assert f.read() == s
        if (3, 4) <= _version:
            if isinstance(obj, llpy.core.Value):
                assert obj.PrintToString() + '\n' == s

class TestContext(DumpTestCase):

    def setUp(self):
        self.ctx = llpy.core.Context()

    def tearDown(self):
        del self.ctx
        gc.collect()

    def test_context(self):
        pass

    def test_md_kind_id(self):
        foo = self.ctx.GetMDKindID('foo')
        bar = self.ctx.GetMDKindID('bar')
        assert isinstance(foo, (int, long))
        assert isinstance(bar, (int, long))
        assert foo != bar

    def test_const_string(self):
        cs1 = self.ctx.ConstString('foo')
        cs2 = self.ctx.ConstString('foo', False)
        assert cs1 is cs2
        cs3 = self.ctx.ConstString('foo', True)
        assert isinstance(cs1, llpy.core.Constant)
        assert isinstance(cs3, llpy.core.Constant)

        self.assertDump(cs1,
r'''[4 x i8] c"foo\00"
''')

        self.assertDump(cs3,
'''[3 x i8] c"foo"
''')

    def test_const_struct(self):
        ctx = self.ctx
        cs1 = ctx.ConstStruct([])
        cs2 = ctx.ConstStruct([
                ctx.ConstString('foo'),
                ctx.ConstString('bar'),
            ],
            True)
        assert isinstance(cs1, llpy.core.ConstantAggregateZero)
        assert isinstance(cs2, llpy.core.ConstantStruct)

        self.assertDump(cs1,
'''{} zeroinitializer
''')

        self.assertDump(cs2,
r'''<{ [4 x i8], [4 x i8] }> <{ [4 x i8] c"foo\00", [4 x i8] c"bar\00" }>
''')

    def test_metadata(self):
        # This test is poorly understood
        ctx = self.ctx
        i32 = llpy.core.IntegerType(ctx, 32)
        mds = ctx.MDString('foo')
        assert isinstance(mds, llpy.core.MDString)
        assert mds.GetMDString() == 'foo'
        mdne = ctx.MDNode([])
        assert isinstance(mdne, llpy.core.MDNode)
        mdni = ctx.MDNode([i32.ConstNull()])
        assert mdni is ctx.MDNode([i32.ConstNull()])
        mdns = ctx.MDNode([mds])
        assert mdns is ctx.MDNode([mds])

        self.assertDump(mds,
'''metadata !"foo"
''')

        self.assertDump(mdne,
'''!{}

''')

        self.assertDump(mdni,
'''!{i32 0}

''')

        self.assertDump(mdns,
'''!{metadata !"foo"}

''')

class TestModule(DumpTestCase):

    def setUp(self):
        self.ctx = llpy.core.Context()
        self.mod = llpy.core.Module(self.ctx, 'TestModule')

    def tearDown(self):
        del self.mod
        del self.ctx
        gc.collect()

    def test_module(self):
        assert self.mod.GetContext() is self.ctx

        self.assertDump(self.mod,
'''; ModuleID = 'TestModule'
''')

    def test_data_layout(self):
        mod = self.mod
        layout = 'e'
        mod.SetDataLayout(layout)
        assert layout == mod.GetDataLayout()

        self.assertDump(mod,
'''; ModuleID = 'TestModule'
target datalayout = "e"
''')

    def test_target(self):
        mod = self.mod
        layout = 'quxfrob'
        mod.SetTarget(layout)
        assert layout == mod.GetTarget()

        self.assertDump(mod,
'''; ModuleID = 'TestModule'
target triple = "quxfrob"
''')

    def test_asm(self):
        mod = self.mod
        mod.SetModuleInlineAsm('\tabc def\n\tghi\n')

        self.assertDump(mod,
r'''; ModuleID = 'TestModule'

module asm "\09abc def"
module asm "\09ghi"
''')

    def test_type_by_name(self):
        st = llpy.core.StructType(self.ctx, None, 'foo')
        assert st is self.mod.GetTypeByName('foo')

    if (3, 1) <= _version:
        def test_named_metadata_operands(self):
            ctx = self.ctx
            mod = self.mod

            mdns = ctx.MDNode([ctx.MDString('foo'), ctx.MDString('bar')])
            mdne = ctx.MDNode([])
            mod.AddNamedMetadataOperand('baz', mdns)
            mod.AddNamedMetadataOperand('baz', mdne)
            mod.AddNamedMetadataOperand('qux', mdne)

            assert mod.GetNamedMetadataOperands('qwerty') == []
            assert mod.GetNamedMetadataOperands('baz') == [mdns, mdne]
            assert mod.GetNamedMetadataOperands('qux') == [mdne]

            self.assertDump(mod,
'''; ModuleID = 'TestModule'

!baz = !{!0, !1}
!qux = !{!1}

!0 = metadata !{metadata !"foo", metadata !"bar"}
!1 = metadata !{}
''')

    def test_function_name(self):
        void = llpy.core.VoidType(self.ctx)
        ft = llpy.core.FunctionType(void, [])
        f = self.mod.AddFunction(ft, 'foo')
        assert f is self.mod.GetNamedFunction('foo')

        self.assertDump(self.mod,
'''; ModuleID = 'TestModule'

declare void @foo()
''')

    def test_function_iteration(self):
        void = llpy.core.VoidType(self.ctx)
        ft = llpy.core.FunctionType(void, [])
        first = self.mod.AddFunction(ft, '')
        last = self.mod.AddFunction(ft, '')
        assert first is self.mod.GetFirstFunction()
        assert last is self.mod.GetLastFunction()
        assert first.GetPreviousFunction() is None
        assert last is first.GetNextFunction()
        assert first is last.GetPreviousFunction()
        assert last.GetNextFunction() is None

    def test_gv(self):
        i32 = llpy.core.IntegerType(self.ctx, 32)
        foo = self.mod.AddGlobal(i32, 'foo')
        assert foo is self.mod.GetNamedGlobal('foo')
        bar = self.mod.AddGlobal(i32, 'bar', 1)

        self.assertDump(self.mod,
'''; ModuleID = 'TestModule'

@foo = external global i32
@bar = external addrspace(1) global i32
''')
        assert foo is self.mod.GetFirstGlobal()
        assert bar is self.mod.GetLastGlobal()
        assert foo.GetPreviousGlobal() is None
        assert bar is foo.GetNextGlobal()
        assert foo is bar.GetPreviousGlobal()
        assert bar.GetNextGlobal() is None

    def test_alias(self):
        i32 = llpy.core.IntegerType(self.ctx, 32)
        foo = self.mod.AddGlobal(i32, 'foo')
        alias_foo = self.mod.AddAlias(foo, 'foo_alias')
        assert isinstance(alias_foo, llpy.core.GlobalAlias)

        self.assertDump(self.mod,
'''; ModuleID = 'TestModule'

@foo = external global i32

@foo_alias = alias i32* @foo
''')

    def test_verify(self):
        self.mod.Verify(llpy.core.VerifierFailureAction.ReturnStatus)

        void = llpy.core.VoidType(self.ctx)
        func_type = llpy.core.FunctionType(void, [])
        func = self.mod.AddFunction(func_type, 'invalid_func')
        bb = func.AppendBasicBlock('entry')
        builder = llpy.core.IRBuilder(self.ctx)
        builder.PositionBuilderAtEnd(bb)
        builder.BuildUnreachable()
        builder.BuildUnreachable() # oops :)

        with self.assertRaises(OSError):
            self.mod.Verify(llpy.core.VerifierFailureAction.ReturnStatus)

class TestType(DumpTestCase):

    def setUp(self):
        self.ctx = llpy.core.Context()

    def tearDown(self):
        del self.ctx
        gc.collect()

    def ty_str(self, ty):
        s = str(ty)
        if (3, 4) <= _version:
            assert s == ty.PrintToString()
            self.assertDump(ty, s)
        return s

    def test_int(self):
        # also tests general type stuff
        # this should probably be split into multiple test cases
        ctx = self.ctx
        # integers of size 1,8,16,32,64 are handled differently internally
        i2 = llpy.core.IntegerType(ctx, 2)
        assert self.ty_str(i2) == 'i2'
        assert i2 is llpy.core.IntegerType(ctx, 2)
        assert isinstance(i2, llpy.core.IntegerType)
        assert 2 == i2.GetIntTypeWidth()
        assert i2.GetTypeContext() is ctx
        i64 = llpy.core.IntegerType(ctx, 64)
        assert self.ty_str(i64) == 'i64'
        assert i64 is llpy.core.IntegerType(ctx, 64)
        assert isinstance(i2, llpy.core.IntegerType)
        assert 64 == i64.GetIntTypeWidth()
        assert i64.GetTypeContext() is ctx
        assert i64.IsSized()
        zero = i64.ConstNull()
        assert i64 is zero.TypeOf()
        assert isinstance(zero, llpy.core.ConstantInt)
        assert zero.IsNull()
        assert zero is i64.ConstNull()
        ones = i64.ConstAllOnes()
        assert i64 is ones.TypeOf()
        assert isinstance(ones, llpy.core.ConstantInt)
        assert not ones.IsNull()
        undef = i64.GetUndef()
        assert i64 is undef.TypeOf()
        assert isinstance(undef, llpy.core.UndefValue)
        assert not undef.IsNull()

        self.assertDump(zero,
'''i64 0
''')

        self.assertDump(ones,
'''i64 -1
''')

        self.assertDump(undef,
'''i64 undef
''')

        arr3 = i64.ConstArray([zero, ones, undef])
        assert arr3.GetNumOperands() == 3
        assert arr3.GetOperand(0) is zero
        assert arr3.GetOperand(1) is ones
        assert arr3.GetOperand(2) is undef
        arr3type = arr3.TypeOf()
        assert arr3type.GetArrayLength() == 3
        assert arr3type.GetElementType() is i64

        self.assertDump(arr3,
'''[3 x i64] [i64 0, i64 -1, i64 undef]
''')

        # not using i64 or i32 to avoid confusion
        align = i2.AlignOf()

        self.assertDump(align,
'''i64 ptrtoint (i2* getelementptr ({ i1, i2 }* null, i64 0, i32 1) to i64)
''')
        size = i2.SizeOf()

        self.assertDump(size,
'''i64 ptrtoint (i2* getelementptr (i2* null, i32 1) to i64)
''')

    def test_int_values(self):
        i32 = llpy.core.IntegerType(self.ctx, 32)
        assert i32.ConstInt(0) is i32.ConstNull()
        n1 = i32.ConstAllOnes()
        assert i32.ConstIntOfString('FFffFFff', 16) is n1
        assert n1.GetSExtValue() == -1
        assert n1.GetZExtValue() == 2**32 - 1
        answer = i32.ConstInt(42)
        assert answer is i32.ConstIntOfString('2a', 16)
        #assert answer is i32.ConstIntOfString('33', 13)
        assert answer is i32.ConstIntOfString('52', 8)
        assert answer is i32.ConstIntOfString('101010', 2)

    if (3, 1) <= _version:
        def test_half(self):
            # huh?
            if _version <= (3, 1):
                self.do_test_real(llpy.core.HalfType, 'half', [
                    ('-inf', '0xFFF0000000000000'),
                    ('-0.0', '0x8000000000000000'),
                    ('0.0', '0x0'),
                    ('1.5', '0x3FF8000000000000'),
                    ('nan', '0x7FF8000000000000'),
                ])
            if (3, 2) <= _version:
                self.do_test_real(llpy.core.HalfType, 'half', [
                    ('-inf', '0xHFC00'),
                    ('-0.0', '0xH8000'),
                    ('0.0', '0xH0000'),
                    ('1.5', '0xH3E00'),
                    ('nan', '0xH7E00'),
                ])

    def test_float(self):
        self.do_test_real(llpy.core.FloatType, 'float', [
            ('-inf', '0xFFF0000000000000'),
            ('-0.0', '-0.000000e+00'),
            ('0.0', '0.000000e+00'),
            ('1.5', '1.500000e+00'),
            ('nan', '0x7FF8000000000000'),
        ])

    def test_double(self):
        self.do_test_real(llpy.core.DoubleType, 'double', [
            ('-inf', '0xFFF0000000000000'),
            ('-0.0', '-0.000000e+00'),
            ('0.0', '0.000000e+00'),
            ('1.5', '1.500000e+00'),
            ('nan', '0x7FF8000000000000'),
        ])

    def test_x86_fp80(self):
        if _version <= (3, 2):
            self.do_test_real(llpy.core.X86FP80Type, 'x86_fp80', [
                ('-inf', '0xKFFFF8000000000000000'),
                ('-0.0', '0xK80000000000000000000'),
                ('0.0', '0xK00000000000000000000'),
                ('1.5', '0xK3FFFC000000000000000'),
                ('nan', '0xK7FFF4000000000000000'),
            ])
        if (3, 3) <= _version:
            self.do_test_real(llpy.core.X86FP80Type, 'x86_fp80', [
                ('-inf', '0xKFFFF8000000000000000'),
                ('-0.0', '0xK80000000000000000000'),
                ('0.0', '0xK00000000000000000000'),
                ('1.5', '0xK3FFFC000000000000000'),
                ('nan', '0xK7FFFC000000000000000'),
            ])

    def test_fp128(self):
        self.do_test_real(llpy.core.FP128Type, 'fp128', [
            ('-inf', '0xL0000000000000000FFFF000000000000'),
            ('-0.0', '0xL00000000000000008000000000000000'),
            ('0.0', '0xL00000000000000000000000000000000'),
            ('1.5', '0xL00000000000000003FFF800000000000'),
            ('nan', '0xL00000000000000007FFF800000000000'),
        ])

    def test_ppc_fp128(self):
        # huh?
        if _version <= (3, 1):
            self.do_test_real(llpy.core.PPCFP128Type, 'ppc_fp128', [
                ('-inf', '0xMFFF00000000000000000000000000000'),
                ('-0.0', '0xM80000000000000000000000000000000'),
                ('0.0', '0xM00000000000000000000000000000000'),
                ('1.5', '0xM3FF00000000000003FF0030000000000'),
                ('nan', '0xM7FF00000000000000000010000000000'),
            ])
        if (3, 2) <= _version:
            self.do_test_real(llpy.core.PPCFP128Type, 'ppc_fp128', [
                ('-inf', '0xMFFF00000000000000000000000000000'),
                ('-0.0', '0xM80000000000000000000000000000000'),
                ('0.0', '0xM00000000000000000000000000000000'),
                ('1.5', '0xM3FF80000000000000000000000000000'),
                ('nan', '0xM7FF80000000000000000000000000000'),
            ])

    def do_test_real(self, tyc, name, values):
        real_type = tyc(self.ctx)
        assert self.ty_str(real_type) == name
        assert real_type.IsSized()
        assert real_type.GetTypeContext() is self.ctx

        for ns, s in values:
            fs = float(ns)
            val = real_type.ConstReal(fs)
            assert real_type is val.TypeOf()
            if fs == fs and fs != float('-inf') and fs != float('inf'):
                assert val is real_type.ConstRealOfString(ns)
            if ns == '0.0':
                assert val is real_type.ConstNull()
                assert val.IsNull()
            else:
                assert not val.IsNull()
            assert isinstance(val, llpy.core.ConstantFP)

            self.assertDump(val, name + ' ' + s + '\n')

        undef = real_type.GetUndef()
        assert isinstance(undef, llpy.core.UndefValue)
        assert not val.IsNull()

        self.assertDump(undef, name + ' undef\n')

    def test_function(self):
        i32 = llpy.core.IntegerType(self.ctx, 32)
        i8 = llpy.core.IntegerType(self.ctx, 8)
        i8p = llpy.core.PointerType(i8)
        i8pp = llpy.core.PointerType(i8p)
        main_type = llpy.core.FunctionType(i32, [i32, i8pp])
        printf_type = llpy.core.FunctionType(i32, [i8p], True)
        assert self.ty_str(main_type) == 'i32 (i32, i8**)'
        assert self.ty_str(printf_type) == 'i32 (i8*, ...)'
        assert not main_type.IsSized()
        assert not printf_type.IsSized()
        assert main_type.GetTypeContext() is self.ctx
        assert printf_type.GetTypeContext() is self.ctx

        assert not main_type.IsVarArg()
        assert printf_type.IsVarArg()
        assert main_type.GetReturnType() is i32
        assert printf_type.GetReturnType() is i32
        assert main_type.GetParamTypes() == [i32, i8pp]
        assert printf_type.GetParamTypes() == [i8p]

    def test_struct(self):
        i64 = llpy.core.IntegerType(self.ctx, 64)
        # named struct types never coalesce; anonymous ones do
        st_noa = llpy.core.StructType(self.ctx, None, 'OLoose')
        assert str(st_noa) == 'struct OLoose'
        if (3, 4) <= _version:
            assert st_noa.PrintToString() == '%OLoose = type opaque'
        assert st_noa is not llpy.core.StructType(self.ctx, None, 'OLoose')
        st_nop = llpy.core.StructType(self.ctx, None, 'OPacked')
        assert str(st_nop) == 'struct OPacked'
        if (3, 4) <= _version:
            assert st_nop.PrintToString() == '%OPacked = type opaque'
        assert st_nop is not llpy.core.StructType(self.ctx, None, 'OPacked')
        st_nca = llpy.core.StructType(self.ctx, [i64], 'Loose', False)
        assert str(st_nca) == 'struct Loose { i64 }'
        if (3, 4) <= _version:
            assert st_nca.PrintToString() == '%Loose = type { i64 }'
        assert st_nca is not llpy.core.StructType(self.ctx, [i64], 'Loose', False)
        st_ncp = llpy.core.StructType(self.ctx, [i64], 'Packed', True)
        assert str(st_ncp) == 'struct Packed <{ i64 }>'
        if (3, 4) <= _version:
            assert st_ncp.PrintToString() == '%Packed = type <{ i64 }>'
        assert st_ncp is not llpy.core.StructType(self.ctx, [i64], 'Packed', True)

        st_aca = llpy.core.StructType(self.ctx, [i64], None, False)
        assert str(st_aca) == 'struct { i64 }'
        if (3, 4) <= _version:
            assert st_aca.PrintToString() == '{ i64 }'
        assert st_aca is llpy.core.StructType(self.ctx, [i64], None, False)
        st_acp = llpy.core.StructType(self.ctx, [i64], None, True)
        assert str(st_acp) == 'struct <{ i64 }>'
        if (3, 4) <= _version:
            assert st_acp.PrintToString() == '<{ i64 }>'
        assert st_acp is llpy.core.StructType(self.ctx, [i64], None, True)

        assert 6 == len({id(t) for t in [st_noa, st_nop, st_nca, st_ncp, st_aca, st_acp]})

        assert st_noa.GetStructName() == 'OLoose'
        assert st_noa.IsOpaqueStruct()
        assert not st_noa.IsSized()
        st_noa.StructSetBody([i64], False)
        assert st_noa.GetStructElementTypes() == [i64]
        assert not st_noa.IsPackedStruct()
        assert not st_noa.IsOpaqueStruct()
        assert st_noa.IsSized()
        assert st_noa.GetTypeContext() is self.ctx
        sv_noa = st_noa.ConstNamedStruct([i64.ConstAllOnes()])

        assert st_nop.GetStructName() == 'OPacked'
        assert st_nop.IsOpaqueStruct()
        assert not st_nop.IsSized()
        st_nop.StructSetBody([i64], True)
        assert st_nop.GetStructElementTypes() == [i64]
        assert st_nop.IsPackedStruct()
        assert not st_nop.IsOpaqueStruct()
        assert st_nop.IsSized()
        assert st_nop.GetTypeContext() is self.ctx
        sv_nop = st_nop.ConstNamedStruct([i64.ConstAllOnes()])

        assert st_nca.GetStructName() == 'Loose'
        assert st_nca.GetStructElementTypes() == [i64]
        assert not st_nca.IsPackedStruct()
        assert not st_nca.IsOpaqueStruct()
        assert st_nca.IsSized()
        assert st_nca.GetTypeContext() is self.ctx
        sv_nca = st_nca.ConstNamedStruct([i64.ConstAllOnes()])

        assert st_ncp.GetStructName() == 'Packed'
        assert st_ncp.GetStructElementTypes() == [i64]
        assert st_ncp.IsPackedStruct()
        assert not st_ncp.IsOpaqueStruct()
        assert st_ncp.IsSized()
        assert st_ncp.GetTypeContext() is self.ctx
        sv_ncp = st_ncp.ConstNamedStruct([i64.ConstAllOnes()])

        assert st_aca.GetStructName() is None
        assert st_aca.GetStructElementTypes() == [i64]
        assert not st_aca.IsPackedStruct()
        assert not st_aca.IsOpaqueStruct()
        assert st_aca.IsSized()
        assert st_aca.GetTypeContext() is self.ctx
        sv_aca = st_aca.ConstNamedStruct([i64.ConstAllOnes()])
        assert sv_aca is self.ctx.ConstStruct([i64.ConstAllOnes()], False)

        assert st_acp.GetStructName() is None
        assert st_acp.GetStructElementTypes() == [i64]
        assert st_acp.IsPackedStruct()
        assert not st_acp.IsOpaqueStruct()
        assert st_acp.IsSized()
        assert st_acp.GetTypeContext() is self.ctx
        sv_acp = st_acp.ConstNamedStruct([i64.ConstAllOnes()])
        assert sv_acp is self.ctx.ConstStruct([i64.ConstAllOnes()], True)

        self.assertDump(sv_noa, '%OLoose { i64 -1 }\n')
        self.assertDump(sv_nop, '%OPacked <{ i64 -1 }>\n')
        self.assertDump(sv_nca, '%Loose { i64 -1 }\n')
        self.assertDump(sv_ncp, '%Packed <{ i64 -1 }>\n')
        self.assertDump(sv_aca, '{ i64 } { i64 -1 }\n')
        self.assertDump(sv_acp, '<{ i64 }> <{ i64 -1 }>\n')

    def test_struct_recursive(self):
        mod = llpy.core.Module(self.ctx, 'TestType.test_struct_recursive')
        st = llpy.core.StructType(self.ctx, None, 'Recurse')
        sp = llpy.core.PointerType(st)

        assert st.GetStructName() == 'Recurse'
        st.StructSetBody([sp])
        assert st.GetStructElementTypes() == [sp]

        sv = st.ConstNamedStruct([sp.ConstPointerNull()])
        self.assertDump(sv, '%Recurse zeroinitializer\n')

        sg = mod.AddGlobal(st, 'recurse')
        assert sg.TypeOf() is sp
        self.assertDump(sg,
'''@recurse = external global %Recurse
''')
        self.assertDump(mod,
'''; ModuleID = 'TestType.test_struct_recursive'

%Recurse = type { %Recurse* }

@recurse = external global %Recurse
''')
        sg.SetInitializer(st.ConstNamedStruct([sg]))
        self.assertDump(sg,
'''@recurse = global %Recurse { %Recurse* @recurse }
''')
        self.assertDump(mod,
'''; ModuleID = 'TestType.test_struct_recursive'

%Recurse = type { %Recurse* }

@recurse = global %Recurse { %Recurse* @recurse }
''')

    def test_array(self):
        i64 = llpy.core.IntegerType(self.ctx, 64)
        arr = llpy.core.ArrayType(i64, 2)
        assert self.ty_str(arr) == '[2 x i64]'
        assert i64 is arr.GetElementType()
        assert 2 == arr.GetArrayLength()
        assert arr.IsSized()
        assert arr.GetTypeContext() is self.ctx

        av = i64.ConstArray([i64.ConstNull(), i64.ConstAllOnes()])
        assert av.TypeOf() is arr

        self.assertDump(av, '[2 x i64] [i64 0, i64 -1]\n')

    def test_pointer(self):
        i64 = llpy.core.IntegerType(self.ctx, 64)
        pa0 = llpy.core.PointerType(i64)
        pa1 = llpy.core.PointerType(i64, 1)
        assert self.ty_str(pa0) == 'i64*'
        assert self.ty_str(pa1) == 'i64 addrspace(1)*'
        assert pa0.IsSized()
        assert pa1.IsSized()
        assert pa0.GetTypeContext() is self.ctx
        assert pa1.GetTypeContext() is self.ctx

        assert 0 == pa0.GetPointerAddressSpace()
        assert 1 == pa1.GetPointerAddressSpace()
        assert i64 is pa0.GetElementType()
        assert i64 is pa1.GetElementType()
        null0 = pa0.ConstNull()
        null1 = pa1.ConstNull()
        assert null0.IsNull()
        assert null1.IsNull()
        assert null0 is pa0.ConstPointerNull()
        assert null1 is pa1.ConstPointerNull()

        self.assertDump(null0, 'i64* null\n')
        self.assertDump(null1, 'i64 addrspace(1)* null\n')

    def test_vector(self):
        i64 = llpy.core.IntegerType(self.ctx, 64)
        v2t = llpy.core.VectorType(i64, 2)
        assert self.ty_str(v2t) == '<2 x i64>'
        assert v2t.IsSized()
        assert v2t.GetTypeContext() is self.ctx

        assert i64 is v2t.GetElementType()
        assert 2 == v2t.GetVectorSize()
        v2v = llpy.core.ConstVector([i64.ConstNull(), i64.ConstAllOnes()])

        self.assertDump(v2v, '<2 x i64> <i64 0, i64 -1>\n')

    def test_void(self):
        void = llpy.core.VoidType(self.ctx)
        assert self.ty_str(void) == 'void'
        assert not void.IsSized()
        assert void.GetTypeContext() is self.ctx

    def test_label(self):
        label = llpy.core.LabelType(self.ctx)
        assert self.ty_str(label) == 'label'
        assert not label.IsSized()
        assert label.GetTypeContext() is self.ctx

    def test_x86_mmx(self):
        x86_mmx = llpy.core.X86MMXType(self.ctx)
        assert self.ty_str(x86_mmx) == 'x86_mmx'
        assert x86_mmx.IsSized()
        assert x86_mmx.GetTypeContext() is self.ctx
        # I haven't managed to find anything else that doesn't segfault
        # Is even this technically legal?
        undef = x86_mmx.GetUndef()

        self.assertDump(undef, 'x86_mmx undef\n')

    def test_metadata(self):
        ctx = self.ctx
        i32 = llpy.core.IntegerType(ctx, 32)
        mds = ctx.MDString('foo')
        assert isinstance(mds, llpy.core.MDString)
        mdne = ctx.MDNode([])
        assert isinstance(mdne, llpy.core.MDNode)
        mdni = ctx.MDNode([i32.ConstNull()])
        assert isinstance(mdni, llpy.core.MDNode)
        assert mdni is ctx.MDNode([i32.ConstNull()])
        mdns = ctx.MDNode([mds])
        assert isinstance(mdns, llpy.core.MDNode)
        assert mdns is ctx.MDNode([mds])

        mdst = mds.TypeOf()
        mdnet = mdne.TypeOf()
        mdnit = mdni.TypeOf()
        mdnst = mdns.TypeOf()
        assert isinstance(mdst, llpy.core.MetadataType)
        assert self.ty_str(mdst) == 'metadata'
        assert mdnet is mdst
        assert mdnit is mdst
        assert mdnst is mdst
        assert not mdst.IsSized()
        assert mdst.GetTypeContext() is ctx

        for md in [mds, mdne, mdni, mdns]:
            if (3, 1) <= _version:
                if md is mds:
                    assert md.GetValueName() == 'foo'
                    continue
            assert md.GetValueName() == ''


@unittest.skip('NYI')
class TestIRBuilder(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        gc.collect()

    def test_position(self):
        pass

    def test_debug(self):
        pass


@unittest.skip('NYI')
class TestModuleProvider(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        gc.collect()

    def test_none(self):
        ctx = llpy.core.Context()
        mod = llpy.core.Module(ctx, 'TestModuleProvider')


@unittest.skip('NYI')
class TestPassRegistry(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        gc.collect()

    def test_singleton(self):
        gsi = llpy.core.PassRegistry.get_singleton_instance
        assert gsi() is gsi()

@unittest.skip('NYI')
class TestPassManager(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        gc.collect()

    def test_run(self):
        ctx = llpy.core.Context()
        mod = llpy.core.Module(ctx, 'TestPassManager')
        pm = llpy.core.PassManager()
        changed = pm.run(mod)

@unittest.skip('NYI')
class TestFunctionPassManager(unittest.TestCase):

    def setUp(self):
        self.fpm = llpy.core.FunctionPassManager(mod)

    def tearDown(self):
        del self.fpm
        gc.collect()

    def test_initialize(self):
        changed = self.fpm.initialize()

    def test_run(self):
        changed = self.fpm.run(func)

    def test_finalize(self):
        changed = self.fpm.finalize()


class TestLLVM(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        gc.collect()

    if (3, 4) <= _version:
        @unittest.skip('NYI')
        def test_fatal_errors(self):
            def handler(s):
                pass
            llpy.core.InstallFatalErrorHandler(handler)
            llpy.core.ResetFatalErrorHandler()

        @unittest.skip('NYI')
        def test_pretty_stack(self):
            llpy.core.EnablePrettyStackTrace()

        def test_load_library(self):
            llpy.core.LoadLibraryPermanently(unicode(llpy.c.core._library._cdll._name))
            with self.assertRaises(OSError):
                llpy.core.LoadLibraryPermanently('/nonexistent')

if __name__ == '__main__':
    unittest.main()
