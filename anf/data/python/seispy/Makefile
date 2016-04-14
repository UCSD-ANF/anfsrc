DATA  = __init__.pyc
DATA += segd.pyc
DATA += trmath.so

DATADIR= python/seispy

CLEAN = *.pyc trmath.so

include $(ANFMAKE)

# Don't try to build any subdirectories
DIRS =

trmath.so: trmath.c
	python setup.py build && cp build/lib*/trmath.so .

# Clean up python after build process
clean ::
	@-$(RM) -rf build
