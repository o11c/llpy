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

''' Useful wrappers of the 'ctypes' module.
'''

import ctypes
import traceback


def c_type_name(ty):
    if ty is None:
        return 'void'
    rv = ty.__name__
    while rv.startswith('LP_'):
        rv = rv[3:]
        rv += '*'
    return rv
def c_func_repr(self):
    return '<%s %s(%s)>' % (c_type_name(self.restype), self.__name__, ', '.join(c_type_name(a) for a in self.argtypes))

class Library(object):
    __slots__ = ('_cdll',)

    def __init__(self, name):
        self._cdll = ctypes.cdll.LoadLibrary(name)

    def __repr__(self):
        return 'Library(%r)' % self._cdll._name

    def variable(self, typ, name):
        return typ.in_dll(self._cdll, name)

    def function(self, rt, name, args):
        fun = getattr(self._cdll, name)
        fun.restype = rt
        fun.argtypes = args
        type(fun).__repr__ = c_func_repr
        fun._filename, fun._lineno, _, _ = traceback.extract_stack(limit=2)[0]
        mod_name = 'llpy' + fun._filename.split('llpy')[-1]
        mod_name = mod_name.split('.')[0]
        mod_name = mod_name.replace('/', '.')
        fun.__module__ = mod_name
        fun.__qualname__ = fun.__name__
        return fun

def opaque(name):
    ''' Create an opaque pointer typedef.
    '''
    class Foo(ctypes.Structure):
        __slots__ = ()
    Foo.__name__ = name
    return ctypes.POINTER(Foo)

def enum(name, **kwargs):
    ety = ctypes.c_int # currently don't have a reason to use c_uint
    class Enum(ctypes.Structure):
        __slots__ = ()
        _fields_ = [('value', ety)]
        _enum_names = {v: k for k, v in kwargs.items()}

        def __hash__(self):
            return hash(self.value)

        def __eq__(self, other):
            return self.value == other.value

        def __ne__(self, other):
            return self.value != other.value

        def __bool__(self):
            return bool(self.value)
        __nonzero__ = __bool__

        def __repr__(self):
            try:
                name = Enum._enum_names[self.value]
            except KeyError:
                if self.value:
                    return '%s(%d)' % (Enum.__name__, self.value)
                else:
                    return '%s()' % (Enum.__name__)
            else:
                return '%s.%s' % (Enum.__name__, name)

    Enum.__name__ = name
    for k,v in kwargs.items():
        setattr(Enum, k, Enum(v))
    return Enum

def bit_enum(name, **kwargs):
    ety = ctypes.c_int
    if 1 << 31 in kwargs.values():
        ety = ctypes.c_uint
    class Enum(ctypes.Structure):
        __slots__ = ()
        _fields_ = [('value', ety)]
        _enum_names = {v: k for k, v in kwargs.items()}

        def __hash__(self):
            return hash(self.value)

        def __eq__(self, other):
            return self.value == other.value

        def __ne__(self, other):
            return self.value != other.value

        def __bool__(self):
            return bool(self.value)
        __nonzero__ = __bool__

        def __or__(self, other):
            return Enum(self.value | other.value)

        def __and__(self, other):
            return Enum(self.value & other.value)

        def __xor__(self, other):
            return Enum(self.value ^ other.value)

        def __invert__(self):
            return Enum(~self.value)

        def __repr__(self):
            value = self.value
            if not value:
                return '%s()' % (Enum.__name__)
            if value < 0:
                return '~(%r)' % (~self)

            names = list()
            fail = 0

            itr = 1
            while value:
                if value & itr:
                    try:
                        name = Enum._enum_names[itr]
                    except KeyError:
                        fail |= itr
                    else:
                        names.append('%s.%s' % (Enum.__name__, name))
                    value &= ~itr
                itr <<= 1

            if fail:
                names.append('%s(0x%X)' % (Enum.__name__, fail))
            return ' | '.join(names)

    Enum.__name__ = name
    for k,v in kwargs.items():
        setattr(Enum, k, Enum(v))

    return Enum

string_buffer = ctypes.POINTER(ctypes.c_char)

def buffer_as_bytes(sb, n):
    return ctypes.cast(sb, ctypes.POINTER(ctypes.c_char * n)).contents.raw

def pointer_value(ptr):
    return ctypes.cast(ctypes.pointer(ptr),
            ctypes.POINTER(ctypes.c_size_t)
            ).contents.value

def pointer_same(a, b):
    return pointer_value(a) == pointer_value(b)
