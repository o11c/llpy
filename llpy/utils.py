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

''' General utility methods used by this LLVM wrapper.
'''

import functools
import warnings

import llpy

def u2b(u):
    ''' Convert a unicode string to bytes, without exception.
    '''
    assert isinstance(u, str)
    return u.encode('utf-8', 'surrogateescape')

def b2u(b):
    ''' Convert a byte string to unicode, without exception.
    '''
    assert isinstance(b, bytes)
    return b.decode('utf-8', 'surrogateescape')

# These things are ugly as decorators,
# and also they don't interoperate well with the unit tests,
# so at present they just return the function
def deprecated(f):
    ''' Decorator to deprecate a function.
    '''
    if not llpy.__deprecate:
        return f

    @functools.wraps(f)
    def inner(*args, **kwargs):
        t = (f.__name__, f.__code__.co_filename, f.__code__.co_firstlineno)
        warnings.warn('%r deprecated at %s:%d' % t)
        return f(*args, **kwargs)
    return inner

def untested(f):
    ''' Decorator to mark a python function as untested.
    '''
    if llpy.__untested:
        return f

    @functools.wraps(f)
    def inner(*args, **kwargs):
        t = (f.__name__, f.__code__.co_filename, f.__code__.co_firstlineno)
        raise UserWarning('%r untested at %s:%d' % t)
        return f(*args, **kwargs) # unreachable
    return inner

def cuntested(f):
    ''' Decorator to mark a C function as untested.
    '''
    if llpy.__cuntested:
        return f

    @functools.wraps(f)
    def inner(*args, **kwargs):
        t = (f.__name__, f._filename, f._lineno)
        raise UserWarning('%r untested at %s:%d' % t)
        return f(*args, **kwargs) # unreachable
    return inner

def dangerous(f):
    ''' Decorator to mark a function as dangerous in Python,
        due to ownership issues.
    '''
    if llpy.__dangerous:
        return f

    @functools.wraps(f)
    def inner(*args, **kwargs):
        t = (f.__name__, f.__code__.co_filename, f.__code__.co_firstlineno)
        raise UserWarning('%r dangerous at %s:%d' % t)
        return f(*args, **kwargs) # unreachable
    return inner

del llpy.check_deprecation
del llpy.allow_untested
del llpy.ignore_danger
