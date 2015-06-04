BIN = orb2ringserver
MAN1 = orb2ringserver.1

CLEAN=$(BIN)

cflags= -Ilibmseed -Ilibdali
ldflags= -Llibmseed -Llibdali
ldlibs= $(ORBLIBS) -lmseed -ldali

include $(ANFMAKE) # This line must appear following the definitions above,
                   # and before the DIRS definition below..
DIRS = libmseed libdali

OBJS = orb2ringserver.o

$(BIN) : $(OBJS)
	$(CC) $(CFLAGS) -o $@ $(OBJS) $(LDFLAGS) $(LDLIBS)
