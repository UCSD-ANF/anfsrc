# Makefile to install Python modules under $ANF
#

DIRS  = virtualenv
DIRS += virtualenvwrapper
DIRS += beautifulsoup
DIRS += nose
DIRS += mock
DIRS += pyflickr
DIRS += rrdtool
DIRS += numpy
DIRS += scipy
DIRS += lxml
DIRS += suds
DIRS += sqlalchemy
DIRS += obspy
DIRS += cython
DIRS += pygooglevoice
DIRS += python-geoip-geolite2
DIRS += python-geoip
DIRS += pymongo
DIRS += pyasn1
DIRS += pysnmp
DIRS += pysnmp-mibs
DIRS += spectrum
DIRS += urllib3
DIRS += requests

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
	@echo Building the following dirs: $(DIRS)

FORCED:
