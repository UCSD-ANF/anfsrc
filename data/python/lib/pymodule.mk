# Makefile to install Python modules under $ANF
#
# Requirements:
# * Python's setuptools module
# * GNU make - gmake on Solaris, make on Linux, Darwin
#
# To use this script, create a GNUmakefile with the following contents
# MODULE_NAME = MyPythonModule
# MODULE_VERSION = x.y.z
#
# include ../lib/pymodule.mk
#

ANTELOPEMAKELOCAL = $(ANTELOPE)/local/include/antelopemake.local

#include $(ANFMAKE)
include $(ANTELOPEMAKELOCAL)

EASY_INSTALL       = $(PYTHON_EXECUTABLE) -m easy_install
EASY_INSTALL_ARGS  = -d $(ANF_PYTHON_LIB_DIR) -s $(ANF_PYTHON_SCRIPTS_DIR) -N
ANF_PYTHON_LIB_DIR     = $(ANF)/lib/python
ANF_PYTHON_SCRIPTS_DIR = $(ANF)/bin

Include all : install

$(ANF_PYTHON_LIB_DIR) :
	@echo "Creating Python Library Dir $(ANF_PYTHON_LIB_DIR)"
	mkdir -p $(ANF_PYTHON_LIB_DIR)

EGGFILE = $(shell $(PYTHON_EXECUTABLE) -c 'import sys; print "%s-%s-py%s.egg" % ("'$(MODULE_NAME)'", "'$(MODULE_VERSION)'", sys.version[:3])')

$(ANF_PYTHON_LIB_DIR)/$(EGGFILE) : $(ANF_PYTHON_LIB_DIR)
	$(EASY_INSTALL) $(EASY_INSTALL_ARGS) $(MODULE_NAME)==$(MODULE_VERSION)

install: $(ANF_PYTHON_LIB_DIR)/$(EGGFILE)

# No-op commands
installMAN pf relink clean tags:

uninstall:
	$(EASY_INSTALL) $(EASY_INSTALL_ARGS) -mx $(MODULE_NAME)==$(MODULE_VERSION)
	rm -f $(EGGFILE)
