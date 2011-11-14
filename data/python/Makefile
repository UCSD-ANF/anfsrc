OS=$(shell getid os)
GMAKE_SunOS = gmake
GMAKE_Darwin = make
GMAKE_Linux = make
GMAKE_PLATFORM = GMAKE_$(OS)

all:
	/bin/bash -c "\
	  if [[ `getid os` == 'SunOS' ]]; then \
	    if [[ -e /opt/csw/bin/gmake ]] ; then \
	      gmake -f GNUmakefile;\
	    else \
	      echo \"Can't find gmake on this SunOS system. The python bindings require GNU Make in order to run properly.\" && exit 1; \
	    fi;\
	  else $(MAKE) -f GNUmakefile; fi
