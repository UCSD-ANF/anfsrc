#
# Create missing directories under $ANTELOPE for local compilation
#
DIRNAMES += $(ANTELOPE)/local/man
DIRNAMES += $(ANTELOPE)/local/bin
DIRNAMES += $(ANTELOPE)/local/include
DIRNAMES += $(ANTELOPE)/local/lib
DIRNAMES += $(ANTELOPE)/local/data
DIRNAMES += $(ANTELOPE)/local/static

all Include install installMAN pf relink :: dirs

dirs: $(DIRNAMES)

$(ANTELOPE)/local :
	mkdir -p $(ANTELOPE)/local

$(DIRNAMES) : $(ANTELOPE)/local
	mkdir -p $@
