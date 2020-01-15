###
### Macros
###
PYTHON_EXECUTABLE=/opt/antelope/python$(shell getid python_fullversion)/bin/python$(shell getid python_mainversion)

REQUIREMENTS=requirements-python$(shell getid python_mainversion).txt

ANF_PYTHON_LIB_DIR     = $(ANF)/lib/python$(shell getid python_mainversion)/site_packages
ANF_PYTHON_SCRIPTS_DIR = $(ANF)/bin

ENV_VAR_OVERRIDES  = PYTHONPATH=$(ANF_PYTHON_LIB_DIR) $(EXTRA_ENV_VAR_OVERRIDES)

all install Include ::
	$(ENV_VAR_OVERRIDES) pip install --prefix $(ANF) --requirement $(REQUIREMENTS)

uninstall ::
	$(ENV_VAR_OVERRIDES) pip uninstall --yes --requirement $(REQUIREMENTS)
