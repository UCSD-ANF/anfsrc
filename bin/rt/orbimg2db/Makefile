BIN=orbimg2db
PF=

MAN1=orbimg2db.1

CLEAN=

cflags = -I/usr/local/include
ldflags = -L/usr/local/lib -R/usr/local/lib -L/opt/sfw/lib -R/opt/sfw/lib
ldlibs = -lMagick -ltiff $(TRLIBS) $(X11LIBS) $(ORBLIBS)

include $(ANTELOPEMAKE)

DBG= -g

DIRS=

OBJS= $(BIN).o
$(BIN) : $(OBJS)
	$(RM) $@
	$(CC) $(CFLAGS) -o $@ $(OBJS) $(LDFLAGS) $(LDLIBS)
