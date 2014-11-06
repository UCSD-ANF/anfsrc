DATA= __init__.pyc\
	  ant.pyc\
	  core.pyc\
	  scec.pyc\
	  cython_module.so

DATADIR= python/anf/loctools3D

CLEAN = *.pyc\
		cython_module.so\
		cython_module.c\

PYTHON_EXECUTABLE=/opt/antelope/$(shell getid python)/bin/python
ANF_PYTHON_LIB_DIR = $(ANF)/lib/python
ENV_VAR_OVERRIDES  = PYTHONPATH=$(ANF_PYTHON_LIB_DIR) $(EXTRA_ENV_VAR_OVERRIDES)

include $(ANFMAKE)
cython_module.so: cython_module.c

cython_module.c: cython_module.pyx
	$(ENV_VAR_OVERRIDES) $(PYTHON_EXECUTABLE) setup.py build_ext --inplace
	mv loctools3D/cython_module.so .
	rm -rf loctools3D build cython_module.c

