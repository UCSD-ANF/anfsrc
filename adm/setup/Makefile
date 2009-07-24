DEST=$(ANF)

Include :: $(DEST)/setup.csh
Include :: $(DEST)/setup.sh
install :: $(DEST)/setup.csh
install :: $(DEST)/setup.sh

all clean Include install installMAN pf relink tags :: FORCED
	@-DIRS="$(DIRS)" ;\
	for i in $$DIRS ; do \
	    printf "+    %-40s  %s\n" $$i "`date`" ; \
	    if [ -f $$i/Makefile -o -f $$i/makefile ] ; then ( cd $$i && $(MAKE) $@ ; ) ; else if [ -d $$i ] ; then echo Error: no Makefile in `pwd`/$$i ; fi ; fi ; \
	done

uninstall :: FORCED
	@-if [ -r $(DEST)/setup.csh ] ; then \
	    DIRS="$(DIRS)" ;\
	    for i in $$DIRS ; do \
	        printf "+    %-40s  %s\n" $$i "`date`" ; \
	        if [ -f $$i/Makefile -o -f $$i/makefile ] ; then ( cd $$i && $(MAKE) $@ ; ) ; else if [ -d $$i ] ; then echo Error: no Makefile in `pwd`/$$i ; fi ; fi ; \
	    done ; \
	    $(RM) $(DEST)/setup.csh; \
	    $(RM) $(DEST)/setup.sh; \
	fi

FORCED:

$(DEST)/setup.csh: setup.csh
	deposit setup.csh $(DEST)

$(DEST)/setup.sh: setup.sh
	deposit setup.sh $(DEST)

setup.csh: setup.csh.id
	getid < setup.csh.id > setup.csh

setup.sh: setup.sh.id
	getid < setup.sh.id > setup.sh

clean :: 
	$(RM) setup.csh setup.sh
