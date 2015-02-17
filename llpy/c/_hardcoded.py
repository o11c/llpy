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

''' Hard-coded knowledge about LLVM.
'''

VARIABLES = [
        'LLPY_LLVM_VERSION',
        'PATH',
]

TARGETS = [
        'AArch64',
        'Alpha',
        'ARM',
        'Blackfin',
        'CBackend',
        'CellSPU',
        'CppBackend',
        'Hexagon',
        'MBlaze',
        'Mips',
        'MSP430',
        'NVPTX',
        'PowerPC',
        'PTX',
        'R600',
        'Sparc',
        'SystemZ',
        'XCore',
        'X86',
]

VERSIONS = [
        '3.0',
        '3.1',
        '3.2',
        '3.3',
        '3.4',
        '3.5',
]

# key: sys.platform
# value['llvm']: name of the main LLVM shared library, in the standard path
# value['lto']: name of the LTO library, in the llvm libdir.
PLATFORMS = {
        'linux': {
            'llvm': 'libLLVM-{major}.{minor}.so.1',
            'lto': 'libLTO.so',
        }
}
PLATFORMS['linux2'] = PLATFORMS['linux']

# key: `uname -m`, aka os.uname()[-1]
# value: `LLVM_NATIVE_ARCH` from llvm/Config/config.h
MACHINES = {
        'i686': 'X86',
        'x86_64': 'X86',
}
