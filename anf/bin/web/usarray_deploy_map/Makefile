BIN=usarray_deploy_map

DATADIR=python

PF  = usarray_deploy_map.pf

CLEAN = *.pyc

include $(ANFMAKE)

test: install
	pfverify -v
	python -m unittest discover -s test_anf_deploymentmap


DIRS = anf
