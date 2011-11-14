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

EASY_INSTALL       = $(ANTELOPE)/local/bin/python -m easy_install
EASY_INSTALL_ARGS  = -d $(PYTHON_LIB_DIR) -s $(PYTHON_SCRIPTS_DIR) -N
PYTHON_LIB_DIR     = $(ANF)/lib/python
PYTHON_SCRIPTS_DIR = $(ANF)/bin

Include all : install

$(PYTHON_LIB_DIR) : 
	@echo "Creating Python Library Dir $(PYTHON_LIB_DIR)
	mkdir -p $(PYTHON_LIB_DIR)

EGGFILE = $(shell $(ANTELOPE)/local/bin/python -c 'import sys; print "%s-%s-py%s.egg" % ("'$(MODULE_NAME)'", "'$(MODULE_VERSION)'", sys.version[:3])')

$(PYTHON_LIB_DIR)/$(EGGFILE) : $(PYTHON_LIB_DIR)
	$(EASY_INSTALL) $(EASY_INSTALL_ARGS) $(MODULE_NAME)==$(MODULE_VERSION)

install: $(PYTHON_LIB_DIR)/$(EGGFILE)

# No-op commands
installMAN pf relink clean tags:

uninstall:
	$(EASY_INSTALL) $(EASY_INSTALL_ARGS) -mx $(MODULE_NAME)==$(MODULE_VERSION)
	rm -f $(EGGFILE)
