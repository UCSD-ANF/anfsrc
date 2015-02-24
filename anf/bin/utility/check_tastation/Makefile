BIN   = check_tastation
PMAN1 = $(BIN)
CLEAN = $(BIN).pd.1
DATA  = edu.ucsd.cmd.tastation
DATADIR = intermapper/probes

include $(ANFMAKE)

% : %.id
	rm -f %
	getid < $@.id > $@
