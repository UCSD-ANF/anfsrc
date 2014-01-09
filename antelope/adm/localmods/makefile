all clean Include install installMAN pf relink tags uninstall :: FORCED
	@case `getid id` in \
		5.3) $(MAKE) -f Makefile-5.3 $@ ;; \
		*) echo "No pf_localmods for this release" ;; \
	esac

FORCED:
