"""Setuptools config for segd to mseed modules."""

from distutils.core import Extension, setup

trmath = Extension("trmath", sources=["trmath.c"])

setup(
    name="SeisPy",
    version="1.0",
    description="A library for generally useful seismic tools.",
    ext_modules=[trmath],
)
