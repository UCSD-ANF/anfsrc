# Makefile to install Python modules under $ANF
#
# This is complicated by the fact that the orginal project fell into a
# defunct state.  A more recent fix exists to compensate for Google
# changing the way their HTTP calls work subsequent to the orginal
# projects going defunct. For details, see
# https://code.google.com/r/kkleidal-pygooglevoiceupdate/source/checkout
#
# To install manually, we need to run the following commands:
#  hg clone https://code.google.com/r/kkleidal-pygooglevoiceupdate/ && \
#  easy_install ./kkleidal-pygooglevoiceupdate                      && \
#  rm -fr ./kkleidal-pygooglevoiceupdate
# The module will then get installed as pygooglevoice.
#
# NOTE: we also have a .gitignore file in this directory to avoid
# errant runs of this build keeping the Mercurial repo around.

MODULE_NAME    = ./kkleidal-pygooglevoiceupdate
CLEAN          = $(MODULE_NAME)
EXTRA_EGG_DEPS = $(MODULE_NAME)

# We include the -a arg to force an update in case the real upstream
# project ever needs to be installed
EXTRA_EASY_INSTALL_ARGS = -a

include ../lib/pymodule.mk

kkleidal-pygooglevoiceupdate:
	hg clone https://code.google.com/r/kkleidal-pygooglevoiceupdate
clean:
	rm -fr $(CLEAN)
