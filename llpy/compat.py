try:
    from tempfile import TemporaryDirectory
except ImportError:
    from shutil import rmtree
    from tempfile import mkdtemp

    class TemporaryDirectory(object):
        def __enter__(self):
            self.name = mkdtemp()
            return self.name

        def __exit__(self, exc, value, tb):
            rmtree(self.name)

try:
    long = long
except NameError:
    long = int

try:
    unicode = unicode
except NameError:
    unicode = str
