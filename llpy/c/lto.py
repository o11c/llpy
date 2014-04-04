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

from . import _c

if False:
    _library = _c.Library('libLTO.so')


    if _version <= (3, 3):
        bool = ctypes.c_bool
        LTO_API_VERSION = 4
    if (3, 4) <= _version:
        if False: # TODO check for MSVC ABI (not just windows!)
            bool = ctypes.c_uchar
        else:
            bool = ctypes.c_bool
        LTO_API_VERSION = 5


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

    lto_codegen_model = _c.enum('lto_codegen_model',
        LTO_CODEGEN_PIC_MODEL_STATIC         = 0,
        LTO_CODEGEN_PIC_MODEL_DYNAMIC        = 1,
        LTO_CODEGEN_PIC_MODEL_DYNAMIC_NO_PIC = 2,
    )

    lto_module = _c.opaque('lto_module')
    lto_code_gen = _c.opaque('lto_code_gen')


    lto_get_version = _library.function(ctypes.c_char_p, 'lto_get_version', [])
    lto_get_error_message = _library.function(ctypes.c_char_p, 'lto_get_error_message', [])
    lto_module_is_object_file = _library.function(ctypes.c_bool, 'lto_module_is_object_file', [ctypes.c_char_p])
    lto_module_is_object_file_for_target = _library.function(ctypes.c_bool, 'lto_module_is_object_file_for_target', [ctypes.c_char_p, ctypes.c_char_p])
    lto_module_is_object_file_in_memory = _library.function(ctypes.c_bool, 'lto_module_is_object_file_in_memory', [_c.string_buffer, ctypes.c_size_t])
    lto_module_is_object_file_in_memory_for_target = _library.function(ctypes.c_bool, 'lto_module_is_object_file_in_memory_for_target', [_c.string_buffer, ctypes.c_size_t, ctypes.c_char_p])
    lto_module_create = _library.function(lto_module, 'lto_module_create', [ctypes.c_char_p])
    lto_module_create_from_memory = _library.function(lto_module, 'lto_module_create_from_memory', [_c.string_buffer, ctypes.c_size_t])
    # off_t is not usable
    #lto_module_create_from_fd = _library.function(lto_module, 'lto_module_create_from_fd', [ctypes.c_int, ctypes.c_char_p, ctypes.c_off_t])
    lto_module_dispose = _library.function(None, 'lto_module_dispose', [lto_module])
    lto_module_get_target_triple = _library.function(ctypes.c_char_p, 'lto_module_get_target_triple', [lto_module])
    lto_module_set_target_triple = _library.function(None, 'lto_module_set_target_triple', [lto_module, ctypes.c_char_p])
    lto_module_get_num_symbols = _library.function(ctypes.c_uint, 'lto_module_get_num_symbols', [lto_module])
    lto_module_get_symbol_name = _library.function(ctypes.c_char_p, 'lto_module_get_symbol_name', [lto_module, ctypes.c_uint])
    lto_module_get_symbol_attribute = _library.function(lto_symbol_attributes, 'lto_module_get_symbol_attribute', [lto_module, ctypes.c_uint])

    lto_codegen_create = _library.function(lto_code_gen, 'lto_codegen_create', [])
    lto_codegen_dispose = _library.function(None, 'lto_codegen_dispose', [lto_code_gen])
    lto_codegen_add_module = _library.function(ctypes.c_bool, 'lto_codegen_add_module', [lto_code_gen, lto_module])
    lto_codegen_set_debug_model = _library.function(ctypes.c_bool, 'lto_codegen_set_debug_model', [lto_code_gen, lto_debug_model])
    lto_codegen_set_pic_model = _library.function(ctypes.c_bool, 'lto_codegen_set_pic_model', [lto_code_gen, lto_codegen_model])
    lto_codegen_set_cpu = _library.function(None, 'lto_codegen_set_cpu', [lto_code_gen, ctypes.c_char_p])
    lto_codegen_set_assembler_path = _library.function(None, 'lto_codegen_set_assembler_path', [lto_code_gen, ctypes.c_char_p])
    lto_codegen_set_assembler_args = _library.function(None, 'lto_codegen_set_assembler_args', [lto_code_gen, ctypes.POINTER(ctypes.c_char_p), ctypes.c_int])
    lto_codegen_add_must_preserve_symbol = _library.function(None, 'lto_codegen_add_must_preserve_symbol', [lto_code_gen, ctypes.c_char_p])
    lto_codegen_write_merged_modules = _library.function(ctypes.c_bool, 'lto_codegen_write_merged_modules', [lto_code_gen, ctypes.c_char_p])
    lto_codegen_compile = _library.function(_c.string_buffer, 'lto_codegen_compile', [lto_code_gen, ctypes.POINTER(ctypes.c_size_t)])
    lto_codegen_debug_options = _library.function(None, 'lto_codegen_debug_options', [lto_code_gen, ctypes.c_char_p])

    if (3, 3) <= _version:
        lto_initialize_disassembler = _library.function(None, 'lto_initialize_disassembler', [])
