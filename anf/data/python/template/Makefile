
DATADIR= templates
DATA= xpy xpys.header xpys.footer

CLEAN  = xpy xpy.contrib xpy.nocontrib
CLEAN += xpys.header xpys.header.contrib xpys.header.nocontrib

include $(ANFMAKE)

# Override the Include rule so that templates get installed before scripts
# need them
Include :: DATA

%: %.id
	rm -f $@
	getid < $@.id > $@

xpy : xpy.nocontrib xpy.contrib
	case `getid id` in \
		5.4) cp xpy.nocontrib xpy ;; \
		* ) cp xpy.contrib xpy ;; \
		esac

xpys.header : xpys.header.nocontrib xpys.header.contrib
	case `getid id` in \
		5.4) cp xpys.header.nocontrib xpys.header ;; \
		* ) cp xpys.header.contrib xpys.header ;; \
		esac
