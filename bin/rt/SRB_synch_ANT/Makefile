# This is a template for a standard Antelope Makefile.
# You should edit it to keep the lines which pertain to what
# you want, and delete the rest, including all the lines beginning with #.

SRBDIR= /export/home/vorb/SRB3_3_1roadnet/
SRBclientObjDir=$(SRBDIR)/obj
SRButilObjDir=$(SRBDIR)/utilities/obj
SRButilBinDir=$(SRBDIR)/utilities/bin

include $(SRBDIR)/mk/mk.config
include $(SRBDIR)/mk/mk.common

# Binary targets which can be "installed".
BIN=	SRB_synch_orbregistries	# commands to be placed in bin

# Man pages for the command or library -- EVERY 
# command, and every external routine in a library
# should have a man page.
MAN1=SRB_synch_orbregistries.1 

# -------------SRB specific stuff----------------
ifeq ($(PORTNAME), PORTNAME_solaris)
LDADD+=-lnsl -lsocket
RANLIB=/usr/ccs/bin/ranlib
else
RANLIB=ranlib
endif

LDADD+= $(SRButilObjDir)/srbClientUtil.o -L$(SRBclientObjDir) -lSrbClient

ifdef GSI_AUTH
ifeq ($(PORTNAME), PORTNAME_aix)
LDADD+= $(LIB_GSI_AUTH) $(KRB_LIBS)
else
LDADD+= $(LIB_GSI_AUTH) $(KRB_LIBS) -z muldefs
endif
endif

# SGI doesn't like -lm in the middle of the CC line
ifeq ($(PORTNAME), PORTNAME_osx)
else
ifeq ($(PORTNAME), PORTNAME_sgi)
else
LDADD+=-lm
endif
endif

LDADD+=-lpthread
# -----------------------------------------


# Extra non-standard options to be added to the corresponding
# uppercase options:
cflags=	$(MY_CFLAG) -D$(PORTNAME)	-I./include -I$(SRBDIR)/src/include -I$(SRBDIR)/src/catalog/include -I$(SRBDIR)/utilities/include# -g or -O is the most common option here and in fflags

# -------------SRB specific stuff----------------
ifdef SEA_AUTH
cflags+= -DSEA_AUTH
LDADD+= $(LIB_SEA)
endif
# -----------------------------------------

fflags= 	# 
ldflags= 	# flags to linker/loader
ldlibs=		# libraries to link in.

include $(ANTELOPEMAKE)  	# This line must appear following the definitions above, 
			# and before the DIRS definition below..

# In general, you must write the rule which builds your executable,
# library, or other target.  The suggestions below are adequate for most
# simple situations; you must fill in the OBJS macro, and substitute for
# target.  If you modify these examples more extensively, be sure to continue 
# to use the macros CC, FC, CFLAGS, FFLAGS, LDFLAGS, and LDLIBS.
#
# Special case: If your executable is constructed from a single
# source file with the same basename, you need not write any rule at all.
# Just fill in the appropriate macros above (BIN, LIB, MANn, cflags, fflags, ..)

# For a command with a c main routine, and multiple source files, 
# modify the following lines to suit:
OBJS=	ds_helper.o srb_helper.o misc_helper.o source.o SRB_synch_orbregistries.o 
SRCS=	ds_helper.c srb_helper.c misc_helper.c source.c SRB_synch_orbregistries.c 
$(BIN) : $(OBJS)
	$(RM) $@
	$(CC) $(OBJS) -o $@ $(LDADD)
$(OBJS) : $(SRCS)
	$(CC) -c $(SRCS) $(CFLAGS)
