#   -*- encoding: utf-8 -*-
#   Copyright © 2013-2015 Ben Longbons
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

'''
LLPY root package. Most of the interesting stuff is in llpy.core.

Some edge cases in LLPY can be controlled by environment variables or by
calling functions in this module. The functions here can only be used
before the interesting modules are imported.

All use of these functions is subject to change without notice. Once the
proper data is filled in and remaining wrappers and testcases are written,
they will no longer be necessary, except when new LLVM APIs are written.
'''


def check_deprecation(value):
    global __deprecate
    __deprecate = bool(value)

def allow_untested(value):
    global __untested
    __untested = bool(value)

def allow_cuntested(value):
    global __cuntested
    __cuntested = bool(value)

def ignore_danger(value):
    global __dangerous
    __dangerous = bool(value)

# this is the only function that is not deleted during import proper
# (because it is only used at runtime, not import time)
def unknown_values(value):
    global __unknown_values
    __unknown_values = bool(value)

def allow_unknown_machines(value):
    global __allow_unknown_machines
    __allow_unknown_machines = bool(value)

__deprecate = False
__untested = False
__cuntested = False
__dangerous = False
__unknown_values = False

__native_fallback_all = True
__allow_unknown_machines = False
