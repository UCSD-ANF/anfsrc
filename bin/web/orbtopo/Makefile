BIN = orbtopo_db map_changes
MAN1 = orbtopo.1 map_changes.1
PF = orbtopo.pf

# WEBDIR = /tmp
WEBDIR = /var/Web
WEBBIN = orbtopo.cgi \
	 orbtopo_detail.cgi

WEBFILES = $(WEBBIN) \
           orbtopo_style.css
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

