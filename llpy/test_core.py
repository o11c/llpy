#!/usr/bin/env python3
import gc
import os
import unittest

import llpy.core

class ReplaceOutFD:
    ''' Capture output send to stderr via C functions
    '''
    def __init__(self, fd):
        self.fd = fd
    def __enter__(self):
        self.saved_fd = os.dup(self.fd)
        r, w = os.pipe()
        os.dup2(w, self.fd)
        os.close(w)
        return os.fdopen(r)

    def __exit__(self, type, value, trace):
        os.dup2(self.saved_fd, self.fd)
        os.close(self.saved_fd)
        del self.saved_fd

class TestContext(unittest.TestCase):
    def setUp(self):
        pass
    def test_context(self):
        llpy.core.Context()
    def test_module(self):
        ctx = llpy.core.Context()
        mod = llpy.core.Module('test_module', ctx)
        with ReplaceOutFD(2) as f:
            mod.Dump()
        with f:
            self.assertEqual(f.read(),
'''; ModuleID = 'test_module'
''')
    def test_module2(self):
        self.test_module()
    def setUp(self):
        pass

if __name__ == '__main__':
    unittest.main()
