# GNU Makefile for ANF localmake configuration

# We rely on the fact that Antelope 5.5 and newer always has contrib in the
# path to detect whether we're on 5.4 and older.
ifneq (,$(findstring contrib,$(PATH)))
	SUBDIR=/contrib
else
	SUBDIR=/local
endif

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

install :: $(ANTELOPE)$(SUBDIR)/include/antelopemake.local
