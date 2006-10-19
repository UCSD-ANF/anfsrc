LIB= libuser.a
DLIB=$(LIB:.a=$(DSUFFIX))
INCLUDE= libuser.h p_libuser.h
PF= nmea_defs.pf

MAN3=

CLEAN=

cflags=
ldflags=
ldlibs = $(TRLIBS)

# install libuser directly in $ANTELOPE
include $(ANTELOPEMAKE)
DBG= -g
DIRS=

OBJS= libuser.o img.o nmea.o vorb.o trwfXML.o orsci.o wicor.o davis.o sbe39.o ORACLEpf.o
$(LIB) : $(OBJS)
	rm -f $@
	$(AR) $(ARFLAGS) $@ $(LORDER) $(OBJS) $(TSORT)
	$(RANLIB) $@

$(DLIB) : $(OBJS)
	$(DLD) $(DLDFLAGS) $(LDLIBS) -o $(DLIB) $(LORDER) $(OBJS) $(TSORT)
