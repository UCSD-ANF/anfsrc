# Makefile to install Python modules under $ANF
#
# Requires installation of pip package installer
# http://pypi.python.org/pypi/pip

EASY_INSTALL = /opt/local/bin/easy_install-2.7
PYTHON_INSTALL_DIR = $(ANF)/lib/python2.7/site-packages

all_modules : beautifulsoup pyflickr twisted matplotlib numpy obspycore obspymseed obspymsac obspygse obspyimaging

beautifulsoup : $(PYTHON_INSTALL_DIR)
	$(EASY_INSTALL) -v --prefix $(ANF) BeautifulSoup

pyflickr : $(PYTHON_INSTALL_DIR)
	$(EASY_INSTALL) -v --prefix $(ANF) flickrapi

twisted : $(PYTHON_INSTALL_DIR)
	$(EASY_INSTALL) -v --prefix $(ANF) twisted

matplotlib : $(PYTHON_INSTALL_DIR)
	$(EASY_INSTALL) -v --prefix $(ANF) matplotlib

numpy : $(PYTHON_INSTALL_DIR)
	$(EASY_INSTALL) -v --prefix $(ANF) numpy

obspycore : $(PYTHON_INSTALL_DIR)
	$(EASY_INSTALL) -v -N --prefix $(ANF) obspy.core

obspymseed : $(PYTHON_INSTALL_DIR)
	$(EASY_INSTALL) -v -N --prefix $(ANF) obspy.mseed

obspymsac : $(PYTHON_INSTALL_DIR)
	$(EASY_INSTALL) -v -N --prefix $(ANF) obspy.sac

obspygse : $(PYTHON_INSTALL_DIR)
	$(EASY_INSTALL) -v -N --prefix $(ANF) obspy.gse2

obspyimaging : $(PYTHON_INSTALL_DIR)
	$(EASY_INSTALL) -v -N --prefix $(ANF) obspy.imaging


$(PYTHON_INSTALL_DIR) : 
	mkdir -p $(PYTHON_INSTALL_DIR)
