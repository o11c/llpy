#!/usr/bin/env python3
from distutils.core import setup
setup(name='llpy',
        version='0.1',
        description='LLVM bindings',
        author='Ben Longbons',
        author_email='b.r.longbons@gmail.com',
        url='http://github.com/o11c/llpy',
        packages=['llpy', 'llpy.c'],
        classifiers=[
            'Development Status :: 3 - Alpha',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)',
            'Operating System :: POSIX :: Linux',
            'Topic :: Software Development :: Code Generators',
            'Topic :: Software Development :: Libraries',
            ],
        )
