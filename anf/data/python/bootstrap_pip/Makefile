PIP_BIN = /opt/antelope/python$(shell getid python_fullversion)/bin/pip)

all install: Include

Include: PIP_BIN

get-pip.py:
	curl -O https://bootstrap.pypa.io/get-pip.py

PIP_BIN: get-pip.py
	/usr/bin/env python get-pip.py

update-get-pip:: get-pip.py FORCED

FORCED:
