Python modules for $ANF/lib/python
----------------------------------

Requirements
============

 * Antelope 5.2-64 or newer with a working Python install.
 * A working localmake\_config setup - See `antelope/adm/localmake` in this
   repository.
   needed symlink in `$ANTELOPE/local/bin/python`
 * GNU make - This is typically `gmake` on Solaris, `make` on Linux and
   Darwin (Mac OSX)

Usage
=====

To use this module installer, do the following:

1. Create a directory named after the module
2. Add that directory name to the `DIRS` variable in the `GNUmakefile`
   located in this directory
3. Create a `GNUmakefile` in the new module subdirectory. It should look
   like this:
```
# Install Python module MyPythonModule
MODULE_NAME = MyPythonModule
MODULE_VERSION = x.y.x # Where x.y.z is the requested version of the module
include ../pymodule.mk
```
