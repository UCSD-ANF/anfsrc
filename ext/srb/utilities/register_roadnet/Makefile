SRBDIR = /export/home/vorb/SRB3_1_0roadnet/
include $(SRBDIR)/mk/mk.config
include $(SRBDIR)/mk/mk.common

ifeq ($(PORTNAME), PORTNAME_solaris)
LDADD+=-lnsl -lsocket
RANLIB=/usr/ccs/bin/ranlib
else
RANLIB=ranlib
endif

clientObjDir=$(SRBDIR)/obj
utilObjDir=$(SRBDIR)/utilities/obj
utilBinDir=$(SRBDIR)/utilities/bin
LDADD+= $(utilObjDir)/srbClientUtil.o -L$(clientObjDir) -lSrbClient

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

ifeq ($(PORTNAME), PORTNAME_solaris)
ifdef GSI_AUTH
SCRIPT=sample_script_solaris_gsi
else
SCRIPT=sample_script_solaris
endif
else
ifdef GSI_AUTH
SCRIPT=sample_script_linux_gsi
else
SCRIPT=sample_script_linux
endif
endif

ifeq ($(PORTNAME), PORTNAME_solaris)
ifdef GSI_AUTH
TARBALL=GSImySRB4Solaris.tar
else
TARBALL=mySRB4Solaris.tar
endif
else
ifdef GSI_AUTH
TARBALL=GSImySRB4Linux.tar
else
TARBALL=mySRB4Linux.tar
endif
endif

LDADD+=-lpthread

CFLAGS=$(MY_CFLAG)
CFLAGS+= -D$(PORTNAME)

CFLAGS+=-I./include -I$(SRBDIR)/src/include -I$(SRBDIR)/src/catalog/include -I$(SRBDIR)/utilities/include

ifdef SEA_AUTH
CFLAGS+= -DSEA_AUTH
LDADD+= $(LIB_SEA)
endif

LIB_OBJECTS = ds_helper.o srb_helper.o misc_helper.o source.o
RO_OBJECTS = $(LIB_OBJECTS) SRB_synch_orbregistries.o 
TEST_OBJECTS = test.o

all: SRB_synch_orbregistries test.exe

SRB_synch_orbregistries: $(RO_OBJECTS)
	$(CC) $(RO_OBJECTS) -o SRB_synch_orbregistries $(LDADD)
test.exe: $(TEST_OBJECTS)
	$(CC) $(TEST_OBJECTS) -o test.exe $(LDADD)
SRB_synch_orbregistries.o: SRB_synch_orbregistries.c
	$(CC) -c SRB_synch_orbregistries.c $(CFLAGS)
ds_helper.o: ds_helper.c
	$(CC) -c ds_helper.c $(CFLAGS)
srb_helper.o: srb_helper.c
	$(CC) -c srb_helper.c $(CFLAGS)	
misc_helper.o: misc_helper.c
	$(CC) -c misc_helper.c $(CFLAGS)
source.o: source.c
	$(CC) -c source.c $(CFLAGS)			
test.o: test.c
	$(CC) -c test.c $(CFLAGS)
clean:
	rm -f *.exe *.o 	
