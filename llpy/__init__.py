# Use of these functions is subject to change without notice.
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

def set_library(soname, version):
    global __library_soname, __library_version
    version = tuple(int(x) for x in version.split('.'))
    assert __MIN_LIBRARY_VERSION <= version #<= __MAX_LIBRARY_VERSION
    if version not in __TESTED_LIBRARY_VERSIONS:
        warnings.warn('Untested LLVM library version: %d.%d' % version)
    __library_version = version
    __library_soname = soname

__deprecate = False
__untested = False
__dangerous = False
__unknown_values = False

# There are subtle differences between versions
# I have not yet investigated what is necessary to support more than one.
__library_version = (3, 2)
__library_soname = 'libLLVM-%d.%d.so.1' % __library_version

__MIN_LIBRARY_VERSION = (3, 0)
# __MAX_LIBRARY_VERSION = (3, 3)
__TESTED_LIBRARY_VERSIONS = [
        (3, 0),
        (3, 1),
        (3, 2),
        # (3, 3),
        # (3, 4),
]
