BIN = orb3d		
DATADIR = orb3d
DATA = data/tripod.iv \
       data/grid.iv	
INCLUDE =
PF = orb3d.pf

MAN1= orb3d.1

CLEAN= 	

#COIN = /home/atul/Coin-2.3.0
COIN = /usr/local
COINFLAGS = -I$(COIN)/include
COINLIBS = -L$(COIN)/lib -Wl,-rpath,$(COIN)/lib -lCoin 
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

NOGRAPHICSOBJS= \
	wv_nographics_start.o \
	orb3d_nographics.o

nographics : $(NOGRAPHICSOBJS)
	$(RM) $(BIN)
	$(CXX) $(CCFLAGS) -D NOGRAPHICS -o $(BIN) $(NOGRAPHICSOBJS) $(LDFLAGS) $(LDLIBS)

orb3d_nographics.o: orb3d.cxx
	$(CXX) $(CXXFLAGS) -D NOGRAPHICS -o $@ -c orb3d.cxx


CXXFLAGS += $(DBG) $(cflags) $(CEXTRA) -I$(XINCLUDE) $(DCFLAGS)

.SUFFIXES: .SUFFIXES .cxx 

.cxx.o :
	$(CXX) $(CXXFLAGS) -c $<
