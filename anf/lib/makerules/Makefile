OSMAKES=solaris linux darwin darwin-intel
OSMAKESIN=solaris.in linux.in darwin.in darwin-intel.in

CLEAN  =$(OSMAKES)
DEST=$(ANF)

Include :: $(DEST)/include/anfmake
install :: $(DEST)/include/anfmake

all clean Include install installMAN pf relink tags :: FORCED
	@-DIRS="$(DIRS)" ;\
	for i in $$DIRS ; do \
	    printf "+    %-40s  %s\n" $$i "`date`" ; \
	    if [ -f $$i/Makefile -o -f $$i/makefile ] ; then ( cd $$i && $(MAKE) $@ ; ) ; else if [ -d $$i ] ; then echo Error: no Makefile in `pwd`/$$i ; fi ; fi ; \
	done

uninstall :: FORCED
	@-if [ -r $(DEST)/include/anfmake ] ; then \
	    DIRS="$(DIRS)" ;\
	    for i in $$DIRS ; do \
	        printf "+    %-40s  %s\n" $$i "`date`" ; \
	        if [ -f $$i/Makefile -o -f $$i/makefile ] ; then ( cd $$i && $(MAKE) $@ ; ) ; else if [ -d $$i ] ; then echo Error: no Makefile in `pwd`/$$i ; fi ; fi ; \
	    done ; \
	    $(RM) $(DEST)/include/anfmake; \
	fi

FORCED:

$(DEST)/include/anfmake: $(OSMAKES)
	@case `uname -s` in \
	    SunOS) deposit -r solaris $@; echo deposit -r solaris $@ ;; \
	    Linux) deposit -r linux   $@; echo deposit -r linux $@ ;; \
	    Darwin) case `uname -p` in \
		powerpc) deposit -r darwin  $@; echo deposit -r darwin $@ ;; \
		i386) deposit -r darwin-intel  $@; echo deposit -r darwin-intel $@ ;; \
		*) echo "Error: processor type `uname -p` on Darwin not recognized." ;; \
	    esac ;; \
	    *)  echo "Error: System type `uname -s` not recognized." ;;\
	esac

$(OSMAKES) : $(OSMAKESIN) commonheader commonfooter
	$(RM) $@
	cat commonheader $@.in commonfooter > $@
