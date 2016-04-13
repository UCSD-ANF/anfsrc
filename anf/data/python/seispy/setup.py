from distutils.core import setup, Extension

trmath = Extension('trmath',
                   sources = ['trmath.c'])

setup (name = 'SeisPy',
        version = '1.0',
        description = 'A library for generally useful seismic tools.',
        ext_modules = [trmath])
