import unittest
from tempfile import mkstemp
import os
import sys
from circus import get_arbiter


def resolve_name(name):
    ret = None
    parts = name.split('.')
    cursor = len(parts)
    module_name = parts[:cursor]
    last_exc = None

    while cursor > 0:
        try:
            ret = __import__('.'.join(module_name))
            break
        except ImportError, exc:
            last_exc = exc
            if cursor == 0:
                raise
            cursor -= 1
            module_name = parts[:cursor]

    for part in parts[1:]:
        try:
            ret = getattr(ret, part)
        except AttributeError:
            if last_exc is not None:
                raise last_exc
            raise ImportError(name)

    if ret is None:
        if last_exc is not None:
            raise last_exc
        raise ImportError(name)

    return ret


class TestCircus(unittest.TestCase):

    def setUp(self):
        self.arbiters = []
        self.files = []

    def tearDown(self):
        self._stop_runners()
        for file in self.files:
            if os.path.exists(file):
                os.remove(file)

    def _run_circus(self, callable):
        resolve_name(callable)   # used to check the callable
        fd, testfile = mkstemp()
        os.close(fd)
        wdir = os.path.dirname(__file__)
        cmd = '%s generic.py %s %s' % (sys.executable, callable, testfile)
        worker = {'cmd': cmd, 'working_dir': wdir, 'name': 'test'}
        arbiter = get_arbiter([worker], background=True)
        arbiter.start()
        self.arbiters.append(arbiter)
        self.files.append(testfile)
        return testfile

    def _stop_runners(self):
        for arbiter in self.arbiters:
            arbiter.stop()
        self.arbiters = []
