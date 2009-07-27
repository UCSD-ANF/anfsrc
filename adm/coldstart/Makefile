coldstart: .FORCED
ifdef ANTELOPE
	ANF=/opt/anf/`getid id`; export ANF; \
	ANFMAKE=/opt/anf/`getid id`/include/anfmake; export ANFMAKE; \
	( cd ../setup; make install ) ; \
	( cd ../../lib/makerules; make install ) ; \
	( cd ../..; make Include ) ; \
	mkdir /opt/anf/`getid id`/man ; \
	( cd ../..; make install )
else
	@echo "The Antelope environment is not set. In order to use coldstart, you"
	@echo "will need to set up the Antelope environment using the stock"
	@echo "BRTT-provided setup.sh or setup.csh scripts."
	@exit 1
endif

.FORCED:
