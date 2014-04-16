# Copyright (c) 1997-2007 Boulder Real Time Technologies, Inc.
# All rights reserved
# Copyright (c) 2013-2014 The Regents of the University of California

#
#      libwffilanf implements three filters:
#      NOISE - a white noise filter suitable for simulating digitizer noise.
#      VAR   - a variance filter
#      SKEW  - a skewness filter
#

LIB=libwffilanf.a
DLIB=$(LIB:.a=$(DSUFFIX))

MAN3= wffilanf.3

INCLUDE=wffilanf.h

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
