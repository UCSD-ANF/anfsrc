QUANTA_THREAD_TYPE=pthreads
include /home/atul/QUANTA_0.2/include/QUANTA_APPLICATION_INCLUDES

BIN= wiggleview

MAN1=

CLEAN=


INVENTOR_LIB = /home/atul/install/lib
INVENTOR_INC = /home/atul/install/include

SIMAGE_LIB = /home/atul/install/lib
SIMAGE_INC = /home/atul/install/include

GLUT_LIB = /usr/X11R6/lib
GLUT_INC = /usr/X11R6/include

QUANTA_LIB = /home/atul/QUANTA_0.2/src
QUANTA_INC = /home/atul/QUANTA_0.2/include

LIBS = -L. -L$(INVENTOR_LIB) -L$(SIMAGE_LIB) -L$(GLUT_LIB) -L$(QUANTA_LIB)  -L/usr/X11/lib -L/usr/lib -L/usr/X11R6/lib
INCL = -I$(INVENTOR_INC) -I$(SIMAGE_INC) -I$(GLUT_INC) -I$(QUANTA_INC) -I../include -I../include/antelope -I/usr/include

#LIBS = -L. -L$(INVENTOR_LIB) -L$(SIMAGE_LIB) -L$(GLUT_LIB)  -L/usr/X11/lib -L/usr/lib -L/usr/X11R6/lib
#INCL = -I$(INVENTOR_INC) -I$(SIMAGE_INC) -I$(GLUT_INC) -I../include -I../include/antelope -I/usr/include

ALL_LIB = $(LIBS) -lCoin -lglut -lsimage -lquanta_32 \
	-lXext -lXmu -lXt -lGL -lGLU \
	-lm -lpthread

cflags= $(INCL) $(QUANTA_CFLAGS) -Wno-deprecated
fflags=
ldflags=
ldlibs= $(ORBLIBS)
include $(ANTELOPEMAKE)
CC=g++
STOCKLIBS=-lcoords -lstock $(NSLLIBS) -lm -lrt -lpthread
DBLIBS=-lds -ltrvltm -lresponse $(STOCKLIBS)
GPLLIBS=-lgpl -lol -ltks -lgrx $(X11LIBS)
TRLIBS=-ltr $(DBLIBS) 
ORBLIBS=-lxtra -lPkt -lforb -lorb $(TRLIBS) $(ALL_LIB)
DIRS=

OBJS= CAnimConfig.o  CAnimControl.o CUtil.o CSearch.o CText.o CSeismometer.o CSeismogram.o CChannel.o CParticle.o CTimer.o CServer.o wiggleview.o
#default: $(BIN)
#.cxx.o:
#	$(CXX) $(CFLAG) $(INCL) -o $@ $<

$(BIN) : $(OBJS)
	$(RM) $@
	$(CC) $(CFLAGS) -o $@ $(OBJS) $(LDFLAGS) $(LDLIBS)

