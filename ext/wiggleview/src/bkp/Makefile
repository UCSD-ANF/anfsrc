# Linux compile options
QUANTA_THREAD_TYPE=pthreads
include /usr/local/include/QUANTA/QUANTA_APPLICATION_INCLUDES

INVENTOR_LIB = /usr/local/lib
INVENTOR_INC = /usr/local/include

SIMAGE_LIB = /usr/local/lib
SIMAGE_INC = /usr/local/include

GLUT_LIB = /home/atul/glut-3.7/lib/glut
GLUT_INC = /home/atul/glut-3.7/include

QUANTA_LIB = /usr/local/lib
QUANTA_INC = /usr/local/include/QUANTA

LIBS = -L. -L$(INVENTOR_LIB) -L$(SIMAGE_LIB) -L$(GLUT_LIB) -L$(QUANTA_LIB)  -L/usr/X11/lib -L/usr/lib -L/usr/X11R6/lib
INCL = -I$(INVENTOR_INC) -I$(SIMAGE_INC) -I$(GLUT_INC) -I$(QUANTA_INC) -I../include -I/usr/include

OPT = -g
CXX = g++

ALL_LIB = $(LIBS) -lCoin -lglut -lsimage -lquanta_32 \
	-lXext -lXmu -lXt -lGL -lGLU \
	-lm -lpthread 


TARGET = wiggleview

ifeq ($(debug),1)
  DEBUG_MODE = -DDEBUG
endif
ifeq ($(bbox),1)
  USE_BBOX = -DMANIP_BBOX
endif

CFLAG = $(OPT) -c $(DEBUG_MODE)  $(USE_BBOX) -DLINUX  $(QUANTA_CFLAGS)
LFLAG = $(OPT)


OBJS = \
  CAnimConfig.o \
  CAnimControl.o \
  CUtil.o \
  CSearch.o \
  CText.o \
  CSeismometer.o \
  CSeismogram.o \
  CChannel.o \
  CParticle.o \
  CTimer.o \
  CServer.o \
  wiggleview.o

SOURCES = $(OBJS:.o=.cxx)

.SUFFIXES:
.SUFFIXES: .cxx .o .h .hxx

default: $(TARGET)
.cxx.o:
	$(CXX) $(CFLAG) $(INCL) -o $@ $<

wiggleview: $(OBJS)
	$(CXX) $(LFLAG) -o $@ $(OBJS) $(ALL_LIB)

clean:
	rm -rf *.o $(TARGET) ii_files depends.mk

depends:
	echo 'Generating depends.mk'
	$(CXX) -M $(INCL) ${SOURCES} >> depends.mk

sinclude depends.mk
