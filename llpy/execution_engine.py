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

''' Wrap the C interface to the llvm-c/ExecutionEngine.h
'''

import ctypes

from llpy.utils import u2b, untested
from llpy.c import (
        _c,
        core as _core,
        execution_engine as _engine,
        target as _target,
)
from llpy.core import (
        _message_to_string,
        _version,
        Value,
)
from llpy.target import TargetData


if (3, 3) <= _version:
    from llpy.c.execution_engine import MCJITCompilerOptions


from llpy.c.execution_engine import (
        LinkInJIT,
        LinkInMCJIT,
        LinkInInterpreter,
)

class GenericValue(object):
    __slots__ = ('_raw')

    @untested
    def __init__(self, ty, value):
        assert isinstance(ty, Type)
        if isinstance(value, int):
            self._raw = _engine.CreateGenericValueOfInt(ty._raw, value, value < 0)
        elif isinstance(value, float):
            self._raw = _engine.CreateGenericValueOfFloat(ty._raw, value)
        else:
            raise TypeError('Can only (currently) create GenericValue from int or float')
            # _engine.CreateGenericValueOfPointer takes (void *)

    @untested
    def __del__(self):
        _engine.DisposeGenericValue(self._raw)

    @untested
    def IntWidth(self):
        return _engine.GenericValueIntWidth(self._raw)

    @untested
    def ToInt(self, signed):
        assert isinstance(signed, bool)
        rv = _engine.GenericValueToInt(self._raw, signed)
        if signed and rv >= 2 ** 63:
            rv -= 2 ** 64
        return rv

    if 0:
        @untested
        def ToPointer(self):
            rv = _engine.GenericValueToPointer(self._raw)
            return rv

    @untested
    def ToFloat(self, ty):
        assert isinstance(ty, Type)
        return _engine.GenericValueToFloat(ty._raw, self._raw)

class ExecutionEngine(object):
    __slots__ = ('_raw')

    @untested
    def __del__(self):
        _engine.DisposeExecutionEngine(self._raw)

    @untested
    def __new__(cls, mod):
        assert isinstance(mod, Module)
        assert cls is ExecutionEngine
        error = _c.string_buffer()
        ee = _engine.ExecutionEngine()
        rv = bool(_engine.CreateExecutionEngineForModule(ctypes.byref(ee), mod._raw, ctypes.byref(error)))
        error = _message_to_string(error)
        if rv:
            raise OSError(error)
        self = object.__new__(ExecutionEngine)
        self._raw = ee
        return self

    @staticmethod
    @untested
    def CreateInterpreter(mod):
        assert isinstance(mod, Module)
        error = _c.string_buffer()
        ee = _engine.ExecutionEngine()
        rv = bool(_engine.CreateInterpreterForModule(ctypes.byref(ee), mod._raw, ctypes.byref(error)))
        error = _message_to_string(error)
        if rv:
            raise OSError(error)
        self = object.__new__(ExecutionEngine)
        self._raw = ee
        return self

    @staticmethod
    @untested
    def CreateJITCompiler(mod, opt):
        assert isinstance(mod, Module)
        assert is_int(opt)
        error = _c.string_buffer()
        ee = _engine.ExecutionEngine()
        rv = bool(_engine.CreateJITCompilerForModule(ctypes.byref(ee), mod._raw, opt, ctypes.byref(error)))
        error = _message_to_string(error)
        if rv:
            raise OSError(error)
        self = object.__new__(ExecutionEngine)
        self._raw = ee
        return self

    if (3, 3) <= _version:
        @staticmethod
        @untested
        def CreateMCJITCompiler(mod, mcjit_opt):
            assert isinstance(mod, Module)
            assert isinstance(mcjit_opt, MCJITCompilerOptions)
            error = _c.string_buffer()
            ee = _engine.ExecutionEngine()
            rv = bool(_engine.CreateMCJITCompilerForModule(ctypes.byref(ee), mod._raw, ctypes.byref(mcjit_opt), ctypes.sizeof(mcjit_opt), ctypes.byref(error)))
            error = _message_to_string(error)
            if rv:
                raise OSError(error)
            self = object.__new__(ExecutionEngine)
            self._raw = ee
            return self

    @untested
    def RunStaticConstructors(self):
        _engine.RunStaticConstructors(self._raw)

    @untested
    def RunStaticDestructors(self):
        _engine.RunStaticDestructors(self._raw)

    @untested
    def RunFunctionAsMain(self, func, args, env):
        assert isinstance(func, Function)
        argv = [ctypes.c_char_p(u2b(a)) for a in args]
        argv.append(ctypes.c_char_p())
        envp = [ctypes.c_char_p(u2b('%s=%s' % kv)) for kv in env.items()]
        envp.append(ctypes.c_char_p())
        al = len(argv)
        aat = ctypes.c_char_p * al
        el = len(envp)
        eat = ctypes.c_char_p * el
        return _engine.RunFunctionAsMain(self._raw, func._raw, al, aat(*args), eat(*envp))

    @untested
    def RunFunction(self, func, gvalues):
        assert isinstance(func, Function)
        assert all(isinstance(v, GenericValue) for v in gvalues)
        vl = len(gvalues)
        vals = (_engine.GenericValue * vl)(*[v._raw for v in gvalues])
        rv = _engine.RunFunction(self._raw, func._raw, vl, vals)
        gv = object.__new__(GenericValue)
        gv._raw = rv
        return gv

    @untested
    def FreeMachineCodeForFunction(self, func):
        assert isinstance(func, Function)
        _engine.FreeMachineCodeForFunction(self._raw, func._raw)

    @untested
    def AddModule(self, mod):
        assert isinstance(mod, Module)
        _engine.AddModule(self._raw, mod._raw)

    @untested
    def RemoveModule(self, mod):
        assert isinstance(mod, Module)
        omod = _core.Module() # not useful these days
        error = _c.string_buffer()
        rv = bool(_engine.RemoveModule(self._raw, mod._raw, ctypes.byref(omod), ctypes.byref(error)))
        error = _message_to_string(error)
        if rv:
            # never happens these days
            raise OSError(error)

    @untested
    def FindFunction(self, name):
        oval = _core.Value()
        rv = bool(_engine.FindFunction(self._raw, u2b(name), ctypes.byref(oval)))
        if rv:
            raise OSError()
        return Value(self.ctx, oval)

    @untested
    def RecompileAndRelinkFunction(self, func):
        assert isinstance(func, Function)
        raise NotImplementedError
        rp = _engine.RecompileAndRelinkFunction(self._raw, func._raw)
        return ctypes.cast(func.TypeOf().ctypes_type(), rp)

    @untested
    def GetExecutionEngineTargetData(self):
        raw_td = _engine.GetExecutionEngineTargetData(self._raw)
        return TargetData(_message_to_string(_target.CopyStringRepOfTargetData(raw_td)))

    if 0:
        @untested
        def AddGlobalMapping(self, glob, vp):
            assert isinstance(glob, GlobalValue)
            _engine.AddGlobalMapping(self._raw, glob._raw, vp)

    @untested
    def GetPointerToGlobal(self, glob):
        assert isinstance(glob, GlobalValue)
        raise NotImplementedError
        rp = _engine.GetPointerToGlobal(self._raw, glob._raw)
        return ctypes.cast(glob.TypeOf().ctypes_type(), rp)
