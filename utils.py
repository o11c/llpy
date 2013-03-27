''' General utility methods used by this LLVM wrapper.

    GPL3+. Someday I'll fill in the whole copyright header ...
'''

def u2b(u):
    ''' Convert a unicode string to bytes, without exception.
    '''
    return bytes(u, 'utf-8', 'surrogateescape')

def b2u(b):
    ''' Convert a byte string to unicode, without exception.
    '''
    return str(b, 'utf-8', 'surrogateescape')
