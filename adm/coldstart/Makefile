coldstart: .FORCED
	ANF=/opt/anf/`getid id`; export ANF; \
	ANFMAKE=/opt/anf/`getid id`/include/anfmake; export ANFMAKE; \
	( cd ../setup; make install ) ; \
	( cd ../../anf/lib/makerules; make install ) ; \
	( cd ../..; make Include ) ; \
	mkdir -p /opt/anf/`getid id`/man ; \
	( cd ../..; make install )

.FORCED:
