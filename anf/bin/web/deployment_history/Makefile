PF= usarray_deploy_map.pf

#MAN1=

BIN  = usarray_deploy_map
BIN += mk_deployment_movies

# Insert dummy rule for .sh files
.sh :
	$(RM) $@
	cp -f $*.sh $@

include $(ANFMAKE)
# Don't process any subdirs
DIRS =
