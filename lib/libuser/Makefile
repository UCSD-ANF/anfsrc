LIB= libuser.a
DLIB=$(LIB:.a=$(DSUFFIX))
INCLUDE= libuser.h p_libuser.h
PF= nmea_defs.pf

MAN3=

CLEAN=

cflags = -I/usr/local/include
ldflags = -L/usr/local/lib -R/usr/local/lib -L/opt/sfw/lib -R/opt/sfw/lib
ldlibs = $(TRLIBS) $(X11LIBS)

# install libuser directly in $ANTELOPE
include $(ANTELOPEMAKE)
DBG= -g
DIRS=

OBJS= libuser.o img.o nmea.o vorb.o trwfXML.o orsci.o wicor.o
$(LIB) : $(OBJS)
	rm -f $@
	$(AR) $(ARFLAGS) $@ $(LORDER) $(OBJS) $(TSORT)
	$(RANLIB) $@

$(DLIB) : $(OBJS)
	$(DLD) $(DLDFLAGS) $(LDLIBS) -o $(DLIB) $(LORDER) $(OBJS) $(TSORT)
