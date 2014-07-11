from distutils.core import setup
from Cython.Build import cythonize

setup(
    name='segd cython module',
    ext_modules=cythonize('segd_cython.pyx'),
)
