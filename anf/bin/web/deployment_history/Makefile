PF = usarray_deploy_map.pf

MAN1 = deployment_map_python.1

BIN  = deployment_map_python \
		usarray_deploy_map \
		mk_deployment_movies

# Insert dummy rule for .sh files
.sh :
	$(RM) $@
	cp -f $*.sh $@

include $(ANFMAKE)
# Don't process any subdirs
DIRS =
