DATA  = __init__.py
DATA += segd.py
DATA += trmath.so

DATADIR= python/seispy

CLEAN = trmath.so

include $(ANFMAKE)

# Don't try to build any subdirectories
DIRS =

trmath.so: trmath.c
	python setup.py build && cp build/lib*/trmath.*.so ./trmath.so

# Clean up python after build process
clean ::
	@-$(RM) -rf build
