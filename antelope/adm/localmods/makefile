# This is the master makefile for localmods. To generate localmods for a
# given release of Antelope, do the following:
# 1. Add a line to the case statement below that calls a second stage makefile
# for that specific version of Antelope.
# 2. Construct the version-specific Makefile using normal ANTELOPEMAKE
# conventions
#
# Example for 5.3:
#
#all clean Include install installMAN pf relink tags uninstall :: FORCED
#	@case `getid id` in \
#		5.3) $(MAKE) -f Makefile-5.3 $@ ;; \
#		*) echo "No pf_localmods for this release" ;; \
#	esac
#
all clean Include install installMAN pf relink tags uninstall :: FORCED
	@case `getid id` in \
		*) echo "No pf_localmods for this release" ;; \
	esac

FORCED:
