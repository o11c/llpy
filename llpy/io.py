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

''' Wrap the C interface to the llvm IO.

    The underlying functions are scattered among many headers.
'''

import ctypes

from llpy.compat import is_int
from llpy.utils import u2b
from llpy.c import (
        _c,
        core as _core,
        bit_reader as _bit_reader,
        bit_writer as _bit_writer,
        ir_reader as _ir_reader,
)
from llpy.core import (
        Context,
        Module,
        _message_to_string,
        _version,
)


class MemoryBuffer(object):
    __slots__ = ('_raw',)

    def __init__(self, filename, body=None):
        if body is not None:
            assert filename is not None
            assert (3, 3) <= _version
            assert isinstance(body, bytes)
            size = len(body)
            filename = u2b(filename)
            self._raw = _core.CreateMemoryBufferWithMemoryRangeCopy(body, size, filename)
            return

        self._raw = _core.MemoryBuffer()
        error = _c.string_buffer()

        if filename is not None:
            rv = bool(_core.CreateMemoryBufferWithContentsOfFile(u2b(filename), ctypes.byref(self._raw), ctypes.byref(error)))
        else:
            rv = bool(_core.CreateMemoryBufferWithSTDIN(ctypes.byref(self._raw), ctypes.byref(error)))
        error = _message_to_string(error)

        if rv:
            raise OSError(error)

    if (3, 3) <= _version:
        def Get(self):
            ptr = _core.GetBufferStart(self._raw)
            size = _core.GetBufferSize(self._raw)
            arr = ctypes.cast(ptr, ctypes.POINTER(ctypes.c_char * size))
            return arr.contents.raw

    def __del__(self):
        _core.DisposeMemoryBuffer(self._raw)


def WriteBitcodeToFile(mod, path):
    ''' Writes a module to the specified path.
    '''
    assert isinstance(mod, Module)
    if _bit_writer.WriteBitcodeToFile(mod._raw, u2b(path)):
        raise OSError

def WriteBitcodeToFD(mod, fd, close, unbuffered=False):
    ''' Writes a module to an open file descriptor.
    '''
    assert isinstance(mod, Module)
    assert is_int(fd)
    assert isinstance(close, bool)
    if _bit_writer.WriteBitcodeToFD(mod._raw, fd, close, unbuffered):
        raise OSError

def ParseBitcode(ctx, mbuf):
    assert isinstance(ctx, Context)
    assert isinstance(mbuf, MemoryBuffer)
    mod = _core.Module()
    error = _c.string_buffer()
    rv = bool(_bit_reader.ParseBitcodeInContext(ctx._raw, mbuf._raw, ctypes.byref(mod), ctypes.byref(error)))
    error = _message_to_string(error)
    if rv:
        raise OSError(error)
    m = Module.__new__(Module)
    m._raw = mod
    m._context = ctx
    return m

# The GetBitcodeModuleProvider function is lazy, but is not really
# usable because it changes ownership (this is not documented!)

if (3, 2) <= _version:
    def PrintModuleToFile(mod, path):
        assert isinstance(mod, Module)
        error = _c.string_buffer()
        rv = _core.PrintModuleToFile(mod._raw, u2b(path), ctypes.byref(error))
        error = _message_to_string(error)
        if rv:
            raise OSError(error)

if (3, 4) <= _version:
    def ParseIR(ctx, mbuf):
        assert isinstance(ctx, Context)
        assert isinstance(mbuf, MemoryBuffer)
        mod = _core.Module()
        error = _c.string_buffer()
        rv = bool(_ir_reader.ParseIRInContext(ctx._raw, mbuf._raw, ctypes.byref(mod), ctypes.byref(error)))
        error = _message_to_string(error)
        if rv:
            raise OSError(error)
        m = Module.__new__(Module)
        m._raw = mod
        m._context = ctx
        return m
