DEST=$(ANF)

Include :: $(DEST)/setup.csh
install :: $(DEST)/setup.csh

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
	fi

FORCED:

$(DEST)/setup.csh: setup.csh
	deposit setup.csh $(DEST)

setup.csh: setup.csh.id
	getid < setup.csh.id > setup.csh

clean :: 
	$(RM) setup.csh
