
DATADIR= templates
DATA= xpl

CLEAN= xpl

include $(ANFMAKE)

# Override the Include rule so that templates get installed before scripts
# need them
Include :: DATA

xpl: xpl.id
	rm -f $@
	getid < $@.id > $@
