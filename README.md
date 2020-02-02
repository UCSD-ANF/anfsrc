anfsrc - Source for the `/opt/anf` tree
=====================================

This repository is designed to be used in conjuction with BRTT Antelope
[http://brtt.com].  It creates a tree under /opt/anf with a version number
that matches the current Antelope version. Using this repository will set up
an environment variable named $ANF, similar to the $ANTELOPE variable.

Supported Antelope Versions
--------- -------- --------
As the ANF group typically runs multiple versions of Antelope in our environment for production and
testing purposes, it's necessary for this repository to support more than just the
latest version of Antelope.

We typically support:

* the current release version of Antelope (branch `master`)
* the previous release version of Antelope (branch `master`)
* the current pre-release version of Antelope, if available. (branch `next`)

Currently supported releases (last updated 2010-02-01):

| Previous Production | Current Production | Pre-release |
| ------------------- | ------------------ | ----------- |
| 5.7 (5.8 not used)  | 5.9                | none        |

Repository Organization
-----------------------


There are three top-level subdirectories:
* `adm`
* `anf`
* `antelope`

The `adm` directory contains files that are specific to this repository,
 including the code that bootstraps the `$ANF` tree.

The `anf` directory contains source files that will be installed into `$ANF`.

The `antelope` directory contains source files that will be installed into
$ANTELOPE that do not belong in antelope_contrib. This is typically limited to
instrument response files and a coupld of other items where alternate
directories were not supported.

This repository was originally created with the `build_sourcetree` application in
`antelope_contrib` but has been modified significantly to support installation of
files into the core `$ANTELOPE` directory as well as the `$ANF` directory.

Code in this repostory should be built similar to that in `antelope_contrib`.
Once this repository has been bootstrap installed, see the man page for
anfmakefile(5) for details on how to write code to extend this repository.

Usage Instructions
------------------

After the code has been built (see below), you can include the environment in
your shell. It will automatically include the Antelope environment.

Replace VERSION with the version of Antelope that you want to use, such as 5.5
or 5.6

For bourne compatible shells like sh, ksh, bash:

    . /opt/anf/VERSION/setup.sh # Note the period at the beginning

For csh shells like tcsh and csh:

    source /opt/anf/VERSION/setup.csh

Build Instructions
------------------

The Build process requires the $ANF and $ANFMAKE environment variables to be
set as well as $ANTELOPE. This creates a chicken-and-egg problem, because you
use this repository to generate the script that configures the requisite
environment variables. Thus, a bootstrap procedure must be used the first time
you build the $ANF tree.

First Time Bootstrap:
* Install Antelope on your system.
* Ensure that you have sourced the Antelope environment into your shell. This
  will set the environment variable $ANTELOPE when done correctly.
* Change dirs to the repository root
* ```cd adm/coldstart; make```
* Source the newly created /opt/anf/VERSION/setup.{sh,csh} file for your
  respective shell (see usage section above)
* ```cd ../../``` # Changes dirs back to the repository root
* ```make Include; make; make install```

Subsequent builds:
* Source /opt/anf/VERSION/setup.{sh,csh} file for your respective shell (see
  usage section above)
* Change dirs to the repository root
* ```make Include; make; make install```

Working with multiple Antelope versions
---------------------------------------

A single working copy of the anfsrc repository cannot be made to work with two
versions of Antelope simultaneously. Your options are to either:
* clean up all build artifacts from your current checkout and do the first time
  bootstrap step detailed above, *or*:
* check out a second copy of the `anfsrc` repository.

If you decide to reuse your existing checkout, you will need to prepare your
source code repository for the new Antelope version. The build process leaves a
number of compiled products around, and for a number of complicated reasons,
the `make clean` target won't clean things up when changing Antelope versions.

The best way to clean out the repository is to change to the top level directory, then run:
```git clean -dxf```
