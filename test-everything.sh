#!/bin/bash -e
export LLPY_LLVM_VERSION
for LLPY_LLVM_VERSION in $(python -c 'import llpy; print(" ".join("%d.%d" % p for p in llpy.__TESTED_LLVM_VERSIONS))')
do
    echo Testing with LLVM $LLPY_LLVM_VERSION
    ./runtests.py
done
