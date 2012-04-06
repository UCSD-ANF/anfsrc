# Makefile to install Python modules under $ANF
#

# Bring in antelopemake.local for the value of PYTHON_EXECUTABLE
ANTELOPEMAKELOCAL = $(ANTELOPE)/local/include/antelopemake.local
include $(ANTELOPEMAKELOCAL)


DIRS  = beautifulsoup
DIRS += pyflickr
DIRS += obspycore
DIRS += obspymseed
DIRS += obspysac
DIRS += obspygse
DIRS += obspyimaging

# Check whether we have a BRTT-provided Python
BRTT_PYTHON = $(findstring antelope, $(PYTHON_EXECUTABLE) )

ifeq ($(strip $(BRTT_PYTHON)),)
# We only build the following modules for Antelope versions prior to
# 5.2-64. They are included in 5.2 and greater
DIRS += twisted
DIRS += matplotlib
DIRS += numpy
DIRS += pil
DIRS += python-dateutil
endif


all install installMAN pf relink clean Include tags uninstall :: FORCED
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

check:
	echo BRTT_PYTHON is $(BRTT_PYTHON)

FORCED:
