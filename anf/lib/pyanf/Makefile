DATADIR = python/anf

DATA = $(filter-out setup.py, $(wildcard *.py))

CLEAN = testrunner

MAN3Y = pythoneloghandler.3y

include $(ANFMAKE)

test: testrunner FORCE
	@echo Running Python Tests:
	@./testrunner

DIRS = anf

FORCE:
