QUANTA_THREAD_TYPE=pthreads
include /usr/local/include/QUANTA/QUANTA_APPLICATION_INCLUDES

BIN= wiggleview

MAN1=

CLEAN=


INVENTOR_LIB = /usr/local/lib
INVENTOR_INC = /usr/local/include

SIMAGE_LIB = /usr/local/lib
SIMAGE_INC = /usr/local/include

GLUT_LIB = /usr/lib
GLUT_INC = /usr/include/GL

QUANTA_LIB = /usr/local/lib
QUANTA_INC = /usr/local/include/QUANTA/include

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

