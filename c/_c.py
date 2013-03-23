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
