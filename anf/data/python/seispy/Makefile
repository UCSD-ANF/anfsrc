DATA= __init__.pyc\
	  segd.pyc\
	  trmath.so

DATADIR= python/seispy

CLEAN = *.pyc

include $(ANFMAKE)

trmath.so: trmath.c
	python setup.py build && mv build/lib*/trmath.so . && rm -rf build
