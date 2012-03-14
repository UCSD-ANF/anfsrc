# Makefile to install Python modules under $ANF
#

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

FORCED:
