BIN= cbdeck2orb
DATADIR=
DATA=
INCLUDE=
PF=

MAN1= cbdeck2orb.1
MAN3=
MAN5=

CLEAN=

cflags= -L $(ANTELOPE)/src/vorb/lib/libuser -I $(ANTELOPE)/src/vorb/lib/libuser
fflags=
ldflags= -luser $(ORBLIBS)
ldlibs=

include $(ANTELOPEMAKE)

cbdecktest: cbdecktest.c
	cc -o cbdecktest cbdecktest.c -lnsl

