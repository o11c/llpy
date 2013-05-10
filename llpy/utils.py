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

def u2b(u):
    ''' Convert a unicode string to bytes, without exception.
    '''
    return bytes(u, 'utf-8', 'surrogateescape')

def b2u(b):
    ''' Convert a byte string to unicode, without exception.
    '''
    return str(b, 'utf-8', 'surrogateescape')
