BIN = orb3d		
DATADIR = orb3d
DATA = data/tripod.iv \
       data/grid.iv	
INCLUDE =
PF = orb3d.pf

MAN1= orb3d.1

CLEAN= 	

COINFLAGS = -I/home/atul/Coin-2.3.0/include
COINLIBS = -L/home/atul/Coin-2.3.0/src/.libs -Wl,-rpath,/home/atul/Coin-2.3.0/src/.libs -lCoin 
GRAPHICSLIBS = -lglut -lXi -lXmu -lXext -lXt -lGL -lGLU

cflags=  -m32 -Wno-deprecated  -I./include -I/usr/local/include -I/usr/include	$(COINFLAGS)
ldflags= -L/usr/lib
ldlibs= -lbrttpkt -lbrttutil $(DBLIBS) $(ORBLIBS) $(COINLIBS) $(X11LIBS) $(GRAPHICSLIBS)

include $(ANTELOPEMAKE)  	

CXX = g++ 
DIRS=	

OBJS= \
	CUtil.o \
	CSearch.o \
	CAnimConfig.o \
	CText.o \
	CTimeTick.o \
	CChannel.o \
	CParticle.o \
	CSeismometer.o \
	CWindow.o \
	wv_graphics_start.o \
	orb3d.o

$(BIN) : $(OBJS) 
	$(RM) $@
	$(CXX) $(CCFLAGS) -o $@ $(OBJS) $(LDFLAGS) $(LDLIBS)

TESTOBJS= \
	wv_nographics_start.o \
	orb3d_test.o

test : $(TESTOBJS)
	$(RM) $(BIN)
	$(CXX) $(CCFLAGS) -D NOGRAPHICS -o $(BIN) $(TESTOBJS) $(LDFLAGS) $(LDLIBS)

orb3d_test.o: orb3d.cxx
	$(CXX) $(CXXFLAGS) -D NOGRAPHICS -o $@ -c orb3d.cxx


CXXFLAGS += $(DBG) $(cflags) $(CEXTRA) -I$(XINCLUDE) $(DCFLAGS)

.SUFFIXES: .SUFFIXES .cxx .cpp

.cpp.o :
	$(CXX) $(CXXFLAGS) -c $<

.cxx.o :
	$(CXX) $(CXXFLAGS) -c $<
