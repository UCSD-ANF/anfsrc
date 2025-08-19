anfsrc - Source for the `/opt/anf` tree
=====================================

This repository is designed to be used in conjuction with [BRTT Antelope
](http://brtt.com).  It creates a tree under `/opt/anf` with a version number
that matches an Antelope version. Using this repository will set up
an environment variable named `$ANF`, similar to the `$ANTELOPE` variable.

Supported Antelope Versions
---------------------------
As the ANF group typically runs multiple versions of Antelope in our
environment for production and testing purposes, it's necessary for this
repository to support more than just the latest version of Antelope.

We typically support:

* the current release version of Antelope (branch `master`)
* the previous release version of Antelope (branch `master`)
* the current pre-release version of Antelope, if available. (branch `next`)

Currently supported releases (last updated 2020-02-01):

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

This repository was originally created with the `build_sourcetree` application in [antelope-contrib](https://github.com/antelopeusersgroup/antelope-contrib)
but has been modified significantly to support installation of
files into the core `$ANTELOPE` directory as well as the `$ANF` directory.

Code in this repostory should be built similar to that in `antelope_contrib`.
Once this repository has been bootstrap installed, see the man page for
[anfmakefile(5)](adm/docs/anfmakefile.5) for details on how to write code to
extend this repository.

Antelope uses a very peculiar build mechanism for interpreted languages like Perl and Python that is similar to the one used for C and C++ applications. Normal python idioms like setup.py and the like are not used in most cases, which makes development tricky.

Code in this repository is written in a number of languages including C, C++, Perl, Python, TCL, and even a little Fortran.

There is a lot of Python Code that is still in Python2 format but needs to be migrated to Python3.
