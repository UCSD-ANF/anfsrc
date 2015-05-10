# GNU Makefile for ANF localmake configuration
# Note that this needs a newer version of localmake_config that supports the -f
# option (either from contrib or included in Antelope 5.5 and later)

SUBDIR= /local
PF=localmake_config.pf
CLEAN=$(PF)

# Set up some helper variables. Use the := operator to force immediate
# evaluation before any other rules
GETID_OS := $(shell getid os)
GETID_ID := $(shell getid id)

# Generate the platform-specific source parameter file name
PLATFORM_PF = $(PF)-$(GETID_OS)-$(GETID_ID)

$(PF) : $(PLATFORM_PF)
	cp -f $< $@

# This rule has the side-effect of copying the PF file into place
$(ANTELOPE)$(SUBDIR)/include/antelopemake.local: $(ANTELOPE)$(SUBDIR)/data/pf/$(PF)
	$(ANTELOPE)/bin/localmake_config -if

include $(ANTELOPEMAKE)

install :: $(ANTELOPE)/local/include/antelopemake.local
