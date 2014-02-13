Python modules for $ANF/lib/python
==================================

This directory contains a set of Make rules to install Python modules in
`$ANF/lib/python`.

Requirements
------------

 * Antelope 5.2-64 or newer with a working Python install.
   repository.
 * GNU make - This is typically `gmake` on Solaris, `make` on Linux and
   Darwin (Mac OSX)

NOTE: Some of the modules require that development header files are installed
on the system in order to compile the Python bindings. Typically these are
included in the \*-devel packages on RedHat-like Linux systems, eg
_rrdtool-devel_ for _rrdtool_.

Usage
-----

To use this module installer, do the following:

Before you begin, determine if the module has any other Python module
dependencies. Then, for each module you are adding:

1. Create a directory named after the module
2. Add that directory name to the `DIRS` variable in the `GNUmakefile`
   located in this directory, keeping dependencies in mind
3. Create a `GNUmakefile` in the new module subdirectory. Use the example
   below as a template. Be sure to note any system-level dependencies such as
   C header files (typically in devel packages) in the comments or in a README.
4. (bonus points) Make sure that any development packages get installed
   automatically on the development systems via Puppet - see
   [puppet-environments][1]

[1]: https://github.com/UCSD-ANF/puppet-environments

Example GNUmakefile
-------------------

```
# Install Python module MyPythonModule
# Requires:
# * C header files for the foo package, available as foo-devel on RedHat/CentOS
MODULE_NAME = MyPythonModule
MODULE_VERSION = x.y.x # Where x.y.z is the requested version of the module
include ../lib/pymodule.mk
```
