#   -*- encoding: utf-8 -*-
#   Copyright © 2013-2014 Ben Longbons
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

''' low-level wrapper of llvm-c/lto.h

    Note that this does not necessarily follow the same LLVM version.
'''

import ctypes

from . import _c, _detect

_library = _detect.llvm.lib_lto
_version = _detect.llvm.version

from ..utils import cuntested as untested


if _version <= (3, 3):
    bool = ctypes.c_bool
    LTO_API_VERSION = 4
if (3, 4) <= _version:
    if False: # TODO check for MSVC ABI (not just windows!)
        bool = ctypes.c_uchar
    else:
        bool = ctypes.c_bool
if (3, 4) <= _version <= (3, 4):
    LTO_API_VERSION = 5
if (3, 5) <= _version:
    LTO_API_VERSION = 10


lto_symbol_attributes = _c.enum('lto_symbol_attributes',
    LTO_SYMBOL_ALIGNMENT_MASK              = 0x0000001F,
    LTO_SYMBOL_PERMISSIONS_MASK            = 0x000000E0,
    LTO_SYMBOL_PERMISSIONS_CODE            = 0x000000A0,
    LTO_SYMBOL_PERMISSIONS_DATA            = 0x000000C0,
    LTO_SYMBOL_PERMISSIONS_RODATA          = 0x00000080,
    LTO_SYMBOL_DEFINITION_MASK             = 0x00000700,
    LTO_SYMBOL_DEFINITION_REGULAR          = 0x00000100,
    LTO_SYMBOL_DEFINITION_TENTATIVE        = 0x00000200,
    LTO_SYMBOL_DEFINITION_WEAK             = 0x00000300,
    LTO_SYMBOL_DEFINITION_UNDEFINED        = 0x00000400,
    LTO_SYMBOL_DEFINITION_WEAKUNDEF        = 0x00000500,
    LTO_SYMBOL_SCOPE_MASK                  = 0x00003800,
    LTO_SYMBOL_SCOPE_INTERNAL              = 0x00000800,
    LTO_SYMBOL_SCOPE_HIDDEN                = 0x00001000,
    LTO_SYMBOL_SCOPE_PROTECTED             = 0x00002000,
    LTO_SYMBOL_SCOPE_DEFAULT               = 0x00001800,
    LTO_SYMBOL_SCOPE_DEFAULT_CAN_BE_HIDDEN = 0x00002800,
)

lto_debug_model = _c.enum('lto_debug_model',
    LTO_DEBUG_MODEL_NONE         = 0,
    LTO_DEBUG_MODEL_DWARF        = 1,
)

models = dict(
    LTO_CODEGEN_PIC_MODEL_STATIC         = 0,
    LTO_CODEGEN_PIC_MODEL_DYNAMIC        = 1,
    LTO_CODEGEN_PIC_MODEL_DYNAMIC_NO_PIC = 2,
)
if (3, 5) <= _version:
    models.update(
        LTO_CODEGEN_PIC_MODEL_DEFAULT = 3,
    )
lto_codegen_model = _c.enum('lto_codegen_model',
    **models
)
del models

lto_module = _c.opaque('lto_module')
lto_code_gen = _c.opaque('lto_code_gen')

lto_codegen_diagnostic_severity = _c.enum('lto_codegen_diagnostic_severity',
    LTO_DS_ERROR    = 0,
    LTO_DS_WARNING  = 1,
    LTO_DS_REMARK   = 3,
    LTO_DS_NOTE     = 2,
)
if (3, 5) <= _version:
    lto_diagnostic_handler = ctypes.CFUNCTYPE(None, *[lto_codegen_diagnostic_severity, ctypes.c_char_p, ctypes.c_void_p])


lto_get_version = _library.function(ctypes.c_char_p, 'lto_get_version', [])
lto_get_version = untested(lto_get_version)
lto_get_error_message = _library.function(ctypes.c_char_p, 'lto_get_error_message', [])
lto_get_error_message = untested(lto_get_error_message)
lto_module_is_object_file = _library.function(ctypes.c_bool, 'lto_module_is_object_file', [ctypes.c_char_p])
lto_module_is_object_file = untested(lto_module_is_object_file)
lto_module_is_object_file_for_target = _library.function(ctypes.c_bool, 'lto_module_is_object_file_for_target', [ctypes.c_char_p, ctypes.c_char_p])
lto_module_is_object_file_for_target = untested(lto_module_is_object_file_for_target)
lto_module_is_object_file_in_memory = _library.function(ctypes.c_bool, 'lto_module_is_object_file_in_memory', [_c.string_buffer, ctypes.c_size_t])
lto_module_is_object_file_in_memory = untested(lto_module_is_object_file_in_memory)
lto_module_is_object_file_in_memory_for_target = _library.function(ctypes.c_bool, 'lto_module_is_object_file_in_memory_for_target', [_c.string_buffer, ctypes.c_size_t, ctypes.c_char_p])
lto_module_is_object_file_in_memory_for_target = untested(lto_module_is_object_file_in_memory_for_target)
lto_module_create = _library.function(lto_module, 'lto_module_create', [ctypes.c_char_p])
lto_module_create = untested(lto_module_create)
lto_module_create_from_memory = _library.function(lto_module, 'lto_module_create_from_memory', [_c.string_buffer, ctypes.c_size_t])
lto_module_create_from_memory = untested(lto_module_create_from_memory)
if (3, 5) <= _version:
    lto_module_create_from_memory_with_path = _library.function(lto_module, 'lto_module_create_from_memory_with_path', [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_char_p])
    lto_module_create_from_memory_with_path = untested(lto_module_create_from_memory_with_path)
# off_t is not usable
#lto_module_create_from_fd = _library.function(lto_module, 'lto_module_create_from_fd', [ctypes.c_int, ctypes.c_char_p, ctypes.c_off_t])
lto_module_dispose = _library.function(None, 'lto_module_dispose', [lto_module])
lto_module_dispose = untested(lto_module_dispose)
lto_module_get_target_triple = _library.function(ctypes.c_char_p, 'lto_module_get_target_triple', [lto_module])
lto_module_get_target_triple = untested(lto_module_get_target_triple)
lto_module_set_target_triple = _library.function(None, 'lto_module_set_target_triple', [lto_module, ctypes.c_char_p])
lto_module_set_target_triple = untested(lto_module_set_target_triple)
lto_module_get_num_symbols = _library.function(ctypes.c_uint, 'lto_module_get_num_symbols', [lto_module])
lto_module_get_num_symbols = untested(lto_module_get_num_symbols)
lto_module_get_symbol_name = _library.function(ctypes.c_char_p, 'lto_module_get_symbol_name', [lto_module, ctypes.c_uint])
lto_module_get_symbol_name = untested(lto_module_get_symbol_name)
lto_module_get_symbol_attribute = _library.function(lto_symbol_attributes, 'lto_module_get_symbol_attribute', [lto_module, ctypes.c_uint])
lto_module_get_symbol_attribute = untested(lto_module_get_symbol_attribute)
if (3, 5) <= _version:
    lto_module_get_num_deplibs = _library.function(ctypes.c_uint, 'lto_module_get_num_deplibs', [lto_module])
    lto_module_get_num_deplibs = untested(lto_module_get_num_deplibs)
    lto_module_get_deplib = _library.function(ctypes.c_char_p, 'lto_module_get_deplib', [lto_module, ctypes.c_uint])
    lto_module_get_deplib = untested(lto_module_get_deplib)
    lto_module_get_num_linkeropts = _library.function(ctypes.c_uint, 'lto_module_get_num_linkeropts', [lto_module])
    lto_module_get_num_linkeropts = untested(lto_module_get_num_linkeropts)
    lto_module_get_linkeropt = _library.function(ctypes.c_char_p, 'lto_module_get_linkeropt', [lto_module, ctypes.c_uint])
    lto_module_get_linkeropt = untested(lto_module_get_linkeropt)

    lto_codegen_set_diagnostic_handler = _library.function(None, 'lto_codegen_set_diagnostic_handler', [lto_code_gen, lto_diagnostic_handler, ctypes.c_void_p])
    lto_codegen_set_diagnostic_handler = untested(lto_codegen_set_diagnostic_handler)

lto_codegen_create = _library.function(lto_code_gen, 'lto_codegen_create', [])
lto_codegen_create = untested(lto_codegen_create)
lto_codegen_dispose = _library.function(None, 'lto_codegen_dispose', [lto_code_gen])
lto_codegen_dispose = untested(lto_codegen_dispose)
lto_codegen_add_module = _library.function(ctypes.c_bool, 'lto_codegen_add_module', [lto_code_gen, lto_module])
lto_codegen_add_module = untested(lto_codegen_add_module)
lto_codegen_set_debug_model = _library.function(ctypes.c_bool, 'lto_codegen_set_debug_model', [lto_code_gen, lto_debug_model])
lto_codegen_set_debug_model = untested(lto_codegen_set_debug_model)
lto_codegen_set_pic_model = _library.function(ctypes.c_bool, 'lto_codegen_set_pic_model', [lto_code_gen, lto_codegen_model])
lto_codegen_set_pic_model = untested(lto_codegen_set_pic_model)
lto_codegen_set_cpu = _library.function(None, 'lto_codegen_set_cpu', [lto_code_gen, ctypes.c_char_p])
lto_codegen_set_cpu = untested(lto_codegen_set_cpu)
lto_codegen_set_assembler_path = _library.function(None, 'lto_codegen_set_assembler_path', [lto_code_gen, ctypes.c_char_p])
lto_codegen_set_assembler_path = untested(lto_codegen_set_assembler_path)
lto_codegen_set_assembler_args = _library.function(None, 'lto_codegen_set_assembler_args', [lto_code_gen, ctypes.POINTER(ctypes.c_char_p), ctypes.c_int])
lto_codegen_set_assembler_args = untested(lto_codegen_set_assembler_args)
lto_codegen_add_must_preserve_symbol = _library.function(None, 'lto_codegen_add_must_preserve_symbol', [lto_code_gen, ctypes.c_char_p])
lto_codegen_add_must_preserve_symbol = untested(lto_codegen_add_must_preserve_symbol)
lto_codegen_write_merged_modules = _library.function(ctypes.c_bool, 'lto_codegen_write_merged_modules', [lto_code_gen, ctypes.c_char_p])
lto_codegen_write_merged_modules = untested(lto_codegen_write_merged_modules)
lto_codegen_compile = _library.function(_c.string_buffer, 'lto_codegen_compile', [lto_code_gen, ctypes.POINTER(ctypes.c_size_t)])
lto_codegen_compile = untested(lto_codegen_compile)
lto_codegen_debug_options = _library.function(None, 'lto_codegen_debug_options', [lto_code_gen, ctypes.c_char_p])
lto_codegen_debug_options = untested(lto_codegen_debug_options)

if (3, 3) <= _version:
    lto_initialize_disassembler = _library.function(None, 'lto_initialize_disassembler', [])
    lto_initialize_disassembler = untested(lto_initialize_disassembler)
