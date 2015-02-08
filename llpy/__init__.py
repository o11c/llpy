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
import os
import sys
import warnings


def check_deprecation(value):
    global __deprecate
    __deprecate = bool(value)

def allow_untested(value):
    global __untested
    __untested = bool(value)

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

def set_library_pattern(fmt):
    global __library_pattern
    assert len(fmt.replace('%%', '').split('%d')) == 3
    __library_pattern = fmt

def set_llvm_version(version):
    global __library_version
    if version is not None:
        version = tuple(int(x) for x in version.split('.'))
        assert __MIN_LLVM_VERSION <= version #<= __MAX_LLVM_VERSION

        if version not in __TESTED_LLVM_VERSIONS:
            warnings.warn('Untested LLVM library version: %d.%d' % version)
    __library_version = version

__deprecate = False
__untested = False
__dangerous = False
__unknown_values = False

__native_fallback_all = True
__allow_unknown_machines = False

__MIN_LLVM_VERSION = (3, 0)
# __MAX_LLVM_VERSION = (3, 3)
__TESTED_LLVM_VERSIONS = [
        (3, 0),
        (3, 1),
        (3, 2),
        (3, 3),
        (3, 4),
        # (3, 5),
]

# Note: if adding windows support, also need to fix TODO in llpy/c/lto.py
platforms = {
    'linux': 'libLLVM-%d.%d.so.1',
}
platforms['linux2'] = platforms['linux'] # python 3.2 and earlier
# TODO LTO: '/usr/lib/llvm-%d.%d/lib/libLTO.so'

# key is `uname -m` and value is `LLVM_NATIVE_ARCH` from llvm/Config/config.h
# If allow_unknown_machines() is enabled, will fall back to "all arches".
machines = {
    'i686': 'X86',
    'x86_64': 'X86',
}

set_library_pattern(platforms[sys.platform])

set_llvm_version(os.getenv('LLPY_LLVM_VERSION'))
