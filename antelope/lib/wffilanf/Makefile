# Copyright (c) 1997-2007 Boulder Real Time Technologies, Inc.
# All rights reserved
# Copyright (c) 2013-2014 The Regents of the University of California

#
#      libwffilanf implements a white noise filter suitable for
#      simulating digitizer noise.
#

DLIB=libwffilanf$(DSUFFIX)

MAN3= wffilanf.3

OPTIMIZE=wffilanf.c

ldlibs=$(TRLIBS)
include $(ANTELOPEMAKE)
DIRS=

OBJS=wffilanf.o
$(LIB) : $(OBJS)
	$(RM) $@
	$(AR) $(ARFLAGS) $@ $(LORDER) $(OBJS) $(TSORT)
	$(RANLIB) $@

$(DLIB) : $(OBJS)
	$(RM) $@
	$(DLD) $(DLDFLAGS) -o $@ $(LORDER) $(OBJS) $(TSORT) $(DLDLIBS)

$(BUNDLE) : $(OBJS)
	$(RM) $@
	$(DLD)  -flat_namespace -bundle -undefined suppress -o $@   $(OBJS) $(LDFLAGS) $(BLDLIBS)
