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

''' Wrap the C interface to the llvm Transforms.

    Some classes include functions from headers other than llvm-c/Transforms/*.h
'''

import functools

import llpy
from llpy.utils import u2b, b2u, deprecated, untested, dangerous
from llpy.core import (
        _version,
)
from llpy.c import (
        core as _core,
)
from llpy.c.transforms import (
        ipo as _ipo,
        pass_manager_builder as _pmb,
        scalar as _scalar,
        vectorize as _vectorize,
)


class PassRegistry(object):
    __slots__ = ('_raw',)

    @untested
    def __init__(self, raw):
        assert isinstance(raw, _core.PassRegistry)
        self._raw = raw

    @staticmethod
    @untested
    def get_singleton_instance():
        try:
            return PassRegistry.singleton_instance
        except AttributeError:
            pass
        raw = _core.GetGlobalPassRegistry()
        PassRegistry.singleton_instance = PassRegistry(raw)

    @untested
    def InitializeCore(self):
        _initialization.InitializeCore(self._raw)
    @untested
    def InitializeTransformUtils(self):
        _initialization.InitializeTransformUtils(self._raw)

    @untested
    def InitializeScalarOpts(self):
        _initialization.InitializeScalarOpts(self._raw)

    if (3, 3) <= _version:
        @untested
        def InitializeObjCARCOpts(self):
            _initialization.InitializeObjCARCOpts(self._raw)

    if (3, 1) <= _version:
        @untested
        def InitializeVectorization(self):
            _initialization.InitializeVectorization(self._raw)

    @untested
    def InitializeInstCombine(self):
        _initialization.InitializeInstCombine(self._raw)

    @untested
    def InitializeIPO(self):
        _initialization.InitializeIPO(self._raw)

    @untested
    def InitializeInstrumentation(self):
        _initialization.InitializeInstrumentation(self._raw)

    @untested
    def InitializeAnalysis(self):
        _initialization.InitializeAnalysis(self._raw)

    @untested
    def InitializeIPA(self):
        _initialization.InitializeIPA(self._raw)

    @untested
    def InitializeCodeGen(self):
        _initialization.InitializeCodeGen(self._raw)

    @untested
    def InitializeTarget(self):
        _initialization.InitializeTarget(self._raw)


def py_fun(c_fun):
    @functools.wraps(c_fun)
    def inner(self):
        c_fun(self._raw)
    assert inner.__name__.startswith('LLVM')
    inner.__name__ = inner.__name__[4:]
    inner.__qualname__ = 'PassManagerBase.%s' % inner.__name__
    inner.__module__ = __name__
    return inner

class PassManagerBase(object):
    __slots__ = ('_raw',)

    @untested
    def __init__(self, raw):
        assert isinstance(raw, _core.PassManager)
        self._raw = raw

    @untested
    def __del__(self):
        ''' Frees the memory of a pass pipeline. For function pipelines,
            does not free the module.
        '''
        _core.DisposePassManager(self._raw)

    for mod, lst in [
            ('ipo',
                [
                    'AddArgumentPromotionPass',
                    'AddConstantMergePass',
                    'AddDeadArgEliminationPass',
                    'AddFunctionAttrsPass',
                    'AddFunctionInliningPass',
                    'AddAlwaysInlinerPass',
                    'AddGlobalDCEPass',
                    'AddGlobalOptimizerPass',
                    'AddIPConstantPropagationPass',
                    'AddPruneEHPass',
                    'AddIPSCCPPass',
                    'AddInternalizePass',
                    'AddStripDeadPrototypesPass',
                    'AddStripSymbolsPass',
                ],
            ),
            ('scalar',
                [
                    'AddAggressiveDCEPass',
                    'AddCFGSimplificationPass',
                    'AddDeadStoreEliminationPass',
                    'AddScalarizerPass',
                    'AddMergedLoadStoreMotionPass',
                    'AddGVNPass',
                    'AddIndVarSimplifyPass',
                    'AddInstructionCombiningPass',
                    'AddJumpThreadingPass',
                    'AddLICMPass',
                    'AddLoopDeletionPass',
                    'AddLoopIdiomPass',
                    'AddLoopRotatePass',
                    'AddLoopRerollPass',
                    'AddLoopUnrollPass',
                    'AddLoopUnswitchPass',
                    'AddMemCpyOptPass',
                    'AddPartiallyInlineLibCallsPass',
                    'AddPromoteMemoryToRegisterPass',
                    'AddReassociatePass',
                    'AddSCCPPass',
                    'AddScalarReplAggregatesPass',
                    'AddScalarReplAggregatesPassSSA',
                    'AddScalarReplAggregatesPassWithThreshold',
                    'AddSimplifyLibCallsPass',
                    'AddTailCallEliminationPass',
                    'AddConstantPropagationPass',
                    'AddDemoteMemoryToRegisterPass',
                    'AddVerifierPass',
                    'AddCorrelatedValuePropagationPass',
                    'AddEarlyCSEPass',
                    'AddLowerExpectIntrinsicPass',
                    'AddTypeBasedAliasAnalysisPass',
                    'AddBasicAliasAnalysisPass',
                ],
            ),
            ('vectorize',
                [
                    'AddBBVectorizePass',
                    'AddLoopVectorizePass',
                    'AddSLPVectorizePass',
                ],
            ),
    ]:
        mod = getattr(llpy.c.transforms, mod)
        for pass_ in lst:
            # add only if present
            c_fun = getattr(mod, pass_, None)
            if c_fun is None:
                continue
            # TODO remove this untested, and just rely on the C untested
            locals()[pass_] = untested(py_fun(c_fun))
    del mod, lst, pass_, c_fun

class ModulePassManager(PassManagerBase):
    __slots__ = ()

    @untested
    def __init__(self, builder=None):
        ''' Constructs a new whole-module pass pipeline.

            This type of pipeline is suitable for link-time optimization
            and whole-module transformations.
        '''
        raw = _core.CreatePassManager()
        PassManagerBase.__init__(self, raw)
        if builder is not None:
            _pmb.PassManagerBuilderPopulateModulePassManager(builder._raw, self._raw)

    @untested
    def run(self, mod):
        ''' Initializes, executes on the provided module, and finalizes all
            of the passes scheduled in the pass manager.

            Returns 1 if any of the passes modified the module, 0 otherwise.
        '''
        return bool(_core.RunPassManager(self._raw, mod._raw))

class FunctionPassManager(PassManagerBase):
    __slots__ = ()

    @untested
    def __init__(self, mod, builder=None):
        ''' Constructs a new function-by-function pass pipeline over the
            module.

            It does not take ownership of the module. This type of pipeline
            is suitable for code generation and JIT compilation tasks.
        '''
        raw = _core.CreateFunctionPassManagerForModule(mod._raw)
        PassManagerBase.__init__(self, raw)
        if builder is not None:
            _pmb.PassManagerBuilderPopulateFunctionPassManager(builder._raw, self._raw)

    @untested
    def initialize(self):
        ''' Initializes all of the function passes scheduled in the
            function pass manager.

            Returns 1 if any of the passes modified the module, 0 otherwise.
        '''
        return bool(_core.InitializeFunctionPassManager(self._raw))

    @untested
    def run(self, func):
        ''' Executes all of the function passes scheduled in the
            function pass manager on the provided function.

            Returns 1 if any of the passes modified the function,
            false otherwise.
        '''
        return bool(_core.RunFunctionPassManager(self._raw, func._raw))

    @untested
    def finalize(self):
        ''' Finalizes all of the function passes scheduled in in the
            function pass manager.

            Returns 1 if any of the passes modified the module, 0 otherwise.
        '''
        return bool(_core.FinalizeFunctionPassManager(self._raw))

class PassManagerBuilder:
    __slots__ = ('_raw',)

    @untested
    def __init__(self):
        self._raw = _pmb.PassManagerBuilderCreate()

    @untested
    def __del__(self):
        _pmb.PassManagerBuilderDispose(self._raw)

    @untested
    def SetOptLevel(self, level):
        assert isinstance(level, int)
        _pmb.PassManagerBuilderSetOptLevel(self._raw, level)

    @untested
    def SetSizeLevel(self, level):
        assert isinstance(level, int)
        _pmb.PassManagerBuilderSetSizeLevel(self._raw, level)

    @untested
    def SetDisableUnitAtATime(self, boo):
        assert isinstance(boo, bool)
        _pmb.PassManagerBuilderSetDisableUnitAtATime(self._raw, boo)

    @untested
    def SetDisableUnrollLoops(self, boo):
        assert isinstance(boo, bool)
        _pmb.PassManagerBuilderSetDisableUnrollLoops(self._raw, boo)

    @untested
    def SetDisableSimplifyLibCalls(self, boo):
        assert isinstance(boo, bool)
        _pmb.PassManagerBuilderSetDisableSimplifyLibCalls(self._raw, boo)

    @untested
    def UseInlinerWithThreshold(self, level):
        assert isinstance(level, int)
        _pmb.PassManagerBuilderUseInlinerWithThreshold(self._raw, level)
