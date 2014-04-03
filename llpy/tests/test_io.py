#!/usr/bin/env python3

import os
import tempfile
import unittest

import llpy.core
import llpy.io

def slurp(filename):
    with open(filename, 'rb') as f:
        return f.read()

class TestIO(unittest.TestCase):

    def test_bc(self):
        ctx = llpy.core.Context()
        mod = llpy.core.Module(ctx, 'TestIO')
        st = llpy.core.StructType(ctx, None, 'Foo')
        stp = llpy.core.PointerType(st)
        st.StructSetBody([stp])
        glo = mod.AddGlobal(st, 'goo')
        glo.SetInitializer(st.ConstNamedStruct([glo]))
        with tempfile.TemporaryDirectory() as tdn:
            path_file = os.path.join(tdn, 'file')
            path_fd = os.path.join(tdn, 'fd')
            llpy.io.WriteBitcodeToFile(mod, path_file)
            llpy.io.WriteBitcodeToFD(mod, os.open(path_fd, os.O_WRONLY | os.O_CREAT | os.O_EXCL), True)
            assert slurp(path_file) == slurp(path_fd)

            mb = llpy.core.MemoryBuffer(path_file)
            mod2 = llpy.io.ParseBitcode(ctx, mb)
            assert mod2.GetTypeByName('Foo') is st
            glo2 = mod2.GetNamedGlobal('goo')
            assert glo2.GetInitializer().GetOperand(0) is glo2

    @unittest.skip('NYI')
    def test_stdin(self):
        with ReplaceInFD(0) as f:
            f.write('contents')
            mbuf = llpy.core.MemoryBuffer(None)

    def test_error(self):
        with self.assertRaises(OSError):
            llpy.core.MemoryBuffer('/nonexistent/no-such-file')
