DATA= __init__.pyc\
	  ant.pyc\
	  core.pyc\
	  scec.pyc\
	  cython_module.so

DATADIR= python/anf/loctools3D

CLEAN = *.pyc\
		cython_module.so\
		cython_module.c\

cython_module.so: cython_module.c

cython_module.c: cython_module.pyx
	python setup.py build_ext --inplace && mv loctools3D/cython_module.so . && rm -rf loctools3D build cython_module.c

include $(ANFMAKE)
