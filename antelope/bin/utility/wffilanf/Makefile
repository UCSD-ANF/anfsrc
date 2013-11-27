# Copyright (c) 1997-2007 Boulder Real Time Technologies, Inc.
# All rights reserved 

# This software module is wholly owned by Boulder Real Time 
# Technologies, Inc. Any use of this software module without
# express written permission from Boulder Real Time Technologies,
# Inc. is prohibited.

#
#       libwffilbrtt implements the Antelope waveform filtering
#       methods based on time-dmina digital recursion filtering.
#	This can be used through the wffil generic interface or
#	on its own.
#

DLIB=libwffilanf$(DSUFFIX)

#MAN3= wffilanf.3

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

