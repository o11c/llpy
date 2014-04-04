# Use of these functions is subject to change without notice.
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

def unknown_values(value):
    global __unknown_values
    __unknown_values = bool(value)

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

set_library_pattern(platforms[sys.platform])

set_llvm_version(os.getenv('LLPY_LLVM_VERSION'))
