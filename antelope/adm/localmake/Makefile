localmake_config.pf: FORCED
	cp -f localmake_config.pf-`getid os`-`getid id` localmake_config.pf
	$(ANTELOPE)/bin/localmake_config -if

PF=localmake_config.pf
CLEAN=localmake_config.pf
all:: $(ANTELOPE)/local/include/antelopemake.local

include $(ANTELOPEMAKE)
SUBDIR= /local
