#!/usr/bin/env python3

from __future__ import unicode_literals

import gc
import os
import tempfile
import unittest

import llpy.core
from llpy.core import _version
import llpy.io

from llpy.compat import TemporaryDirectory
from llpy.utils import u2b, b2u

from .test_core_misc import DumpTestCase


def slurp(filename):
    with open(filename, 'rb') as f:
        return f.read()

class TestIO(DumpTestCase):

    def setUp(self):
        pass

    def tearDown(self):
        gc.collect()

    def test_bc(self):
        ctx = llpy.core.Context()
        mod = llpy.core.Module(ctx, 'TestIO')
        st = llpy.core.StructType(ctx, None, 'Foo')
        stp = llpy.core.PointerType(st)
        st.StructSetBody([stp])
        glo = mod.AddGlobal(st, 'goo')
        glo.SetInitializer(st.ConstNamedStruct([glo]))
        with TemporaryDirectory() as tdn:
            path_file = os.path.join(tdn, 'file')
            path_fd = os.path.join(tdn, 'fd')
            llpy.io.WriteBitcodeToFile(mod, path_file)
            llpy.io.WriteBitcodeToFD(mod, os.open(path_fd, os.O_WRONLY | os.O_CREAT | os.O_EXCL), True)
            assert slurp(path_file) == slurp(path_fd)

            mb = llpy.io.MemoryBuffer(path_file)
        mod2 = llpy.io.ParseBitcode(ctx, mb)
        assert mod2.GetTypeByName('Foo') is st
        glo2 = mod2.GetNamedGlobal('goo')
        assert glo2.GetInitializer().GetOperand(0) is glo2

    if (3, 2) <= _version:
        @unittest.skip('NYI')
        def test_ir(self):
            ctx = llpy.core.Context()
            mod = llpy.core.Module(ctx, 'TestIO')
            st = llpy.core.StructType(ctx, None, 'Foo')
            stp = llpy.core.PointerType(st)
            st.StructSetBody([stp])
            glo = mod.AddGlobal(st, 'goo')
            glo.SetInitializer(st.ConstNamedStruct([glo]))

            with TemporaryDirectory() as tdn:
                path_file = os.path.join(tdn, 'file')
                llpy.io.PrintModuleToFile(mod, path_file)
                txt = b2u(slurp(path_file))
            if (3, 4) <= _version:
                assert txt == mod.PrintToString()
            self.assertDump(mod, txt)

            if (3, 4) <= _version:
                # Parsing is exposed in 3.4, MemoryBuffer from bytes in 3.3.
                mb = llpy.io.MemoryBuffer(path_file, u2b(txt))
                mod2 = llpy.io.ParseIR(ctx, mb)
                assert mod2.GetTypeByName('Foo') is st
                glo2 = mod2.GetNamedGlobal('goo')
                assert glo2.GetInitializer().GetOperand(0) is glo2

    if (3, 3) <= _version:
        def test_mbuf(self):
            stuff = b'abc'
            buf = llpy.io.MemoryBuffer('name', stuff)
            assert buf.Get() == stuff

    @unittest.skip('NYI')
    def test_stdin(self):
        with ReplaceInFD(0) as f:
            f.write('contents')
            mbuf = llpy.io.MemoryBuffer(None)

    def test_error(self):
        with self.assertRaises(OSError):
            llpy.io.MemoryBuffer('/nonexistent/no-such-file')

if __name__ == '__main__':
    unittest.main()
