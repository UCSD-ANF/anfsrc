# Makefile to install Python modules under $ANF
#
# Requires installation of pip package installer
# http://pypi.python.org/pypi/pip

EASY_INSTALL       = $(ANTELOPE)/local/bin/python -m easy_install
EASY_INSTALL_ARGS  = -d $(PYTHON_LIB_DIR) -s $(PYTHON_SCRIPTS) -N
PYTHON_LIB_DIR     = $(ANF)/lib/python
PYTHON_SCRIPTS_DIR = $(ANF)/bin

PY_MODULES += BeautifulSoup
PY_MODULES += flickrapi
PY_MODULES += twisted
PY_MODULES += numpy
PY_MODULES += matplotlib
PY_MODULES += obspy.core
PY_MODULES += obspy.mseed
PY_MODULES += obspy.sac
PY_MODULES += obspy.gse2
PY_MODULES += obspy.imaging

all_modules : $(PY_MODULES)

BeautifulSoup : $(PYTHON_LIB_DIR)
	$(EASY_INSTALL) $(EASY_INSTALL_ARGS) $@

flickrapi : $(PYTHON_LIB_DIR)
	$(EASY_INSTALL) $(EASY_INSTALL_ARGS) $@

twisted : $(PYTHON_LIB_DIR)
	$(EASY_INSTALL) $(EASY_INSTALL_ARGS) $@

matplotlib : $(PYTHON_LIB_DIR)
	$(EASY_INSTALL) $(EASY_INSTALL_ARGS) $@

numpy : $(PYTHON_LIB_DIR)
	$(EASY_INSTALL) $(EASY_INSTALL_ARGS) $@

freetype : $(PYTHON_LIB_DIR)
	$(EASY_INSTALL) $(EASY_INSTALL_ARGS) $@

obspy.core : $(PYTHON_LIB_DIR)
	$(EASY_INSTALL) $(EASY_INSTALL_ARGS) $@

obspy.mseed : $(PYTHON_LIB_DIR)
	$(EASY_INSTALL) $(EASY_INSTALL_ARGS) $@

obspy.sac : $(PYTHON_LIB_DIR)
	$(EASY_INSTALL) $(EASY_INSTALL_ARGS) $@

obspy.gse2 : $(PYTHON_LIB_DIR)
	$(EASY_INSTALL) $(EASY_INSTALL_ARGS) $@

obspy.imaging : $(PYTHON_LIB_DIR)
	$(EASY_INSTALL) $(EASY_INSTALL_ARGS) $@


$(PYTHON_LIB_DIR) : 
	@echo "Creating Python Library Dir $(PYTHON_LIB_DIR)
	mkdir -p $(PYTHON_LIB_DIR)
