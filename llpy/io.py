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

''' Wrap the C interface to the llvm-c/BitReader.h and llvm-c/BitWriter.h
'''

import ctypes

from llpy.utils import u2b
from llpy.c import (
        _c,
        core as _core,
        bit_reader as _bit_reader,
        bit_writer as _bit_writer,
)
from llpy.core import (
        Module,
        _message_to_string
)


def WriteBitcodeToFile(mod, path):
    ''' Writes a module to the specified path.
    '''
    if _bit_writer.WriteBitcodeToFile(mod._raw, u2b(path)):
        raise OSError

def WriteBitcodeToFD(mod, fd, close, unbuffered=False):
    ''' Writes a module to an open file descriptor.
    '''
    if _bit_writer.WriteBitcodeToFD(mod._raw, fd, close, unbuffered):
        raise OSError

def ParseBitcode(ctx, mbuf):
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
