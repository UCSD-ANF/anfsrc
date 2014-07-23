
DATADIR= templates
DATA= xpy

CLEAN= xpy

include $(ANFMAKE)

# Override the Include rule so that templates get installed before scripts
# need them
Include :: DATA

xpy: xpy.id
	rm -f $@
	getid < $@.id > $@
