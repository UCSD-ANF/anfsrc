# GNU Makefile for ANF localmake configuration

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
# Fall back to using localmake_config -i if localmake_config -if fails (happens
# in 5.4 due to old version of localmake_config included in Antelope.)
$(ANTELOPE)$(SUBDIR)/include/antelopemake.local: $(ANTELOPE)$(SUBDIR)/data/pf/$(PF)
	localmake_config -if || localmake_config -i

include $(ANTELOPEMAKE)

install :: $(ANTELOPE)/local/include/antelopemake.local
