README for anf/data/python/bootstrap_pip
====

Author: Geoff Davis <geoff@ucsd.edu> 2020-01-13

This directory contains an `antelopemakefile` target that will install or
upgrade the PIP installer for the current version of Python. It will work on
Python 2.7 and 3.6, which are the versions included with recent releases of
Antelope.

There is a vendored copy of (get-pip.py)[https://bootstrap.pypa.io/get-pip.py]
in this repository. To update it, there is a target called `update-get-pip`. Be
sure to commit the changed version to this repository.
