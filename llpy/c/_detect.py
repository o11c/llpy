#   -*- encoding: utf-8 -*-
#   Copyright © 2015 Ben Longbons
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

from __future__ import unicode_literals

''' Figure out what versions of LLVM are installed on the system,
    and load the best one.
'''

import os
import subprocess
import sys
import warnings

import llpy
from ..compat import unicode
from ..utils import b2u
from . import _c, _hardcoded

for var in _hardcoded.VARIABLES:
    val = os.getenv(var)
    if val is not None:
        val = unicode(val)
    globals()[var] = val
del var, val

def f(llvm, lto):
    global llvm_pattern, lto_pattern
    llvm_pattern = llvm
    lto_pattern = lto
f(**_hardcoded.PLATFORMS[sys.platform])
del f
machine_target = _hardcoded.MACHINES[os.uname()[-1]]

class Version(object):
    __slots__ = ('txt', 'tuple2', 'tuple3')

    def __init__(self, vers):
        self.txt = vers
        assert isinstance(vers, unicode)
        try:
            vers = tuple(int(x) for x in vers.split('.'))
        except ValueError as e:
            raise ValueError("%s doesn't look like a version (x.y or x.y.z)" % vers)
        if len(vers) == 2:
            self.tuple2 = vers
            self.tuple3 = vers + (0,)
        elif len(vers) == 3:
            self.tuple2 = vers[:2]
            self.tuple3 = vers
        else:
            raise ValueError('%s as a version should have 2 or 3 components (x.y or x.y.z)')

    def __repr__(self):
        return 'Version(%r)' % self.txt

    def format_dict(self):
        major, minor, patch = self.tuple3
        return {'major': major, 'minor': minor, 'patch': patch}

    def __lt__(self, other):
        return self.tuple2 < other

    def __gt__(self, other):
        return self.tuple2 > other

    def __le__(self, other):
        return self.tuple2 <= other

    def __ge__(self, other):
        return self.tuple2 >= other

class LLVM(object):
    __slots__ = ('version', 'config', 'bindir', 'libdir', 'host')
    __slots__ += ('lib_llvm', 'lib_lto')
    __slots__ += ('llc', 'lli', 'opt', 'link', 'clang', 'gcc', 'cc')

    def __repr__(self):
        return 'LLVM(%s)' % ', '.join('%s=%r' % (k, getattr(self, k)) for k in self.__slots__)

def check(cmds):
    rv = b2u(subprocess.check_output(cmds))
    if rv.endswith('\n'):
        rv = rv[:-1]
    return rv

def if_execs(exe):
    # I thought about checking os.stat.st_mode for both, but that would
    # not be correct with acls and would require an extra 2 syscalls to
    # get the fsuid/fsgid anyway.
    if os.path.exists(exe) and os.access(exe, os.X_OK):
        return exe
    return None

def which(exe):
    if os.path.sep in exe or (os.path.altsep and os.path.altsep in exe):
        exe = os.path.realpath(exe)
        return if_execs(exe)
    for path in PATH.split(os.path.pathsep):
        tmp = if_execs(os.path.join(path, exe))
        if tmp:
            return tmp
    return None

def detect_llvm():
    llvm = LLVM()
    if LLPY_LLVM_VERSION:
        llvm.version = Version(LLPY_LLVM_VERSION)
        config = 'llvm-config-%d.%d' % llvm.version.tuple2
        try:
            check([config, '--version'])
        except OSError:
            llvm.config = None
        else:
            llvm.config = config
    else:
        try:
            v = check(['llvm-config', '--version'])
        except OSError:
            for v in reversed(_hardcoded.VERSIONS):
                try:
                    v = check(['llvm-config-%s' % v, '--version'])
                except OSError:
                    continue
                else:
                    llvm.version = Version(v)
                    llvm.config = 'llvm-config-%d.%d' % llvm.version.tuple2
                    break
            else:
                llvm.version = None
                llvm.config = None
        else:
            llvm.version = Version(v)
            llvm.config = 'llvm-config'

    if llvm.config is not None:
        llvm.bindir = check([llvm.config, '--bindir'])
        llvm.libdir = check([llvm.config, '--libdir'])
        llvm.host = check([llvm.config, '--host-target'])

        targets = set(check([llvm.config, '--targets-built']).split())
        targets -= set(_hardcoded.TARGETS)
        targets = sorted(targets)
        if targets:
            warnings.warn('Unknown targets: %s' % ', '.join(targets))
    else:
        llvm.bindir = None
        llvm.libdir = None
        llvm.host = None

    if llvm.libdir is not None:
        # Arguably this *should* be relative to llvm.libdir, but it doesn't
        # actually work out that way.
        llvm.lib_llvm = _c.Library(llvm_pattern.format(**llvm.version.format_dict()))
        llvm.lib_lto = _c.Library(os.path.join(llvm.libdir, lto_pattern.format(**llvm.version.format_dict())))
    else:
        for v in reversed(_hardcoded.VERSIONS):
            try:
                lib = _c.Library(llvm_pattern.format(**Version(v).format_dict()))
            except OSError:
                continue
            else:
                llvm.lib_llvm = lib
                break
        else:
            raise OSError('Unable to locate LLVM library, bailing out!')
        llvm.lib_lto = None
    if llvm.bindir is not None:
        llvm.llc = if_execs(os.path.join(llvm.bindir, 'llc'))
        llvm.lli = if_execs(os.path.join(llvm.bindir, 'lli'))
        llvm.opt = if_execs(os.path.join(llvm.bindir, 'opt'))
        llvm.link = if_execs(os.path.join(llvm.bindir, 'llvm-link'))
        # no point in llvm-dis or llvm-as ?
        llvm.clang = if_execs(os.path.join(llvm.bindir, 'clang'))
    else:
        llvm.clang = which('clang')
    llvm.gcc = which('gcc')
    if llvm.clang is not None:
        llvm.cc = llvm.clang
    elif llvm.gcc is not None:
        llvm.cc = llvm.gcc
    else:
        llvm.cc = which('cc')

    if llvm.version.txt not in _hardcoded.VERSIONS:
        warnings.warn('Found untested LLVM version %s, not in %s' % (llvm.version.txt, ', '.join(_hardcoded.VERSIONS)))
    if not llvm.config:
        warnings.warn('Unable to find `llvm-config` for version %s' % llvm.version.txt)
    assert llvm.lib_llvm
    if not llvm.lib_lto:
        warnings.warn('Unable to find LTO lib for version %s' % llvm.version.txt)
    if not llvm.llc:
        warnings.warn('Unable to find `llc` for version %s' % llvm.version.txt)
    if not llvm.lli:
        warnings.warn('Unable to find `lli` for version %s' % llvm.version.txt)
    if not llvm.opt:
        warnings.warn('Unable to find `opt` for version %s' % llvm.version.txt)
    if not llvm.link:
        warnings.warn('Unable to find `llvm-link` for version %s' % llvm.version.txt)
    if not llvm.clang:
        warnings.warn('Unable to find `clang` for version %s' % llvm.version.txt)

    return llvm


llvm = detect_llvm()
