MODULE_NAME = readline
MODULE_VERSION = 6.2.4.1
###
### Macros
###
PYTHON_EXECUTABLE=$(ANTELOPE)/bin/python

ANTELOPE_PYTHON_LIB_DIR = $(shell $(PYTHON_EXECUTABLE) -c 'from distutils.sysconfig import get_python_lib; print(get_python_lib())')
ANF_PYTHON_LIB_DIR     = $(ANF)/lib/python
ANF_PYTHON_SCRIPTS_DIR = $(ANF)/bin

EASY_INSTALL       = $(PYTHON_EXECUTABLE) -m easy_install
EASY_INSTALL_ARGS  = -N

# Generate the name of the EGGFILE that will be created by the module.
EGGFILE = $(shell $(PYTHON_EXECUTABLE) -c 'import sys; print "%s-%s-py%s.egg" % ("'$(MODULE_NAME)'", "'$(MODULE_VERSION)'", sys.version[:3])')

###
### Targets
###

Include all : install

# Create ANF_PYTHON_LIB_DIR
#$(ANF_PYTHON_LIB_DIR) :
#	@echo "Creating Python Library Dir $(ANF_PYTHON_LIB_DIR)"
#	mkdir -p $(ANF_PYTHON_LIB_DIR)

# Create the Eggfile
$(ANTELOPE_PYTHON_LIB_DIR)/$(EGGFILE) : $(ANTELOPE_PYTHON_LIB_DIR)
	$(EASY_INSTALL) $(EASY_INSTALL_ARGS) $(MODULE_NAME)==$(MODULE_VERSION)

install: $(ANTELOPE_PYTHON_LIB_DIR)/$(EGGFILE)

# No-op commands
installMAN pf relink clean tags:

uninstall:
	$(EASY_INSTALL) $(EASY_INSTALL_ARGS) -mx $(MODULE_NAME)==$(MODULE_VERSION)
	rm -f $(EGGFILE)
