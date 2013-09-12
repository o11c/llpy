#!/usr/bin/env python3
from functools import reduce
import gc
import operator
import os
import unittest

import llpy.core
from llpy.c.core import _version

class ReplaceOutFD:
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

    def assertDump(self, obj, str):
        if _version <= (3, 1):
            if isinstance(obj, llpy.core.GlobalVariable):
                str += '\n'
        with ReplaceOutFD(2) as f:
            obj.Dump()
        with f:
            assert f.read() == str

class TestContext(DumpTestCase):

    def setUp(self):
        self.ctx = llpy.core.Context()

    def test_context(self):
        pass

    def test_md_kind_id(self):
        foo = self.ctx.GetMDKindID('foo')
        bar = self.ctx.GetMDKindID('bar')
        assert isinstance(foo, int)
        assert isinstance(bar, int)
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

    def tearDown(self):
        del self.ctx
        gc.collect()

class TestModule(DumpTestCase):

    def setUp(self):
        self.ctx = llpy.core.Context()
        self.mod = llpy.core.Module(self.ctx, 'TestModule')

    def test_module(self):
        assert self.mod.GetContext() is self.ctx

        self.assertDump(self.mod,
'''; ModuleID = 'TestModule'
''')

    def test_data_layout(self):
        mod = self.mod
        layout = 'foobarbaz'
        mod.SetDataLayout(layout)
        assert layout == mod.GetDataLayout()

        self.assertDump(mod,
'''; ModuleID = 'TestModule'
target datalayout = "foobarbaz"
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
        alias_foo = self.mod.AddAlias(i32, foo, 'foo_alias')
        assert isinstance(alias_foo, llpy.core.GlobalAlias)
        alias_val = self.mod.AddAlias(i32, i32.ConstAllOnes(), 'anon_alias')
        assert isinstance(alias_val, llpy.core.GlobalAlias)

        self.assertDump(self.mod,
'''; ModuleID = 'TestModule'

@foo = external global i32

@foo_alias = alias i32* @foo
@anon_alias = alias i32 -1
''')

    def test_verify(self):
        self.mod.Verify(llpy.core.VerifierFailureAction.ReturnStatus)
        i32 = llpy.core.IntegerType(self.ctx, 32)
        self.mod.AddAlias(i32, i32.ConstNull(), 'foo')
        with self.assertRaises(OSError):
            self.mod.Verify(llpy.core.VerifierFailureAction.ReturnStatus)

    def tearDown(self):
        del self.mod
        del self.ctx
        gc.collect()

class TestType(DumpTestCase):

    def setUp(self):
        self.ctx = llpy.core.Context()

    def test_int(self):
        # also tests general type stuff
        # this should probably be split into multiple test cases
        ctx = self.ctx
        # integers of size 1,8,16,32,64 are handled differently internally
        i2 = llpy.core.IntegerType(ctx, 2)
        assert str(i2) == 'i2'
        assert i2 is llpy.core.IntegerType(ctx, 2)
        assert isinstance(i2, llpy.core.IntegerType)
        assert 2 == i2.GetIntTypeWidth()
        assert i2.GetTypeContext() is ctx
        i64 = llpy.core.IntegerType(ctx, 64)
        assert str(i64) == 'i64'
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
        assert answer is i32.ConstIntOfString('33', 13)
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
        assert str(real_type) == name
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
        assert str(main_type) == 'i32(i32, i8**)'
        assert str(printf_type) == 'i32(i8*, ...)'
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
        assert st_noa is not llpy.core.StructType(self.ctx, None, 'OLoose')
        st_nop = llpy.core.StructType(self.ctx, None, 'OPacked')
        assert str(st_nop) == 'struct OPacked'
        assert st_nop is not llpy.core.StructType(self.ctx, None, 'OPacked')
        st_nca = llpy.core.StructType(self.ctx, [i64], 'Loose', False)
        assert str(st_nca) == 'struct Loose { i64 }'
        assert st_nca is not llpy.core.StructType(self.ctx, [i64], 'Loose', False)
        st_ncp = llpy.core.StructType(self.ctx, [i64], 'Packed', True)
        assert str(st_ncp) == 'struct Packed <{ i64 }>'
        assert st_ncp is not llpy.core.StructType(self.ctx, [i64], 'Packed', True)

        st_aca = llpy.core.StructType(self.ctx, [i64], None, False)
        assert str(st_aca) == 'struct { i64 }'
        assert st_aca is llpy.core.StructType(self.ctx, [i64], None, False)
        st_acp = llpy.core.StructType(self.ctx, [i64], None, True)
        assert str(st_acp) == 'struct <{ i64 }>'
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
        assert str(arr) == '[2 x i64]'
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
        assert str(pa0) == 'i64*'
        assert str(pa1) == 'i64 addrspace(1)*'
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
        assert str(v2t) == '<2 x i64>'
        assert v2t.IsSized()
        assert v2t.GetTypeContext() is self.ctx

        assert i64 is v2t.GetElementType()
        assert 2 == v2t.GetVectorSize()
        v2v = llpy.core.ConstVector([i64.ConstNull(), i64.ConstAllOnes()])

        self.assertDump(v2v, '<2 x i64> <i64 0, i64 -1>\n')

    def test_void(self):
        void = llpy.core.VoidType(self.ctx)
        assert str(void) == 'void'
        assert not void.IsSized()
        assert void.GetTypeContext() is self.ctx

    def test_label(self):
        label = llpy.core.LabelType(self.ctx)
        assert str(label) == 'label'
        assert not label.IsSized()
        assert label.GetTypeContext() is self.ctx

    def test_x86_mmx(self):
        x86_mmx = llpy.core.X86MMXType(self.ctx)
        assert str(x86_mmx) == 'x86_mmx'
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
        assert str(mdst) == 'metadata'
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

    def tearDown(self):
        del self.ctx
        gc.collect()

class TestBuilder(DumpTestCase):

    def setUp(self):
        self.ctx = llpy.core.Context()
        self.mod = llpy.core.Module(self.ctx, 'TestBuilder')
        self.builder = llpy.core.IRBuilder(self.ctx)

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
            v = llpy.core.ConstVector([i1.ConstNull(), i1.ConstNull()])
            arrv = v.TypeOf().ConstArray([v])
            assert instr.GetOperand(2) is arrv
        assert instr.GetOperand(3) is bb_false
        if _version <= (3, 1):
            assert instr.GetOperand(4) is i1.ConstAllOnes()
        if (3, 2) <= _version:
            v = llpy.core.ConstVector([i1.ConstAllOnes(), i1.ConstAllOnes()])
            arrv = v.TypeOf().ConstArray([v])
            assert instr.GetOperand(4) is arrv
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

        instr = builder.BuildLoad(ptr, 'load')
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
  %load = load i32* %aa
  ret void
}

''')
        if (3, 1) <= _version:
            assert not instr.GetVolatile()
            instr.SetVolatile(True)
            assert instr.GetVolatile()
            self.assertDump(instr, '  %load = load volatile i32* %aa\n')

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


        instr3 = builder.BuildGEP(ptr, [i64.ConstNull(), i32.ConstNull(), idx], 'gep3')
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
  %gep3 = getelementptr { [2 x i32] }* %ptr, i64 0, i32 0, i32 %idx
  ret i32* %gep3
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


        instr3 = builder.BuildInBoundsGEP(ptr, [i64.ConstNull(), i32.ConstNull(), idx], 'gep3')
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
  %gep3 = getelementptr inbounds { [2 x i32] }* %ptr, i64 0, i32 0, i32 %idx
  ret i32* %gep3
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
        pass

    def tearDown(self):
        del self.builder
        del self.mod
        del self.ctx
        gc.collect()

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

    def tearDown(self):
        del self.func
        del self.mod
        del self.ctx
        gc.collect()

class TestBasicBlock(DumpTestCase):

    def setUp(self):
        self.ctx = llpy.core.Context()
        self.mod = llpy.core.Module(self.ctx, 'TestBasicBlock')
        void = llpy.core.VoidType(self.ctx)
        func_type = llpy.core.FunctionType(void, [])
        self.func = self.mod.AddFunction(func_type, 'func')

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

    def tearDown(self):
        del self.mod
        del self.ctx
        gc.collect()


class TestInlineAsm(DumpTestCase):
    __slots__ = ()

    def setUp(self):
        ctx = llpy.core.Context()
        void = llpy.core.VoidType(ctx)
        self.fty = llpy.core.FunctionType(void, [])

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

    def tearDown(self):
        del self.fty
        gc.collect()

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

class TestBlockAddress(DumpTestCase):

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
            if (3, 3) <= _version:
                ir = 'minsize nobuiltin noduplicate nonlazybind returned sspstrong sanitize_address sanitize_thread sanitize_memory'
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
        if (3, 3) <= _version:
            irs += ' nobuiltin noduplicate returned sspstrong'
            irs = ' '.join(sorted(irs.split(' ')))
            irs = irs.replace('uwtable', 'sanitize_address sanitize_thread sanitize_memory uwtable')
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
        if _version <= (3, 2):
            self.assertDump(self.func_decl,
'''
declare private hidden fastcc i32 @func_decl() noreturn section "section" align 1 gc "gc"

''')
        if (3, 3) <= _version:
            self.assertDump(self.func_decl,
'''
; Function Attrs: noreturn
declare private hidden fastcc i32 @func_decl() #0 section "section" align 1 gc "gc"

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

    def tearDown(self):
        del self.func_decl
        del self.func_def
        del self.i32
        del self.mod
        del self.ctx
        gc.collect()


class TestGlobalAlias(DumpTestCase):

    def setUp(self):
        self.ctx = llpy.core.Context()
        self.mod = llpy.core.Module(self.ctx, 'TestGlobalAlias')
        self.i32 = llpy.core.IntegerType(self.ctx, 32)
        func_type = llpy.core.FunctionType(self.i32, [])
        self.func = self.mod.AddFunction(func_type, 'func')
        self.var = self.mod.AddGlobal(self.i32, 'var')

    def test_decl(self):
        a = self.mod.AddAlias(self.i32, self.func, 'func_alias')
        assert not a.IsDeclaration()
        self.assertDump(a, '@func_alias = alias i32 ()* @func\n\n')
        a = self.mod.AddAlias(self.i32, self.var, 'var_alias')
        assert not a.IsDeclaration()
        self.assertDump(a, '@var_alias = alias i32* @var\n\n')
        a = self.mod.AddAlias(self.i32, self.i32.ConstInt(2), 'val_alias')
        assert not a.IsDeclaration()
        self.assertDump(a, '@val_alias = alias i32 2\n\n')
        self.assertDump(self.mod,
'''; ModuleID = 'TestGlobalAlias'

@var = external global i32

@func_alias = alias i32 ()* @func
@var_alias = alias i32* @var
@val_alias = alias i32 2

declare i32 @func()
''')

    def test_linkage(self):
        Linkage = llpy.core.Linkage
        a = self.mod.AddAlias(self.i32, self.func, 'func_alias')
        assert a.GetLinkage() == Linkage.External
        a.SetLinkage(Linkage.Private)
        assert a.GetLinkage() == Linkage.Private
        self.assertDump(a, '@func_alias = alias private i32 ()* @func\n\n')
        a = self.mod.AddAlias(self.i32, self.var, 'var_alias')
        assert a.GetLinkage() == Linkage.External
        a.SetLinkage(Linkage.Private)
        assert a.GetLinkage() == Linkage.Private
        self.assertDump(a, '@var_alias = alias private i32* @var\n\n')
        a = self.mod.AddAlias(self.i32, self.i32.ConstInt(2), 'val_alias')
        assert a.GetLinkage() == Linkage.External
        a.SetLinkage(Linkage.Private)
        assert a.GetLinkage() == Linkage.Private
        self.assertDump(a, '@val_alias = alias private i32 2\n\n')
        self.assertDump(self.mod,
'''; ModuleID = 'TestGlobalAlias'

@var = external global i32

@func_alias = alias private i32 ()* @func
@var_alias = alias private i32* @var
@val_alias = alias private i32 2

declare i32 @func()
''')

    def test_section(self):
        # aliases have, but ignore, a section
        a = self.mod.AddAlias(self.i32, self.func, 'func_alias')
        assert a.GetSection() == ''
        a.SetSection('foo')
        assert a.GetSection() == 'foo'
        self.assertDump(a, '@func_alias = alias i32 ()* @func\n\n')
        a = self.mod.AddAlias(self.i32, self.var, 'var_alias')
        assert a.GetSection() == ''
        a.SetSection('foo')
        assert a.GetSection() == 'foo'
        self.assertDump(a, '@var_alias = alias i32* @var\n\n')
        a = self.mod.AddAlias(self.i32, self.i32.ConstInt(2), 'val_alias')
        assert a.GetSection() == ''
        a.SetSection('foo')
        assert a.GetSection() == 'foo'
        self.assertDump(a, '@val_alias = alias i32 2\n\n')
        self.assertDump(self.mod,
'''; ModuleID = 'TestGlobalAlias'

@var = external global i32

@func_alias = alias i32 ()* @func
@var_alias = alias i32* @var
@val_alias = alias i32 2

declare i32 @func()
''')

    def test_visibility(self):
        Visibility = llpy.core.Visibility
        a = self.mod.AddAlias(self.i32, self.func, 'func_alias')
        assert a.GetVisibility() == Visibility.Default
        a.SetVisibility(Visibility.Hidden)
        assert a.GetVisibility() == Visibility.Hidden
        self.assertDump(a, '@func_alias = hidden alias i32 ()* @func\n\n')
        a = self.mod.AddAlias(self.i32, self.var, 'var_alias')
        assert a.GetVisibility() == Visibility.Default
        a.SetVisibility(Visibility.Hidden)
        assert a.GetVisibility() == Visibility.Hidden
        self.assertDump(a, '@var_alias = hidden alias i32* @var\n\n')
        a = self.mod.AddAlias(self.i32, self.i32.ConstInt(2), 'val_alias')
        assert a.GetVisibility() == Visibility.Default
        a.SetVisibility(Visibility.Hidden)
        assert a.GetVisibility() == Visibility.Hidden
        self.assertDump(a, '@val_alias = hidden alias i32 2\n\n')
        self.assertDump(self.mod,
'''; ModuleID = 'TestGlobalAlias'

@var = external global i32

@func_alias = hidden alias i32 ()* @func
@var_alias = hidden alias i32* @var
@val_alias = hidden alias i32 2

declare i32 @func()
''')

    def test_alignment(self):
        # aliases have, but ignore, an alignment
        a = self.mod.AddAlias(self.i32, self.func, 'func_alias')
        assert a.GetAlignment() == 0
        a.SetAlignment(1)
        assert a.GetAlignment() == 1
        self.assertDump(a, '@func_alias = alias i32 ()* @func\n\n')
        a = self.mod.AddAlias(self.i32, self.var, 'var_alias')
        assert a.GetAlignment() == 0
        a.SetAlignment(1)
        assert a.GetAlignment() == 1
        self.assertDump(a, '@var_alias = alias i32* @var\n\n')
        a = self.mod.AddAlias(self.i32, self.i32.ConstInt(2), 'val_alias')
        assert a.GetAlignment() == 0
        a.SetAlignment(1)
        assert a.GetAlignment() == 1
        self.assertDump(a, '@val_alias = alias i32 2\n\n')
        self.assertDump(self.mod,
'''; ModuleID = 'TestGlobalAlias'

@var = external global i32

@func_alias = alias i32 ()* @func
@var_alias = alias i32* @var
@val_alias = alias i32 2

declare i32 @func()
''')

    def tearDown(self):
        del self.var
        del self.func
        del self.i32
        del self.mod
        del self.ctx
        gc.collect()


class TestGlobalVariable(DumpTestCase):

    def setUp(self):
        self.ctx = llpy.core.Context()
        self.mod = llpy.core.Module(self.ctx, 'TestGlobalVariable')
        self.i32 = llpy.core.IntegerType(self.ctx, 32)
        self.ext = self.mod.AddGlobal(self.i32, 'ext')
        self.ini = self.mod.AddGlobal(self.i32, 'ini')
        self.ini.SetInitializer(self.i32.ConstInt(42))

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
        self.ini.SetInitializer(None)
        self.assertDump(self.ini, '@ini = external global i32\n')

    def test_threadlocal(self):
        assert not self.ext.IsThreadLocal()
        self.ext.SetThreadLocal(True)
        self.assertDump(self.ext, '@ext = external thread_local global i32\n')
        assert not self.ini.IsThreadLocal()
        self.ini.SetThreadLocal(True)
        self.assertDump(self.ini, '@ini = thread_local global i32 42\n')
        self.assertDump(self.mod,
'''; ModuleID = 'TestGlobalVariable'

@ext = external thread_local global i32
@ini = thread_local global i32 42
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

    @unittest.expectedFailure
    def test_GetIntrinsicID(self):
        raise NotImplementedError

    def tearDown(self):
        del self.ext
        del self.ini
        del self.i32
        del self.mod
        del self.ctx
        gc.collect()


class TestInstruction(DumpTestCase):

    @unittest.expectedFailure
    def test_metadata(self):
        raise NotImplementedError


class TestAnyCallOrInvoke(DumpTestCase):

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

    @unittest.expectedFailure
    def test_tail(self):
        raise NotImplementedError


class TestUse(DumpTestCase):

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


@unittest.skip('NYI')
class TestIRBuilder(unittest.TestCase):

    def test_position(self):
        pass

    def test_debug(self):
        pass


@unittest.skip('NYI')
class TestModuleProvider(unittest.TestCase):

    def test_none(self):
        ctx = llpy.core.Context()
        mod = llpy.core.Module(ctx, 'TestModuleProvider')


@unittest.skip('NYI')
class TestPassRegistry(unittest.TestCase):

    def test_singleton(self):
        gsi = llpy.core.PassRegistry.get_singleton_instance
        assert gsi() is gsi()

@unittest.skip('NYI')
class TestPassManager(unittest.TestCase):

    def test_run(self):
        ctx = llpy.core.Context()
        mod = llpy.core.Module(ctx, 'TestPassManager')
        pm = llpy.core.PassManager()
        changed = pm.run(mod)

@unittest.skip('NYI')
class TestFunctionPassManager(unittest.TestCase):

    def setUp(self):
        self.fpm = llpy.core.FunctionPassManager(mod)

    def test_initialize(self):
        changed = self.fpm.initialize()

    def test_run(self):
        changed = self.fpm.run(func)

    def test_finalize(self):
        changed = self.fpm.finalize()

    def tearDown(self):
        del self.fpm
        gc.collect()

if __name__ == '__main__':
    unittest.main()
