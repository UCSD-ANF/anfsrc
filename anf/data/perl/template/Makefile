
DATADIR= templates
DATA= xpl xpls.header xpls.footer

CLEAN= xpl xpls.header

include $(ANFMAKE)

# Override the Include rule so that templates get installed before scripts
# need them
Include :: DATA

% : %.id
	rm -f $@
	getid < $@.id > $@
