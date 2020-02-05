DATADIR = python/anf
DATA  = __init__.py
DATA += eloghandler.py
DATA += str2bool.py
DATA += logutil.py
DATA += orbpfparser.py

MAN3Y = pythoneloghandler.3y

include $(ANFMAKE)

test: install
	python -m unittest discover -s test

DIRS =
