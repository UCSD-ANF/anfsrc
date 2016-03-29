BIN=xvfbwrap
# This intermediate build step is necessary to keep the built-in Antelope
# clean target from removing the xvfbwrap executable
% : %.bash
	cp -f $@.bash $@ && chmod +x $@
include $(ANFMAKE)
