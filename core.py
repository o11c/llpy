''' low-level wrapper of LLVM.

    GPL3+. Some day I'll put the full copyright header here ...
'''

import sys
import weakref

from llpy.utils import u2b, b2u
from llpy.c import core as _core, _c
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
)

#def ConstantFP:
#def Function:
#def FunctionType:

## Not sure what these are for.
#InitializeCore = _library.function(None, 'LLVMInitializeCore', [PassRegistry])
#DisposeMessage = _library.function(None, 'LLVMDisposeMessage', [_c.string_buffer])

class Context:
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

class Module:
    ''' Modules represent the top-level structure in a LLVM program. An LLVM
        module is effectively a translation unit or a collection of
        translation units merged together.
    '''
    __slots__ = ('_raw', '_context')

    def __init__(self, name, context):
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

    def SetTarget(self):
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

    def GetModuleContext(self):
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
        temp_buf = (_core.Value * num)()
        _core.GetNamedMetadataOperands(self._raw, bname, temp_buf)
        return [Value(temp_buf[i], self._context) for i in range(num)]

    def AddNamedMetadataOperand(self, name, val):
        ''' Add an operand to named metadata.
        '''
        bname = u2b(name)
        _core.AddNamedMetadataOperand(self._raw, bname, val._raw)


    def AddFunction(self, name, ftype):
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
    # see class Function for increment/decrement

class Type:
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
    kind_type_map = {}
    __slots__ = ('_raw', '_context')
    def __new__(cls, raw, context):
        ''' Deeply magic wrapper that constructs a Type from a C Type*.

            It will always return the same object as long as it exists,
            which will actually be an instance of a subclass.
        '''
        assert isinstance(raw, _core.Type)
        assert isinstance(context, Context)
        assert cls == Type # subclasses must override it
        raw_ptr = _c.pointer_value(raw)
        if raw_ptr == 0:
            return None
        try:
            return context.type_cache[raw_ptr]
        except KeyError:
            pass
        kind = _core.GetTypeKind(raw)
        self = object.__new__(Type.kind_type_map[kind])
        context.type_cache[raw_ptr] = self
        self._raw = raw
        self._context = context
        return self

    if 0: # make pylint shut up a little
        def __init__(self, raw, context):
            self._raw = raw
            self._context = context
    # no __del__

    def GetTypeKind(self):
        ''' Obtain the enumerated type of a Type instance.

            This is never needed in Python code - use type(self) instead.
        '''
        # no outer wrapping - enum okay
        return _core.GetTypeKind(self._raw)

    def TypeIsSized(self):
        ''' Whether the type has a known size.

            Things that don't have a size are abstract types, labels, and void.
        '''
        return bool(_core.TypeIsSized(self._raw))

    def GetTypeContext(self):
        ''' Obtain the context to which this type instance is associated.
        '''
        return self._context

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

    def GetIntTypeWidth(self):
        return _core.GetIntTypeWidth(self._raw)
Type.kind_type_map[TypeKind.Integer] = IntegerType

class RealType(Type):
    ''' abstract base of all real types
    '''
    __slots__ = ()
    def __new__(cls):
        raise TypeError

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
Type.kind_type_map[TypeKind.Half] = HalfType

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
Type.kind_type_map[TypeKind.Float] = FloatType

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
Type.kind_type_map[TypeKind.Double] = DoubleType

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
Type.kind_type_map[TypeKind.X86_FP80] = X86FP80Type

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
Type.kind_type_map[TypeKind.FP128] = FP128Type

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
Type.kind_type_map[TypeKind.PPC_FP128] = PPCFP128Type

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
        self = Type.__new__(self, raw_ft, rt._context)
        assert type(self) is FunctionType
        return self

    def IsFunctionVarArg(self):
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
Type.kind_type_map[TypeKind.Function] = FunctionType


class StructType(Type):
    __slots__ = ()
    def __new__(cls, context, name, body, packed=False):
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
                _core.StructSetBody(rv, raw_body, num, packed)
        self = Type.__new__(Type, raw_struct, context)
        assert type(self) is StructType
        return self

    def GetStructName(self):
        ''' Obtain the name of a structure.
        '''
        return b2u(_core.GetStructName(self._raw))

    def StructSetBody(self, body, packed=False):
        ''' Set the contents of a structure type.
        '''
        num = len(body)
        raw_body = (_core.Type * num)(*[i._raw for i in body])
        _core.StructSetBody(self._raw, raw_body, num, packed)

    def GetStructElementTypes(self):
        ''' Get the elements within a structure.
        '''
        num = _core.CountStructElementTypes(self._raw)
        temp_buf = (_core.Type * num)()
        _core.GetStructElementTypes(self._raw, temp_buf)
        return [Type(temp_buf[i], self._context) for i in range(num)]

    def IsPackedStruct():
        ''' Determine whether a structure is packed.
        '''
        return bool(_core.IsPackedStruct(self._raw))

    def IsOpaqueStruct():
        ''' Determine whether a structure is opaque.
        '''
        return bool(_core.IsOpaqueStruct(self._raw))
Type.kind_type_map[TypeKind.Struct] = StructType

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

    def GetArrayLength(self):
        ''' Obtain the length of an array type.
        '''
        return _core.GetArrayLength(self._raw)
Type.kind_type_map[TypeKind.Array] = ArrayType

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

    def GetPointerAddressSpace(self):
        ''' Obtain the address space of a pointer type.
        '''
        return _core.GetPointerAddressSpace(self._raw)
Type.kind_type_map[TypeKind.Pointer] = PointerType

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
        self = Type.__new__(cls, raw, elem._context)
        assert type(self) is VectorType
        return self

    def GetVectorSize(self):
        ''' Obtain the number of elements in a vector type.
        '''
        return _core.GetVectorSize(self._raw)
Type.kind_type_map[TypeKind.Vector] = VectorType

class VoidType(Type):
    __slots__ = ()
    def __new__(cls, context):
        ''' Create a void type in a context.
        '''
        assert cls is VoidType
        raw = _core.VoidTypeInContext(context._raw)
        self = Type.__new__(cls, raw, context)
        assert type(self) is VoidType
        return self
Type.kind_type_map[TypeKind.Void] = VoidType

class LabelType(Type):
    __slots__ = ()
    def __new__(cls, context):
        ''' Create a label type in a context.
        '''
        assert cls is LabelType
        raw = _core.LabelTypeInContext(context._raw)
        self = Type.__new__(cls, raw, context)
        assert type(self) is LabelType
        return self
Type.kind_type_map[TypeKind.Label] = LabelType

class X86MMXType(Type):
    __slots__ = ()
    def __new__(cls, context):
        ''' Create a X86 MMX type in a context.
        '''
        assert cls is X86MMXType
        raw = _core.X86MMXTypeInContext(context._raw)
        self = Type.__new__(cls, raw, context)
        assert type(self) is X86MMXType
        return self
Type.kind_type_map[TypeKind.X86_MMX] = X86MMXType

if 1:
    # I'm not sure how to instantiate this in the C API ...
    class MetadataType(Type):
        __slots__ = ()
        def __new__(cls):
            raise NotImplementedError
    Type.kind_type_map[TypeKind.Metadata] = MetadataType


class Value:
    __slots__ = ('_raw', '_context')

    def __new__(cls, raw, context):
        assert isinstance(raw, _core.Value)
        assert isinstance(context, Context)
        assert cls == Value # do not attempt to create a subclass directly.
        raw_ptr = _c.pointer_value(raw)
        if raw_ptr == 0:
            return None
        try:
            return context.value_cache[raw_ptr]
        except KeyError:
            pass
        cls = Value._figure_out(raw)
        self = object.__new__(cls)
        context.value_cache[raw_ptr] = self
        self._raw = raw
        self._context = context
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
                if _core.IsAConstantExpr(value): return ConstantExpr
                if _core.IsAConstantFP(value): return ConstantFP
                if _core.IsAConstantInt(value): return ConstantInt
                if _core.IsAConstantPointerNull(value): return ConstantPointerNull
                if _core.IsAConstantStruct(value): return ConstantStruct
                if _core.IsAConstantVector(value): return ConstantVector
                if _core.IsAGlobalValue(value):
                    if _core.IsAFunction(value): return Function
                    if _core.IsAGlobalAlias(value): return GlobalAlias
                    if _core.IsAGlobalVariable(value): return GlobalVariable
                    print('Uh-oh, unknown GlobalValue subclass.', file=sys.stderr)
                    return GlobalValue
                if _core.IsAUndefValue(value): return UndefValue
                print('Uh-oh, unknown Constant subclass.', file=sys.stderr)
                return Constant
            if _core.IsAInstruction(value):
                if _core.IsABinaryOperator(value): return BinaryOperator
                if _core.IsACallInst(value):
                    if _core.IsAIntrinsicInst(value):
                        if _core.IsADbgInfoIntrinsic(value):
                            if _core.IsADbgDeclareInst(value): return DbgDeclareInst
                            print('Uh-oh, unknown DbgInfoIntrinsic subclass.', file=sys.stderr)
                            return DbgInfoIntrinsic
                        if _core.IsAMemIntrinsic(value):
                            if _core.IsAMemCpyInst(value): return MemCpyInst
                            if _core.IsAMemMoveInst(value): return MemMoveInst
                            if _core.IsAMemSetInst(value): return MemSetInst
                            print('Uh-oh, unknown MemIntrinsic subclass.', file=sys.stderr)
                            return MemIntrinsic
                        print('Uh-oh, unknown IntrinsicInst subclass.', file=sys.stderr)
                        return IntrinsicInst
                    print('Uh-oh, unknown CallInst subclass.', file=sys.stderr)
                    return CallInst
                if _core.IsACmpInst(value):
                    if _core.IsAFCmpInst(value): return FCmpInst
                    if _core.IsAICmpInst(value): return ICmpInst
                    print('Uh-oh, unknown CmpInst subclass.', file=sys.stderr)
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
                    print('Uh-oh, unknown TerminatorInst subclass.', file=sys.stderr)
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
                        print('Uh-oh, unknown CastInst subclass.', file=sys.stderr)
                        return CastInst
                    if _core.IsAExtractValueInst(value): return ExtractValueInst
                    if _core.IsALoadInst(value): return LoadInst
                    if _core.IsAVAArgInst(value): return VAArgInst
                    print('Uh-oh, unknown UnaryInstruction subclass.', file=sys.stderr)
                    return UnaryInstruction
            print('Uh-oh, unknown User subclass.', file=sys.stderr)
            return User
        print('Uh-oh, unknown Value subclass.', file=sys.stderr)
        return Value

    def TypeOf(self):
        return Type(_core.TypeOf(self._raw), self._context)

    def GetValueName(self):
        return b2u(_core.GetValueName(self._raw))

    def SetValueName(self, name):
        _core.SetValueName(self._raw, u2b(name))

    def DumpValue(self):
        _core.DumpValue(self._raw)

    def ReplaceAllUsesWith(self, other):
        _core.ReplaceAllUsesWith(self._raw, other._raw)

    def IsConstant(self):
        return bool(_core.IsConstant(self._raw))

    def IsUndef(self):
        return bool(_core.IsUndef(self._raw))


class Argument(Value):
    __slots__ = ()

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

class InlineAsm(Value):
    __slots__ = ()

class MDNode(Value):
    __slots__ = ()

class MDString(Value):
    __slots__ = ()

class User(Value):
    __slots__ = ()

class  Constant(User):
    __slots__ = ()

class   BlockAddress(Constant):
    __slots__ = ()

class   ConstantAggregateZero(Constant):
    __slots__ = ()

class   ConstantArray(Constant):
    __slots__ = ()

class   ConstantExpr(Constant):
    __slots__ = ()

class   ConstantFP(Constant):
    __slots__ = ()

class   ConstantInt(Constant):
    __slots__ = ()

class   ConstantPointerNull(Constant):
    __slots__ = ()

class   ConstantStruct(Constant):
    __slots__ = ()

class   ConstantVector(Constant):
    __slots__ = ()

class   GlobalValue(Constant):
    __slots__ = ()

class    Function(GlobalValue):
    __slots__ = ()

    def GetNextFunction(self):
        ''' Advance a Function iterator to the next Function.

            Returns None if the iterator was already at the end and
            there are no more functions.
        '''
        return Value(_core.GetNextFunction(self._raw))

    def GetPreviousFunction(self):
        ''' Decrement a Function iterator to the previous Function.

            Returns None if the iterator was already at the beginning
            and there are no previous functions.
        '''
        return Value(_core.GetPreviousFunction(self._raw))

class    GlobalAlias(GlobalValue):
    __slots__ = ()

class    GlobalVariable(GlobalValue):
    __slots__ = ()

class   UndefValue(Constant):
    __slots__ = ()

class  Instruction(User):
    __slots__ = ()

class   BinaryOperator(Instruction):
    __slots__ = ()

class   CallInst(Instruction):
    __slots__ = ()

class    IntrinsicInst(CallInst):
    __slots__ = ()

class     DbgInfoIntrinsic(IntrinsicInst):
    __slots__ = ()

class      DbgDeclareInst(DbgInfoIntrinsic):
    __slots__ = ()

class     MemIntrinsic(IntrinsicInst):
    __slots__ = ()

class      MemCpyInst(MemIntrinsic):
    __slots__ = ()

class      MemMoveInst(MemIntrinsic):
    __slots__ = ()

class      MemSetInst(MemIntrinsic):
    __slots__ = ()

class   CmpInst(Instruction):
    __slots__ = ()

class    FCmpInst(CmpInst):
    __slots__ = ()

class    ICmpInst(CmpInst):
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
    __slots__ = ()

class   PHINode(Instruction):
    __slots__ = ()

class   SelectInst(Instruction):
    __slots__ = ()

class   ShuffleVectorInst(Instruction):
    __slots__ = ()

class   StoreInst(Instruction):
    __slots__ = ()

class   TerminatorInst(Instruction):
    __slots__ = ()

class    BranchInst(TerminatorInst):
    __slots__ = ()

class    IndirectBrInst(TerminatorInst):
    __slots__ = ()

class    InvokeInst(TerminatorInst):
    __slots__ = ()

class    ReturnInst(TerminatorInst):
    __slots__ = ()

class    SwitchInst(TerminatorInst):
    __slots__ = ()

class    UnreachableInst(TerminatorInst):
    __slots__ = ()

class    ResumeInst(TerminatorInst):
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

class    LoadInst(UnaryInstruction):
    __slots__ = ()

class    VAArgInst(UnaryInstruction):
    __slots__ = ()

if 0:
    class IRBuilder:
        __slots__ = ('_raw',)
        def __init__(self, raw):
            assert isinstance(raw, _core.Builder)
            self._raw = raw
    class ModuleProvider:
        __slots__ = ('_raw',)
        def __init__(self, raw):
            assert isinstance(raw, _core.ModuleProvider)
            self._raw = raw
    class MemoryBuffer:
        __slots__ = ('_raw',)
        def __init__(self, raw):
            assert isinstance(raw, _core.MemoryBuffer)
            self._raw = raw
    class PassManager:
        __slots__ = ('_raw',)
        def __init__(self, raw):
            assert isinstance(raw, _core.PassManager)
            self._raw = raw
    class PassRegistry:
        __slots__ = ('_raw',)
        def __init__(self, raw):
            assert isinstance(raw, _core.PassRegistry)
            self._raw = raw
    class Use:
        __slots__ = ('_raw',)
        def __init__(self, raw):
            assert isinstance(raw, _core.Use)
            self._raw = raw




    IsAArgument = _library.function(Value, 'LLVMIsAArgument', [Value])
    IsABasicBlock = _library.function(Value, 'LLVMIsABasicBlock', [Value])
    IsAInlineAsm = _library.function(Value, 'LLVMIsAInlineAsm', [Value])
    IsAMDNode = _library.function(Value, 'LLVMIsAMDNode', [Value])
    IsAMDString = _library.function(Value, 'LLVMIsAMDString', [Value])
    IsAUser = _library.function(Value, 'LLVMIsAUser', [Value])
    IsAConstant = _library.function(Value, 'LLVMIsAConstant', [Value])
    IsABlockAddress = _library.function(Value, 'LLVMIsABlockAddress', [Value])
    IsAConstantAggregateZero = _library.function(Value, 'LLVMIsAConstantAggregateZero', [Value])
    IsAConstantArray = _library.function(Value, 'LLVMIsAConstantArray', [Value])
    IsAConstantExpr = _library.function(Value, 'LLVMIsAConstantExpr', [Value])
    IsAConstantFP = _library.function(Value, 'LLVMIsAConstantFP', [Value])
    IsAConstantInt = _library.function(Value, 'LLVMIsAConstantInt', [Value])
    IsAConstantPointerNull = _library.function(Value, 'LLVMIsAConstantPointerNull', [Value])
    IsAConstantStruct = _library.function(Value, 'LLVMIsAConstantStruct', [Value])
    IsAConstantVector = _library.function(Value, 'LLVMIsAConstantVector', [Value])
    IsAGlobalValue = _library.function(Value, 'LLVMIsAGlobalValue', [Value])
    IsAFunction = _library.function(Value, 'LLVMIsAFunction', [Value])
    IsAGlobalAlias = _library.function(Value, 'LLVMIsAGlobalAlias', [Value])
    IsAGlobalVariable = _library.function(Value, 'LLVMIsAGlobalVariable', [Value])
    IsAUndefValue = _library.function(Value, 'LLVMIsAUndefValue', [Value])
    IsAInstruction = _library.function(Value, 'LLVMIsAInstruction', [Value])
    IsABinaryOperator = _library.function(Value, 'LLVMIsABinaryOperator', [Value])
    IsACallInst = _library.function(Value, 'LLVMIsACallInst', [Value])
    IsAIntrinsicInst = _library.function(Value, 'LLVMIsAIntrinsicInst', [Value])
    IsADbgInfoIntrinsic = _library.function(Value, 'LLVMIsADbgInfoIntrinsic', [Value])
    IsADbgDeclareInst = _library.function(Value, 'LLVMIsADbgDeclareInst', [Value])
    IsAMemIntrinsic = _library.function(Value, 'LLVMIsAMemIntrinsic', [Value])
    IsAMemCpyInst = _library.function(Value, 'LLVMIsAMemCpyInst', [Value])
    IsAMemMoveInst = _library.function(Value, 'LLVMIsAMemMoveInst', [Value])
    IsAMemSetInst = _library.function(Value, 'LLVMIsAMemSetInst', [Value])
    IsACmpInst = _library.function(Value, 'LLVMIsACmpInst', [Value])
    IsAFCmpInst = _library.function(Value, 'LLVMIsAFCmpInst', [Value])
    IsAICmpInst = _library.function(Value, 'LLVMIsAICmpInst', [Value])
    IsAExtractElementInst = _library.function(Value, 'LLVMIsAExtractElementInst', [Value])
    IsAGetElementPtrInst = _library.function(Value, 'LLVMIsAGetElementPtrInst', [Value])
    IsAInsertElementInst = _library.function(Value, 'LLVMIsAInsertElementInst', [Value])
    IsAInsertValueInst = _library.function(Value, 'LLVMIsAInsertValueInst', [Value])
    IsALandingPadInst = _library.function(Value, 'LLVMIsALandingPadInst', [Value])
    IsAPHINode = _library.function(Value, 'LLVMIsAPHINode', [Value])
    IsASelectInst = _library.function(Value, 'LLVMIsASelectInst', [Value])
    IsAShuffleVectorInst = _library.function(Value, 'LLVMIsAShuffleVectorInst', [Value])
    IsAStoreInst = _library.function(Value, 'LLVMIsAStoreInst', [Value])
    IsATerminatorInst = _library.function(Value, 'LLVMIsATerminatorInst', [Value])
    IsABranchInst = _library.function(Value, 'LLVMIsABranchInst', [Value])
    IsAIndirectBrInst = _library.function(Value, 'LLVMIsAIndirectBrInst', [Value])
    IsAInvokeInst = _library.function(Value, 'LLVMIsAInvokeInst', [Value])
    IsAReturnInst = _library.function(Value, 'LLVMIsAReturnInst', [Value])
    IsASwitchInst = _library.function(Value, 'LLVMIsASwitchInst', [Value])
    IsAUnreachableInst = _library.function(Value, 'LLVMIsAUnreachableInst', [Value])
    IsAResumeInst = _library.function(Value, 'LLVMIsAResumeInst', [Value])
    IsAUnaryInstruction = _library.function(Value, 'LLVMIsAUnaryInstruction', [Value])
    IsAAllocaInst = _library.function(Value, 'LLVMIsAAllocaInst', [Value])
    IsACastInst = _library.function(Value, 'LLVMIsACastInst', [Value])
    IsABitCastInst = _library.function(Value, 'LLVMIsABitCastInst', [Value])
    IsAFPExtInst = _library.function(Value, 'LLVMIsAFPExtInst', [Value])
    IsAFPToSIInst = _library.function(Value, 'LLVMIsAFPToSIInst', [Value])
    IsAFPToUIInst = _library.function(Value, 'LLVMIsAFPToUIInst', [Value])
    IsAFPTruncInst = _library.function(Value, 'LLVMIsAFPTruncInst', [Value])
    IsAIntToPtrInst = _library.function(Value, 'LLVMIsAIntToPtrInst', [Value])
    IsAPtrToIntInst = _library.function(Value, 'LLVMIsAPtrToIntInst', [Value])
    IsASExtInst = _library.function(Value, 'LLVMIsASExtInst', [Value])
    IsASIToFPInst = _library.function(Value, 'LLVMIsASIToFPInst', [Value])
    IsATruncInst = _library.function(Value, 'LLVMIsATruncInst', [Value])
    IsAUIToFPInst = _library.function(Value, 'LLVMIsAUIToFPInst', [Value])
    IsAZExtInst = _library.function(Value, 'LLVMIsAZExtInst', [Value])
    IsAExtractValueInst = _library.function(Value, 'LLVMIsAExtractValueInst', [Value])
    IsALoadInst = _library.function(Value, 'LLVMIsALoadInst', [Value])
    IsAVAArgInst = _library.function(Value, 'LLVMIsAVAArgInst', [Value])


    GetFirstUse = _library.function(Use, 'LLVMGetFirstUse', [Value])
    GetNextUse = _library.function(Use, 'LLVMGetNextUse', [Use])
    GetUser = _library.function(Value, 'LLVMGetUser', [Use])
    GetUsedValue = _library.function(Value, 'LLVMGetUsedValue', [Use])


    GetOperand = _library.function(Value, 'LLVMGetOperand', [Value, ctypes.c_uint])
    SetOperand = _library.function(None, 'LLVMSetOperand', [Value, ctypes.c_uint, Value])
    GetNumOperands = _library.function(ctypes.c_int, 'LLVMGetNumOperands', [Value])


    ConstNull = _library.function(Value, 'LLVMConstNull', [Type])
    ConstAllOnes = _library.function(Value, 'LLVMConstAllOnes', [Type])
    GetUndef = _library.function(Value, 'LLVMGetUndef', [Type])
    IsNull = _library.function(Bool, 'LLVMIsNull', [Value])
    ConstPointerNull = _library.function(Value, 'LLVMConstPointerNull', [Type])

    ConstInt = _library.function(Value, 'LLVMConstInt', [Type, ctypes.c_ulonglong, Bool])
    ConstIntOfArbitraryPrecision = _library.function(Value, 'LLVMConstIntOfArbitraryPrecision', [Type, ctypes.c_uint, ctypes.POINTER(ctypes.c_uint64)])
    ConstIntOfString = _library.function(Value, 'LLVMConstIntOfString', [Type, ctypes.c_char_p, ctypes.c_uint8])
    ConstIntOfStringAndSize = _library.function(Value, 'LLVMConstIntOfStringAndSize', [Type, ctypes.c_char_p, ctypes.c_uint, ctypes.c_uint8])
    ConstReal = _library.function(Value, 'LLVMConstReal', [Type, ctypes.c_double])
    ConstRealOfString = _library.function(Value, 'LLVMConstRealOfString', [Type, ctypes.c_char_p])
    ConstRealOfStringAndSize = _library.function(Value, 'LLVMConstRealOfStringAndSize', [Type, ctypes.c_char_p, ctypes.c_uint])
    ConstIntGetZExtValue = _library.function(ctypes.c_ulonglong, 'LLVMConstIntGetZExtValue', [Value])
    ConstIntGetSExtValue = _library.function(ctypes.c_longlong, 'LLVMConstIntGetSExtValue', [Value])

    ConstStringInContext = _library.function(Value, 'LLVMConstStringInContext', [Context, ctypes.c_char_p, ctypes.c_uint, Bool])
    ConstString = _library.function(Value, 'LLVMConstString', [ctypes.c_char_p, ctypes.c_uint, Bool])
    ConstStructInContext = _library.function(Value, 'LLVMConstStructInContext', [Context, ctypes.POINTER(Value), ctypes.c_uint, Bool])
    ConstStruct = _library.function(Value, 'LLVMConstStruct', [ctypes.POINTER(Value), ctypes.c_uint, Bool])
    ConstArray = _library.function(Value, 'LLVMConstArray', [Type, ctypes.POINTER(Value), ctypes.c_uint])
    ConstNamedStruct = _library.function(Value, 'LLVMConstNamedStruct', [Type, ctypes.POINTER(Value), ctypes.c_uint])
    ConstVector = _library.function(Value, 'LLVMConstVector', [ctypes.POINTER(Value), ctypes.c_uint])

    GetConstOpcode = _library.function(Opcode, 'LLVMGetConstOpcode', [Value])
    AlignOf = _library.function(Value, 'LLVMAlignOf', [Type])
    SizeOf = _library.function(Value, 'LLVMSizeOf', [Type])
    ConstNeg = _library.function(Value, 'LLVMConstNeg', [Value])
    ConstNSWNeg = _library.function(Value, 'LLVMConstNSWNeg', [Value])
    ConstNUWNeg = _library.function(Value, 'LLVMConstNUWNeg', [Value])
    ConstFNeg = _library.function(Value, 'LLVMConstFNeg', [Value])
    ConstNot = _library.function(Value, 'LLVMConstNot', [Value])
    ConstAdd = _library.function(Value, 'LLVMConstAdd', [Value, Value])
    ConstNSWAdd = _library.function(Value, 'LLVMConstNSWAdd', [Value, Value])
    ConstNUWAdd = _library.function(Value, 'LLVMConstNUWAdd', [Value, Value])
    ConstFAdd = _library.function(Value, 'LLVMConstFAdd', [Value, Value])
    ConstSub = _library.function(Value, 'LLVMConstSub', [Value, Value])
    ConstNSWSub = _library.function(Value, 'LLVMConstNSWSub', [Value, Value])
    ConstNUWSub = _library.function(Value, 'LLVMConstNUWSub', [Value, Value])
    ConstFSub = _library.function(Value, 'LLVMConstFSub', [Value, Value])
    ConstMul = _library.function(Value, 'LLVMConstMul', [Value, Value])
    ConstNSWMul = _library.function(Value, 'LLVMConstNSWMul', [Value, Value])
    ConstNUWMul = _library.function(Value, 'LLVMConstNUWMul', [Value, Value])
    ConstFMul = _library.function(Value, 'LLVMConstFMul', [Value, Value])
    ConstUDiv = _library.function(Value, 'LLVMConstUDiv', [Value, Value])
    ConstSDiv = _library.function(Value, 'LLVMConstSDiv', [Value, Value])
    ConstExactSDiv = _library.function(Value, 'LLVMConstExactSDiv', [Value, Value])
    ConstFDiv = _library.function(Value, 'LLVMConstFDiv', [Value, Value])
    ConstURem = _library.function(Value, 'LLVMConstURem', [Value, Value])
    ConstSRem = _library.function(Value, 'LLVMConstSRem', [Value, Value])
    ConstFRem = _library.function(Value, 'LLVMConstFRem', [Value, Value])
    ConstAnd = _library.function(Value, 'LLVMConstAnd', [Value, Value])
    ConstOr = _library.function(Value, 'LLVMConstOr', [Value, Value])
    ConstXor = _library.function(Value, 'LLVMConstXor', [Value, Value])
    ConstICmp = _library.function(Value, 'LLVMConstICmp', [IntPredicate, Value, Value])
    ConstFCmp = _library.function(Value, 'LLVMConstFCmp', [RealPredicate, Value, Value])
    ConstShl = _library.function(Value, 'LLVMConstShl', [Value, Value])
    ConstLShr = _library.function(Value, 'LLVMConstLShr', [Value, Value])
    ConstAShr = _library.function(Value, 'LLVMConstAShr', [Value, Value])
    ConstGEP = _library.function(Value, 'LLVMConstGEP', [Value, ctypes.POINTER(Value), ctypes.c_uint])
    ConstInBoundsGEP = _library.function(Value, 'LLVMConstInBoundsGEP', [Value, ctypes.POINTER(Value), ctypes.c_uint])
    ConstTrunc = _library.function(Value, 'LLVMConstTrunc', [Value, Type])
    ConstSExt = _library.function(Value, 'LLVMConstSExt', [Value, Type])
    ConstZExt = _library.function(Value, 'LLVMConstZExt', [Value, Type])
    ConstFPTrunc = _library.function(Value, 'LLVMConstFPTrunc', [Value, Type])
    ConstFPExt = _library.function(Value, 'LLVMConstFPExt', [Value, Type])
    ConstUIToFP = _library.function(Value, 'LLVMConstUIToFP', [Value, Type])
    ConstSIToFP = _library.function(Value, 'LLVMConstSIToFP', [Value, Type])
    ConstFPToUI = _library.function(Value, 'LLVMConstFPToUI', [Value, Type])
    ConstFPToSI = _library.function(Value, 'LLVMConstFPToSI', [Value, Type])
    ConstPtrToInt = _library.function(Value, 'LLVMConstPtrToInt', [Value, Type])
    ConstIntToPtr = _library.function(Value, 'LLVMConstIntToPtr', [Value, Type])
    ConstBitCast = _library.function(Value, 'LLVMConstBitCast', [Value, Type])
    ConstZExtOrBitCast = _library.function(Value, 'LLVMConstZExtOrBitCast', [Value, Type])
    ConstSExtOrBitCast = _library.function(Value, 'LLVMConstSExtOrBitCast', [Value, Type])
    ConstTruncOrBitCast = _library.function(Value, 'LLVMConstTruncOrBitCast', [Value, Type])
    ConstPointerCast = _library.function(Value, 'LLVMConstPointerCast', [Value, Type])
    ConstIntCast = _library.function(Value, 'LLVMConstIntCast', [Value, Type, Bool])
    ConstFPCast = _library.function(Value, 'LLVMConstFPCast', [Value, Type])
    ConstSelect = _library.function(Value, 'LLVMConstSelect', [Value, Value, Value])
    ConstExtractElement = _library.function(Value, 'LLVMConstExtractElement', [Value, Value])
    ConstInsertElement = _library.function(Value, 'LLVMConstInsertElement', [Value, Value, Value])
    ConstShuffleVector = _library.function(Value, 'LLVMConstShuffleVector', [Value, Value, Value])
    ConstExtractValue = _library.function(Value, 'LLVMConstExtractValue', [Value, ctypes.POINTER(ctypes.c_uint), ctypes.c_uint])
    ConstInsertValue = _library.function(Value, 'LLVMConstInsertValue', [Value, Value, ctypes.POINTER(ctypes.c_uint), ctypes.c_uint])
    ConstInlineAsm = _library.function(Value, 'LLVMConstInlineAsm', [Type, ctypes.c_char_p, ctypes.c_char_p, Bool, Bool])
    BlockAddress = _library.function(Value, 'LLVMBlockAddress', [Value, BasicBlock])

    GetGlobalParent = _library.function(Module, 'LLVMGetGlobalParent', [Value])
    IsDeclaration = _library.function(Bool, 'LLVMIsDeclaration', [Value])
    GetLinkage = _library.function(Linkage, 'LLVMGetLinkage', [Value])
    SetLinkage = _library.function(None, 'LLVMSetLinkage', [Value, Linkage])
    GetSection = _library.function(ctypes.c_char_p, 'LLVMGetSection', [Value])
    SetSection = _library.function(None, 'LLVMSetSection', [Value, ctypes.c_char_p])
    GetVisibility = _library.function(Visibility, 'LLVMGetVisibility', [Value])
    SetVisibility = _library.function(None, 'LLVMSetVisibility', [Value, Visibility])
    GetAlignment = _library.function(ctypes.c_uint, 'LLVMGetAlignment', [Value])
    SetAlignment = _library.function(None, 'LLVMSetAlignment', [Value, ctypes.c_uint])

    AddGlobal = _library.function(Value, 'LLVMAddGlobal', [Module, Type, ctypes.c_char_p])
    AddGlobalInAddressSpace = _library.function(Value, 'LLVMAddGlobalInAddressSpace', [Module, Type,  ctypes.c_char_p, ctypes.c_uint])
    GetNamedGlobal = _library.function(Value, 'LLVMGetNamedGlobal', [Module, ctypes.c_char_p])
    GetFirstGlobal = _library.function(Value, 'LLVMGetFirstGlobal', [Module])
    GetLastGlobal = _library.function(Value, 'LLVMGetLastGlobal', [Module])
    GetNextGlobal = _library.function(Value, 'LLVMGetNextGlobal', [Value])
    GetPreviousGlobal = _library.function(Value, 'LLVMGetPreviousGlobal', [Value])
    DeleteGlobal = _library.function(None, 'LLVMDeleteGlobal', [Value])
    GetInitializer = _library.function(Value, 'LLVMGetInitializer', [Value])
    SetInitializer = _library.function(None, 'LLVMSetInitializer', [Value, Value])
    IsThreadLocal = _library.function(Bool, 'LLVMIsThreadLocal', [Value])
    SetThreadLocal = _library.function(None, 'LLVMSetThreadLocal', [Value, Bool])
    IsGlobalConstant = _library.function(Bool, 'LLVMIsGlobalConstant', [Value])
    SetGlobalConstant = _library.function(None, 'LLVMSetGlobalConstant', [Value, Bool])

    AddAlias = _library.function(Value, 'LLVMAddAlias', [Module, Type, Value, ctypes.c_char_p])

    DeleteFunction = _library.function(None, 'LLVMDeleteFunction', [Value])
    GetIntrinsicID = _library.function(ctypes.c_uint, 'LLVMGetIntrinsicID', [Value])
    GetFunctionCallConv = _library.function(ctypes.c_uint, 'LLVMGetFunctionCallConv', [Value])
    SetFunctionCallConv = _library.function(None, 'LLVMSetFunctionCallConv', [Value, ctypes.c_uint])
    GetGC = _library.function(ctypes.c_char_p, 'LLVMGetGC', [Value])
    SetGC = _library.function(None, 'LLVMSetGC', [Value, ctypes.c_char_p])
    AddFunctionAttr = _library.function(None, 'LLVMAddFunctionAttr', [Value, Attribute])
    GetFunctionAttr = _library.function(Attribute, 'LLVMGetFunctionAttr', [Value])
    RemoveFunctionAttr = _library.function(None, 'LLVMRemoveFunctionAttr', [Value, Attribute])

    CountParams = _library.function(ctypes.c_uint, 'LLVMCountParams', [Value])
    GetParams = _library.function(None, 'LLVMGetParams', [Value, ctypes.POINTER(Value)])
    GetParam = _library.function(Value, 'LLVMGetParam', [Value, ctypes.c_uint])
    GetParamParent = _library.function(Value, 'LLVMGetParamParent', [Value])
    GetFirstParam = _library.function(Value, 'LLVMGetFirstParam', [Value])
    GetLastParam = _library.function(Value, 'LLVMGetLastParam', [Value])
    GetNextParam = _library.function(Value, 'LLVMGetNextParam', [Value])
    GetPreviousParam = _library.function(Value, 'LLVMGetPreviousParam', [Value])
    AddAttribute = _library.function(None, 'LLVMAddAttribute', [Value, Attribute])
    RemoveAttribute = _library.function(None, 'LLVMRemoveAttribute', [Value, Attribute])
    GetAttribute = _library.function(Attribute, 'LLVMGetAttribute', [Value])
    SetParamAlignment = _library.function(None, 'LLVMSetParamAlignment', [Value, ctypes.c_uint])


    MDStringInContext = _library.function(Value, 'LLVMMDStringInContext', [Context, _c.string_buffer, ctypes.c_uint])
    MDString = _library.function(Value, 'LLVMMDString', [_c.string_buffer, ctypes.c_uint])
    MDNodeInContext = _library.function(Value, 'LLVMMDNodeInContext', [Context, ctypes.POINTER(Value), ctypes.c_uint])
    MDNode = _library.function(Value, 'LLVMMDNode', [ctypes.POINTER(Value), ctypes.c_uint])
    GetMDString = _library.function(_c.string_buffer, 'LLVMGetMDString', [Value, ctypes.POINTER(ctypes.c_uint)])


    BasicBlockAsValue = _library.function(Value, 'LLVMBasicBlockAsValue', [BasicBlock])
    ValueIsBasicBlock = _library.function(Bool, 'LLVMValueIsBasicBlock', [Value])
    ValueAsBasicBlock = _library.function(BasicBlock, 'LLVMValueAsBasicBlock', [Value])
    GetBasicBlockParent = _library.function(Value, 'LLVMGetBasicBlockParent', [BasicBlock])
    GetBasicBlockTerminator = _library.function(Value, 'LLVMGetBasicBlockTerminator', [BasicBlock])
    CountBasicBlocks = _library.function(ctypes.c_uint, 'LLVMCountBasicBlocks', [Value])
    GetBasicBlocks = _library.function(None, 'LLVMGetBasicBlocks', [Value, ctypes.POINTER(BasicBlock)])
    GetFirstBasicBlock = _library.function(BasicBlock, 'LLVMGetFirstBasicBlock', [Value])
    GetLastBasicBlock = _library.function(BasicBlock, 'LLVMGetLastBasicBlock', [Value])
    GetNextBasicBlock = _library.function(BasicBlock, 'LLVMGetNextBasicBlock', [BasicBlock])
    GetPreviousBasicBlock = _library.function(BasicBlock, 'LLVMGetPreviousBasicBlock', [BasicBlock])
    GetEntryBasicBlock = _library.function(BasicBlock, 'LLVMGetEntryBasicBlock', [Value])
    AppendBasicBlockInContext = _library.function(BasicBlock, 'LLVMAppendBasicBlockInContext', [Context, Value, ctypes.c_char_p])
    AppendBasicBlock = _library.function(BasicBlock, 'LLVMAppendBasicBlock', [Value, ctypes.c_char_p])
    InsertBasicBlockInContext = _library.function(BasicBlock, 'LLVMInsertBasicBlockInContext', [Context, BasicBlock, ctypes.c_char_p])
    InsertBasicBlock = _library.function(BasicBlock, 'LLVMInsertBasicBlock', [BasicBlock, ctypes.c_char_p])
    DeleteBasicBlock = _library.function(None, 'LLVMDeleteBasicBlock', [BasicBlock])
    RemoveBasicBlockFromParent = _library.function(None, 'LLVMRemoveBasicBlockFromParent', [BasicBlock])
    MoveBasicBlockBefore = _library.function(None, 'LLVMMoveBasicBlockBefore', [BasicBlock, BasicBlock])
    MoveBasicBlockAfter = _library.function(None, 'LLVMMoveBasicBlockAfter', [BasicBlock, BasicBlock])
    GetFirstInstruction = _library.function(Value, 'LLVMGetFirstInstruction', [BasicBlock])
    GetLastInstruction = _library.function(Value, 'LLVMGetLastInstruction', [BasicBlock])

    HasMetadata = _library.function(ctypes.c_int, 'LLVMHasMetadata', [Value])
    GetMetadata = _library.function(Value, 'LLVMGetMetadata', [Value, ctypes.c_uint])
    SetMetadata = _library.function(None, 'LLVMSetMetadata', [Value, ctypes.c_uint, Value])
    GetInstructionParent = _library.function(BasicBlock, 'LLVMGetInstructionParent', [Value])
    GetNextInstruction = _library.function(Value, 'LLVMGetNextInstruction', [Value])
    GetPreviousInstruction = _library.function(Value, 'LLVMGetPreviousInstruction', [Value])
    InstructionEraseFromParent = _library.function(None, 'LLVMInstructionEraseFromParent', [Value])
    GetInstructionOpcode = _library.function(Opcode, 'LLVMGetInstructionOpcode', [Value])
    GetICmpPredicate = _library.function(IntPredicate, 'LLVMGetICmpPredicate', [Value])

    SetInstructionCallConv = _library.function(None, 'LLVMSetInstructionCallConv', [Value, ctypes.c_uint])
    GetInstructionCallConv = _library.function(ctypes.c_uint, 'LLVMGetInstructionCallConv', [Value])
    AddInstrAttribute = _library.function(None, 'LLVMAddInstrAttribute', [Value, ctypes.c_uint, Attribute])
    RemoveInstrAttribute = _library.function(None, 'LLVMRemoveInstrAttribute', [Value, ctypes.c_uint,  Attribute])
    SetInstrParamAlignment = _library.function(None, 'LLVMSetInstrParamAlignment', [Value, ctypes.c_uint, ctypes.c_uint])
    IsTailCall = _library.function(Bool, 'LLVMIsTailCall', [Value])
    SetTailCall = _library.function(None, 'LLVMSetTailCall', [Value, Bool])

    GetSwitchDefaultDest = _library.function(BasicBlock, 'LLVMGetSwitchDefaultDest', [Value])

    AddIncoming = _library.function(None, 'LLVMAddIncoming', [Value, ctypes.POINTER(Value), ctypes.POINTER(BasicBlock), ctypes.c_uint])
    CountIncoming = _library.function(ctypes.c_uint, 'LLVMCountIncoming', [Value])
    GetIncomingValue = _library.function(Value, 'LLVMGetIncomingValue', [Value, ctypes.c_uint])
    GetIncomingBlock = _library.function(BasicBlock, 'LLVMGetIncomingBlock', [Value, ctypes.c_uint])


    CreateBuilderInContext = _library.function(Builder, 'LLVMCreateBuilderInContext', [Context])
    CreateBuilder = _library.function(Builder, 'LLVMCreateBuilder', [])
    PositionBuilder = _library.function(None, 'LLVMPositionBuilder', [Builder, BasicBlock, Value])
    PositionBuilderBefore = _library.function(None, 'LLVMPositionBuilderBefore', [Builder, Value])
    PositionBuilderAtEnd = _library.function(None, 'LLVMPositionBuilderAtEnd', [Builder, BasicBlock])
    GetInsertBlock = _library.function(BasicBlock, 'LLVMGetInsertBlock', [Builder])
    ClearInsertionPosition = _library.function(None, 'LLVMClearInsertionPosition', [Builder])
    InsertIntoBuilder = _library.function(None, 'LLVMInsertIntoBuilder', [Builder, Value])
    InsertIntoBuilderWithName = _library.function(None, 'LLVMInsertIntoBuilderWithName', [Builder, Value, ctypes.c_char_p])
    DisposeBuilder = _library.function(None, 'LLVMDisposeBuilder', [Builder])

    SetCurrentDebugLocation = _library.function(None, 'LLVMSetCurrentDebugLocation', [Builder, Value])
    GetCurrentDebugLocation = _library.function(Value, 'LLVMGetCurrentDebugLocation', [Builder])
    SetInstDebugLocation = _library.function(None, 'LLVMSetInstDebugLocation', [Builder, Value])

    BuildRetVoid = _library.function(Value, 'LLVMBuildRetVoid', [Builder])
    BuildRet = _library.function(Value, 'LLVMBuildRet', [Builder, Value])
    BuildAggregateRet = _library.function(Value, 'LLVMBuildAggregateRet', [Builder, ctypes.POINTER(Value), ctypes.c_uint])
    BuildBr = _library.function(Value, 'LLVMBuildBr', [Builder, BasicBlock])
    BuildCondBr = _library.function(Value, 'LLVMBuildCondBr', [Builder, Value, BasicBlock, BasicBlock])
    BuildSwitch = _library.function(Value, 'LLVMBuildSwitch', [Builder, Value, BasicBlock, ctypes.c_uint])
    BuildIndirectBr = _library.function(Value, 'LLVMBuildIndirectBr', [Builder, Value, ctypes.c_uint])
    BuildInvoke = _library.function(Value, 'LLVMBuildInvoke', [Builder, Value, ctypes.POINTER(Value), ctypes.c_uint, BasicBlock, BasicBlock, ctypes.c_char_p])
    BuildLandingPad = _library.function(Value, 'LLVMBuildLandingPad', [Builder, Type, Value, ctypes.c_uint, ctypes.c_char_p])
    BuildResume = _library.function(Value, 'LLVMBuildResume', [Builder, Value])
    BuildUnreachable = _library.function(Value, 'LLVMBuildUnreachable', [Builder])
    AddCase = _library.function(None, 'LLVMAddCase', [Value, Value, BasicBlock])
    AddDestination = _library.function(None, 'LLVMAddDestination', [Value, BasicBlock])
    AddClause = _library.function(None, 'LLVMAddClause', [Value, Value])
    SetCleanup = _library.function(None, 'LLVMSetCleanup', [Value, Bool])

    BuildAdd = _library.function(Value, 'LLVMBuildAdd', [Builder, Value, Value, ctypes.c_char_p])
    BuildNSWAdd = _library.function(Value, 'LLVMBuildNSWAdd', [Builder, Value, Value, ctypes.c_char_p])
    BuildNUWAdd = _library.function(Value, 'LLVMBuildNUWAdd', [Builder, Value, Value, ctypes.c_char_p])
    BuildFAdd = _library.function(Value, 'LLVMBuildFAdd', [Builder, Value, Value, ctypes.c_char_p])
    BuildSub = _library.function(Value, 'LLVMBuildSub', [Builder, Value, Value, ctypes.c_char_p])
    BuildNSWSub = _library.function(Value, 'LLVMBuildNSWSub', [Builder, Value, Value, ctypes.c_char_p])
    BuildNUWSub = _library.function(Value, 'LLVMBuildNUWSub', [Builder, Value, Value, ctypes.c_char_p])
    BuildFSub = _library.function(Value, 'LLVMBuildFSub', [Builder, Value, Value, ctypes.c_char_p])
    BuildMul = _library.function(Value, 'LLVMBuildMul', [Builder, Value, Value, ctypes.c_char_p])
    BuildNSWMul = _library.function(Value, 'LLVMBuildNSWMul', [Builder, Value, Value, ctypes.c_char_p])
    BuildNUWMul = _library.function(Value, 'LLVMBuildNUWMul', [Builder, Value, Value, ctypes.c_char_p])
    BuildFMul = _library.function(Value, 'LLVMBuildFMul', [Builder, Value, Value, ctypes.c_char_p])
    BuildUDiv = _library.function(Value, 'LLVMBuildUDiv', [Builder, Value, Value, ctypes.c_char_p])
    BuildSDiv = _library.function(Value, 'LLVMBuildSDiv', [Builder, Value, Value, ctypes.c_char_p])
    BuildExactSDiv = _library.function(Value, 'LLVMBuildExactSDiv', [Builder, Value, Value, ctypes.c_char_p])
    BuildFDiv = _library.function(Value, 'LLVMBuildFDiv', [Builder, Value, Value, ctypes.c_char_p])
    BuildURem = _library.function(Value, 'LLVMBuildURem', [Builder, Value, Value, ctypes.c_char_p])
    BuildSRem = _library.function(Value, 'LLVMBuildSRem', [Builder, Value, Value, ctypes.c_char_p])
    BuildFRem = _library.function(Value, 'LLVMBuildFRem', [Builder, Value, Value, ctypes.c_char_p])
    BuildShl = _library.function(Value, 'LLVMBuildShl', [Builder, Value, Value, ctypes.c_char_p])
    BuildLShr = _library.function(Value, 'LLVMBuildLShr', [Builder, Value, Value, ctypes.c_char_p])
    BuildAShr = _library.function(Value, 'LLVMBuildAShr', [Builder, Value, Value, ctypes.c_char_p])
    BuildAnd = _library.function(Value, 'LLVMBuildAnd', [Builder, Value, Value, ctypes.c_char_p])
    BuildOr = _library.function(Value, 'LLVMBuildOr', [Builder, Value, Value, ctypes.c_char_p])
    BuildXor = _library.function(Value, 'LLVMBuildXor', [Builder, Value, Value, ctypes.c_char_p])
    BuildBinOp = _library.function(Value, 'LLVMBuildBinOp', [Builder, Opcode, Value, Value, ctypes.c_char_p])
    BuildNeg = _library.function(Value, 'LLVMBuildNeg', [Builder, Value, ctypes.c_char_p])
    BuildNSWNeg = _library.function(Value, 'LLVMBuildNSWNeg', [Builder, Value, ctypes.c_char_p])
    BuildNUWNeg = _library.function(Value, 'LLVMBuildNUWNeg', [Builder, Value, ctypes.c_char_p])
    BuildFNeg = _library.function(Value, 'LLVMBuildFNeg', [Builder, Value, ctypes.c_char_p])
    BuildNot = _library.function(Value, 'LLVMBuildNot', [Builder, Value, ctypes.c_char_p])

    BuildMalloc = _library.function(Value, 'LLVMBuildMalloc', [Builder, Type, ctypes.c_char_p])
    BuildArrayMalloc = _library.function(Value, 'LLVMBuildArrayMalloc', [Builder, Type, Value, ctypes.c_char_p])
    BuildAlloca = _library.function(Value, 'LLVMBuildAlloca', [Builder, Type, ctypes.c_char_p])
    BuildArrayAlloca = _library.function(Value, 'LLVMBuildArrayAlloca', [Builder, Type, Value, ctypes.c_char_p])
    BuildFree = _library.function(Value, 'LLVMBuildFree', [Builder, Value])
    BuildLoad = _library.function(Value, 'LLVMBuildLoad', [Builder, Value, ctypes.c_char_p])
    BuildStore = _library.function(Value, 'LLVMBuildStore', [Builder, Value, Value])
    BuildGEP = _library.function(Value, 'LLVMBuildGEP', [Builder, Value, ctypes.POINTER(Value), ctypes.c_uint, ctypes.c_char_p])
    BuildInBoundsGEP = _library.function(Value, 'LLVMBuildInBoundsGEP', [Builder, Value, ctypes.POINTER(Value), ctypes.c_uint, ctypes.c_char_p])
    BuildStructGEP = _library.function(Value, 'LLVMBuildStructGEP', [Builder, Value, ctypes.c_uint, ctypes.c_char_p])
    BuildGlobalString = _library.function(Value, 'LLVMBuildGlobalString', [Builder, ctypes.c_char_p, ctypes.c_char_p])
    BuildGlobalStringPtr = _library.function(Value, 'LLVMBuildGlobalStringPtr', [Builder, ctypes.c_char_p, ctypes.c_char_p])
    GetVolatile = _library.function(Bool, 'LLVMGetVolatile', [Value])
    SetVolatile = _library.function(None, 'LLVMSetVolatile', [Value, Bool])

    BuildTrunc = _library.function(Value, 'LLVMBuildTrunc', [Builder, Value, Type, ctypes.c_char_p])
    BuildZExt = _library.function(Value, 'LLVMBuildZExt', [Builder, Value, Type, ctypes.c_char_p])
    BuildSExt = _library.function(Value, 'LLVMBuildSExt', [Builder, Value, Type, ctypes.c_char_p])
    BuildFPToUI = _library.function(Value, 'LLVMBuildFPToUI', [Builder, Value, Type, ctypes.c_char_p])
    BuildFPToSI = _library.function(Value, 'LLVMBuildFPToSI', [Builder, Value, Type, ctypes.c_char_p])
    BuildUIToFP = _library.function(Value, 'LLVMBuildUIToFP', [Builder, Value, Type, ctypes.c_char_p])
    BuildSIToFP = _library.function(Value, 'LLVMBuildSIToFP', [Builder, Value, Type, ctypes.c_char_p])
    BuildFPTrunc = _library.function(Value, 'LLVMBuildFPTrunc', [Builder, Value, Type, ctypes.c_char_p])
    BuildFPExt = _library.function(Value, 'LLVMBuildFPExt', [Builder, Value, Type, ctypes.c_char_p])
    BuildPtrToInt = _library.function(Value, 'LLVMBuildPtrToInt', [Builder, Value, Type, ctypes.c_char_p])
    BuildIntToPtr = _library.function(Value, 'LLVMBuildIntToPtr', [Builder, Value, Type, ctypes.c_char_p])
    BuildBitCast = _library.function(Value, 'LLVMBuildBitCast', [Builder, Value, Type, ctypes.c_char_p])
    BuildZExtOrBitCast = _library.function(Value, 'LLVMBuildZExtOrBitCast', [Builder, Value, Type, ctypes.c_char_p])
    BuildSExtOrBitCast = _library.function(Value, 'LLVMBuildSExtOrBitCast', [Builder, Value, Type, ctypes.c_char_p])
    BuildTruncOrBitCast = _library.function(Value, 'LLVMBuildTruncOrBitCast', [Builder, Value, Type, ctypes.c_char_p])
    BuildCast = _library.function(Value, 'LLVMBuildCast', [Builder, Opcode, Value, Type, ctypes.c_char_p])
    BuildPointerCast = _library.function(Value, 'LLVMBuildPointerCast', [Builder, Value, Type, ctypes.c_char_p])
    BuildIntCast = _library.function(Value, 'LLVMBuildIntCast', [Builder, Value, Type, ctypes.c_char_p])
    BuildFPCast = _library.function(Value, 'LLVMBuildFPCast', [Builder, Value, Type, ctypes.c_char_p])

    BuildICmp = _library.function(Value, 'LLVMBuildICmp', [Builder, IntPredicate, Value, Value, ctypes.c_char_p])
    BuildFCmp = _library.function(Value, 'LLVMBuildFCmp', [Builder, RealPredicate, Value, Value, ctypes.c_char_p])

    BuildPhi = _library.function(Value, 'LLVMBuildPhi', [Builder, Type, ctypes.c_char_p])
    BuildCall = _library.function(Value, 'LLVMBuildCall', [Builder, Value, ctypes.POINTER(Value), ctypes.c_uint, ctypes.c_char_p])
    BuildSelect = _library.function(Value, 'LLVMBuildSelect', [Builder, Value, Value, Value, ctypes.c_char_p])
    BuildVAArg = _library.function(Value, 'LLVMBuildVAArg', [Builder, Value, Type, ctypes.c_char_p])
    BuildExtractElement = _library.function(Value, 'LLVMBuildExtractElement', [Builder, Value, Value, ctypes.c_char_p])
    BuildInsertElement = _library.function(Value, 'LLVMBuildInsertElement', [Builder, Value, Value, Value, ctypes.c_char_p])
    BuildShuffleVector = _library.function(Value, 'LLVMBuildShuffleVector', [Builder, Value, Value, Value, ctypes.c_char_p])
    BuildExtractValue = _library.function(Value, 'LLVMBuildExtractValue', [Builder, Value, ctypes.c_uint, ctypes.c_char_p])
    BuildInsertValue = _library.function(Value, 'LLVMBuildInsertValue', [Builder, Value, Value, ctypes.c_uint, ctypes.c_char_p])

    BuildIsNull = _library.function(Value, 'LLVMBuildIsNull', [Builder, Value, ctypes.c_char_p])
    BuildIsNotNull = _library.function(Value, 'LLVMBuildIsNotNull', [Builder, Value, ctypes.c_char_p])
    BuildPtrDiff = _library.function(Value, 'LLVMBuildPtrDiff', [Builder, Value, Value, ctypes.c_char_p])


    CreateModuleProviderForExistingModule = _library.function(ModuleProvider, 'LLVMCreateModuleProviderForExistingModule', [Module])
    DisposeModuleProvider = _library.function(None, 'LLVMDisposeModuleProvider', [ModuleProvider])


    CreateMemoryBufferWithContentsOfFile = _library.function(Bool, 'LLVMCreateMemoryBufferWithContentsOfFile', [ctypes.c_char_p, ctypes.POINTER(MemoryBuffer), ctypes.POINTER(_c.string_buffer)])
    CreateMemoryBufferWithSTDIN = _library.function(Bool, 'LLVMCreateMemoryBufferWithSTDIN', [ctypes.POINTER(MemoryBuffer), ctypes.POINTER(_c.string_buffer)])
    DisposeMemoryBuffer = _library.function(None, 'LLVMDisposeMemoryBuffer', [MemoryBuffer])


    GetGlobalPassRegistry = _library.function(PassRegistry, 'LLVMGetGlobalPassRegistry', [])

    CreatePassManager = _library.function(PassManager, 'LLVMCreatePassManager', [])
    CreateFunctionPassManagerForModule = _library.function(PassManager, 'LLVMCreateFunctionPassManagerForModule', [Module])
    CreateFunctionPassManager = _library.function(PassManager, 'LLVMCreateFunctionPassManager', [ModuleProvider])
    RunPassManager = _library.function(Bool, 'LLVMRunPassManager', [PassManager, Module])
    InitializeFunctionPassManager = _library.function(Bool, 'LLVMInitializeFunctionPassManager', [PassManager])
    RunFunctionPassManager = _library.function(Bool, 'LLVMRunFunctionPassManager', [PassManager, Value])
    FinalizeFunctionPassManager = _library.function(Bool, 'LLVMFinalizeFunctionPassManager', [PassManager])
    DisposePassManager = _library.function(None, 'LLVMDisposePassManager', [PassManager])
