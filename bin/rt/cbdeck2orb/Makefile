BIN= cbdeck2orb
MAN1= cbdeck2orb.1

cflags= -I$(ANTELOPE)/src/vorb/lib/libuser
ldflags=-L$(ANTELOPE)/src/vorb/lib/libuser 
ldlibs=-luser $(ORBLIBS)

include $(ANTELOPEMAKE)

cbdecktest: cbdecktest.c
	cc -o cbdecktest cbdecktest.c -lnsl 

