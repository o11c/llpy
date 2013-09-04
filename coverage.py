#!/usr/bin/env python3
import sys
import trace

# for some reason unittest.main(module=None) kills the process
def inner_main():
    import test_everything
    test_everything.main()

def main():
    ignored = [
            sys.base_prefix, # how is this different than sys.prefix?
            sys.base_exec_prefix, # is this really needed?
            'llpy/tests/',
            'llpy/c/tests/',
    ]
    ignorem = [
            'coverage',
            'test_everything',
    ]
    tracer = trace.Trace(
            ignoredirs=ignored, ignoremods=ignorem,
            trace=0, count=1)
    tracer.runfunc(inner_main)
    r = tracer.results()
    r.write_results(show_missing=True, coverdir='.coverage')

if __name__ == '__main__':
    main()
