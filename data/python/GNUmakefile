# Makefile to install Python modules under $ANF
#

# Bring in antelopemake.local for the value of PYTHON_EXECUTABLE
ANTELOPEMAKELOCAL = $(ANTELOPE)/local/include/antelopemake.local
include $(ANTELOPEMAKELOCAL)

# Check whether we have a BRTT-provided Python. Value is 'antelope' if true
BRTT_PYTHON = $(findstring antelope, $(PYTHON_EXECUTABLE) )

ifneq ($(strip $(BRTT_PYTHON)), antelope)
# Dirs to build for non-BRTT Python
# Some are included in 5.2 and greater
DIRS  = beautifulsoup
DIRS += pyflickr
DIRS += twisted
DIRS += matplotlib
DIRS += numpy
DIRS += obspycore
DIRS += obspymseed
DIRS += obspysac
DIRS += obspygse
DIRS += obspyimaging
DIRS += pil
DIRS += python-dateutil
else
# Dirs to build for BRTT provided python
DIRS  = beautifulsoup
DIRS += pyflickr
DIRS += obspycore
DIRS += obspymseed
DIRS += obspysac
DIRS += obspygse
DIRS += obspyimaging
endif

# Default target
all install installMAN pf relink clean Include tags uninstall :: FORCED print-message
	@-DIRS="$(DIRS)" ;\
	for i in $$DIRS ; do \
	  printf "+    %-40s  %s\n" $$i "`date`" ; \
	  if [ -f $$i/Makefile -o \
	       -f $$i/makefile -o -f $$i/GNUmakefile ] ; \
	  then \
	    ( cd $$i && $(MAKE) $@ ; ) ; \
	  else \
	    if [ -d $$i ] ; then \
	      echo Error: no Makefile in `pwd`/$$i ;\
	    fi \
	  fi \
	done

print-message:
	@echo BRTT_PYTHON is $(BRTT_PYTHON)
	@echo Building the following dirs: $(DIRS)

FORCED:
