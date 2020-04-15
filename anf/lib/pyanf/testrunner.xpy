"""Antelope wrapper for Python tests.

All tests should be in the directory named "test".
"""

import unittest
from pprint import pprint
from six import StringIO

stream = StringIO()
runner = unittest.TextTestRunner(stream=stream)
result = runner.run(unittest.defaultTestLoader.discover(start_dir="./test"))
print('Tests run: ', result.testsRun)
print('Errors:   ', result.errors)
print('Failures:  ', end='')
pprint(result.failures)
stream.seek(0)
print('Test output:\n', stream.read())
