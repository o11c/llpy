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

''' Stuff that has nothing to do with headers.
'''

from . import _c

# Note: this logic is duplicated in lto.py
from llpy import (
        __library_pattern_llvm as __pattern,
        __library_version as _version,
        __TESTED_LLVM_VERSIONS,
        __no_more_version_changes,
)
__no_more_version_changes()
if _version is not None:
    _library = _c.Library(__pattern % _version)
else:
    e = None
    for _version in reversed(__TESTED_LLVM_VERSIONS):
        try:
            _library = _c.Library(__pattern % _version)
        except OSError as e_:
            e = e_
            continue
        else:
            del e
            break
    else:
        raise e
