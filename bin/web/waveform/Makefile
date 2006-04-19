MAN1= waveform.cgi.1
PF = waveform.pf

WEBDIR = /tmp
#WEBDIR = /var/Web
WEBBIN = waveform.cgi 

WEBFILES = $(WEBBIN) 
CLEAN = $(WEBBIN)

include $(ANTELOPEMAKE)

DIRS=
UNINSTALL= $(WEBFILES:%=$(WEBDIR)/%)

all :: $(WEBFILES)

install :: WEBFILES 

WEBFILES :: $(WEBFILES) $(WEBFILES:%=$(WEBDIR)/%)

$(WEBDIR)/% : %
	$(INSTALL) -x $< $(WEBDIR)

# -----------------------------------------------------
# Temporary dot-rules pending upgrade to $ANTELOPEMAKE:
.SUFFIXES: .SUFFIXES .xpls

% : %.xpls $(ANTELOPE)/data/templates/xpls
	produce $@
# End Temporary
# -----------------------------------------------------

