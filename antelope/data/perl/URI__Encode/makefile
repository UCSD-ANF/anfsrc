MODULENAME=URI::Encode

include $(ANTELOPEMAKE)

# Override the install and all targets to run the Include phase
all :: Include
install :: Include

# Only reinstall the requested MODULENAME if it's missing.
Include ::
	sh -c 'perl -M$(MODULENAME) -e 1 2>&1 > /dev/null || \
		cpan -if $(MODULENAME)'
