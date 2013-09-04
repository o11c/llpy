#!/usr/bin/env python3

def main():
    import py.test
    import sys
    return py.test.main(['llpy/'] + sys.argv[1:])

if __name__ == '__main__':
    import sys
    sys.exit(main())
