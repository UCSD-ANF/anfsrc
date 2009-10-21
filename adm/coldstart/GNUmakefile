coldstart: .FORCED
ifdef ANTELOPE
	$(MAKE) -f Makefile $@ 
else
	@echo "The Antelope environment is not set. In order to use coldstart, you"
	@echo "will need to set up the Antelope environment using the stock"
	@echo "BRTT-provided setup.sh or setup.csh scripts."
	@exit 1
endif

.FORCED:
