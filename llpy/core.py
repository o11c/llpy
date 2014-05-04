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

''' Wrap the C interface to the llvm Core.

    Some classes include functions from headers other than llvm-c/Core.h
'''

import ctypes # some wrappers need to know
import weakref

from llpy.utils import u2b, b2u, deprecated, untested, dangerous
from llpy.c import (
        _c,
        core as _core,
        analysis as _analysis,
        initialization as _initialization,
)
# enums are already good enough
from llpy.c.core import (
        Attribute,
        Opcode,
        TypeKind,
        Linkage,
        Visibility,
        CallConv,
        IntPredicate,
        RealPredicate,
        LandingPadClauseTy,

        _version,
)
from llpy.c.analysis import (
        VerifierFailureAction,
)
from llpy import __unknown_values as unknown_values

class Context(object):
    ''' Contexts are execution states for the core LLVM IR system.

        Most types are tied to a context instance. Multiple contexts can
        exist simultaneously. A single context is not thread safe. However,
        different contexts can execute on different threads simultaneously.
    '''
    __slots__ = ('_raw', 'type_cache', 'value_cache')

    def __init__(self):
        ''' Create a new context.
        '''
        self._raw = _core.ContextCreate()
        self.type_cache = weakref.WeakValueDictionary()
        self.value_cache = weakref.WeakValueDictionary()

    # GetGlobalContext omitted ...

    def __del__(self):
        ''' Destroy a context instance.
        '''
        _core.ContextDispose(self._raw)

    def GetMDKindID(self, name):
        bname = u2b(name)
        return _core.GetMDKindIDInContext(self._raw, bname, len(bname))

    def ConstString(self, value, dont_null_terminate=False):
        ''' Create a ConstantDataSequential with string content in the global context.
        '''
        bvalue = u2b(value)
        blen = len(bvalue)
        return Value(_core.ConstStringInContext(self._raw, bvalue, blen, dont_null_terminate) , self)

    def ConstStruct(self, values, packed=False):
        ''' Create an anonymous ConstantStruct with the specified values.
        '''
        n = len(values)
        raw_values = (_core.Value * n)(*[i._raw for i in values])
        return Value(_core.ConstStructInContext(self._raw, raw_values, n, packed), self)

    def MDString(self, s):
        buf = u2b(s)
        return Value(_core.MDStringInContext(self._raw, buf, len(buf)), self)

    def MDNode(self, values):
        n = len(values)
        raw_values = (_core.Value * n)(*[i._raw for i in values])
        return Value(_core.MDNodeInContext(self._raw, raw_values, n), self)

class Module(object):
    ''' Modules represent the top-level structure in a LLVM program. An LLVM
        module is effectively a translation unit or a collection of
        translation units merged together.
    '''
    __slots__ = ('_raw', '_context')

    def __init__(self, context, name):
        ''' Create a new, empty module in a specific context.
        '''
        bname = u2b(name)
        self._raw = _core.ModuleCreateWithNameInContext(bname, context._raw)
        self._context = context

    def __del__(self):
        ''' Destroy a module instance.
        '''
        _core.DisposeModule(self._raw)

    def GetDataLayout(self):
        ''' Obtain the data layout for a module.
        '''
        return b2u(_core.GetDataLayout(self._raw))

    def SetDataLayout(self, s):
        ''' Set the data layout for a module.
        '''
        _core.SetDataLayout(self._raw, u2b(s))

    def GetTarget(self):
        ''' Obtain the target triple for a module.
        '''
        return b2u(_core.GetTarget(self._raw))

    def SetTarget(self, s):
        ''' Set the target triple for a module.
        '''
        _core.SetTarget(self._raw, u2b(s))

    def Dump(self):
        ''' Dump a representation of a module to stderr.
        '''
        _core.DumpModule(self._raw)

    def SetModuleInlineAsm(self, asm):
        ''' Set inline assembly for a module.
        '''
        _core.SetModuleInlineAsm(self._raw, u2b(asm))

    def GetContext(self):
        ''' Obtain the context to which this module is associated.
        '''
        # Does NOT call the C function
        return self._context

    def GetTypeByName(self, name):
        ''' Obtain a Type from a module by its registered name.
        '''
        rawtype = _core.GetTypeByName(self._raw, u2b(name))
        return Type(rawtype, self._context)

    def GetNamedMetadataOperands(self, name):
        ''' Obtain the named metadata operands for a module.

            Return a list of Value instances that stand for llvm::MDNode.
        '''
        bname = u2b(name)
        num = _core.GetNamedMetadataNumOperands(self._raw, bname)
        if not num:
            return []
        temp_buf = (_core.Value * num)()
        _core.GetNamedMetadataOperands(self._raw, bname, temp_buf)
        return [Value(v, self._context) for v in temp_buf]

    if (3, 1) <= _version:
        def AddNamedMetadataOperand(self, name, val):
            ''' Add an MDNOde operand to named metadata.
            '''
            assert isinstance(val, MDNode)
            bname = u2b(name)
            _core.AddNamedMetadataOperand(self._raw, bname, val._raw)


    def AddFunction(self, ftype, name):
        ''' Add a function to a module under a specified name.
        '''
        return Value(_core.AddFunction(self._raw, u2b(name), ftype._raw), self._context)

    def GetNamedFunction(self, name):
        ''' Obtain a Function value from a Module by its name.
        '''
        return Value(_core.GetNamedFunction(self._raw, u2b(name)), self._context)

    def GetFirstFunction(self):
        ''' Obtain an iterator to the first Function in a Module.
        '''
        return Value(_core.GetFirstFunction(self._raw), self._context)

    def GetLastFunction(self):
        ''' Obtain an iterator to the last Function in a Module.
        '''
        return Value(_core.GetLastFunction(self._raw), self._context)
    # see class Function for next/prev

    def AddGlobal(self, ty, name='', address_space=0):
        return Value(_core.AddGlobalInAddressSpace(self._raw, ty._raw, u2b(name), address_space), self._context)

    def GetNamedGlobal(self, name):
        return Value(_core.GetNamedGlobal(self._raw, u2b(name)), self._context)

    def GetFirstGlobal(self):
        return Value(_core.GetFirstGlobal(self._raw), self._context)

    def GetLastGlobal(self):
        return Value(_core.GetLastGlobal(self._raw), self._context)
    # see class GlobalVariable for next/prev

    def AddAlias(self, ty, val, name):
        return Value(_core.AddAlias(self._raw, ty._raw, val._raw, u2b(name)), self._context)

    # from Analysis.h
    def Verify(self, action):
        ''' Verifies that a module is valid, taking the specified action if
            not. Optionally returns a human-readable description of any
            invalid constructs. OutMessage must be disposed with
            LLVMDisposeMessage.
        '''
        error = _c.string_buffer()
        rv = bool(_analysis.VerifyModule(self._raw, action, ctypes.byref(error)))
        error = _message_to_string(error)

        if rv:
            raise OSError(error)



class Type(object):
    ''' Types represent the type of a value.

        Types are associated with a context instance. The context
        internally deduplicates types so there is only 1 instance of a
        specific type alive at a time. In other words, a unique type is
        shared among all consumers within a context.

        A Type in the C API corresponds to llvm::Type.

        Types have the following hierarchy:

          types:
            integer type
            real type
            function type
            sequence types:
              array type
              pointer type
              vector type
            void type
            label type
            opaque type
    '''
    _kind_type_map = {}

    __slots__ = ('_raw', '_context', '__weakref__')

    def __new__(cls, raw, context):
        ''' Deeply magic wrapper that constructs a Type from a C Type*.

            It will always return the same object as long as it exists,
            which will actually be an instance of a subclass.
        '''
        assert isinstance(raw, _core.Type)
        assert isinstance(context, Context)
        assert cls == Type # subclasses must override it
        if not raw:
            return None
        raw_ptr = _c.pointer_value(raw)
        try:
            return context.type_cache[raw_ptr]
        except KeyError:
            pass
        kind = _core.GetTypeKind(raw)
        self = object.__new__(Type._kind_type_map[kind])
        context.type_cache[raw_ptr] = self
        self._raw = raw
        self._context = context
        return self

    def __init__(self, *args, **kwargs):
        # python2 compatibility
        pass

    def IsSized(self):
        ''' Whether the type has a known size.

            Things that don't have a size are abstract types, labels, and void.
        '''
        return bool(_core.TypeIsSized(self._raw))

    def GetTypeContext(self):
        ''' Obtain the context to which this type instance is associated.
        '''
        return self._context

    def ConstNull(self):
        ''' Obtain a constant value referring to the null instance of a type.
        '''
        assert self.IsSized()
        return Value(_core.ConstNull(self._raw), self._context)

    def GetUndef(self):
        ''' Obtain a constant value referring to an undefined value of a type.
        '''
        assert self.IsSized()
        return Value(_core.GetUndef(self._raw), self._context)

    def ConstArray(self, values):
        ''' Create a ConstantArray from values.
        '''
        assert self.IsSized()
        n = len(values)
        raw_values = (_core.Value * n)(*[i._raw for i in values])
        return Value(_core.ConstArray(self._raw, raw_values, n), self._context)

    def AlignOf(self):
        ''' Computes the alignment of a type in a target independent way.

            Note: the return value is a Constant i64.
        '''
        assert self.IsSized()
        return Value(_core.AlignOf(self._raw), self._context)

    def SizeOf(self):
        ''' Computes the (alloc) size of a type (in address-units, not bits) in a target independent way.

            Note: the return value is a Constant i64.
        '''
        assert self.IsSized()
        return Value(_core.SizeOf(self._raw), self._context)

class IntegerType(Type):
    __slots__ = ()

    def __new__(cls, context, bits):
        ''' Obtain an integer type from a context with specified bit width.
        '''
        assert cls is IntegerType
        raw = _core.IntTypeInContext(context._raw, bits)
        self = Type.__new__(Type, raw, context)
        assert type(self) is IntegerType
        return self

    def __repr__(self):
        return 'i%d' % (self.GetIntTypeWidth())

    def GetIntTypeWidth(self):
        return _core.GetIntTypeWidth(self._raw)

    def ConstAllOnes(self):
        ''' Obtain a constant value referring to the instance of a type
            consisting of all ones.
        '''
        return Value(_core.ConstAllOnes(self._raw), self._context)

    def ConstInt(self, value):
        ''' Obtain a constant value for an integer type.
        '''
        assert isinstance(value, int)
        # might be a subclass, e.g. bool
        value = int(value)
        # due to the python nature, this is probably more efficient than
        # converting to an array of uint64_t
        return self.ConstIntOfString(str(value), 10)

    def ConstIntOfString(self, value, radix):
        ''' Obtain a constant value for an integer parsed from a string.
        '''
        assert isinstance(value, str)
        bvalue = u2b(value)
        blen = len(bvalue)
        return Value(_core.ConstIntOfStringAndSize(self._raw, bvalue, blen, radix), self._context)

Type._kind_type_map[TypeKind.Integer] = IntegerType

class RealType(Type):
    ''' abstract base of all real types
    '''
    __slots__ = ()

    def __new__(cls):
        raise TypeError

    def ConstReal(self, value):
        ''' Obtain a constant value referring to a floating point value
            represented as a C double (Python float).
        '''
        assert isinstance(value, float)
        return Value(_core.ConstReal(self._raw, value), self._context)

    def ConstRealOfString(self, value):
        ''' Obtain a constant for a floating point value parsed from a string.
        '''
        assert isinstance(value, str)
        bvalue = u2b(value)
        blen = len(bvalue)
        return Value(_core.ConstRealOfStringAndSize(self._raw, bvalue, blen), self._context)

if (3, 1) <= _version:
    class HalfType(RealType):
        __slots__ = ()

        def __new__(cls, context):
            ''' Obtain a 16-bit floating point type from a context.
            '''
            assert cls is HalfType
            raw = _core.HalfTypeInContext(context._raw)
            self = Type.__new__(Type, raw, context)
            assert type(self) is HalfType
            return self

        def __repr__(self):
            return 'half'

    Type._kind_type_map[TypeKind.Half] = HalfType

class FloatType(RealType):
    __slots__ = ()

    def __new__(cls, context):
        ''' Obtain a 32-bit floating point type from a context.
        '''
        assert cls is FloatType
        raw = _core.FloatTypeInContext(context._raw)
        self = Type.__new__(Type, raw, context)
        assert type(self) is FloatType
        return self

    def __repr__(self):
        return 'float'

Type._kind_type_map[TypeKind.Float] = FloatType

class DoubleType(RealType):
    __slots__ = ()

    def __new__(cls, context):
        ''' Obtain a 64-bit floating point type from a context.
        '''
        assert cls is DoubleType
        raw = _core.DoubleTypeInContext(context._raw)
        self = Type.__new__(Type, raw, context)
        assert type(self) is DoubleType
        return self

    def __repr__(self):
        return 'double'

Type._kind_type_map[TypeKind.Double] = DoubleType

class X86FP80Type(RealType):
    __slots__ = ()

    def __new__(cls, context):
        ''' Obtain a 80-bit floating point type (X87) from a context.
        '''
        assert cls is X86FP80Type
        raw = _core.X86FP80TypeInContext(context._raw)
        self = Type.__new__(Type, raw, context)
        assert type(self) is X86FP80Type
        return self

    def __repr__(self):
        return 'x86_fp80'

Type._kind_type_map[TypeKind.X86_FP80] = X86FP80Type

class FP128Type(RealType):
    __slots__ = ()

    def __new__(cls, context):
        ''' Obtain a 128-bit floating point type (112-bit mantissa) from a
            context.
        '''
        assert cls is FP128Type
        raw = _core.FP128TypeInContext(context._raw)
        self = Type.__new__(Type, raw, context)
        assert type(self) is FP128Type
        return self

    def __repr__(self):
        return 'fp128'

Type._kind_type_map[TypeKind.FP128] = FP128Type

class PPCFP128Type(RealType):
    __slots__ = ()

    def __new__(cls, context):
        ''' Obtain a 128-bit floating point type (two 64-bits) from a
            context.
        '''
        assert cls is PPCFP128Type
        raw = _core.PPCFP128TypeInContext(context._raw)
        self = Type.__new__(Type, raw, context)
        assert type(self) is PPCFP128Type
        return self

    def __repr__(self):
        return 'ppc_fp128'

Type._kind_type_map[TypeKind.PPC_FP128] = PPCFP128Type

class FunctionType(Type):
    __slots__ = ()

    def __new__(cls, rt, params, is_var_arg=False):
        ''' Obtain a function type consisting of a specified signature.

            The function is defined as a tuple of a return Type, a list of
            parameter types, and whether the function is variadic.
        '''
        assert cls is FunctionType
        n = len(params)
        raw_params = (_core.Type * n)(*[i._raw for i in params])
        raw_ft = _core.FunctionType(rt._raw, raw_params, n, is_var_arg)
        self = Type.__new__(Type, raw_ft, rt._context)
        assert type(self) is FunctionType
        return self

    def __repr__(self):
        rt = str(self.GetReturnType())
        at = [str(x) for x in self.GetParamTypes()]
        if self.IsVarArg():
            at.append('...')
        return '%s(%s)' % (rt, ', '.join(at))

    def IsVarArg(self):
        ''' Returns whether a function type is variadic.
        '''
        return bool(_core.IsFunctionVarArg(self._raw))

    def GetReturnType(self):
        ''' Obtain the Type this function Type returns.
        '''
        return Type(_core.GetReturnType(self._raw), self._context)

    def GetParamTypes(self):
        ''' Obtain the types of a function's parameters.
        '''
        num = _core.CountParamTypes(self._raw)
        temp_buf = (_core.Type * num)()
        _core.GetParamTypes(self._raw, temp_buf)
        return [Type(temp_buf[i], self._context) for i in range(num)]

Type._kind_type_map[TypeKind.Function] = FunctionType


class StructType(Type):
    __slots__ = ()

    def __new__(cls, context, body, name, packed=False):
        ''' Depending on arguments, create a named or unnamed struct
            with or without a body.
        '''
        assert cls is StructType
        if name is None:
            if body is None:
                raise ValueError('At least one argument must not be None')
            num = len(body)
            raw_body = (_core.Type * num)(*[i._raw for i in body])
            raw_struct = _core.StructTypeInContext(context._raw, raw_body, num, packed)
        else:
            bname = u2b(name)
            raw_struct = _core.StructCreateNamed(context._raw, bname)
            if body is not None:
                num = len(body)
                raw_body = (_core.Type * num)(*[i._raw for i in body])
                _core.StructSetBody(raw_struct, raw_body, num, packed)
        self = Type.__new__(Type, raw_struct, context)
        assert type(self) is StructType
        return self

    def __repr__(self):
        name = self.GetStructName()
        prefix = 'struct'
        if name is not None:
            prefix = 'struct %s' % name
        if self.IsOpaqueStruct():
            return prefix
        body = [str(x) for x in self.GetStructElementTypes()]
        if self.IsPackedStruct():
            return '%s <{ %s }>' % (prefix, ', '.join(body))
        else:
            return '%s { %s }' % (prefix, ', '.join(body))

    def GetStructName(self):
        ''' Obtain the name of a structure, or None.
        '''
        raw = _core.GetStructName(self._raw)
        if raw is not None:
            return b2u(raw)
        return None

    def StructSetBody(self, body, packed=False):
        ''' Set the contents of a structure type.

            You should probably use the ctor instead.
        '''
        assert self.IsOpaqueStruct()
        num = len(body)
        raw_body = (_core.Type * num)(*[i._raw for i in body])
        _core.StructSetBody(self._raw, raw_body, num, packed)

    def GetStructElementTypes(self):
        ''' Get the elements within a structure.
        '''
        assert not self.IsOpaqueStruct()
        num = _core.CountStructElementTypes(self._raw)
        temp_buf = (_core.Type * num)()
        _core.GetStructElementTypes(self._raw, temp_buf)
        return [Type(temp_buf[i], self._context) for i in range(num)]

    def IsPackedStruct(self):
        ''' Determine whether a structure is packed.
        '''
        assert not self.IsOpaqueStruct()
        return bool(_core.IsPackedStruct(self._raw))

    def IsOpaqueStruct(self):
        ''' Determine whether a structure is opaque.
        '''
        return bool(_core.IsOpaqueStruct(self._raw))

    def ConstNamedStruct(self, values):
        ''' Create a non-anonymous ConstantStruct from values.
        '''
        n = len(values)
        raw_values = (_core.Value * n)(*[i._raw for i in values])
        return Value(_core.ConstNamedStruct(self._raw, raw_values, n), self._context)

Type._kind_type_map[TypeKind.Struct] = StructType

class SequentialType(Type):
    ''' Sequential types represents "arrays" of types. This is a super class
        for array, vector, and pointer types.
    '''
    __slots__ = ()

    def __new__(cls):
        raise TypeError

    def GetElementType(self):
        ''' Obtain the type of elements within a sequential type.

            This works on array, vector, and pointer types.
        '''
        return Type(_core.GetElementType(self._raw), self._context)

class ArrayType(SequentialType):
    __slots__ = ()

    def __new__(cls, elem, count):
        ''' Create a fixed size array type that refers to a specific type.

            The created type will exist in the context that its element type
            exists in.
        '''
        assert cls is ArrayType
        raw = _core.ArrayType(elem._raw, count)
        self = Type.__new__(Type, raw, elem._context)
        assert type(self) is ArrayType
        return self

    def __repr__(self):
        return '[%d x %s]' % (self.GetArrayLength(), self.GetElementType())

    def GetArrayLength(self):
        ''' Obtain the length of an array type.
        '''
        return _core.GetArrayLength(self._raw)

Type._kind_type_map[TypeKind.Array] = ArrayType

class PointerType(SequentialType):
    __slots__ = ()

    def __new__(cls, elem, addr_space=0):
        ''' Create a pointer type that points to a defined type.

            The created type will exist in the context that its pointee type
            exists in.
        '''
        assert cls is PointerType
        raw = _core.PointerType(elem._raw, addr_space)
        self = Type.__new__(Type, raw, elem._context)
        assert type(self) is PointerType
        return self

    def __repr__(self):
        aspc = self.GetPointerAddressSpace()
        if aspc:
            return '%s addrspace(%d)*' % (self.GetElementType(), aspc)
        return '%s*' % (self.GetElementType())

    def GetPointerAddressSpace(self):
        ''' Obtain the address space of a pointer type.
        '''
        return _core.GetPointerAddressSpace(self._raw)

    def ConstPointerNull(self):
        ''' Obtain a constant that is a constant pointer pointing to NULL for a
            specified type.
        '''
        return Value(_core.ConstPointerNull(self._raw), self._context)

Type._kind_type_map[TypeKind.Pointer] = PointerType

class VectorType(SequentialType):
    __slots__ = ()

    def __new__(cls, elem, count):
        ''' Create a vector type that contains a defined type and has a
            specific number of elements.

            The created type will exist in the context thats its element
            type exists in.
        '''
        assert cls is VectorType
        raw = _core.VectorType(elem._raw, count)
        self = Type.__new__(Type, raw, elem._context)
        assert type(self) is VectorType
        return self

    def __repr__(self):
        return '<%d x %s>' % (self.GetVectorSize(), self.GetElementType())

    def GetVectorSize(self):
        ''' Obtain the number of elements in a vector type.
        '''
        return _core.GetVectorSize(self._raw)

Type._kind_type_map[TypeKind.Vector] = VectorType

class VoidType(Type):
    __slots__ = ()

    def __new__(cls, context):
        ''' Create a void type in a context.
        '''
        assert cls is VoidType
        raw = _core.VoidTypeInContext(context._raw)
        self = Type.__new__(Type, raw, context)
        assert type(self) is VoidType
        return self

    def __repr__(self):
        return 'void'

Type._kind_type_map[TypeKind.Void] = VoidType

class LabelType(Type):
    __slots__ = ()

    def __new__(cls, context):
        ''' Create a label type in a context.
        '''
        assert cls is LabelType
        raw = _core.LabelTypeInContext(context._raw)
        self = Type.__new__(Type, raw, context)
        assert type(self) is LabelType
        return self

    def __repr__(self):
        return 'label'

Type._kind_type_map[TypeKind.Label] = LabelType

class X86MMXType(Type):
    __slots__ = ()

    def __new__(cls, context):
        ''' Create a X86 MMX type in a context.
        '''
        assert cls is X86MMXType
        raw = _core.X86MMXTypeInContext(context._raw)
        self = Type.__new__(Type, raw, context)
        assert type(self) is X86MMXType
        return self

    def __repr__(self):
        return 'x86_mmx'

Type._kind_type_map[TypeKind.X86_MMX] = X86MMXType

class MetadataType(Type):
    __slots__ = ()

    def __new__(cls):
        ''' Unlike the rest, there is no direct way to get this singleton.

            However, .TypeOf on an MDNode or MDString will return this.
        '''
        raise NotImplementedError

    def __repr__(self):
        return 'metadata'

Type._kind_type_map[TypeKind.Metadata] = MetadataType


class Value(object):
    __slots__ = ('_raw', '_context', '__weakref__')

    def __new__(cls, raw, context):
        assert isinstance(raw, _core.Value)
        assert isinstance(context, Context)
        assert cls == Value # do not attempt to create a subclass directly.
        if not raw:
            return None
        raw_ptr = _c.pointer_value(raw)
        try:
            return context.value_cache[raw_ptr]
        except KeyError:
            pass
        cls = Value._figure_out(raw)
        self = object.__new__(cls)
        context.value_cache[raw_ptr] = self
        self._raw = raw
        self._context = context
        assert bool(_core.IsConstant(self._raw)) == isinstance(self, Constant)
        assert bool(_core.IsUndef(self._raw)) == isinstance(self, UndefValue)
        return self

    @staticmethod
    def _figure_out(value):
        # I seriously can't figure out a better way ...
        if _core.IsAArgument(value): return Argument
        if _core.IsABasicBlock(value): return BasicBlock
        if _core.IsAInlineAsm(value): return InlineAsm
        if _core.IsAMDNode(value): return MDNode
        if _core.IsAMDString(value): return MDString
        if _core.IsAUser(value):
            if _core.IsAConstant(value):
                if _core.IsABlockAddress(value): return BlockAddress
                if _core.IsAConstantAggregateZero(value): return ConstantAggregateZero
                if _core.IsAConstantArray(value): return ConstantArray
                if _core.IsAConstantExpr(value): return ConstantExpr._figure_out(value)
                if _core.IsAConstantFP(value): return ConstantFP
                if _core.IsAConstantInt(value): return ConstantInt
                if _core.IsAConstantPointerNull(value): return ConstantPointerNull
                if _core.IsAConstantStruct(value): return ConstantStruct
                if _core.IsAConstantVector(value): return ConstantVector
                if _core.IsAGlobalValue(value):
                    if _core.IsAFunction(value): return Function
                    if _core.IsAGlobalAlias(value): return GlobalAlias
                    if _core.IsAGlobalVariable(value): return GlobalVariable
                    assert unknown_values, 'Uh-oh, unknown GlobalValue subclass.'
                    return GlobalValue
                if _core.IsAUndefValue(value): return UndefValue
                # As of LLVM 3.3, these still aren't exposed in the C API.
                if True:
                    # can't do Type(_core.TypeOf(value))
                    # unless we also pass the (high-level) context.
                    tk = _core.GetTypeKind(_core.TypeOf(value))
                    if tk == TypeKind.Vector:
                        return ConstantDataVector
                    if tk == TypeKind.Array:
                        return ConstantDataArray
                assert unknown_values, 'Uh-oh, unknown Constant subclass.'
                return Constant
            if _core.IsAInstruction(value):
                if _core.IsABinaryOperator(value): return BinaryOperator
                if _core.IsACallInst(value):
                    if _core.IsAIntrinsicInst(value):
                        if _core.IsADbgInfoIntrinsic(value):
                            if _core.IsADbgDeclareInst(value): return DbgDeclareInst
                            assert unknown_values, 'Uh-oh, unknown DbgInfoIntrinsic subclass.'
                            return DbgInfoIntrinsic
                        if _core.IsAMemIntrinsic(value):
                            if _core.IsAMemCpyInst(value): return MemCpyInst
                            if _core.IsAMemMoveInst(value): return MemMoveInst
                            if _core.IsAMemSetInst(value): return MemSetInst
                            assert unknown_values, 'Uh-oh, unknown MemIntrinsic subclass.'
                            return MemIntrinsic
                        assert unknown_values, 'Uh-oh, unknown IntrinsicInst subclass.'
                        return IntrinsicInst
                    # This is normal
                    #assert unknown_values, 'Uh-oh, unknown CallInst subclass.'
                    return CallInst
                if _core.IsACmpInst(value):
                    if _core.IsAFCmpInst(value): return FCmpInst
                    if _core.IsAICmpInst(value): return ICmpInst
                    assert unknown_values, 'Uh-oh, unknown CmpInst subclass.'
                    return CmpInst
                if _core.IsAExtractElementInst(value): return ExtractElementInst
                if _core.IsAGetElementPtrInst(value): return GetElementPtrInst
                if _core.IsAInsertElementInst(value): return InsertElementInst
                if _core.IsAInsertValueInst(value): return InsertValueInst
                if _core.IsALandingPadInst(value): return LandingPadInst
                if _core.IsAPHINode(value): return PHINode
                if _core.IsASelectInst(value): return SelectInst
                if _core.IsAShuffleVectorInst(value): return ShuffleVectorInst
                if _core.IsAStoreInst(value): return StoreInst
                if _core.IsATerminatorInst(value):
                    if _core.IsABranchInst(value): return BranchInst
                    if _core.IsAIndirectBrInst(value): return IndirectBrInst
                    if _core.IsAInvokeInst(value): return InvokeInst
                    if _core.IsAReturnInst(value): return ReturnInst
                    if _core.IsASwitchInst(value): return SwitchInst
                    if _core.IsAUnreachableInst(value): return UnreachableInst
                    if _core.IsAResumeInst(value): return ResumeInst
                    assert unknown_values, 'Uh-oh, unknown TerminatorInst subclass.'
                    return TerminatorInst
                if _core.IsAUnaryInstruction(value):
                    if _core.IsAAllocaInst(value): return AllocaInst
                    if _core.IsACastInst(value):
                        if _core.IsABitCastInst(value): return BitCastInst
                        if _core.IsAFPExtInst(value): return FPExtInst
                        if _core.IsAFPToSIInst(value): return FPToSIInst
                        if _core.IsAFPToUIInst(value): return FPToUIInst
                        if _core.IsAFPTruncInst(value): return FPTruncInst
                        if _core.IsAIntToPtrInst(value): return IntToPtrInst
                        if _core.IsAPtrToIntInst(value): return PtrToIntInst
                        if _core.IsASExtInst(value): return SExtInst
                        if _core.IsASIToFPInst(value): return SIToFPInst
                        if _core.IsATruncInst(value): return TruncInst
                        if _core.IsAUIToFPInst(value): return UIToFPInst
                        if _core.IsAZExtInst(value): return ZExtInst
                        assert unknown_values, 'Uh-oh, unknown CastInst subclass.'
                        return CastInst
                    if _core.IsAExtractValueInst(value): return ExtractValueInst
                    if _core.IsALoadInst(value): return LoadInst
                    if _core.IsAVAArgInst(value): return VAArgInst
                    assert unknown_values, 'Uh-oh, unknown UnaryInstruction subclass.'
                    return UnaryInstruction
            assert unknown_values, 'Uh-oh, unknown User subclass.'
            return User
        assert unknown_values, 'Uh-oh, unknown Value subclass.'
        return Value

    def TypeOf(self):
        return Type(_core.TypeOf(self._raw), self._context)

    def GetValueName(self):
        return b2u(_core.GetValueName(self._raw))

    def SetValueName(self, name):
        _core.SetValueName(self._raw, u2b(name))

    def Dump(self):
        _core.DumpValue(self._raw)

    def ReplaceAllUsesWith(self, other):
        _core.ReplaceAllUsesWith(self._raw, other._raw)

    def GetFirstUse(self):
        ''' Obtain the first use of a value.

            Uses are obtained in an iterator fashion. First, call this
            function to obtain a reference to the first use. Then, call
            GetNextUse() on that instance and all subsequently obtained
            instances until GetNextUse() returns None.
        '''
        return Use(_core.GetFirstUse(self._raw), self._context)

class Argument(Value):
    __slots__ = ()

    def GetParamParent(self):
        ''' Obtain the function to which this argument belongs.
        '''
        return Value(_core.GetParamParent(self._raw), self._context)

    def GetNextParam(self):
        ''' Obtain the next parameter to a function.
        '''
        return Value(_core.GetNextParam(self._raw), self._context)

    def GetPreviousParam(self):
        ''' Obtain the previous parameter to a function.
        '''
        return Value(_core.GetPreviousParam(self._raw), self._context)

    def AddAttribute(self, pa):
        ''' Add an attribute to a function argument.
        '''
        _core.AddAttribute(self._raw, pa)

    def RemoveAttribute(self, pa):
        ''' Remove an attribute from a function argument.
        '''
        _core.RemoveAttribute(self._raw, pa)

    def GetAttribute(self):
        ''' Get an attribute from a function argument.
        '''
        return _core.GetAttribute(self._raw)

    def SetParamAlignment(self, align):
        ''' Set the alignment for a function parameter.
        '''
        _core.SetParamAlignment(self._raw, align)


class BasicBlock(Value):
    __slots__ = ('_raw_bb',)

    def __init__(self, raw, context):
        ''' DO NOT CALL THIS DIRECTLY.

            It will be magically called when constructing a Value().

            It only does a little extra work required for BBs.
        '''
        # this may be called more than once
        if not hasattr(self, '_raw_bb'):
            self._raw_bb = _core.ValueAsBasicBlock(raw)

    def GetBasicBlockParent(self):
        ''' Obtain the function to which a basic block belongs.
        '''
        return Value(_core.GetBasicBlockParent(self._raw_bb), self._context)

    def GetBasicBlockTerminator(self):
        ''' Obtain the terminator instruction for a basic block.

            If the basic block does not have a terminator (it is not
            well-formed if it doesn't), then NULL is returned.
        '''
        return Value(_core.GetBasicBlockTerminator(self._raw_bb), self._context)

    def GetNextBasicBlock(self):
        ''' Advance a basic block iterator.
        '''
        return Value(_core.BasicBlockAsValue(_core.GetNextBasicBlock(self._raw_bb)), self._context)

    def GetPreviousBasicBlock(self):
        ''' Go backwards in a basic block iterator.
        '''
        return Value(_core.BasicBlockAsValue(_core.GetPreviousBasicBlock(self._raw_bb)), self._context)

    def InsertBasicBlock(self, name=''):
        ''' Insert a basic block in a function before another basic block.

            The function to add to is determined by the function of the
            passed basic block.
        '''
        return Value(_core.BasicBlockAsValue(_core.InsertBasicBlockInContext(self._context._raw, self._raw_bb, u2b(name))), self._context)

    # This function is dangerous in Python mode.
    # We *could* just delete it from the cache, though, and hope.
    @dangerous
    @untested
    def DeleteBasicBlock(self):
        ''' Remove a basic block from a function and delete it.

            This deletes the basic block from its containing function and
            deletes the basic block itself.
        '''
        _core.DeleteBasicBlock(self._raw_bb)

    if 0:
        # This frontend does not support detached BBs.
        @untested
        def RemoveBasicBlockFromParent(self):
            ''' Remove a basic block from a function.

                This deletes the basic block from its containing function
                but keep the basic block alive.
            '''
            _core.RemoveBasicBlockFromParent(self._raw_bb)

    def MoveBasicBlockBefore(self, other):
        ''' Move a basic block to before another one.
        '''
        _core.MoveBasicBlockBefore(self._raw_bb, other._raw_bb)

    def MoveBasicBlockAfter(self, other):
        ''' Move a basic block to after another one.
        '''
        _core.MoveBasicBlockAfter(self._raw_bb, other._raw_bb)

    def GetFirstInstruction(self):
        ''' Obtain the first Instruction in a basic block.
        '''
        return Value(_core.GetFirstInstruction(self._raw_bb), self._context)

    def GetLastInstruction(self):
        ''' Obtain the last instruction in a basic block.
        '''
        return Value(_core.GetLastInstruction(self._raw_bb), self._context)
    # see also next/prev in Instruction


class InlineAsm(Value):
    __slots__ = ()

    def __new__(cls, fty, asm_string, constraints, has_side_effects, is_align_stack):
        assert cls == InlineAsm
        assert isinstance(fty, FunctionType)
        return Value(_core.ConstInlineAsm(fty._raw, u2b(asm_string), u2b(constraints), has_side_effects, is_align_stack), fty._context)

class MDNode(Value):
    __slots__ = ()

class MDString(Value):
    __slots__ = ()

    def GetMDString(self):
        raw_len = ctypes.c_uint()
        raw_out = _core.GetMDString(self._raw, ctypes.byref(raw_len))
        return b2u(_c.buffer_as_bytes(raw_out, raw_len.value))


class User(Value):
    __slots__ = ()

    def GetOperand(self, index):
        return Value(_core.GetOperand(self._raw, index), self._context)

    @untested
    def SetOperand(self, index, value):
        _core.SetOperand(self._raw, index, value._raw)

    def GetNumOperands(self):
        return _core.GetNumOperands(self._raw)

class  Constant(User):
    __slots__ = ()

    def IsNull(self):
        ''' Determine whether a value instance is null.
        '''
        return bool(_core.IsNull(self._raw))

    def ConstNeg(self):
        return Value(_core.ConstNeg(self._raw), self._context)

    def ConstNSWNeg(self):
        return Value(_core.ConstNSWNeg(self._raw), self._context)

    def ConstNUWNeg(self):
        return Value(_core.ConstNUWNeg(self._raw), self._context)

    def ConstFNeg(self):
        return Value(_core.ConstFNeg(self._raw), self._context)

    def ConstNot(self):
        return Value(_core.ConstNot(self._raw), self._context)

    def ConstAdd(self, other):
        return Value(_core.ConstAdd(self._raw, other._raw), self._context)

    def ConstNSWAdd(self, other):
        return Value(_core.ConstNSWAdd(self._raw, other._raw), self._context)

    def ConstNUWAdd(self, other):
        return Value(_core.ConstNUWAdd(self._raw, other._raw), self._context)

    def ConstFAdd(self, other):
        return Value(_core.ConstFAdd(self._raw, other._raw), self._context)

    def ConstSub(self, other):
        return Value(_core.ConstSub(self._raw, other._raw), self._context)

    def ConstNSWSub(self, other):
        return Value(_core.ConstNSWSub(self._raw, other._raw), self._context)

    def ConstNUWSub(self, other):
        return Value(_core.ConstNUWSub(self._raw, other._raw), self._context)

    def ConstFSub(self, other):
        return Value(_core.ConstFSub(self._raw, other._raw), self._context)

    def ConstMul(self, other):
        return Value(_core.ConstMul(self._raw, other._raw), self._context)

    def ConstNSWMul(self, other):
        return Value(_core.ConstNSWMul(self._raw, other._raw), self._context)

    def ConstNUWMul(self, other):
        return Value(_core.ConstNUWMul(self._raw, other._raw), self._context)

    def ConstFMul(self, other):
        return Value(_core.ConstFMul(self._raw, other._raw), self._context)

    def ConstUDiv(self, other):
        return Value(_core.ConstUDiv(self._raw, other._raw), self._context)

    def ConstSDiv(self, other):
        return Value(_core.ConstSDiv(self._raw, other._raw), self._context)

    def ConstExactSDiv(self, other):
        return Value(_core.ConstExactSDiv(self._raw, other._raw), self._context)

    def ConstFDiv(self, other):
        return Value(_core.ConstFDiv(self._raw, other._raw), self._context)

    def ConstURem(self, other):
        return Value(_core.ConstURem(self._raw, other._raw), self._context)

    def ConstSRem(self, other):
        return Value(_core.ConstSRem(self._raw, other._raw), self._context)

    def ConstFRem(self, other):
        return Value(_core.ConstFRem(self._raw, other._raw), self._context)

    def ConstAnd(self, other):
        return Value(_core.ConstAnd(self._raw, other._raw), self._context)

    def ConstOr(self, other):
        return Value(_core.ConstOr(self._raw, other._raw), self._context)

    def ConstXor(self, other):
        return Value(_core.ConstXor(self._raw, other._raw), self._context)

    def ConstICmp(self, ipred, other):
        return Value(_core.ConstICmp(ipred, self._raw, other._raw), self._context)

    def ConstFCmp(self, rpred, other):
        return Value(_core.ConstFCmp(rpred, self._raw, other._raw), self._context)

    def ConstShl(self, other):
        return Value(_core.ConstShl(self._raw, other._raw), self._context)

    def ConstLShr(self, other):
        return Value(_core.ConstLShr(self._raw, other._raw), self._context)

    def ConstAShr(self, other):
        return Value(_core.ConstAShr(self._raw, other._raw), self._context)

    def ConstGEP(self, indices):
        n = len(indices)
        raw_indices = (_core.Value * n)(*[i._raw for i in indices])
        return Value(_core.ConstGEP(self._raw, raw_indices, n), self._context)

    def ConstInBoundsGEP(self, indices):
        n = len(indices)
        raw_indices = (_core.Value * n)(*[i._raw for i in indices])
        return Value(_core.ConstInBoundsGEP(self._raw, raw_indices, n), self._context)

    def ConstTrunc(self, ty):
        return Value(_core.ConstTrunc(self._raw, ty._raw), self._context)

    def ConstSExt(self, ty):
        return Value(_core.ConstSExt(self._raw, ty._raw), self._context)

    def ConstZExt(self, ty):
        return Value(_core.ConstZExt(self._raw, ty._raw), self._context)

    def ConstFPTrunc(self, ty):
        return Value(_core.ConstFPTrunc(self._raw, ty._raw), self._context)

    def ConstFPExt(self, ty):
        return Value(_core.ConstFPExt(self._raw, ty._raw), self._context)

    def ConstUIToFP(self, ty):
        return Value(_core.ConstUIToFP(self._raw, ty._raw), self._context)

    def ConstSIToFP(self, ty):
        return Value(_core.ConstSIToFP(self._raw, ty._raw), self._context)

    def ConstFPToUI(self, ty):
        return Value(_core.ConstFPToUI(self._raw, ty._raw), self._context)

    def ConstFPToSI(self, ty):
        return Value(_core.ConstFPToSI(self._raw, ty._raw), self._context)

    def ConstPtrToInt(self, ty):
        return Value(_core.ConstPtrToInt(self._raw, ty._raw), self._context)

    def ConstIntToPtr(self, ty):
        return Value(_core.ConstIntToPtr(self._raw, ty._raw), self._context)

    def ConstBitCast(self, ty):
        return Value(_core.ConstBitCast(self._raw, ty._raw), self._context)

    @deprecated
    @untested
    def ConstZExtOrBitCast(self, ty):
        return Value(_core.ConstZExtOrBitCast(self._raw, ty._raw), self._context)

    @deprecated
    @untested
    def ConstSExtOrBitCast(self, ty):
        return Value(_core.ConstSExtOrBitCast(self._raw, ty._raw), self._context)

    @deprecated
    @untested
    def ConstTruncOrBitCast(self, ty):
        return Value(_core.ConstTruncOrBitCast(self._raw, ty._raw), self._context)

    @deprecated
    @untested
    def ConstPointerCast(self, ty):
        return Value(_core.ConstPointerCast(self._raw, ty._raw), self._context)

    @deprecated
    @untested
    def ConstIntCast(self, ty, is_signed):
        return Value(_core.ConstIntCast(self._raw, ty._raw, is_signed), self._context)

    @deprecated
    @untested
    def ConstFPCast(self, ty):
        return Value(_core.ConstFPCast(self._raw, ty._raw), self._context)

    def ConstSelect(self, if_true, if_false):
        return Value(_core.ConstSelect(self._raw, if_true._raw, if_false._raw), self._context)

    def ConstExtractElement(self, index):
        return Value(_core.ConstExtractElement(self._raw, index._raw), self._context)

    def ConstInsertElement(self, value, index):
        return Value(_core.ConstInsertElement(self._raw, value._raw, index._raw), self._context)

    def ConstShuffleVector(self, other, mask):
        return Value(_core.ConstShuffleVector(self._raw, other._raw, mask._raw), self._context)

    def ConstExtractValue(self, indices):
        n = len(indices)
        raw_indices = (ctypes.c_uint * n)(*indices)
        return Value(_core.ConstExtractValue(self._raw, raw_indices, n), self._context)

    def ConstInsertValue(self, value, indices):
        n = len(indices)
        raw_indices = (ctypes.c_uint * n)(*indices)
        return Value(_core.ConstInsertValue(self._raw, value._raw, raw_indices, n), self._context)

class   AnyConstantArray(Value):
    '''Mixin for ConstantArray and ConstantDataArray
    '''
    __slots__ = ()

class   AnyConstantVector(Value):
    '''Mixin for ConstantVector and ConstantDataVector
    '''
    __slots__ = ()

if (3, 1) <= _version:
    class   ConstantDataSequential(Constant):
        __slots__ = ()

    class    ConstantDataArray(ConstantDataSequential, AnyConstantArray):
        __slots__ = ()

    class    ConstantDataVector(ConstantDataSequential, AnyConstantVector):
        __slots__ = ()

class   BlockAddress(Constant):
    __slots__ = ()

    def __new__(cls, bb):
        fv = bb.GetBasicBlockParent()
        return Value(_core.BlockAddress(fv._raw, bb._raw_bb), fv._context)

class   ConstantAggregateZero(Constant):
    __slots__ = ()

class   ConstantArray(Constant, AnyConstantArray):
    __slots__ = ()

class   ConstantExpr(Constant):
    __slots__ = ()
    _subclasses = {}

    @staticmethod
    def _figure_out(value):
        # value is a _core.Value that is a ConstantExpr
        op = _core.GetConstOpcode(value)
        assert op in ConstantExpr._subclasses
        cls = ConstantExpr._subclasses[op]
        if cls is not None:
            return cls
        assert unknown_values, 'Uh-oh, nonexpression opcode'
        return ConstantExpr
ConstantExpr._subclasses[Opcode.Ret] = None
ConstantExpr._subclasses[Opcode.Br] = None
ConstantExpr._subclasses[Opcode.Switch] = None
ConstantExpr._subclasses[Opcode.IndirectBr] = None
ConstantExpr._subclasses[Opcode.Invoke] = None
ConstantExpr._subclasses[Opcode.Unreachable] = None

class    BinaryConstantExpr(ConstantExpr):
    __slots__ = ()
class     BinaryAddConstantExpr(BinaryConstantExpr):
    __slots__ = ()
ConstantExpr._subclasses[Opcode.Add] = BinaryAddConstantExpr
class     BinaryFAddConstantExpr(BinaryConstantExpr):
    __slots__ = ()
ConstantExpr._subclasses[Opcode.FAdd] = BinaryFAddConstantExpr
class     BinarySubConstantExpr(BinaryConstantExpr):
    __slots__ = ()
ConstantExpr._subclasses[Opcode.Sub] = BinarySubConstantExpr
class     BinaryFSubConstantExpr(BinaryConstantExpr):
    __slots__ = ()
ConstantExpr._subclasses[Opcode.FSub] = BinaryFSubConstantExpr
class     BinaryMulConstantExpr(BinaryConstantExpr):
    __slots__ = ()
ConstantExpr._subclasses[Opcode.Mul] = BinaryMulConstantExpr
class     BinaryFMulConstantExpr(BinaryConstantExpr):
    __slots__ = ()
ConstantExpr._subclasses[Opcode.FMul] = BinaryFMulConstantExpr
class     BinaryUDivConstantExpr(BinaryConstantExpr):
    __slots__ = ()
ConstantExpr._subclasses[Opcode.UDiv] = BinaryUDivConstantExpr
class     BinarySDivConstantExpr(BinaryConstantExpr):
    __slots__ = ()
ConstantExpr._subclasses[Opcode.SDiv] = BinarySDivConstantExpr
class     BinaryFDivConstantExpr(BinaryConstantExpr):
    __slots__ = ()
ConstantExpr._subclasses[Opcode.FDiv] = BinaryFDivConstantExpr
class     BinaryURemConstantExpr(BinaryConstantExpr):
    __slots__ = ()
ConstantExpr._subclasses[Opcode.URem] = BinaryURemConstantExpr
class     BinarySRemConstantExpr(BinaryConstantExpr):
    __slots__ = ()
ConstantExpr._subclasses[Opcode.SRem] = BinarySRemConstantExpr
class     BinaryFRemConstantExpr(BinaryConstantExpr):
    __slots__ = ()
ConstantExpr._subclasses[Opcode.FRem] = BinaryFRemConstantExpr
class     BinaryShlConstantExpr(BinaryConstantExpr):
    __slots__ = ()
ConstantExpr._subclasses[Opcode.Shl] = BinaryShlConstantExpr
class     BinaryLShrConstantExpr(BinaryConstantExpr):
    __slots__ = ()
ConstantExpr._subclasses[Opcode.LShr] = BinaryLShrConstantExpr
class     BinaryAShrConstantExpr(BinaryConstantExpr):
    __slots__ = ()
ConstantExpr._subclasses[Opcode.AShr] = BinaryAShrConstantExpr
class     BinaryAndConstantExpr(BinaryConstantExpr):
    __slots__ = ()
ConstantExpr._subclasses[Opcode.And] = BinaryAndConstantExpr
class     BinaryOrConstantExpr(BinaryConstantExpr):
    __slots__ = ()
ConstantExpr._subclasses[Opcode.Or] = BinaryOrConstantExpr
class     BinaryXorConstantExpr(BinaryConstantExpr):
    __slots__ = ()
ConstantExpr._subclasses[Opcode.Xor] = BinaryXorConstantExpr
ConstantExpr._subclasses[Opcode.Alloca] = None
ConstantExpr._subclasses[Opcode.Load] = None
ConstantExpr._subclasses[Opcode.Store] = None

class    GetElementPtrConstantExpr(ConstantExpr):
    __slots__ = ()
ConstantExpr._subclasses[Opcode.GetElementPtr] = GetElementPtrConstantExpr

# not used for normal unary things
class    UnaryConstantExpr(ConstantExpr):
    __slots__ = ()
class     UnaryTruncConstantExpr(UnaryConstantExpr):
    __slots__ = ()
ConstantExpr._subclasses[Opcode.Trunc] = UnaryTruncConstantExpr
class     UnaryZExtConstantExpr(UnaryConstantExpr):
    __slots__ = ()
ConstantExpr._subclasses[Opcode.ZExt] = UnaryZExtConstantExpr
class     UnarySExtConstantExpr(UnaryConstantExpr):
    __slots__ = ()
ConstantExpr._subclasses[Opcode.SExt] = UnarySExtConstantExpr
class     UnaryFPToUIConstantExpr(UnaryConstantExpr):
    __slots__ = ()
ConstantExpr._subclasses[Opcode.FPToUI] = UnaryFPToUIConstantExpr
class     UnaryFPToSIConstantExpr(UnaryConstantExpr):
    __slots__ = ()
ConstantExpr._subclasses[Opcode.FPToSI] = UnaryFPToSIConstantExpr
class     UnaryUIToFPConstantExpr(UnaryConstantExpr):
    __slots__ = ()
ConstantExpr._subclasses[Opcode.UIToFP] = UnaryUIToFPConstantExpr
class     UnarySIToFPConstantExpr(UnaryConstantExpr):
    __slots__ = ()
ConstantExpr._subclasses[Opcode.SIToFP] = UnarySIToFPConstantExpr
class     UnaryFPTruncConstantExpr(UnaryConstantExpr):
    __slots__ = ()
ConstantExpr._subclasses[Opcode.FPTrunc] = UnaryFPTruncConstantExpr
class     UnaryFPExtConstantExpr(UnaryConstantExpr):
    __slots__ = ()
ConstantExpr._subclasses[Opcode.FPExt] = UnaryFPExtConstantExpr
class     UnaryPtrToIntConstantExpr(UnaryConstantExpr):
    __slots__ = ()
ConstantExpr._subclasses[Opcode.PtrToInt] = UnaryPtrToIntConstantExpr
class     UnaryIntToPtrConstantExpr(UnaryConstantExpr):
    __slots__ = ()
ConstantExpr._subclasses[Opcode.IntToPtr] = UnaryIntToPtrConstantExpr
class     UnaryBitCastConstantExpr(UnaryConstantExpr):
    __slots__ = ()
ConstantExpr._subclasses[Opcode.BitCast] = UnaryBitCastConstantExpr

class    CompareConstantExpr(ConstantExpr):
    __slots__ = ()

class AnyICmp(Value):
    ''' Mixin for ICmpConstantExpr and ICmpInst
    '''
    __slots__ = ()

    def GetICmpPredicate(self):
        ''' Obtain the predicate of an instruction.
        '''
        return _core.GetICmpPredicate(self._raw)

class     ICmpConstantExpr(CompareConstantExpr, AnyICmp):
    __slots__ = ()

ConstantExpr._subclasses[Opcode.ICmp] = ICmpConstantExpr

class     FCmpConstantExpr(CompareConstantExpr):
    __slots__ = ()
ConstantExpr._subclasses[Opcode.FCmp] = FCmpConstantExpr
ConstantExpr._subclasses[Opcode.PHI] = None
ConstantExpr._subclasses[Opcode.Call] = None

class    SelectConstantExpr(ConstantExpr):
    __slots__ = ()
ConstantExpr._subclasses[Opcode.Select] = SelectConstantExpr
# ??
ConstantExpr._subclasses[Opcode.UserOp1] = None
ConstantExpr._subclasses[Opcode.UserOp2] = None
ConstantExpr._subclasses[Opcode.VAArg] = None

class    ExtractElementConstantExpr(ConstantExpr):
    __slots__ = ()
ConstantExpr._subclasses[Opcode.ExtractElement] = ExtractElementConstantExpr

class    InsertElementConstantExpr(ConstantExpr):
    __slots__ = ()

ConstantExpr._subclasses[Opcode.InsertElement] = InsertElementConstantExpr

class    ShuffleVectorConstantExpr(ConstantExpr):
    __slots__ = ()

    @untested
    def __init__(self):
        'since indices are constants, this does not seem to happen'
ConstantExpr._subclasses[Opcode.ShuffleVector] = ShuffleVectorConstantExpr

class    ExtractValueConstantExpr(ConstantExpr):
    __slots__ = ()

    @untested
    def __init__(self):
        'since indices are constants, this does not seem to happen'
ConstantExpr._subclasses[Opcode.ExtractValue] = ExtractValueConstantExpr

class    InsertValueConstantExpr(ConstantExpr):
    __slots__ = ()

    @untested
    def __init__(self):
        'since indices are constants, this does not seem to happen'
ConstantExpr._subclasses[Opcode.InsertValue] = InsertValueConstantExpr
ConstantExpr._subclasses[Opcode.Fence] = None
ConstantExpr._subclasses[Opcode.AtomicCmpXchg] = None
ConstantExpr._subclasses[Opcode.AtomicRMW] = None
ConstantExpr._subclasses[Opcode.Resume] = None
ConstantExpr._subclasses[Opcode.LandingPad] = None
if _version <= (3, 0):
    ConstantExpr._subclasses[Opcode.Unwind] = None


class   ConstantFP(Constant):
    __slots__ = ()

class   ConstantInt(Constant):
    __slots__ = ()

    def GetZExtValue(self):
        return _core.ConstIntGetZExtValue(self._raw)

    def GetSExtValue(self):
        return _core.ConstIntGetSExtValue(self._raw)

class   ConstantPointerNull(Constant):
    __slots__ = ()

class   ConstantStruct(Constant):
    __slots__ = ()

class   ConstantVector(Constant, AnyConstantVector):
    __slots__ = ()

class   GlobalValue(Constant):
    __slots__ = ()

    # Can't enable because Module is not cached.
    # Haven't cached because it would cause issues.
    # I'm also not convinced this is very useful.
    #@untested
    #def GetGlobalParent(self):
    #    return _core.GetGlobalParent(self)

    def IsDeclaration(self):
        return bool(_core.IsDeclaration(self._raw))

    def GetLinkage(self):
        return _core.GetLinkage(self._raw)

    def SetLinkage(self, linkage):
        _core.SetLinkage(self._raw, linkage)

    def GetSection(self):
        return b2u(_core.GetSection(self._raw))

    def SetSection(self, name):
        _core.SetSection(self._raw, u2b(name))

    def GetVisibility(self):
        return _core.GetVisibility(self._raw)

    def SetVisibility(self, viz):
        _core.SetVisibility(self._raw, viz)

    def GetAlignment(self):
        return _core.GetAlignment(self._raw)

    def SetAlignment(self, align):
        _core.SetAlignment(self._raw, align)


class    Function(GlobalValue):
    __slots__ = ()

    def GetNextFunction(self):
        ''' Advance a Function iterator to the next Function.

            Returns None if the iterator was already at the end and
            there are no more functions.
        '''
        return Value(_core.GetNextFunction(self._raw), self._context)

    def GetPreviousFunction(self):
        ''' Decrement a Function iterator to the previous Function.

            Returns None if the iterator was already at the beginning
            and there are no previous functions.
        '''
        return Value(_core.GetPreviousFunction(self._raw), self._context)

    # This function is dangerous in Python mode.
    # We *could* just delete it from the cache, though, and hope.
    @dangerous
    @untested
    def DeleteFunction(self):
        ''' Remove a function from its containing module and deletes it.
        '''
        _core.DeleteFunction(self._raw)

    @untested
    def GetIntrinsicID(self):
        ''' Obtain the ID number from a function instance.
        '''
        return _core.GetIntrinsicID(self._raw)

    def GetCallConv(self):
        ''' Obtain the calling convention of a function.
        '''
        return _core.GetFunctionCallConv(self._raw)

    def SetCallConv(self, cc):
        ''' Set the calling convention of a function.
        '''
        _core.SetFunctionCallConv(self._raw, cc)

    def GetGC(self):
        ''' Obtain the name of the garbage collector to use during code
            generation.
        '''
        raw_gc = _core.GetGC(self._raw)
        if raw_gc is None:
            return None
        return b2u(raw_gc)

    def SetGC(self, gc):
        ''' Define the garbage collector to use during code generation.
        '''
        if gc is None:
            raw_gc = None
        else:
            raw_gc = u2b(gc)
        _core.SetGC(self._raw, raw_gc)

    def AddAttr(self, attr):
        ''' Add an attribute to a function.
        '''
        _core.AddFunctionAttr(self._raw, attr)

    def GetAttr(self):
        ''' Obtain an attribute from a function.
        '''
        return _core.GetFunctionAttr(self._raw)

    def RemoveAttr(self, attr):
        ''' Remove an attribute from a function.
        '''
        _core.RemoveFunctionAttr(self._raw, attr)

    def CountParams(self):
        ''' Obtain the number of parameters in a function.
        '''
        return _core.CountParams(self._raw)

    def GetParams(self):
        ''' Obtain the parameters in a function.

            Returns a python list of Argument instances.
        '''
        n = self.CountParams()
        if not n:
            return []
        raw_out = (_core.Value * n)()
        _core.GetParams(self._raw, raw_out)
        context = self._context
        return [Value(v, context) for v in raw_out]

    def GetParam(self, index):
        ''' Obtain the parameter at the specified index.

            Parameters are indexed from 0.
        '''
        return Value(_core.GetParam(self._raw, index), self._context)

    # not sure it's actually worth exposing anything besides GetParams
    @deprecated
    def GetFirstParam(self):
        ''' Obtain the first parameter to a function.
        '''
        return Value(_core.GetFirstParam(self._raw), self._context)

    @deprecated
    def GetLastParam(self):
        ''' Obtain the last parameter to a function.
        '''
        return Value(_core.GetLastParam(self._raw), self._context)


    def CountBasicBlocks(self):
        ''' Obtain the number of basic blocks in a function.
        '''
        return _core.CountBasicBlocks(self._raw)

    def GetBasicBlocks(self):
        ''' Obtain all of the basic blocks in a function.

            Returns a python list.
        '''
        n = self.CountBasicBlocks()
        if not n:
            return []
        raw_out = (_core.BasicBlock * n)()
        _core.GetBasicBlocks(self._raw, raw_out)
        context = self._context
        return [Value(_core.BasicBlockAsValue(bb), context) for bb in raw_out]

    def GetFirstBasicBlock(self):
        ''' Obtain the first basic block in a function.

            The returned basic block can be used as an iterator. You will
            likely eventually call into LLVMGetNextBasicBlock() with it.
        '''
        return Value(_core.BasicBlockAsValue(_core.GetFirstBasicBlock(self._raw)), self._context)

    def GetLastBasicBlock(self):
        ''' Obtain the last basic block in a function.
        '''
        return Value(_core.BasicBlockAsValue(_core.GetLastBasicBlock(self._raw)), self._context)

    def GetEntryBasicBlock(self):
        ''' Obtain the basic block that corresponds to the entry point of a
            function.
        '''
        return Value(_core.BasicBlockAsValue(_core.GetEntryBasicBlock(self._raw)), self._context)

    def AppendBasicBlock(self, name=''):
        ''' Append a basic block to the end of a function.
        '''
        return Value(_core.BasicBlockAsValue(_core.AppendBasicBlockInContext(self._context._raw, self._raw, u2b(name))), self._context)

    # from Analysis.h
    def Verify(self, action):
        ''' Verifies that a single function is valid, taking the specified
            action. Useful for debugging.
        '''
        rv = bool(_analysis.VerifyFunction(self._raw, action))

        if rv:
            raise OSError

    def ViewCFG(self):
        ''' Open up a ghostview window that displays the CFG of the current
            function, including instructions. Useful for debugging.
        '''
        _analysis.ViewFunctionCFG(self._raw)

    def ViewCFGOnly(self):
        ''' Open up a ghostview window that displays the CFG of the current
            function, with just the blocks. Useful for debugging.
        '''
        _analysis.ViewFunctionCFGOnly(self._raw)

class    GlobalAlias(GlobalValue):
    __slots__ = ()

class    GlobalVariable(GlobalValue):
    __slots__ = ()

    def GetNextGlobal(self):
        return Value(_core.GetNextGlobal(self._raw), self._context)

    def GetPreviousGlobal(self):
        return Value(_core.GetPreviousGlobal(self._raw), self._context)

    @dangerous
    @untested
    def DeleteGlobal(self):
        _core.DeleteGlobal(self._raw)

    def GetInitializer(self):
        return Value(_core.GetInitializer(self._raw), self._context)

    def SetInitializer(self, val):
        if val is None:
            _core.SetInitializer(self._raw, None)
        else:
            _core.SetInitializer(self._raw, val._raw)

    def IsThreadLocal(self):
        return bool(_core.IsThreadLocal(self._raw))

    def SetThreadLocal(self, is_tl):
        _core.SetThreadLocal(self._raw, is_tl)

    def IsConstant(self):
        return bool(_core.IsGlobalConstant(self._raw))

    def SetConstant(self, is_c):
        _core.SetGlobalConstant(self._raw, is_c)

class   UndefValue(Constant):
    __slots__ = ()

class  Instruction(User):
    __slots__ = ()

    @untested
    def HasMetadata(self):
        ''' Determine whether an instruction has any metadata attached.
        '''
        return bool(_core.HasMetadata(self._raw))

    @untested
    def GetMetadata(self, kind_id):
        ''' Return metadata associated with an instruction value.
        '''
        return Value(_core.GetMetadata([Value, ctypes.c_uint]), self._context)

    @untested
    def SetMetadata(self, kind_id, md):
        ''' Set metadata associated with an instruction value.
        '''
        _core.SetMetadata([Value, ctypes.c_uint, Value])

    def GetInstructionParent(self):
        ''' Obtain the basic block to which an instruction belongs.
        '''
        return Value(_core.BasicBlockAsValue(_core.GetInstructionParent(self._raw)), self._context)

    def GetNextInstruction(self):
        ''' Obtain the instruction that occurs after the one specified.

            The next instruction will be from the same basic block.

            If this is the last instruction in a basic block, None will be
            returned.
        '''
        return Value(_core.GetNextInstruction(self._raw), self._context)

    def GetPreviousInstruction(self):
        ''' Obtain the instruction that occured before this one.

            If the instruction is the first instruction in a basic block,
            None will be returned.
        '''
        return Value(_core.GetPreviousInstruction(self._raw), self._context)

    # This function is dangerous in Python mode.
    # We *could* just delete it from the cache, though, and hope.
    @dangerous
    @untested
    def InstructionEraseFromParent(self):
        ''' Remove and delete an instruction.

            The instruction specified is removed from its containing
            building block and then deleted.
        '''
        _core.InstructionEraseFromParent(self._raw)

    def GetInstructionOpcode(self):
        ''' Obtain the code Opcode for an individual instruction.
        '''
        return _core.GetInstructionOpcode(self._raw)

class   BinaryOperator(Instruction):
    __slots__ = ()

class AnyCallOrInvoke(Value):
    ''' Mixin to treat CallInst and InvokeInst uniformly.

        This corresponds roughly to llvm::CallSite.
    '''
    __slots__ = ()

    @untested
    def SetInstructionCallConv(self, cc):
        ''' Set the calling convention for a call instruction.
        '''
        _core.SetInstructionCallConv(self._raw, cc)

    @untested
    def GetInstructionCallConv(self):
        ''' Obtain the calling convention for a call instruction.
        '''
        return _core.GetInstructionCallConv(self._raw)

    @untested
    def AddInstrAttribute(self, index, attr):
        _core.AddInstrAttribute(self._raw, index, attr)

    @untested
    def RemoveInstrAttribute(self, index, attr):
        _core.RemoveInstrAttribute(self._raw, index, attr)

    @untested
    def SetInstrParamAlignment(self, index, align):
        _core.SetInstrParamAlignment(self._raw, index, align)

class   CallInst(Instruction, AnyCallOrInvoke):
    __slots__ = ()

    @untested
    def IsTailCall(self):
        ''' Obtain whether a call instruction is a tail call.
        '''
        return bool(_core.IsTailCall(self._raw))

    @untested
    def SetTailCall(self, is_tc):
        ''' Set whether a call instruction is a tail call.
        '''
        _core.SetTailCall(self._raw, is_tc)

class    IntrinsicInst(CallInst):
    __init__ = untested(lambda *args: None)
    __slots__ = ()

class     DbgInfoIntrinsic(IntrinsicInst):
    __init__ = untested(lambda *args: None)
    __slots__ = ()

class      DbgDeclareInst(DbgInfoIntrinsic):
    __init__ = untested(lambda *args: None)
    __slots__ = ()

class     MemIntrinsic(IntrinsicInst):
    __init__ = untested(lambda *args: None)
    __slots__ = ()

class      MemCpyInst(MemIntrinsic):
    __init__ = untested(lambda *args: None)
    __slots__ = ()

class      MemMoveInst(MemIntrinsic):
    __init__ = untested(lambda *args: None)
    __slots__ = ()

class      MemSetInst(MemIntrinsic):
    __init__ = untested(lambda *args: None)
    __slots__ = ()

class   CmpInst(Instruction):
    __slots__ = ()

class    FCmpInst(CmpInst):
    __slots__ = ()

class    ICmpInst(CmpInst, AnyICmp):
    __slots__ = ()

class   ExtractElementInst(Instruction):
    __slots__ = ()

class   GetElementPtrInst(Instruction):
    __slots__ = ()

class   InsertElementInst(Instruction):
    __slots__ = ()

class   InsertValueInst(Instruction):
    __slots__ = ()

class   LandingPadInst(Instruction):
    __init__ = untested(lambda *args: None)
    __slots__ = ()

    @untested
    def AddClause(self, clause_val):
        _core.AddClause(self._raw, clause_val._raw)

    @untested
    def SetCleanup(self, v):
        _core.SetCleanup(self._raw, v)

class   PHINode(Instruction):
    __slots__ = ()

    def AddIncoming(self, values, blocks):
        ''' Add incoming values to the end of a PHI list.
        '''
        n = len(values)
        assert n == len(blocks)
        raw_values = (_core.Value * n)(*[i._raw for i in values])
        raw_blocks = (_core.BasicBlock * n)(*[i._raw_bb for i in blocks])
        _core.AddIncoming(self._raw, raw_values, raw_blocks, n)

    def CountIncoming(self):
        ''' Obtain the number of incoming basic blocks to a PHI node.
        '''
        return _core.CountIncoming(self._raw)

    def GetIncomingValue(self, index):
        ''' Obtain an incoming value to a PHI node as a LLVMValueRef.
        '''
        return Value(_core.GetIncomingValue(self._raw, index), self._context)

    def GetIncomingBlock(self, index):
        ''' Obtain an incoming value to a PHI node as a LLVMBasicBlockRef.
        '''
        return Value(_core.BasicBlockAsValue(_core.GetIncomingBlock(self._raw, index)), self._context)

class   SelectInst(Instruction):
    __slots__ = ()

class   ShuffleVectorInst(Instruction):
    __slots__ = ()

class AnyMemAccessInst(Value):
    __slots__ = ()

    if (3, 1) <= _version:
        def GetVolatile(self):
            return bool(_core.GetVolatile(self._raw))

        def SetVolatile(self, vol):
            _core.SetVolatile(self._raw, vol)

class   StoreInst(Instruction, AnyMemAccessInst):
    __slots__ = ()

class   TerminatorInst(Instruction):
    __slots__ = ()

class    BranchInst(TerminatorInst):
    __slots__ = ()

class    IndirectBrInst(TerminatorInst):
    __slots__ = ()

    def AddDestination(self, dest):
        _core.AddDestination(self._raw, dest._raw_bb)

class    InvokeInst(TerminatorInst, AnyCallOrInvoke):
    __init__ = untested(lambda *args: None)
    __slots__ = ()

class    ReturnInst(TerminatorInst):
    __slots__ = ()

class    SwitchInst(TerminatorInst):
    __slots__ = ()

    def GetSwitchDefaultDest(self):
        return Value(_core.BasicBlockAsValue(_core.GetSwitchDefaultDest(self._raw)), self._context)

    def AddCase(self, onval, dest):
        _core.AddCase(self._raw, onval._raw, dest._raw_bb)

class    UnreachableInst(TerminatorInst):
    __slots__ = ()

class    ResumeInst(TerminatorInst):
    __init__ = untested(lambda *args: None)
    __slots__ = ()

class   UnaryInstruction(Instruction):
    __slots__ = ()

class    AllocaInst(UnaryInstruction):
    __slots__ = ()

class    CastInst(UnaryInstruction):
    __slots__ = ()

class     BitCastInst(CastInst):
    __slots__ = ()

class     FPExtInst(CastInst):
    __slots__ = ()

class     FPToSIInst(CastInst):
    __slots__ = ()

class     FPToUIInst(CastInst):
    __slots__ = ()

class     FPTruncInst(CastInst):
    __slots__ = ()

class     IntToPtrInst(CastInst):
    __slots__ = ()

class     PtrToIntInst(CastInst):
    __slots__ = ()

class     SExtInst(CastInst):
    __slots__ = ()

class     SIToFPInst(CastInst):
    __slots__ = ()

class     TruncInst(CastInst):
    __slots__ = ()

class     UIToFPInst(CastInst):
    __slots__ = ()

class     ZExtInst(CastInst):
    __slots__ = ()

class    ExtractValueInst(UnaryInstruction):
    __slots__ = ()

class    LoadInst(UnaryInstruction, AnyMemAccessInst):
    __slots__ = ()

class    VAArgInst(UnaryInstruction):
    __init__ = untested(lambda *args: None)
    __slots__ = ()



class Use(object):
    ''' Is it even worth exposing this in the public API?
        A mere iterable-of-values might suffice ...
    '''
    __slots__ = ('_raw', '_context')

    def __new__(cls, raw, context):
        assert isinstance(raw, _core.Use)
        assert isinstance(context, Context)
        assert cls == Use
        if not raw:
            return None
        # No cache implemented ...
        self = object.__new__(Use)
        self._raw = raw
        self._context = context
        return self

    def GetNextUse(self):
        ''' Obtain the next use of a value.

            This effectively advances the iterator. It returns NULL if
            you are on the final use and no more are available.
        '''
        return Use(_core.GetNextUse(self._raw), self._context)

    def GetUser(self):
        ''' Obtain the user value for a user.
        '''
        return Value(_core.GetUser(self._raw), self._context)

    def GetUsedValue(self):
        ''' Obtain the value this use corresponds to.
        '''
        return Value(_core.GetUsedValue(self._raw), self._context)


def ConstVector(values):
    ''' Create a ConstantVector from values.
    '''
    n = len(values)
    assert n
    raw_values = (_core.Value * n)(*[i._raw for i in values])
    return Value(_core.ConstVector(raw_values, n), values[0]._context)

class IRBuilder(object):
    __slots__ = ('_raw', '_context')

    def __init__(self, context):
        self._raw = _core.CreateBuilderInContext(context._raw)
        self._context = context

    def __del__(self):
        _core.DisposeBuilder(self._raw)

    @untested
    def PositionBuilder(self, block, instr):
        _core.PositionBuilder(self._raw, block._raw_bb, instr._raw)

    @untested
    def PositionBuilderBefore(self, instr):
        _core.PositionBuilderBefore(self._raw, instr._raw)

    def PositionBuilderAtEnd(self, block):
        _core.PositionBuilderAtEnd(self._raw, block._raw_bb)

    def GetInsertBlock(self):
        return Value(_core.BasicBlockAsValue(_core.GetInsertBlock(self._raw)), self._context)

    def ClearInsertionPosition(self):
        _core.ClearInsertionPosition(self._raw)

    @untested
    def InsertIntoBuilder(self, instr, name=None):
        if name is None:
            _core.InsertIntoBuilder(self._raw, instr._raw)
        else:
            _core.InsertIntoBuilderWithName(self._raw, instr._raw, u2b(name))

    # Metadata
    @untested
    def SetCurrentDebugLocation(self, l):
        _core.SetCurrentDebugLocation(self._raw, l._raw)

    @untested
    def GetCurrentDebugLocation(self):
        return Value(_core.GetCurrentDebugLocation(self._raw), self._context)

    @untested
    def SetInstDebugLocation(self, inst):
        _core.SetInstDebugLocation(self._raw, inst._raw)

    # Terminators
    def BuildRetVoid(self):
        return Value(_core.BuildRetVoid(self._raw), self._context)

    def BuildRet(self, v):
        return Value(_core.BuildRet(self._raw, v._raw), self._context)

    def BuildAggregateRet(self, values):
        n = len(values)
        raw_values = (_core.Value * n)(*[i._raw for i in values])
        return Value(_core.BuildAggregateRet(self._raw, raw_values, n), self._context)

    def BuildBr(self, dest):
        return Value(_core.BuildBr(self._raw, dest._raw_bb), self._context)

    def BuildCondBr(self, if_, then, else_):
        return Value(_core.BuildCondBr(self._raw, if_._raw, then._raw_bb, else_._raw_bb), self._context)

    def BuildSwitch(self, v, else_, n):
        return Value(_core.BuildSwitch(self._raw, v._raw, else_._raw_bb, n), self._context)

    def BuildIndirectBr(self, addr, n):
        return Value(_core.BuildIndirectBr(self._raw, addr._raw, n), self._context)

    @untested
    def BuildInvoke(self, fn, args, then, catch, name):
        n = len(args)
        raw_args = (_core.Value * n)(*[i._raw for i in args])
        return Value(_core.BuildInvoke(self._raw, fn._raw, raw_args, n, then._raw_bb, catch._raw_bb, u2b(name)), self._context)

    @untested
    def BuildLandingPad(self, ty, persfn, n, name):
        return Value(_core.BuildLandingPad(self._raw, ty._raw, persfn._raw, n, u2b(name)), self._context)

    @untested
    def BuildResume(self, exn):
        return Value(_core.BuildResume(self._raw, exn._raw), self._context)

    def BuildUnreachable(self):
        return Value(_core.BuildUnreachable(self._raw), self._context)

    # Arithmetic
    def BuildAdd(self, lhs, rhs, name=''):
        return Value(_core.BuildAdd(self._raw, lhs._raw, rhs._raw, u2b(name)), self._context)

    def BuildNSWAdd(self, lhs, rhs, name=''):
        return Value(_core.BuildNSWAdd(self._raw, lhs._raw, rhs._raw, u2b(name)), self._context)

    def BuildNUWAdd(self, lhs, rhs, name=''):
        return Value(_core.BuildNUWAdd(self._raw, lhs._raw, rhs._raw, u2b(name)), self._context)

    def BuildFAdd(self, lhs, rhs, name=''):
        return Value(_core.BuildFAdd(self._raw, lhs._raw, rhs._raw, u2b(name)), self._context)

    def BuildSub(self, lhs, rhs, name=''):
        return Value(_core.BuildSub(self._raw, lhs._raw, rhs._raw, u2b(name)), self._context)

    def BuildNSWSub(self, lhs, rhs, name=''):
        return Value(_core.BuildNSWSub(self._raw, lhs._raw, rhs._raw, u2b(name)), self._context)

    def BuildNUWSub(self, lhs, rhs, name=''):
        return Value(_core.BuildNUWSub(self._raw, lhs._raw, rhs._raw, u2b(name)), self._context)

    def BuildFSub(self, lhs, rhs, name=''):
        return Value(_core.BuildFSub(self._raw, lhs._raw, rhs._raw, u2b(name)), self._context)

    def BuildMul(self, lhs, rhs, name=''):
        return Value(_core.BuildMul(self._raw, lhs._raw, rhs._raw, u2b(name)), self._context)

    def BuildNSWMul(self, lhs, rhs, name=''):
        return Value(_core.BuildNSWMul(self._raw, lhs._raw, rhs._raw, u2b(name)), self._context)

    def BuildNUWMul(self, lhs, rhs, name=''):
        return Value(_core.BuildNUWMul(self._raw, lhs._raw, rhs._raw, u2b(name)), self._context)

    def BuildFMul(self, lhs, rhs, name=''):
        return Value(_core.BuildFMul(self._raw, lhs._raw, rhs._raw, u2b(name)), self._context)

    def BuildUDiv(self, lhs, rhs, name=''):
        return Value(_core.BuildUDiv(self._raw, lhs._raw, rhs._raw, u2b(name)), self._context)

    def BuildSDiv(self, lhs, rhs, name=''):
        return Value(_core.BuildSDiv(self._raw, lhs._raw, rhs._raw, u2b(name)), self._context)

    def BuildExactSDiv(self, lhs, rhs, name=''):
        return Value(_core.BuildExactSDiv(self._raw, lhs._raw, rhs._raw, u2b(name)), self._context)

    def BuildFDiv(self, lhs, rhs, name=''):
        return Value(_core.BuildFDiv(self._raw, lhs._raw, rhs._raw, u2b(name)), self._context)

    def BuildURem(self, lhs, rhs, name=''):
        return Value(_core.BuildURem(self._raw, lhs._raw, rhs._raw, u2b(name)), self._context)

    def BuildSRem(self, lhs, rhs, name=''):
        return Value(_core.BuildSRem(self._raw, lhs._raw, rhs._raw, u2b(name)), self._context)

    def BuildFRem(self, lhs, rhs, name=''):
        return Value(_core.BuildFRem(self._raw, lhs._raw, rhs._raw, u2b(name)), self._context)

    def BuildShl(self, lhs, rhs, name=''):
        return Value(_core.BuildShl(self._raw, lhs._raw, rhs._raw, u2b(name)), self._context)

    def BuildLShr(self, lhs, rhs, name=''):
        return Value(_core.BuildLShr(self._raw, lhs._raw, rhs._raw, u2b(name)), self._context)

    def BuildAShr(self, lhs, rhs, name=''):
        return Value(_core.BuildAShr(self._raw, lhs._raw, rhs._raw, u2b(name)), self._context)

    def BuildAnd(self, lhs, rhs, name=''):
        return Value(_core.BuildAnd(self._raw, lhs._raw, rhs._raw, u2b(name)), self._context)

    def BuildOr(self, lhs, rhs, name=''):
        return Value(_core.BuildOr(self._raw, lhs._raw, rhs._raw, u2b(name)), self._context)

    def BuildXor(self, lhs, rhs, name=''):
        return Value(_core.BuildXor(self._raw, lhs._raw, rhs._raw, u2b(name)), self._context)

    @deprecated
    @untested
    def BuildBinOp(self, op, lhs, rhs, name):
        return Value(_core.BuildBinOp(self._raw, op, lhs._raw, rhs._raw, u2b(name)), self._context)

    def BuildNeg(self, rhs, name=''):
        return Value(_core.BuildNeg(self._raw, rhs._raw, u2b(name)), self._context)

    def BuildNSWNeg(self, rhs, name=''):
        return Value(_core.BuildNSWNeg(self._raw, rhs._raw, u2b(name)), self._context)

    def BuildNUWNeg(self, rhs, name=''):
        return Value(_core.BuildNUWNeg(self._raw, rhs._raw, u2b(name)), self._context)

    def BuildFNeg(self, rhs, name=''):
        return Value(_core.BuildFNeg(self._raw, rhs._raw, u2b(name)), self._context)

    def BuildNot(self, rhs, name=''):
        return Value(_core.BuildNot(self._raw, rhs._raw, u2b(name)), self._context)

    # Memory
    @dangerous # declares malloc() with wrong prototype
    @untested
    def BuildMalloc(self, ty, name):
        return Value(_core.BuildMalloc(self._raw, ty._raw, u2b(name)), self._context)

    @dangerous # as BuildMalloc
    @untested
    def BuildArrayMalloc(self, ty, val, name):
        return Value(_core.BuildArrayMalloc(self._raw, ty._raw, val._raw, u2b(name)), self._context)

    def BuildAlloca(self, ty, name=''):
        return Value(_core.BuildAlloca(self._raw, ty._raw, u2b(name)), self._context)

    def BuildArrayAlloca(self, ty, val, name=''):
        return Value(_core.BuildArrayAlloca(self._raw, ty._raw, val._raw, u2b(name)), self._context)

    @dangerous # not really, just for symmetry with BuildMalloc
    @untested
    def BuildFree(self, ptr):
        return Value(_core.BuildFree(self._raw, ptr._raw), self._context)

    def BuildLoad(self, ptr, name=''):
        return Value(_core.BuildLoad(self._raw, ptr._raw, u2b(name)), self._context)

    def BuildStore(self, val, ptr):
        return Value(_core.BuildStore(self._raw, val._raw, ptr._raw), self._context)

    def BuildGEP(self, ptr, indices, name=''):
        n = len(indices)
        raw_indices = (_core.Value * n)(*[i._raw for i in indices])
        return Value(_core.BuildGEP(self._raw, ptr._raw, raw_indices, n, u2b(name)), self._context)

    def BuildInBoundsGEP(self, ptr, indices, name=''):
        n = len(indices)
        raw_indices = (_core.Value * n)(*[i._raw for i in indices])
        return Value(_core.BuildInBoundsGEP(self._raw, ptr._raw, raw_indices, n, u2b(name)), self._context)

    @untested
    def BuildStructGEP(self, ptr, index, name=''):
        return Value(_core.BuildStructGEP(self._raw, ptr._raw, index, u2b(name)), self._context)

    def BuildGlobalString(self, s, name=''):
        return Value(_core.BuildGlobalString(self._raw, u2b(s), u2b(name)), self._context)

    def BuildGlobalStringPtr(self, s, name=''):
        return Value(_core.BuildGlobalStringPtr(self._raw, u2b(s), u2b(name)), self._context)

    # Casts
    def BuildTrunc(self, rhs, ty, name=''):
        return Value(_core.BuildTrunc(self._raw, rhs._raw, ty._raw, u2b(name)), self._context)

    def BuildZExt(self, rhs, ty, name=''):
        return Value(_core.BuildZExt(self._raw, rhs._raw, ty._raw, u2b(name)), self._context)

    def BuildSExt(self, rhs, ty, name=''):
        return Value(_core.BuildSExt(self._raw, rhs._raw, ty._raw, u2b(name)), self._context)

    def BuildFPToUI(self, rhs, ty, name=''):
        return Value(_core.BuildFPToUI(self._raw, rhs._raw, ty._raw, u2b(name)), self._context)

    def BuildFPToSI(self, rhs, ty, name=''):
        return Value(_core.BuildFPToSI(self._raw, rhs._raw, ty._raw, u2b(name)), self._context)

    def BuildUIToFP(self, rhs, ty, name=''):
        return Value(_core.BuildUIToFP(self._raw, rhs._raw, ty._raw, u2b(name)), self._context)

    def BuildSIToFP(self, rhs, ty, name=''):
        return Value(_core.BuildSIToFP(self._raw, rhs._raw, ty._raw, u2b(name)), self._context)

    def BuildFPTrunc(self, rhs, ty, name=''):
        return Value(_core.BuildFPTrunc(self._raw, rhs._raw, ty._raw, u2b(name)), self._context)

    def BuildFPExt(self, rhs, ty, name=''):
        return Value(_core.BuildFPExt(self._raw, rhs._raw, ty._raw, u2b(name)), self._context)

    def BuildPtrToInt(self, rhs, ty, name=''):
        return Value(_core.BuildPtrToInt(self._raw, rhs._raw, ty._raw, u2b(name)), self._context)

    def BuildIntToPtr(self, rhs, ty, name=''):
        return Value(_core.BuildIntToPtr(self._raw, rhs._raw, ty._raw, u2b(name)), self._context)

    def BuildBitCast(self, rhs, ty, name=''):
        return Value(_core.BuildBitCast(self._raw, rhs._raw, ty._raw, u2b(name)), self._context)

    @deprecated
    @untested
    def BuildZExtOrBitCast(self, rhs, ty, name):
        return Value(_core.BuildZExtOrBitCast(self._raw, rhs._raw, ty._raw, u2b(name)), self._context)

    @deprecated
    @untested
    def BuildSExtOrBitCast(self, rhs, ty, name):
        return Value(_core.BuildSExtOrBitCast(self._raw, rhs._raw, ty._raw, u2b(name)), self._context)

    @deprecated
    @untested
    def BuildTruncOrBitCast(self, rhs, ty, name):
        return Value(_core.BuildTruncOrBitCast(self._raw, rhs._raw, ty._raw, u2b(name)), self._context)

    @deprecated
    @untested
    def BuildCast(self, op, rhs, ty, name):
        return Value(_core.BuildCast(self._raw, op, rhs._raw, ty._raw, u2b(name)), self._context)

    @deprecated
    @untested
    def BuildPointerCast(self, rhs, ty, name):
        return Value(_core.BuildPointerCast(self._raw, rhs._raw, ty._raw, u2b(name)), self._context)

    @deprecated
    @untested
    def BuildIntCast(self, rhs, ty, name):
        return Value(_core.BuildIntCast(self._raw, rhs._raw, ty._raw, u2b(name)), self._context)

    @deprecated
    @untested
    def BuildFPCast(self, rhs, ty, name):
        return Value(_core.BuildFPCast(self._raw, rhs._raw, ty._raw, u2b(name)), self._context)

    # Comparisons
    def BuildICmp(self, ipred, lhs, rhs, name=''):
        return Value(_core.BuildICmp(self._raw, ipred, lhs._raw, rhs._raw, u2b(name)), self._context)

    def BuildFCmp(self, rpred, lhs, rhs, name=''):
        return Value(_core.BuildFCmp(self._raw, rpred, lhs._raw, rhs._raw, u2b(name)), self._context)

    # Miscellaneous instructions
    def BuildPhi(self, ty, name=''):
        return Value(_core.BuildPhi(self._raw, ty._raw, u2b(name)), self._context)

    def BuildCall(self, fn, args, name=''):
        n = len(args)
        raw_args = (_core.Value * n)(*[i._raw for i in args])
        return Value(_core.BuildCall(self._raw, fn._raw, raw_args, n, u2b(name)), self._context)

    def BuildSelect(self, if_, then, else_, name=''):
        return Value(_core.BuildSelect(self._raw, if_._raw, then._raw, else_._raw, u2b(name)), self._context)

    @untested
    def BuildVAArg(self, lst, ty, name):
        return Value(_core.BuildVAArg(self._raw, lst._raw, ty._raw, u2b(name)), self._context)

    def BuildExtractElement(self, vecval, index, name=''):
        return Value(_core.BuildExtractElement(self._raw, vecval._raw, index._raw, u2b(name)), self._context)

    def BuildInsertElement(self, vecval, eltval, index, name=''):
        return Value(_core.BuildInsertElement(self._raw, vecval._raw, eltval._raw, index._raw, u2b(name)), self._context)

    def BuildShuffleVector(self, v1, v2, mask, name=''):
        return Value(_core.BuildShuffleVector(self._raw, v1._raw, v2._raw, mask._raw, u2b(name)), self._context)

    def BuildExtractValue(self, aggval, index, name=''):
        return Value(_core.BuildExtractValue(self._raw, aggval._raw, index, u2b(name)), self._context)

    def BuildInsertValue(self, aggval, eltval, index, name=''):
        return Value(_core.BuildInsertValue(self._raw, aggval._raw, eltval._raw, index, u2b(name)), self._context)

    def BuildIsNull(self, val, name=''):
        return Value(_core.BuildIsNull(self._raw, val._raw, u2b(name)), self._context)

    def BuildIsNotNull(self, val, name=''):
        return Value(_core.BuildIsNotNull(self._raw, val._raw, u2b(name)), self._context)

    def BuildPtrDiff(self, lhs, rhs, name=''):
        return Value(_core.BuildPtrDiff(self._raw, lhs._raw, rhs._raw, u2b(name)), self._context)

class ModuleProvider(object):
    __slots__ = ('_raw', '_mod')

    @untested
    def __init__(self, mod):
        # Since LLVM 2.7, _raw and _mod are really the same pointer
        # This greatly simplifies the ownership semantics.
        self._raw = _core.CreateModuleProviderForExistingModule(mod._raw)
        self._mod = mod
    # Something like this would have been necessary in LLVM 2.6,
    # (along with removing ownership from the Module),
    # but I'm not supporting anything that old.
    #@untested
    #def __del__(self):
    #    _core.DisposeModuleProvider(self._raw)

def _message_to_string(message):
    ''' Convert an LLVM "message" to a python string, freeing the C version
    '''
    if not message:
        return None
    s = ctypes.cast(message, ctypes.c_char_p).value
    # Don't panic.
    _core.DisposeMessage(message)
    return b2u(s)

class MemoryBuffer(object):
    __slots__ = ('_raw',)

    def __init__(self, filename):
        self._raw = _core.MemoryBuffer()
        error = _c.string_buffer()

        if filename is not None:
            rv = bool(_core.CreateMemoryBufferWithContentsOfFile(u2b(filename), ctypes.byref(self._raw), ctypes.byref(error)))
        else:
            rv = bool(_core.CreateMemoryBufferWithSTDIN(ctypes.byref(self._raw), ctypes.byref(error)))
        error = _message_to_string(error)

        if rv:
            raise OSError(error)

    def __del__(self):
        _core.DisposeMemoryBuffer(self._raw)

class PassRegistry(object):
    __slots__ = ('_raw',)

    @untested
    def __init__(self, raw):
        assert isinstance(raw, _core.PassRegistry)
        self._raw = raw

    @staticmethod
    @untested
    def get_singleton_instance():
        try:
            return PassRegistry.singleton_instance
        except AttributeError:
            pass
        raw = _core.GetGlobalPassRegistry()
        PassRegistry.singleton_instance = PassRegistry(raw)

    @untested
    def InitializeCore(self):
        _initialization.InitializeCore(self._raw)
    @untested
    def InitializeTransformUtils(self):
        _initialization.InitializeTransformUtils(self._raw)

    @untested
    def InitializeScalarOpts(self):
        _initialization.InitializeScalarOpts(self._raw)

    if (3, 3) <= _version:
        @untested
        def InitializeObjCARCOpts(self):
            _initialization.InitializeObjCARCOpts(self._raw)

    if (3, 1) <= _version:
        @untested
        def InitializeVectorization(self):
            _initialization.InitializeVectorization(self._raw)

    @untested
    def InitializeInstCombine(self):
        _initialization.InitializeInstCombine(self._raw)

    @untested
    def InitializeIPO(self):
        _initialization.InitializeIPO(self._raw)

    @untested
    def InitializeInstrumentation(self):
        _initialization.InitializeInstrumentation(self._raw)

    @untested
    def InitializeAnalysis(self):
        _initialization.InitializeAnalysis(self._raw)

    @untested
    def InitializeIPA(self):
        _initialization.InitializeIPA(self._raw)

    @untested
    def InitializeCodeGen(self):
        _initialization.InitializeCodeGen(self._raw)

    @untested
    def InitializeTarget(self):
        _initialization.InitializeTarget(self._raw)


class PassManagerBase(object):
    __slots__ = ('_raw',)

    @untested
    def __init__(self, raw):
        assert isinstance(raw, _core.PassManager)
        self._raw = raw

    @untested
    def __del__(self):
        ''' Frees the memory of a pass pipeline. For function pipelines,
            does not free the module.
        '''
        _core.DisposePassManager(self._raw)

class PassManager(PassManagerBase):
    __slots__ = ()

    @untested
    def __init__(self):
        ''' Constructs a new whole-module pass pipeline.

            This type of pipeline is suitable for link-time optimization
            and whole-module transformations.
        '''
        raw = _core.CreatePassManager()
        PassManagerBase.__init__(self, raw)

    @untested
    def run(self, mod):
        ''' Initializes, executes on the provided module, and finalizes all
            of the passes scheduled in the pass manager.

            Returns 1 if any of the passes modified the module, 0 otherwise.
        '''
        return bool(_core.RunPassManager(self._raw, mod._raw))

class FunctionPassManager(PassManagerBase):
    __slots__ = ()

    @untested
    def __init__(self, mod):
        ''' Constructs a new function-by-function pass pipeline over the
            module.

            It does not take ownership of the module. This type of pipeline
            is suitable for code generation and JIT compilation tasks.
        '''
        raw = _core.CreateFunctionPassManagerForModule(mod._raw)
        PassManagerBase.__init__(self, raw)

    @untested
    def initialize(self):
        ''' Initializes all of the function passes scheduled in the
            function pass manager.

            Returns 1 if any of the passes modified the module, 0 otherwise.
        '''
        return bool(_core.InitializeFunctionPassManager(self._raw))

    @untested
    def run(self, func):
        ''' Executes all of the function passes scheduled in the
            function pass manager on the provided function.

            Returns 1 if any of the passes modified the function,
            false otherwise.
        '''
        return bool(_core.RunFunctionPassManager(self._raw, func._raw))

    @untested
    def finalize(self):
        ''' Finalizes all of the function passes scheduled in in the
            function pass manager.

            Returns 1 if any of the passes modified the module, 0 otherwise.
        '''
        return bool(_core.FinalizeFunctionPassManager(self._raw))
