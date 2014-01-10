BIN= ice92orb 
MAN1= ice92orb.1
PF=ice92orb.pf
ldlibs = $(ORBLIBS)
include $(ANTELOPEMAKE)


ice9test: ice9test.c ice9test.h
	cc -o ice9test ice9test.c -lsocket -lnsl
