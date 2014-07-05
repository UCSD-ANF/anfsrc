from distutils.core import setup
from Cython.Build import cythonize

setup(
    name='segd2db cython module',
    ext_modules=cythonize('segd2db_cython.pyx'),
)
