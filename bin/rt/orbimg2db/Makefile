BIN=orbimg2db
PF= orbimg2db.pf

MAN1=orbimg2db.1

CLEAN=

cflags = 
ldflags = 
ldlibs = $(TRLIBS) $(ORBLIBS)

include $(ANTELOPEMAKE)

DBG= -g

DIRS=

OBJS= $(BIN).o
$(BIN) : $(OBJS)
	$(RM) $@
	$(CC) $(CFLAGS) -o $@ $(OBJS) $(LDFLAGS) $(LDLIBS)
