
BIN= nmea2orb
DATADIR=
DATA=
INCLUDE=
PF=

MAN1= nmea2orb.1
MAN3=
MAN5=

CLEAN=

cflags=
fflags=
ldflags=
ldlibs= -luser $(ORBLIBS)

include $(ANTELOPEMAKE)

DBG= -g 

OBJS= $(BIN).o
$(BIN) : $(OBJS)
	$(RM) $@
	$(CC) $(CFLAGS) -o $@ $(OBJS) $(LDFLAGS) $(LDLIBS)
