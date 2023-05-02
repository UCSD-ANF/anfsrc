Python modules for $ANF/lib/python
==================================

This directory contains a set of Make rules to install Python modules in
`$ANF/lib/python`.

It uses the "Pip" command to install modules based on a particular version of Python.

Requirements
------------

* Antelope 5.2-64 or newer with a working Python install.
   repository.
* GNU make - This is typically `gmake` on Solaris, `make` on Linux and
   Darwin (Mac OSX)
* The `pip` command - see (../bootstrap_pip) for installation.

NOTE: Some of the modules require that development header files are installed
on the system in order to compile the Python bindings. Typically these are
included in the \*-devel packages on RedHat-like Linux systems, eg
_rrdtool-devel_ for _rrdtool_.

Usage
-----

1. Create a requirements file for the Python version used by Antelope. Determine the version by running `getid python_mainversion` in an Antelope-enabled shell.
2. Add the package to the requirements file.
3. (bonus points) Make sure that any development packages get installed
   automatically on the development systems via Puppet - see
   [puppet-environments][1]

[1]: https://github.com/UCSD-ANF/puppet-environments
