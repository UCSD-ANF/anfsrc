BIN=ds2sql
PF=

MAN1=ds2sql.1

CLEAN=rm $(BIN).o $(BIN)

cflags = 
ldflags = 
ldlibs = $(DBLIBS) 

include $(ANTELOPEMAKE)

DBG= -g

DIRS=

OBJS= $(BIN).o
$(BIN) : $(OBJS)
	$(RM) $@
	$(CC) $(CFLAGS) -o $@ $(OBJS) $(LDFLAGS) $(LDLIBS)
