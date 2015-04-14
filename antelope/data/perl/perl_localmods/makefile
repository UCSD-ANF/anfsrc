
all clean Include install installMAN pf relink tags uninstall :: FORCED
	@case `getid id` in \
	    4.11p) $(MAKE) -f Makefile-4.11p $@ ;; \
	    *) echo "No pf_localmods for this release" ;; \
	  esac

FORCED:
