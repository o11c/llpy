#!/bin/bash -e
export LLPY_LLVM_VERSION
for LLPY_LLVM_VERSION in 3.0 3.1 3.2 3.3 3.4
do
    echo Testing with LLVM $LLPY_LLVM_VERSION
    ./runtests.py
done
