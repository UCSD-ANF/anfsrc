DATADIR=system
DATA= envrc \
      aliasrc \
      tcsh_properties \
      tcshrc_default \
      windowbars

CLEAN= tcshrc_default 

include $(ANFMAKE)

tcshrc_default: tcshrc_default.id
	getid < tcshrc_default.id > tcshrc_default
