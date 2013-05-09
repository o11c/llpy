''' Useful wrappers of the 'ctypes' module.

    GPL3+. Some day I'll put the full copyright header here ...
'''

import ctypes

class Library:
    __slots__ = ('_cdll',)

    def __init__(self, name):
        self._cdll = ctypes.cdll.LoadLibrary(name)

    def variable(self, typ, name):
        return typ.in_dll(self._cdll, name)

    def function(self, rt, name, args):
        fun = getattr(self._cdll, name)
        fun.restype = rt
        fun.argtypes = args
        return fun

def opaque(name):
    ''' Create an opaque pointer typedef.
    '''
    class Foo(ctypes.Structure):
        __slots__ = ()
    Foo.__name__ = name
    return ctypes.POINTER(Foo)

def enum(name, **kwargs):
    class Enum(ctypes.Structure):
        __slots__ = ()
        _fields_ = [('value', ctypes.c_int)]

        def __hash__(self):
            return hash(self.value)

        def __eq__(self, other):
            return self.value == other.value

        def __ne__(self, other):
            return self.value != other.value

        def __bool__(self):
            return self.value

    Enum.__name__ = name
    for k,v in kwargs.items():
        setattr(Enum, k, Enum(v))
    return Enum

def bit_enum(name, **kwargs):
    Enum = enum(name, **kwargs)

    Enum.__or__ = lambda self, other: Enum(self.value | other.value)
    Enum.__and__ = lambda self, other: Enum(self.value & other.value)
    Enum.__xor__ = lambda self, other: Enum(self.value ^ other.value)
    Enum.__invert__ = lambda self: Enum(~self.value)

    return Enum

string_buffer = ctypes.POINTER(ctypes.c_char)

def buffer_as_bytes(sb, n):
    return ctypes.cast(sb, ctypes.POINTER(ctypes.c_char * n)).contents.raw
# for the reverse, the implicit conversion is enough

def pointer_value(ptr):
    return ctypes.cast(ctypes.pointer(ptr),
            ctypes.POINTER(ctypes.c_size_t)
            ).contents.value

def pointer_same(a, b):
    return pointer_value(a) == pointer_value(b)
